"""
Cold-Start Diagnostic Probe System (TASK-014)

Manages initial diagnostic probes for new users (turns 0, 1, 2) to rapidly converge
band estimates using accelerated EMA alpha (0.5), transitioning to standard alpha (0.2)
from turn 3 (4th turn) onwards.
"""

import logging
from typing import Any

from app.db import get_db_connection
from app.user_profile_engine import update_band

logger = logging.getLogger(__name__)

COLD_START_TURNS: int = 3
COLD_START_ALPHA: float = 0.5
STANDARD_ALPHA: float = 0.2

FALLBACK_PROBES: list[dict[str, Any]] = [
    {
        "id": "probe_001",
        "question": "Could you describe your hometown and what makes it special to you?",
        "topic_tag": "hometown",
        "turn_type": "opening",
        "target_band_min": 4.0,
        "target_band_max": 9.0,
    },
    {
        "id": "probe_002",
        "question": "What do you enjoy doing in your free time, and why do you like it?",
        "topic_tag": "hobbies",
        "turn_type": "opening",
        "target_band_min": 4.0,
        "target_band_max": 9.0,
    },
    {
        "id": "probe_003",
        "question": "Tell me about a memorable experience or challenge you faced recently.",
        "topic_tag": "experience",
        "turn_type": "opening",
        "target_band_min": 4.0,
        "target_band_max": 9.0,
    },
]


def is_cold_start(turn_count: int) -> bool:
    """Check if the session/user is in cold-start diagnostic phase.

    Turns 0, 1, 2 (< 3) are considered cold start.
    """
    return turn_count < COLD_START_TURNS


def get_alpha(turn_count: int) -> float:
    """Return base EMA alpha depending on whether session is in cold-start phase."""
    if is_cold_start(turn_count):
        return COLD_START_ALPHA
    return STANDARD_ALPHA


def get_diagnostic_probes(limit: int = 3) -> list[dict[str, Any]]:
    """Fetch diagnostic probe questions from database (content_units / sample_dialogues).

    Falls back to curated open-ended probes if DB query fails or returns insufficient probes.
    """
    probes: list[dict[str, Any]] = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sd.id, sd.ai_line AS question, sd.function_tag AS topic_tag, sd.band_level
            FROM sample_dialogues sd
            WHERE sd.turn_type = 'opening'
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            if isinstance(r, dict):
                row_dict = r
            elif hasattr(r, "keys"):
                row_dict = dict(r)
            else:
                cols = [col[0] for col in cursor.description]
                row_dict = dict(zip(cols, r))

            probes.append(
                {
                    "id": str(row_dict.get("id", "")),
                    "question": str(row_dict.get("question", "")),
                    "topic_tag": str(row_dict.get("topic_tag", "general")),
                    "turn_type": "opening",
                    "band_level": float(row_dict.get("band_level", 6.0)),
                }
            )
    except Exception as e:
        logger.warning(f"[ColdStart] Failed to fetch probes from DB: {e}. Using fallback probes.")

    if len(probes) < limit:
        existing_questions = {p["question"] for p in probes}
        for fb in FALLBACK_PROBES:
            if len(probes) >= limit:
                break
            if fb["question"] not in existing_questions:
                probes.append(fb)

    return probes[:limit]


class ColdStartManager:
    """Manager for cold-start diagnostic probe state and band update calculations."""

    def __init__(
        self,
        cold_start_turns: int = COLD_START_TURNS,
        cold_start_alpha: float = COLD_START_ALPHA,
        standard_alpha: float = STANDARD_ALPHA,
    ) -> None:
        self.cold_start_turns = cold_start_turns
        self.cold_start_alpha = cold_start_alpha
        self.standard_alpha = standard_alpha

    def is_cold_start(self, turn_count: int) -> bool:
        return turn_count < self.cold_start_turns

    def get_alpha(self, turn_count: int) -> float:
        if self.is_cold_start(turn_count):
            return self.cold_start_alpha
        return self.standard_alpha

    def get_probes(self, limit: int = 3) -> list[dict[str, Any]]:
        return get_diagnostic_probes(limit=limit)

    def process_turn(
        self,
        user_id: str,
        turn_count: int,
        raw_score: float,
        word_count: int,
        avg_asr_confidence: float,
        consecutive_skip_count: int = 0,
        sub_scores: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Process a conversation turn and update user band with diagnostic or standard alpha."""
        alpha = self.get_alpha(turn_count)
        result = update_band(
            user_id=user_id,
            raw_score=raw_score,
            word_count=word_count,
            avg_asr_confidence=avg_asr_confidence,
            base_alpha=alpha,
            consecutive_skip_count=consecutive_skip_count,
            sub_scores=sub_scores,
        )
        result["is_cold_start"] = self.is_cold_start(turn_count)
        result["applied_base_alpha"] = alpha
        result["turn_count"] = turn_count
        return result


def process_cold_start_turn(
    user_id: str,
    turn_count: int,
    raw_score: float,
    word_count: int,
    avg_asr_confidence: float,
    consecutive_skip_count: int = 0,
    sub_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Helper function to process cold start or standard turn update."""
    manager = ColdStartManager()
    return manager.process_turn(
        user_id=user_id,
        turn_count=turn_count,
        raw_score=raw_score,
        word_count=word_count,
        avg_asr_confidence=avg_asr_confidence,
        consecutive_skip_count=consecutive_skip_count,
        sub_scores=sub_scores,
    )
