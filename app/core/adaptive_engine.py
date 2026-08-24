"""
app/adaptive_engine.py
=======================
Multi-Armed Bandit / Adaptive Spaced Repetition Engine (TASK-021).

Provides adaptive difficulty selection via Upper Confidence Bound (UCB1) Multi-Armed Bandit
and vocabulary/grammar review scheduling via SuperMemo-2 (SM-2) Spaced Repetition.
"""

import logging
import math
import uuid
from typing import Any

from app.rag.retrieval import RetrievedDialogue, retrieve_dialogues
from app.storage.db import get_db_connection, init_db

log = logging.getLogger(__name__)

# Default Arms representing relative band offsets from user base band
DEFAULT_BANDIT_ARMS: list[float] = [-1.0, -0.5, 0.0, 0.5, 1.0]


class BanditDifficultyEngine:
    """
    UCB1 Multi-Armed Bandit for selecting optimal difficulty band offsets.
    Balances exploration of challenge/scaffold levels with exploitation of historical success.
    """

    def __init__(self, arms: list[float] | None = None, exploration_c: float = 1.0):
        self.arms = arms if arms is not None else DEFAULT_BANDIT_ARMS
        self.exploration_c = exploration_c

    def _get_user_arm_stats(self, user_id: str, conn: Any = None) -> dict[float, dict[str, float]]:
        """Fetch pull count and average reward for each arm for the specified user."""
        init_db()
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        stats: dict[float, dict[str, float]] = {
            arm: {"pull_count": 0.0, "total_reward": 0.0, "avg_reward": 0.0}
            for arm in self.arms
        }

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT arm_offset, pull_count, total_reward, avg_reward FROM user_bandit_stats WHERE user_id = ?",
                (user_id,),
            )
            rows = cursor.fetchall()
            for r in rows:
                if isinstance(r, dict):
                    row_dict = r
                elif hasattr(r, "keys"):
                    row_dict = dict(r)
                else:
                    row_dict = {
                        "arm_offset": r[0],
                        "pull_count": r[1],
                        "total_reward": r[2],
                        "avg_reward": r[3],
                    }
                offset = float(row_dict["arm_offset"])
                if offset in stats:
                    stats[offset] = {
                        "pull_count": float(row_dict["pull_count"]),
                        "total_reward": float(row_dict["total_reward"]),
                        "avg_reward": float(row_dict["avg_reward"]),
                    }
        except Exception as e:
            log.error("Failed to read user_bandit_stats: %s", e)
        finally:
            if close_conn:
                conn.close()

        return stats

    def select_difficulty_arm(
        self, user_id: str, base_band: float, conn: Any = None
    ) -> tuple[float, float]:
        """
        Selects optimal band offset arm using UCB1 algorithm.
        Returns tuple: (chosen_arm_offset, target_band_estimate) clamped between 4.0 and 9.0.
        """
        stats = self._get_user_arm_stats(user_id, conn=conn)
        total_pulls = sum(st["pull_count"] for st in stats.values())

        # If any arm has 0 pulls, select an unpulled arm first for initial exploration
        unpulled = [arm for arm, st in stats.items() if st["pull_count"] == 0]
        if unpulled:
            chosen_arm = unpulled[0]
        else:
            best_score = -float("inf")
            chosen_arm = self.arms[0]

            for arm, st in stats.items():
                n_i = st["pull_count"]
                avg_r = st["avg_reward"]
                # UCB1 score calculation
                bonus = self.exploration_c * math.sqrt(math.log(total_pulls + 1) / n_i)
                ucb_score = avg_r + bonus

                if ucb_score > best_score:
                    best_score = ucb_score
                    chosen_arm = arm

        target_band = max(4.0, min(9.0, base_band + chosen_arm))
        return chosen_arm, target_band

    def update_arm_reward(
        self, user_id: str, arm_offset: float, reward: float, conn: Any = None
    ) -> dict[str, float]:
        """
        Updates reward statistics for the specified arm_offset and user_id.
        Reward is expected to be normalized (e.g. between 0.0 and 1.0).
        """
        init_db()
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        updated_stat = {"pull_count": 1.0, "total_reward": reward, "avg_reward": reward}

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pull_count, total_reward FROM user_bandit_stats WHERE user_id = ? AND arm_offset = ?",
                (user_id, arm_offset),
            )
            r = cursor.fetchone()

            if r:
                if isinstance(r, dict):
                    old_pulls = float(r["pull_count"])
                    old_reward = float(r["total_reward"])
                elif hasattr(r, "keys"):
                    old_dict = dict(r)
                    old_pulls = float(old_dict["pull_count"])
                    old_reward = float(old_dict["total_reward"])
                else:
                    old_pulls = float(r[0])
                    old_reward = float(r[1])

                new_pulls = old_pulls + 1.0
                new_total = old_reward + reward
                new_avg = new_total / new_pulls

                cursor.execute(
                    """
                    UPDATE user_bandit_stats
                    SET pull_count = ?, total_reward = ?, avg_reward = ?, updated_at = datetime('now')
                    WHERE user_id = ? AND arm_offset = ?
                    """,
                    (new_pulls, new_total, new_avg, user_id, arm_offset),
                )
                updated_stat = {
                    "pull_count": new_pulls,
                    "total_reward": new_total,
                    "avg_reward": new_avg,
                }
            else:
                cursor.execute(
                    """
                    INSERT INTO user_bandit_stats (user_id, arm_offset, pull_count, total_reward, avg_reward, updated_at)
                    VALUES (?, ?, 1, ?, ?, datetime('now'))
                    """,
                    (user_id, arm_offset, reward, reward),
                )

            conn.commit()
        except Exception as e:
            log.error("Failed to update user_bandit_stats: %s", e)
        finally:
            if close_conn:
                conn.close()

        return updated_stat


class SpacedRepetitionEngine:
    """
    SuperMemo-2 (SM-2) inspired Spaced Repetition engine for scheduling vocabulary and grammar review.
    """

    def add_item(
        self,
        user_id: str,
        item_id: str,
        item_text: str,
        item_type: str = "vocabulary",
        conn: Any = None,
    ) -> dict[str, Any]:
        """Adds a new vocabulary or grammar item to user spaced repetition schedule."""
        init_db()
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        rec_id = f"sr_{uuid.uuid4().hex[:12]}"
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO user_spaced_repetition (
                    id, user_id, item_id, item_text, item_type, easiness_factor,
                    interval_days, repetitions, next_review_at, created_at
                ) VALUES (?, ?, ?, ?, ?, 2.5, 1, 0, datetime('now'), datetime('now'))
                """,
                (rec_id, user_id, item_id, item_text, item_type),
            )
            conn.commit()
        except Exception as e:
            log.error("Failed to add spaced repetition item: %s", e)
        finally:
            if close_conn:
                conn.close()

        return {
            "id": rec_id,
            "user_id": user_id,
            "item_id": item_id,
            "item_text": item_text,
            "item_type": item_type,
            "easiness_factor": 2.5,
            "interval_days": 1,
            "repetitions": 0,
        }

    def get_due_items(
        self, user_id: str, limit: int = 5, conn: Any = None
    ) -> list[dict[str, Any]]:
        """Retrieves items due for review (next_review_at <= current timestamp)."""
        init_db()
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        items: list[dict[str, Any]] = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, item_id, item_text, item_type, easiness_factor,
                       interval_days, repetitions, next_review_at
                FROM user_spaced_repetition
                WHERE user_id = ? AND next_review_at <= datetime('now')
                ORDER BY next_review_at ASC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            for r in rows:
                if isinstance(r, dict):
                    row_dict = r
                elif hasattr(r, "keys"):
                    row_dict = dict(r)
                else:
                    row_dict = {
                        "id": r[0],
                        "user_id": r[1],
                        "item_id": r[2],
                        "item_text": r[3],
                        "item_type": r[4],
                        "easiness_factor": r[5],
                        "interval_days": r[6],
                        "repetitions": r[7],
                        "next_review_at": r[8],
                    }
                items.append(
                    {
                        "id": row_dict["id"],
                        "user_id": row_dict["user_id"],
                        "item_id": row_dict["item_id"],
                        "item_text": row_dict["item_text"],
                        "item_type": row_dict["item_type"],
                        "easiness_factor": float(row_dict["easiness_factor"]),
                        "interval_days": int(row_dict["interval_days"]),
                        "repetitions": int(row_dict["repetitions"]),
                        "next_review_at": str(row_dict["next_review_at"]),
                    }
                )
        except Exception as e:
            log.error("Failed to fetch due spaced repetition items: %s", e)
        finally:
            if close_conn:
                conn.close()

        return items

    def record_performance(
        self, user_id: str, item_id: str, quality: int, conn: Any = None
    ) -> dict[str, Any]:
        """
        Updates SM-2 review parameters based on user recall quality rating (0-5 scale).
          0: Blackout, 1: Wrong, 2: Heavy difficulty, 3: Normal difficulty, 4: Good recall, 5: Perfect recall.
        """
        init_db()
        q = max(0, min(5, quality))

        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        result = {
            "item_id": item_id,
            "quality": q,
            "new_interval": 1,
            "new_ef": 2.5,
            "repetitions": 0,
        }

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, easiness_factor, interval_days, repetitions
                FROM user_spaced_repetition
                WHERE user_id = ? AND item_id = ?
                """,
                (user_id, item_id),
            )
            r = cursor.fetchone()

            if not r:
                # Add item dynamically if not existing
                self.add_item(user_id, item_id, item_id, conn=conn)
                old_ef = 2.5
                old_interval = 1
                old_reps = 0
            else:
                if isinstance(r, dict):
                    old_ef = float(r["easiness_factor"])
                    old_interval = int(r["interval_days"])
                    old_reps = int(r["repetitions"])
                elif hasattr(r, "keys"):
                    d = dict(r)
                    old_ef = float(d["easiness_factor"])
                    old_interval = int(d["interval_days"])
                    old_reps = int(d["repetitions"])
                else:
                    old_ef = float(r[1])
                    old_interval = int(r[2])
                    old_reps = int(r[3])

            # SM-2 Algorithm calculation
            if q >= 3:
                if old_reps == 0:
                    new_interval = 1
                elif old_reps == 1:
                    new_interval = 6
                else:
                    new_interval = math.ceil(old_interval * old_ef)
                new_reps = old_reps + 1
            else:
                new_interval = 1
                new_reps = 0

            # Calculate new Easiness Factor (EF)
            new_ef = old_ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            new_ef = max(1.3, new_ef)

            cursor.execute(
                """
                UPDATE user_spaced_repetition
                SET easiness_factor = ?, interval_days = ?, repetitions = ?,
                    next_review_at = datetime('now', '+' || ? || ' days')
                WHERE user_id = ? AND item_id = ?
                """,
                (new_ef, new_interval, new_reps, new_interval, user_id, item_id),
            )
            conn.commit()

            result = {
                "item_id": item_id,
                "quality": q,
                "new_interval": new_interval,
                "new_ef": round(new_ef, 3),
                "repetitions": new_reps,
            }
        except Exception as e:
            log.error("Failed to record performance for SR item: %s", e)
        finally:
            if close_conn:
                conn.close()

        return result


def recommend_adaptive_pool(
    user_id: str,
    topic_tags: list[str] | str,
    base_band: float,
    query_embedding: list[float] | None = None,
    limit: int = 4,
    conn: Any = None,
) -> dict[str, Any]:
    """
    Unified Adaptive Engine recommendation:
      1. Uses BanditDifficultyEngine to pick adaptive band offset.
      2. Uses SpacedRepetitionEngine to retrieve due review vocabulary/grammar items.
      3. Calls retrieve_dialogues to select target dialogue samples matching adaptive band window.
    """
    bandit = BanditDifficultyEngine()
    sr = SpacedRepetitionEngine()

    arm_offset, target_band = bandit.select_difficulty_arm(user_id, base_band, conn=conn)

    # Compute band window centered around target_band
    band_min = max(4.0, target_band - 0.5)
    band_max = min(9.0, target_band + 1.0)

    due_items = sr.get_due_items(user_id, limit=5, conn=conn)

    dialogues: list[RetrievedDialogue] = retrieve_dialogues(
        user_id=user_id,
        topic_tags=topic_tags,
        band_min=band_min,
        band_max=band_max,
        query_embedding=query_embedding,
        limit=limit,
        conn=conn,
    )

    return {
        "user_id": user_id,
        "base_band": base_band,
        "chosen_arm_offset": arm_offset,
        "target_band": target_band,
        "band_window": (band_min, band_max),
        "due_spaced_repetition_items": due_items,
        "dialogues": dialogues,
    }
