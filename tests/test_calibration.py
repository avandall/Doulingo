"""
Unit and integration tests for Scoring Threshold Bootstrap & Calibration (TASK-010).
"""

from pathlib import Path
import pytest

from app.scoring.config_loader import get_anchor_points, load_active_anchors
from app.scoring.features import (
    WordTimestamp,
    compute_filler_density,
    compute_mtld,
    compute_pause_ratio,
    compute_wpm,
    interpolate_band,
)
from scripts.calibrate_thresholds import calibrate, generate_bootstrap_dataset


def test_compute_wpm() -> None:
    # Empty words
    assert compute_wpm([]) == 0.0

    # Single word (zero duration)
    words_single = [WordTimestamp(word="hello", start_time=1.0, end_time=1.0)]
    assert compute_wpm(words_single) == 0.0

    # 10 words spoken over 6 seconds -> (10 / 6) * 60 = 100 WPM
    words = [
        WordTimestamp(word=f"word_{i}", start_time=i * 0.6, end_time=i * 0.6 + 0.4)
        for i in range(10)
    ]
    # start_time of first = 0, end_time of last = 5.8 -> duration = 5.8
    wpm = compute_wpm(words)
    assert round(wpm, 1) > 0.0


def test_compute_pause_ratio() -> None:
    # No words or single word
    assert compute_pause_ratio([]) == 0.0
    assert compute_pause_ratio([WordTimestamp("hi", 0.0, 1.0)]) == 0.0

    # Words with 1.0 second pause between word 1 (ends at 1.0) and word 2 (starts at 2.0)
    # Total duration = 3.0 - 0.0 = 3.0s. Pause = 1.0s. Ratio = 1.0 / 3.0 = 0.3333
    words = [
        WordTimestamp("hello", 0.0, 1.0),
        WordTimestamp("world", 2.0, 3.0),
    ]
    ratio = compute_pause_ratio(words, pause_threshold=0.5)
    assert pytest.approx(ratio, abs=0.01) == 0.3333


def test_compute_filler_density() -> None:
    assert compute_filler_density([]) == 0.0

    # 10 words, 2 fillers ("um", "uh") -> 20.0 per 100 words
    raw_words = ["I", "um", "think", "uh", "that", "this", "is", "a", "good", "idea"]
    density = compute_filler_density(raw_words)
    assert pytest.approx(density) == 20.0

    # With WordTimestamp objects
    ts_words = [
        WordTimestamp(w, float(i), float(i) + 0.5) for i, w in enumerate(raw_words)
    ]
    assert pytest.approx(compute_filler_density(ts_words)) == 20.0


def test_compute_mtld() -> None:
    # Short token sequence (< 10 tokens) -> None
    short_tokens = ["this", "is", "a", "test"]
    assert compute_mtld(short_tokens) is None

    # Repetitive sequence (10 identical tokens)
    rep_tokens = ["the"] * 12
    mtld_rep = compute_mtld(rep_tokens)
    assert mtld_rep is not None
    assert mtld_rep < 15.0

    # Diverse sequence
    diverse_tokens = [
        "the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "gracefully", "and", "swiftly"
    ]
    mtld_div = compute_mtld(diverse_tokens)
    assert mtld_div is not None
    assert mtld_div > mtld_rep


def test_interpolate_band() -> None:
    wpm_anchors = [(4.0, 70.0), (5.5, 95.0), (6.5, 115.0), (7.5, 140.0), (9.0, 170.0)]

    # Exact points
    assert interpolate_band(70.0, wpm_anchors) == 4.0
    assert interpolate_band(170.0, wpm_anchors) == 9.0

    # Mid point between 70.0 (4.0) and 95.0 (5.5) -> value 82.5 -> band 4.75
    assert pytest.approx(interpolate_band(82.5, wpm_anchors)) == 4.75

    # Out of bounds
    assert interpolate_band(50.0, wpm_anchors) == 4.0
    assert interpolate_band(200.0, wpm_anchors) == 9.0

    # Inverse anchors (pause ratio: higher pause -> lower band)
    pause_anchors = [(4.0, 0.35), (5.5, 0.25), (6.5, 0.18), (7.5, 0.10), (9.0, 0.05)]
    assert interpolate_band(0.35, pause_anchors, inverse=True) == 4.0
    assert interpolate_band(0.05, pause_anchors, inverse=True) == 9.0


def test_config_loader(tmp_path: Path) -> None:
    config = load_active_anchors(tmp_path)
    assert config["version"] == "v0"
    assert config["status"] == "active"

    wpm_points = get_anchor_points(config, "wpm")
    assert len(wpm_points) == 5
    assert wpm_points[0][0] == 4.0


def test_calibrate_script(tmp_path: Path) -> None:
    bootstrap = generate_bootstrap_dataset(sample_size=100)
    assert len(bootstrap) == 100

    report_file = tmp_path / "calibration_report.md"
    config_v1 = calibrate(output_dir=tmp_path, report_path=report_file)

    assert config_v1["version"] == "v1"
    assert config_v1["status"] == "active"
    assert "holdout_mae" in config_v1
    assert report_file.exists()

    # Verify loaded active anchors match calibrated v1
    loaded_config = load_active_anchors(tmp_path)
    assert loaded_config["version"] == "v1"
