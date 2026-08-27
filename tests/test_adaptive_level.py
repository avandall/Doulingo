"""
tests/test_adaptive_level.py
=============================
Unit tests for app/core/adaptive_level_detector.py (TASK-009).
"""

import os

import pytest

from app.core.adaptive_level_detector import (
    AdaptiveLevelDetector,
    ASRFeatureExtractor,
    ASRTranscriptMetrics,
    IRTLevelModel,
    get_effective_level,
)
from app.storage.db import init_db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Set up temporary SQLite database for testing."""
    test_db = str(tmp_path / "test_adaptive.db")
    monkeypatch.setattr("app.storage.db.DB_PATH", test_db)
    init_db()


class TestIRTLevelModel:
    """Test suite for Item Response Theory mathematical conversions and calculations."""

    def test_theta_to_level_mapping(self):
        assert IRTLevelModel.theta_to_level(-3.0) == 1
        assert IRTLevelModel.theta_to_level(0.0) == 10
        assert IRTLevelModel.theta_to_level(3.0) == 20

    def test_level_to_theta_mapping(self):
        assert IRTLevelModel.level_to_theta(1) == -3.0
        assert IRTLevelModel.level_to_theta(10) == -0.158
        assert IRTLevelModel.level_to_theta(20) == 3.0

    def test_level_to_cefr_and_band(self):
        assert IRTLevelModel.level_to_cefr(1) in ["Pre-A1", "A1"]
        assert IRTLevelModel.level_to_cefr(10) == "B1"
        assert IRTLevelModel.level_to_cefr(20) == "C2+"

        assert IRTLevelModel.level_to_band(1) == 4.0
        assert IRTLevelModel.level_to_band(20) == 9.0

    def test_predict_success_probability(self):
        # Equal ability and item difficulty -> 50% success probability
        p_equal = IRTLevelModel.predict_success_probability(0.0, 0.0)
        assert abs(p_equal - 0.5) < 1e-4

        # High ability vs low difficulty -> high success probability
        p_high = IRTLevelModel.predict_success_probability(2.0, -1.0)
        assert p_high > 0.9

        # Low ability vs high difficulty -> low success probability
        p_low = IRTLevelModel.predict_success_probability(-2.0, 1.0)
        assert p_low < 0.1

    def test_update_theta(self):
        # High observed score -> theta should increase
        theta_up = IRTLevelModel.update_theta(0.0, 0.0, observed_score=1.0, learning_rate=0.4)
        assert theta_up > 0.0

        # Low observed score -> theta should decrease
        theta_down = IRTLevelModel.update_theta(0.0, 0.0, observed_score=0.0, learning_rate=0.4)
        assert theta_down < 0.0


class TestASRFeatureExtractor:
    """Test suite for transcript feature extraction."""

    def test_empty_transcript(self):
        metrics = ASRFeatureExtractor.analyze_transcript("")
        assert metrics.word_count == 0
        assert metrics.wpm == 0.0
        assert metrics.item_difficulty == -3.0

    def test_simple_a1_transcript(self):
        text = "Hello I like coffee. Coffee is good."
        metrics = ASRFeatureExtractor.analyze_transcript(text, duration_sec=5.0)

        assert metrics.word_count == 7
        assert metrics.sentence_count == 2
        assert metrics.wpm == 84.0  # (7 / 5) * 60
        assert metrics.filler_count == 0
        assert metrics.item_difficulty < 1.0

    def test_advanced_c1_transcript(self):
        text = (
            "Subsequently, the dichotomy between technological innovation and human interiority "
            "presents a profound dilemma. Furthermore, modern architecture fundamentally restructures "
            "our daily aesthetic experiences in this bustling metropolis."
        )
        metrics = ASRFeatureExtractor.analyze_transcript(text, duration_sec=12.0)

        assert metrics.word_count > 20
        assert metrics.advanced_vocab_count >= 5
        assert metrics.advanced_vocab_ratio > 0.15
        assert metrics.item_difficulty > 0.5

    def test_filler_density_detection(self):
        text = "Um I think uh we should like go to the store um yeah."
        metrics = ASRFeatureExtractor.analyze_transcript(text, duration_sec=6.0)

        assert metrics.filler_count >= 3
        assert metrics.filler_density > 15.0


class TestAdaptiveLevelDetector:
    """Test suite for AdaptiveLevelDetector multi-turn level updates and persistence."""

    def test_short_transcript_guardrail(self):
        detector = AdaptiveLevelDetector()
        res = detector.update_user_level("user_test_short", "Hi yes", current_level=5)

        assert res["difficulty_adjustment"] == "hold"
        assert "too short" in res["reason"]

    def test_initial_state_defaults(self):
        detector = AdaptiveLevelDetector()
        state = detector.get_user_level_state("user_new", default_level=4)

        assert state["current_level"] == 4
        assert state["turn_count"] == 0
        assert state["history"] == []

    def test_level_promotion_on_advanced_speech(self):
        detector = AdaptiveLevelDetector(learning_rate=0.5)
        user_id = "user_adv_test"
        start_level = 3

        adv_text = (
            "Furthermore, the persistent dichotomy between empirical rationalism and philosophical inquiry "
            "represents a profoundly unhelpful intellectual fracture. Each domain when pursued to its outermost frontier "
            "inevitably reveals the indispensability of the other."
        )

        # Simulate 3 turns of high-level advanced speech
        for _ in range(3):
            res = detector.update_user_level(user_id, adv_text, duration_sec=10.0, current_level=start_level)

        assert res["turn_count"] == 3
        assert res["measured_level"] > start_level
        assert res["difficulty_adjustment"] == "increase"

    def test_get_effective_level(self):
        user_id = "user_eff_test"
        assert get_effective_level(user_id, default_level=6) == 6

        detector = AdaptiveLevelDetector()
        adv_text = (
            "Subsequently, we must analyze the paradigm shift in contemporary communication strategies "
            "with great precision and academic rigor."
        )
        detector.update_user_level(user_id, adv_text, duration_sec=8.0, current_level=6)

        effective = get_effective_level(user_id, default_level=6)
        assert isinstance(effective, int)
        assert 1 <= effective <= 20
