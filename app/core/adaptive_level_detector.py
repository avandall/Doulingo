"""
app/core/adaptive_level_detector.py
===================================
ASR Adaptive Level Detector using Item Response Theory (IRT Model) (TASK-009).

Analyzes spoken user transcripts from ASR (speech rate/WPM, utterance length/MLU,
lexical diversity, filler density, vocabulary complexity) to dynamically estimate
and update the user's actual CEFR level (Levels 1-20 / Pre-A1 to C2+) using an IRT
Rasch (1PL/2PL) model after every few turns.

Provides:
  - ASRTranscriptMetrics: dataclass for speech transcript feature extraction.
  - IRTLevelModel: 1PL/2PL Item Response Theory mathematical mapping engine.
  - AdaptiveLevelDetector: core class managing user level state, updates & dynamic difficulty adjustment.
  - get_effective_level: integration helper for AI Engine to query active dynamic level.
"""

import json
import logging
import math
import re
from dataclasses import asdict, dataclass
from typing import Any

from app.core.level_config import LEVEL_CONFIGS
from app.storage.db import get_db_connection, init_db

log = logging.getLogger("duolingo_speak.adaptive_level_detector")

FILLER_WORDS = {"um", "uh", "umm", "uhh", "er", "erm", "ah", "ahh", "hmm", "err"}
ADVANCED_VOCAB_MARKERS = {
    "consequently", "subsequently", "nevertheless", "furthermore", "moreover",
    "notwithstanding", "predominantly", "substantially", "simultaneously", "fundamentally",
    "inevitably", "indispensable", "paradox", "dichotomy", "aesthetic", "contemplate",
    "paradigm", "profound", "articulate", "trajectory", "resilience", "ubiquitous",
    "metropolis", "obsolescence", "encroachment", "proliferation", "epistemic", "autonomy"
}


@dataclass
class ASRTranscriptMetrics:
    """Dataclass holding extracted ASR transcript metrics."""

    word_count: int
    sentence_count: int
    duration_sec: float
    wpm: float
    mlu: float  # Mean Length of Utterance (words per sentence)
    filler_count: int
    filler_density: float  # fillers per 100 words
    unique_words: int
    ttr: float  # Type-Token Ratio
    advanced_vocab_count: int
    advanced_vocab_ratio: float  # ratio of advanced words (length >= 7 or in marker set)
    item_difficulty: float  # Item difficulty beta derived from metrics


class IRTLevelModel:
    """
    Item Response Theory (1PL/2PL Rasch Model) for language proficiency.
    Maps user theta parameter (-3.0 to +3.0) to CEFR Level (1 to 20) and IELTS Band (4.0 to 9.0).
    """

    MIN_THETA = -3.0
    MAX_THETA = 3.0
    DEFAULT_THETA = 0.0  # Level 10 (B1)

    @staticmethod
    def theta_to_level(theta: float) -> int:
        """Map IRT theta (-3.0 to +3.0) linearly to CEFR Level (1 to 20)."""
        clamped_theta = max(IRTLevelModel.MIN_THETA, min(IRTLevelModel.MAX_THETA, float(theta)))
        # Level 1 = -3.0, Level 10 = 0.0, Level 20 = +3.0
        scaled = 1.0 + ((clamped_theta - IRTLevelModel.MIN_THETA) / (IRTLevelModel.MAX_THETA - IRTLevelModel.MIN_THETA)) * 19.0
        return int(max(1, min(20, round(scaled))))

    @staticmethod
    def level_to_theta(level: int) -> float:
        """Map CEFR Level (1 to 20) to IRT theta (-3.0 to +3.0)."""
        lvl = max(1, min(20, int(level)))
        theta = IRTLevelModel.MIN_THETA + ((lvl - 1) / 19.0) * (IRTLevelModel.MAX_THETA - IRTLevelModel.MIN_THETA)
        return round(theta, 3)

    @staticmethod
    def level_to_cefr(level: int) -> str:
        """Get CEFR string label for numeric level (1-20)."""
        lvl = max(1, min(20, int(level)))
        cfg = LEVEL_CONFIGS.get(lvl, {})
        return str(cfg.get("cefr", "B1"))

    @staticmethod
    def level_to_band(level: int) -> float:
        """Map numeric level (1-20) to estimated IELTS band (4.0 to 9.0)."""
        lvl = max(1, min(20, int(level)))
        band = 4.0 + (lvl - 1) * (5.0 / 19.0)
        return round(band, 2)

    @staticmethod
    def predict_success_probability(
        theta: float, item_difficulty: float, discrimination: float = 1.0
    ) -> float:
        """
        IRT 2PL Logistic probability function:
        P(success | theta, beta, a) = 1 / (1 + exp(-a * (theta - beta)))
        """
        logit = discrimination * (theta - item_difficulty)
        # Avoid overflow in exp
        logit = max(-15.0, min(15.0, logit))
        return 1.0 / (1.0 + math.exp(-logit))

    @staticmethod
    def update_theta(
        current_theta: float,
        item_difficulty: float,
        observed_score: float,
        learning_rate: float = 0.3,
        discrimination: float = 1.0,
    ) -> float:
        """
        Update IRT theta ability parameter based on observed performance vs expected probability.
        theta_new = theta_old + learning_rate * (observed_score - P(success))
        """
        p_success = IRTLevelModel.predict_success_probability(
            current_theta, item_difficulty, discrimination
        )
        error = observed_score - p_success
        delta = learning_rate * error
        new_theta = current_theta + delta
        return max(IRTLevelModel.MIN_THETA, min(IRTLevelModel.MAX_THETA, round(new_theta, 4)))


class ASRFeatureExtractor:
    """Extracts linguistic and fluency features from ASR transcripts to measure turn difficulty and score."""

    @staticmethod
    def analyze_transcript(
        transcript: str,
        duration_sec: float | None = None,
        words_timestamps: list[Any] | None = None,
    ) -> ASRTranscriptMetrics:
        """
        Analyze transcript text and optional timing data to extract key features.
        """
        if not transcript or not transcript.strip():
            return ASRTranscriptMetrics(
                word_count=0,
                sentence_count=0,
                duration_sec=0.0,
                wpm=0.0,
                mlu=0.0,
                filler_count=0,
                filler_density=0.0,
                unique_words=0,
                ttr=0.0,
                advanced_vocab_count=0,
                advanced_vocab_ratio=0.0,
                item_difficulty=IRTLevelModel.MIN_THETA,
            )

        # Normalize text and extract tokens
        clean_text = transcript.strip()
        tokens = [t.lower().strip(".,!?\"'()[]") for t in clean_text.split() if t.strip(".,!?\"'()[]")]
        word_count = len(tokens)

        # Sentences split
        sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
        sentence_count = max(1, len(sentences))
        mlu = word_count / sentence_count

        # Estimate or use duration_sec
        if duration_sec is not None and duration_sec > 0:
            dur = float(duration_sec)
        else:
            # Heuristic estimation: average speaking speed 120 WPM (2 words per sec)
            dur = max(1.0, word_count / 2.0)

        wpm = (word_count / dur) * 60.0

        # Fillers count
        filler_count = sum(1 for t in tokens if t in FILLER_WORDS)
        filler_density = (filler_count / max(1, word_count)) * 100.0

        # Lexical diversity (TTR)
        unique_set = set(tokens)
        unique_words = len(unique_set)
        ttr = unique_words / max(1, word_count)

        # Advanced vocabulary ratio (words length >= 7 or in marker dictionary)
        adv_count = sum(1 for t in tokens if len(t) >= 7 or t in ADVANCED_VOCAB_MARKERS)
        adv_ratio = adv_count / max(1, word_count)

        # Calculate Item Difficulty (beta) of the utterance on theta scale (-3.0 to +3.0)
        # Higher MLU, WPM, TTR and Adv Ratio increase utterance difficulty
        beta_mlu = min(3.0, (mlu - 8.0) / 4.0)  # MLU 8 = 0.0, MLU 16 = 2.0
        beta_wpm = min(3.0, (wpm - 90.0) / 30.0)  # WPM 90 = 0.0, WPM 150 = 2.0
        beta_ttr = min(3.0, (ttr - 0.5) * 4.0)  # TTR 0.5 = 0.0, TTR 0.75 = 1.0
        beta_adv = min(3.0, adv_ratio * 10.0)

        item_difficulty = (0.35 * beta_mlu) + (0.25 * beta_wpm) + (0.2 * beta_ttr) + (0.2 * beta_adv)
        item_difficulty = max(IRTLevelModel.MIN_THETA, min(IRTLevelModel.MAX_THETA, round(item_difficulty, 3)))

        return ASRTranscriptMetrics(
            word_count=word_count,
            sentence_count=sentence_count,
            duration_sec=round(dur, 2),
            wpm=round(wpm, 2),
            mlu=round(mlu, 2),
            filler_count=filler_count,
            filler_density=round(filler_density, 2),
            unique_words=unique_words,
            ttr=round(ttr, 3),
            advanced_vocab_count=adv_count,
            advanced_vocab_ratio=round(adv_ratio, 3),
            item_difficulty=item_difficulty,
        )


class AdaptiveLevelDetector:
    """
    Main Detector engine for analyzing user speech and maintaining IRT dynamic level state.
    """

    def __init__(self, history_window: int = 5, learning_rate: float = 0.3):
        self.history_window = history_window
        self.learning_rate = learning_rate
        self.feature_extractor = ASRFeatureExtractor()

    def _ensure_db_table(self, conn: Any = None) -> None:
        """Create user_adaptive_level table if not exists."""
        init_db()
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_adaptive_level (
                    user_id         TEXT PRIMARY KEY,
                    current_theta   REAL DEFAULT 0.0,
                    current_level   INTEGER DEFAULT 10,
                    cefr_code       TEXT DEFAULT 'B1',
                    estimated_band  REAL DEFAULT 6.0,
                    turn_count      INTEGER DEFAULT 0,
                    history_json    TEXT DEFAULT '[]',
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except Exception as e:
            log.error("Failed to ensure user_adaptive_level table: %s", e)
        finally:
            if close_conn:
                conn.close()

    def get_user_level_state(self, user_id: str, default_level: int = 1, conn: Any = None) -> dict[str, Any]:
        """Fetch current adaptive level state for user."""
        self._ensure_db_table(conn=conn)
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        default_theta = IRTLevelModel.level_to_theta(default_level)
        default_cefr = IRTLevelModel.level_to_cefr(default_level)
        default_band = IRTLevelModel.level_to_band(default_level)

        state = {
            "user_id": user_id,
            "current_theta": default_theta,
            "current_level": default_level,
            "cefr_code": default_cefr,
            "estimated_band": default_band,
            "turn_count": 0,
            "history": [],
        }

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT current_theta, current_level, cefr_code, estimated_band, turn_count, history_json FROM user_adaptive_level WHERE user_id = ?",
                (user_id,),
            )
            r = cursor.fetchone()
            if r:
                if isinstance(r, dict):
                    row = r
                elif hasattr(r, "keys"):
                    row = dict(r)
                else:
                    row = {
                        "current_theta": r[0],
                        "current_level": r[1],
                        "cefr_code": r[2],
                        "estimated_band": r[3],
                        "turn_count": r[4],
                        "history_json": r[5],
                    }

                hist = []
                if row.get("history_json"):
                    try:
                        hist = json.loads(row["history_json"])
                    except Exception:
                        hist = []

                state = {
                    "user_id": user_id,
                    "current_theta": float(row["current_theta"]),
                    "current_level": int(row["current_level"]),
                    "cefr_code": str(row["cefr_code"]),
                    "estimated_band": float(row["estimated_band"]),
                    "turn_count": int(row["turn_count"]),
                    "history": hist,
                }
        except Exception as e:
            log.error("Failed to read user_adaptive_level: %s", e)
        finally:
            if close_conn:
                conn.close()

        return state

    def update_user_level(
        self,
        user_id: str,
        transcript: str,
        duration_sec: float | None = None,
        current_level: int = 1,
        words_timestamps: list[Any] | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """
        Process a single spoken transcript turn, update user's IRT theta parameter,
        compute dynamic CEFR level, and return evaluation details + adjustment signal.
        """
        self._ensure_db_table(conn=conn)
        state = self.get_user_level_state(user_id, default_level=current_level, conn=conn)

        # Extract features from transcript
        metrics = self.feature_extractor.analyze_transcript(
            transcript, duration_sec=duration_sec, words_timestamps=words_timestamps
        )

        # Guardrail for short utterances (<3 words)
        if metrics.word_count < 3:
            return {
                "user_id": user_id,
                "measured_level": state["current_level"],
                "measured_cefr": state["cefr_code"],
                "estimated_band": state["estimated_band"],
                "current_theta": state["current_theta"],
                "difficulty_adjustment": "hold",
                "reason": "Transcript too short (<3 words) for reliable IRT update",
                "metrics": asdict(metrics),
            }

        # Calculate observed success score S in [0.0, 1.0] based on linguistic fluency metrics
        # Criteria: Good WPM (80-140), Low Filler Density (<5%), High TTR (>0.6), Good MLU (>=8)
        score_wpm = min(1.0, metrics.wpm / 120.0)
        score_mlu = min(1.0, metrics.mlu / 12.0)
        score_filler = max(0.0, 1.0 - (metrics.filler_density / 10.0))
        score_ttr = min(1.0, metrics.ttr / 0.7)

        observed_score = (0.3 * score_wpm) + (0.3 * score_mlu) + (0.2 * score_filler) + (0.2 * score_ttr)
        observed_score = max(0.0, min(1.0, round(observed_score, 3)))

        # IRT Theta update
        old_theta = state["current_theta"]
        item_diff = metrics.item_difficulty
        new_theta = IRTLevelModel.update_theta(
            old_theta, item_diff, observed_score, learning_rate=self.learning_rate
        )

        # Dynamic Level mapping
        raw_new_level = IRTLevelModel.theta_to_level(new_theta)

        # Smooth update using rolling history window
        history = state.get("history", [])
        history.append({
            "transcript": transcript[:100],
            "word_count": metrics.word_count,
            "item_difficulty": item_diff,
            "observed_score": observed_score,
            "theta": new_theta,
            "level": raw_new_level,
        })
        history = history[-self.history_window:]

        # Rolling average level computation
        avg_theta = sum(h["theta"] for h in history) / len(history)
        smoothed_level = IRTLevelModel.theta_to_level(avg_theta)
        cefr_code = IRTLevelModel.level_to_cefr(smoothed_level)
        estimated_band = IRTLevelModel.level_to_band(smoothed_level)

        # Determine difficulty adjustment recommendation relative to target/current level
        if smoothed_level >= current_level + 1:
            adjustment = "increase"
        elif smoothed_level <= current_level - 1:
            adjustment = "decrease"
        else:
            adjustment = "hold"

        # Persist updated state to DB
        turn_count = state["turn_count"] + 1
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_adaptive_level (
                    user_id, current_theta, current_level, cefr_code,
                    estimated_band, turn_count, history_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(user_id) DO UPDATE SET
                    current_theta = excluded.current_theta,
                    current_level = excluded.current_level,
                    cefr_code = excluded.cefr_code,
                    estimated_band = excluded.estimated_band,
                    turn_count = excluded.turn_count,
                    history_json = excluded.history_json,
                    updated_at = datetime('now')
                """,
                (
                    user_id,
                    round(avg_theta, 4),
                    smoothed_level,
                    cefr_code,
                    estimated_band,
                    turn_count,
                    json.dumps(history),
                ),
            )
            conn.commit()
        except Exception as e:
            log.error("Failed to persist user_adaptive_level: %s", e)
        finally:
            if close_conn:
                conn.close()

        return {
            "user_id": user_id,
            "measured_level": smoothed_level,
            "measured_cefr": cefr_code,
            "estimated_band": estimated_band,
            "current_theta": round(avg_theta, 4),
            "observed_score": observed_score,
            "difficulty_adjustment": adjustment,
            "turn_count": turn_count,
            "metrics": asdict(metrics),
        }


def get_effective_level(user_id: str, default_level: int = 1, conn: Any = None) -> int:
    """
    Helper function for AI Engine to retrieve user's dynamically detected IRT level.
    If no history is available, falls back to static default_level.
    """
    detector = AdaptiveLevelDetector()
    state = detector.get_user_level_state(user_id, default_level=default_level, conn=conn)
    if state and state.get("turn_count", 0) > 0:
        return int(state["current_level"])
    return default_level
