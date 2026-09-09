"""
Unit tests for Tier 1 Real-Time Scoring Agent (`app/scoring/tier1_realtime.py`).
"""

import time

from app.scoring.features import WordTimestamp
from app.scoring.tier1_realtime import (
    AcousticMetricsInput,
    Tier1ScoreResult,
    detect_self_corrections,
    evaluate_tier1,
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


def test_detect_self_corrections():
    # Test phrase markers
    words1 = _build_words(
        [
            ("i", 0.0, 0.2),
            ("went", 0.2, 0.5),
            ("to", 0.5, 0.7),
            ("sorry", 0.7, 1.0),
            ("i", 1.0, 1.2),
            ("mean", 1.2, 1.5),
            ("the", 1.5, 1.7),
            ("store", 1.7, 2.0),
        ]
    )
    # "sorry" and "i mean"
    assert detect_self_corrections(words1) >= 2

    # Test immediate word repetition
    words2 = _build_words(
        [
            ("the", 0.0, 0.2),
            ("the", 0.2, 0.4),
            ("cat", 0.4, 0.7),
            ("sat", 0.7, 1.0),
        ]
    )
    assert detect_self_corrections(words2) == 1

    # Filler word repetition should not count as self-correction
    words3 = _build_words(
        [
            ("um", 0.0, 0.2),
            ("um", 0.2, 0.4),
            ("hello", 0.4, 0.7),
        ]
    )
    assert detect_self_corrections(words3) == 0


def test_evaluate_tier1_normal_speech():
    # 15 distinct words over 6 seconds -> 150 WPM
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

    result = evaluate_tier1(words, target_band=6.0)

    assert isinstance(result, Tier1ScoreResult)
    assert result.wpm > 100.0
    assert result.pause_ratio < 0.1
    assert result.filler_density == 0.0
    assert result.mtld is not None
    assert result.estimated_band >= 6.5
    assert result.difficulty_adjustment == "increase"
    assert result.latency_ms < 1000.0


def test_evaluate_tier1_low_fluency():
    # Slow speech, long pauses, fillers
    token_durations = [
        ("um", 0.0, 0.5),
        ("I", 0.5, 0.8),
        ("think", 1.8, 2.2),  # 1s pause
        ("uh", 3.3, 3.8),     # 1.1s pause
        ("food", 5.0, 5.5),   # 1.2s pause
        ("good", 6.8, 7.3),   # 1.3s pause
    ]
    words = _build_words(token_durations, confidence=0.9)

    result = evaluate_tier1(words, target_band=6.5)

    assert result.wpm < 80.0
    assert result.pause_ratio > 0.3
    assert result.filler_density > 10.0
    assert result.estimated_band <= 5.5
    assert result.difficulty_adjustment == "decrease"


def test_evaluate_tier1_guardrail_short_speech():
    # Only 3 words -> word_count < 5
    token_durations = [
        ("Yes", 0.0, 0.3),
        ("I", 0.4, 0.6),
        ("agree", 0.7, 1.0),
    ]
    words = _build_words(token_durations)

    result = evaluate_tier1(words, target_band=6.0)

    assert len(words) < 5
    assert result.difficulty_adjustment == "hold"


def test_evaluate_tier1_guardrail_low_confidence():
    # 10 words but low ASR confidence (0.45 < 0.6)
    token_durations = [
        ("Word", float(i) * 0.4, float(i) * 0.4 + 0.3) for i in range(10)
    ]
    words = _build_words(token_durations, confidence=0.45)

    result = evaluate_tier1(words, avg_asr_confidence=0.45, target_band=6.0)

    assert result.metrics_detail["avg_asr_confidence"] < 0.6
    assert result.difficulty_adjustment == "hold"


def test_evaluate_tier1_latency_benchmark():
    # Benchmark execution time across 50 calls
    token_durations = [
        (f"word_{i}", float(i) * 0.3, float(i) * 0.3 + 0.25) for i in range(25)
    ]
    words = _build_words(token_durations)

    latencies: list[float] = []
    for _ in range(50):
        t0 = time.perf_counter()
        evaluate_tier1(words, target_band=6.0)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    assert avg_latency < 50.0, f"Average latency too high: {avg_latency:.2f}ms"
    assert max_latency < 300.0, f"Max latency exceeded limit: {max_latency:.2f}ms"


def test_evaluate_tier1_custom_config():
    token_durations = [
        (f"word_{i}", float(i) * 0.3, float(i) * 0.3 + 0.25) for i in range(8)
    ]
    words = _build_words(token_durations)

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

    result = evaluate_tier1(words, config=custom_config, target_band=6.0)
    assert result.estimated_band >= 4.0


def test_acoustic_metrics_input_clamping():
    """
    Verifies that AcousticMetricsInput clamps extreme values:
    - pause_duration_ms > 60000 -> 60000
    - wpm > 350 -> 350
    - negative values -> 0.0
    """
    # Over-the-limit values
    inp1 = AcousticMetricsInput(pause_duration_ms=999999.0, wpm=850.0)
    assert inp1.pause_duration_ms == 60000.0
    assert inp1.wpm == 350.0

    # Negative values
    inp2 = AcousticMetricsInput(pause_duration_ms=-100.0, wpm=-50.0)
    assert inp2.pause_duration_ms == 0.0
    assert inp2.wpm == 0.0


def test_evaluate_tier1_with_acoustic_metrics():
    """
    Verifies that evaluate_tier1 incorporates validated acoustic metrics
    and falls back to ASR values if client metrics are zero or invalid.
    """
    token_durations = [
        (f"word_{i}", float(i) * 0.4, float(i) * 0.4 + 0.35) for i in range(12)
    ]
    words = _build_words(token_durations)

    # With valid client acoustic metrics
    acoustic_data = {
        "wpm": 140.0,
        "pause_duration_ms": 1200.0,
        "accumulated_voiced_duration_ms": 4000.0,
    }
    result = evaluate_tier1(words, acoustic_metrics=acoustic_data, target_band=6.0)
    assert result.wpm == 140.0
    assert result.pause_ratio > 0.0

    # With extreme out-of-bounds client acoustic metrics (should clamp safely)
    extreme_data = {
        "wpm": 9999.0,
        "pause_duration_ms": 120000.0,
    }
    res_extreme = evaluate_tier1(words, acoustic_metrics=extreme_data, target_band=6.0)
    assert res_extreme.wpm == 350.0
    assert res_extreme.pause_ratio <= 1.0

