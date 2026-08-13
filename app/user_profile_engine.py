"""
Dynamic User Profile & EMA Band Smoothing Engine (TASK-013)

Updates user profile band estimates using Exponential Moving Average (EMA)
weighted by word count factor and ASR confidence factor.
Only Tier 2 Scorer (or diagnostic cold-start probes) calls this engine.
"""

import logging
from typing import Any

from app.db import get_user_profile, save_user_profile

logger = logging.getLogger(__name__)

BAND_MIN: float = 4.0
BAND_MAX: float = 9.0
MAX_CONSECUTIVE_SKIPS: int = 5
FLOOR_ALPHA: float = 0.05


def compute_effective_alpha(
    base_alpha: float, word_count: int, avg_asr_confidence: float
) -> float:
    """Calculate effective EMA alpha based on response word count and ASR confidence factor.

    - word_count < 5 -> factor = 0.0
    - 5 <= word_count < 10 -> factor = (word_count - 5) / 5 (linear 0 -> 1)
    - word_count >= 10 -> factor = 1.0

    - avg_asr_confidence < 0.6 -> factor = 0.0
    - avg_asr_confidence >= 0.6 -> factor = min(1.0, (avg_asr_confidence - 0.6) / 0.35)
    """
    if word_count < 5:
        word_count_factor = 0.0
    elif word_count < 10:
        word_count_factor = (word_count - 5) / 5.0
    else:
        word_count_factor = 1.0

    if avg_asr_confidence < 0.6:
        confidence_factor = 0.0
    else:
        confidence_factor = min(1.0, (avg_asr_confidence - 0.6) / 0.35)

    effective_alpha = base_alpha * word_count_factor * confidence_factor
    return max(0.0, min(1.0, effective_alpha))


def update_band(
    user_id: str,
    raw_score: float,
    word_count: int,
    avg_asr_confidence: float,
    base_alpha: float = 0.2,
    consecutive_skip_count: int = 0,
    sub_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Update overall band estimate and sub-scores for a user using EMA.

    This function is intended to be called ONLY by Tier 2 Scorer (or cold-start probes),
    using authoritative raw_scores across 4 axes.
    """
    profile = get_user_profile(user_id)
    old_band = float(profile.get("band_estimate_overall", 6.0))

    effective_alpha = compute_effective_alpha(base_alpha, word_count, avg_asr_confidence)

    # Floor-alpha protection against band freeze after consecutive skips
    if effective_alpha == 0.0 and consecutive_skip_count >= MAX_CONSECUTIVE_SKIPS:
        effective_alpha = FLOOR_ALPHA
        logger.info(
            f"User {user_id}: floor_alpha={FLOOR_ALPHA} enforced after {consecutive_skip_count} consecutive skips"
        )

    if effective_alpha == 0.0:
        return {
            "new_band": old_band,
            "updated": False,
            "reason": "insufficient_confidence",
            "effective_alpha": 0.0,
            "consecutive_skip_count": consecutive_skip_count + 1,
            "profile": profile,
        }

    # Clamp raw_score to [BAND_MIN, BAND_MAX] before applying EMA
    raw_score_clamped = max(BAND_MIN, min(BAND_MAX, float(raw_score)))
    new_band = old_band * (1.0 - effective_alpha) + raw_score_clamped * effective_alpha
    new_band = round(max(BAND_MIN, min(BAND_MAX, new_band)), 2)

    profile["band_estimate_overall"] = new_band

    # Update sub-scores if provided
    updated_sub_scores: dict[str, float] = {}
    if sub_scores:
        for key in ["fluency", "lexical", "grammar", "pronunciation"]:
            db_key = f"band_{key}"
            if key in sub_scores:
                old_sub = float(profile.get(db_key, 6.0))
                sub_clamped = max(BAND_MIN, min(BAND_MAX, float(sub_scores[key])))
                new_sub = round(
                    max(BAND_MIN, min(BAND_MAX, old_sub * (1.0 - effective_alpha) + sub_clamped * effective_alpha)),
                    2,
                )
                profile[db_key] = new_sub
                updated_sub_scores[key] = new_sub

    updated_profile = save_user_profile(user_id, profile)

    return {
        "new_band": new_band,
        "updated": True,
        "effective_alpha": effective_alpha,
        "consecutive_skip_count": 0,
        "sub_scores": updated_sub_scores,
        "profile": updated_profile,
    }
