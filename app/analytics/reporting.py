"""
Weekly Performance Reporting Engine & Hidden Scoring System (`app/reporting.py`).

Aggregates weekly performance data across 4 IELTS sub-axes:
- Fluency & Coherence
- Lexical Resource
- Grammatical Range & Accuracy
- Pronunciation

Combines evaluation history from `tier2_evaluations` table with current profile band state
from `user_profile` table to produce a comprehensive weekly performance report without
displaying real-time per-sentence scores on the main conversation UI.
"""

from typing import Any

from app.storage.db import (
    get_tier2_evaluations_history,
    get_user_profile,
    save_tier2_evaluation_record,
)


def save_tier2_evaluation(
    user_id: str,
    score_result: Any,
) -> dict[str, Any]:
    """Log a Tier 2 evaluation result (either Tier2ScoreResult object or dict) into DB history."""
    if isinstance(score_result, dict):
        fluency = score_result.get("fluency_score", 6.0)
        lexical = score_result.get("lexical_score", 6.0)
        grammar = score_result.get("grammar_score", 6.0)
        pronunciation = score_result.get("pronunciation_score", 6.0)
        raw_score = score_result.get("raw_score", 6.0)
    else:
        fluency = getattr(score_result, "fluency_score", 6.0)
        lexical = getattr(score_result, "lexical_score", 6.0)
        grammar = getattr(score_result, "grammar_score", 6.0)
        pronunciation = getattr(score_result, "pronunciation_score", 6.0)
        raw_score = getattr(score_result, "raw_score", 6.0)

    return save_tier2_evaluation_record(
        user_id=user_id,
        fluency=fluency,
        lexical=lexical,
        grammar=grammar,
        pronunciation=pronunciation,
        raw_score=raw_score,
    )


def generate_weekly_report(
    user_id: str,
    days: int = 7,
) -> dict[str, Any]:
    """Generate a detailed weekly performance report for a user.

    Aggregates Tier 2 evaluation history over `days` period and combines with user profile state.
    """
    eval_history = get_tier2_evaluations_history(user_id, days=days)
    profile = get_user_profile(user_id)

    eval_count = len(eval_history)

    if eval_count > 0:
        avg_fluency = round(
            sum(float(e["fluency_score"]) for e in eval_history) / eval_count, 2
        )
        avg_lexical = round(
            sum(float(e["lexical_score"]) for e in eval_history) / eval_count, 2
        )
        avg_grammar = round(
            sum(float(e["grammar_score"]) for e in eval_history) / eval_count, 2
        )
        avg_pronunciation = round(
            sum(float(e["pronunciation_score"]) for e in eval_history) / eval_count, 2
        )
        latest_eval = eval_history[-1]
    else:
        # Fallback to current profile bands if no history records exist yet
        avg_fluency = float(profile.get("band_fluency", 6.0))
        avg_lexical = float(profile.get("band_lexical", 6.0))
        avg_grammar = float(profile.get("band_grammar", 6.0))
        avg_pronunciation = float(profile.get("band_pronunciation", 6.0))
        latest_eval = None

    overall_band = float(profile.get("band_estimate_overall", 6.0))
    recurring_errors = profile.get("recurring_errors", [])

    # Identify strengths and weak areas across 4 axes
    axis_scores = {
        "fluency": avg_fluency,
        "lexical": avg_lexical,
        "grammar": avg_grammar,
        "pronunciation": avg_pronunciation,
    }

    sorted_axes = sorted(axis_scores.items(), key=lambda x: x[1], reverse=True)
    strongest_axis = sorted_axes[0][0]
    weakest_axis = sorted_axes[-1][0]

    # Generate actionable recommendations based on sub-axis performance
    recommendations: list[str] = []
    if avg_fluency < 6.0:
        recommendations.append(
            "Practice speaking in longer continuous phrases to improve speech flow and reduce hesitations."
        )
    else:
        recommendations.append("Maintain good pacing and focus on complex discourse markers.")

    if avg_grammar < 6.0:
        recommendations.append(
            "Focus on subject-verb agreement and subordinate clauses (because, although, which)."
        )
    else:
        recommendations.append("Incorporate more varied sentence structures naturally.")

    if avg_lexical < 6.0:
        recommendations.append("Expand topic-specific vocabulary and avoid repeating common words.")
    else:
        recommendations.append("Continue introducing precise academic & idiomatic expressions.")

    if avg_pronunciation < 6.0:
        recommendations.append("Pay attention to word stress and clear articulation of consonant endings.")

    if recurring_errors:
        error_strs = [
            e.get("error_detail", str(e)) if isinstance(e, dict) else str(e)
            for e in recurring_errors
        ]
        recommendations.append(f"Review recurring errors logged: {', '.join(error_strs[:3])}.")

    summary = (
        f"Weekly summary for user '{user_id}': {eval_count} evaluations completed over last {days} days. "
        f"Overall estimated band: {overall_band}. Strongest area: {strongest_axis} ({axis_scores[strongest_axis]}), "
        f"Target area: {weakest_axis} ({axis_scores[weakest_axis]})."
    )

    return {
        "user_id": user_id,
        "reporting_period_days": days,
        "evaluations_count": eval_count,
        "overall_band": overall_band,
        "axes_scores": {
            "fluency": avg_fluency,
            "lexical": avg_lexical,
            "grammar": avg_grammar,
            "pronunciation": avg_pronunciation,
        },
        "strongest_axis": strongest_axis,
        "weakest_axis": weakest_axis,
        "recurring_errors": recurring_errors,
        "recommendations": recommendations,
        "summary": summary,
        "latest_evaluation": latest_eval,
    }
