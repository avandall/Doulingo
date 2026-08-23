"""
tests/test_fallback_engine.py
==============================
Unit and Integration Tests for Dynamic Anti-Repetition Fallback Engine with Topic-Shift & Context Memory (TASK-002).
"""

import re

from app.ai_engine import LEVEL_CONFIGS, ai_engine


def _compute_jaccard_similarity(s1: str, s2: str) -> float:
    w1 = set(re.findall(r'\w+', s1.lower()))
    w2 = set(re.findall(r'\w+', s2.lower()))
    if not w1 or not w2:
        return 0.0
    return len(w1 & w2) / float(len(w1 | w2))


def test_10_turns_consecutive_anti_repetition():
    """Verify that running 10 consecutive turns in Fallback mode never produces identical or overly similar sentences."""
    scenario = {"id": "everyday_practice", "title": "Everyday Conversation"}
    character = {"id": "lily", "name": "Lily"}
    history = []
    responses = []

    for turn in range(10):
        user_msg = f"Turn {turn}: I want to practice speaking today."
        res = ai_engine._get_context_aware_fallback(
            scenario=scenario,
            character=character,
            user_transcript=user_msg,
            level=5,
            conversation_history=history
        )
        ai_resp = res["ai_response"]
        responses.append(ai_resp)

        # Append to history for next turn context memory
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": ai_resp})

    # Check pair-wise similarity across all 10 responses
    for i in range(len(responses)):
        for j in range(i + 1, len(responses)):
            sim = _compute_jaccard_similarity(responses[i], responses[j])
            assert sim < 0.65, f"Turn {i} and Turn {j} are too similar (Jaccard similarity={sim:.2f}):\n1: {responses[i]}\n2: {responses[j]}"
            assert responses[i] != responses[j], f"Exact duplicate found between turn {i} and turn {j}"


def test_topic_shift_detection_cooking():
    """Verify fallback detects topic shift to cooking when requested."""
    scenario = {"id": "job_interview", "title": "Job Interview Prep"}
    character = {"id": "rajesh", "name": "Rajesh"}
    user_transcript = "Let's change topic to cooking pasta at home."

    res = ai_engine._get_context_aware_fallback(
        scenario=scenario,
        character=character,
        user_transcript=user_transcript,
        level=5
    )
    ai_resp_lower = res["ai_response"].lower()

    assert any(kw in ai_resp_lower for kw in ["cooking", "food", "recipe", "dish", "culinary", "meal"]), \
        f"Fallback response did not reflect cooking topic shift: {res['ai_response']}"


def test_topic_shift_detection_travel():
    """Verify fallback detects topic shift to travel."""
    scenario = {"id": "daily_routine", "title": "Daily Routine"}
    character = {"id": "lily", "name": "Lily"}
    user_transcript = "I love traveling to beach destinations."

    res = ai_engine._get_context_aware_fallback(
        scenario=scenario,
        character=character,
        user_transcript=user_transcript,
        level=5
    )
    ai_resp_lower = res["ai_response"].lower()

    assert any(kw in ai_resp_lower for kw in ["travel", "vacation", "trip", "destination", "hotel", "beach"]), \
        f"Fallback response did not reflect travel topic shift: {res['ai_response']}"


def test_empathetic_fallback_for_negative_transcript():
    """Verify fallback gives empathetic response when user expresses sadness or distress."""
    scenario = {"id": "career_goals", "title": "Career Goals"}
    character = {"id": "lily", "name": "Lily"}
    user_transcript = "I failed my exam and I feel really sad and stressed."

    res = ai_engine._get_context_aware_fallback(
        scenario=scenario,
        character=character,
        user_transcript=user_transcript,
        level=5
    )
    ai_resp = res["ai_response"]

    assert "wonderful" not in ai_resp.lower()
    assert "exciting" not in ai_resp.lower()
    assert any(kw in ai_resp.lower() for kw in ["sorry", "challenging", "difficult", "tough", "empathize", "burden", "courage"])
    assert res["user_feedback"]["duo_reaction"] == "encouraging"


def test_confused_fallback_for_unclear_transcript():
    """Verify fallback handles user confusion gracefully."""
    scenario = {"id": "academic_discussion", "title": "Academic Research"}
    character = {"id": "rajesh", "name": "Rajesh"}
    user_transcript = "I am confused and don't know what you mean."

    res = ai_engine._get_context_aware_fallback(
        scenario=scenario,
        character=character,
        user_transcript=user_transcript,
        level=5
    )
    ai_resp_lower = res["ai_response"].lower()

    assert any(
        kw in ai_resp_lower
        for kw in ["confus", "uncertain", "doubt", "puzzl", "clarity", "clear", "wonder", "unsure", "question", "understand"]
    )


def test_level_word_count_compliance():
    """Verify word count compliance across different levels in fallback mode."""
    scenario = {"id": "everyday_chat", "title": "Everyday Practice"}
    character = {"id": "lily", "name": "Lily"}
    user_transcript = "I had a busy day working on my project."

    for level in [1, 9, 15]:
        cfg = LEVEL_CONFIGS[level]
        res = ai_engine._get_context_aware_fallback(
            scenario=scenario,
            character=character,
            user_transcript=user_transcript,
            level=level
        )
        word_count = len(res["ai_response"].split())
        assert cfg["min_words"] <= word_count <= cfg["max_words"], \
            f"Level {level} word count {word_count} not in [{cfg['min_words']}, {cfg['max_words']}]: {res['ai_response']}"
