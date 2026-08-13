"""
Unit tests for Tier 2 Deep Scoring Agent (`app/scoring/tier2_deep.py`).
"""

from app.scoring.features import WordTimestamp
from app.scoring.tier2_deep import (
    Tier2ScoreResult,
    analyze_grammar_spacy,
    compute_pronunciation_score,
    evaluate_tier2,
)


def _build_words(
    token_durations: list[tuple[str, float, float]], confidence: float = 1.0
) -> list[WordTimestamp]:
    return [
        WordTimestamp(
            word=word,
            start_time=start,
            end_time=end,
            confidence=confidence,
        )
        for word, start, end in token_durations
    ]


def test_analyze_grammar_spacy_basic():
    text = "Although environmental sustainability is challenging, we must act because the planet needs protection."
    info = analyze_grammar_spacy(text)

    assert "total_sentences" in info
    assert info["total_sentences"] >= 1
    assert "subordinate_clause_count" in info
    assert info["subordinate_clause_count"] >= 1
    assert info["clause_ratio"] > 0.0


def test_analyze_grammar_spacy_error_detection():
    text = "He go to school every day and she do not like it. I has a dream."
    info = analyze_grammar_spacy(text)

    assert info["error_count"] >= 1
    assert len(info["detected_errors"]) >= 1


def test_compute_pronunciation_score():
    words_high = _build_words([("hello", 0.0, 0.5)], confidence=0.95)
    score_high = compute_pronunciation_score(words_high)
    assert score_high >= 8.0

    words_low = _build_words([("mumble", 0.0, 0.5)], confidence=0.4)
    score_low = compute_pronunciation_score(words_low)
    assert score_low <= 6.0


def test_evaluate_tier2_normal_speech():
    token_durations = [
        ("I", 0.0, 0.3),
        ("believe", 0.35, 0.7),
        ("that", 0.75, 1.0),
        ("environmental", 1.05, 1.6),
        ("sustainability", 1.65, 2.3),
        ("is", 2.35, 2.5),
        ("one", 2.55, 2.8),
        ("of", 2.85, 3.0),
        ("the", 3.05, 3.2),
        ("most", 3.25, 3.5),
        ("pressing", 3.55, 4.0),
        ("global", 4.05, 4.5),
        ("challenges", 4.55, 5.2),
        ("we", 5.25, 5.5),
        ("face", 5.55, 6.0),
    ]
    words = _build_words(token_durations, confidence=0.95)
    transcript = "I believe that environmental sustainability is one of the most pressing global challenges we face."

    result = evaluate_tier2(words, transcript, target_band=6.0)

    assert isinstance(result, Tier2ScoreResult)
    assert 4.0 <= result.fluency_score <= 9.0
    assert 4.0 <= result.lexical_score <= 9.0
    assert 4.0 <= result.grammar_score <= 9.0
    assert 4.0 <= result.pronunciation_score <= 9.0
    assert 4.0 <= result.raw_score <= 9.0
    assert result.estimated_band == result.raw_score
    assert result.latency_ms > 0.0


def test_evaluate_tier2_low_score_speech():
    token_durations = [
        ("um", 0.0, 0.5),
        ("he", 0.5, 0.8),
        ("go", 1.8, 2.2),
        ("uh", 3.3, 3.8),
        ("store", 5.0, 5.5),
    ]
    words = _build_words(token_durations, confidence=0.5)
    transcript = "um he go uh store"

    result = evaluate_tier2(words, transcript, target_band=6.0)

    assert result.fluency_score <= 6.0
    assert result.grammar_score <= 6.5
    assert result.pronunciation_score <= 7.0
    assert result.raw_score <= 6.5


def test_evaluate_tier2_custom_config():
    token_durations = [("word", 0.0, 0.5)]
    words = _build_words(token_durations, confidence=0.9)
    transcript = "word"

    custom_config = {
        "version": "test_v1",
        "status": "active",
        "anchors": {
            "wpm": [[4.0, 50.0], [9.0, 100.0]],
            "pause_ratio": [[4.0, 0.5], [9.0, 0.0]],
            "filler_density": [[4.0, 10.0], [9.0, 0.0]],
            "mtld": [[4.0, 20.0], [9.0, 100.0]],
        },
    }

    result = evaluate_tier2(words, transcript, config=custom_config)
    assert 4.0 <= result.raw_score <= 9.0
