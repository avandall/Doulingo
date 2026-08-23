"""
Unit tests for app/user_profile_engine.py (TASK-013)
"""

import pytest

import app.storage.db as db_module
from app.storage.db import get_user_profile
from app.analytics.user_profile_engine import (
    BAND_MAX,
    BAND_MIN,
    FLOOR_ALPHA,
    compute_effective_alpha,
    update_band,
)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    test_db_path = str(tmp_path / "test_user_profile.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db_path)
    monkeypatch.setenv("TURSO_DATABASE_URL", "")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "")
    db_module.init_db()
    conn = db_module.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profile")
    conn.commit()
    conn.close()


def test_compute_effective_alpha_word_count_thresholds():
    # word_count < 5 -> factor 0.0
    alpha = compute_effective_alpha(base_alpha=0.2, word_count=4, avg_asr_confidence=0.9)
    assert alpha == 0.0

    # word_count = 7, confidence = 0.75 -> non-zero, < base_alpha
    alpha_mid = compute_effective_alpha(base_alpha=0.2, word_count=7, avg_asr_confidence=0.75)
    assert 0.0 < alpha_mid < 0.2

    # word_count >= 10, confidence >= 0.95 -> effective_alpha == base_alpha
    alpha_full = compute_effective_alpha(base_alpha=0.2, word_count=12, avg_asr_confidence=0.95)
    assert pytest.approx(alpha_full, abs=1e-5) == 0.2


def test_compute_effective_alpha_confidence_thresholds():
    # confidence < 0.6 -> factor 0.0
    alpha = compute_effective_alpha(base_alpha=0.2, word_count=15, avg_asr_confidence=0.5)
    assert alpha == 0.0

    # confidence = 0.6 -> factor 0.0
    alpha_edge = compute_effective_alpha(base_alpha=0.2, word_count=15, avg_asr_confidence=0.6)
    assert alpha_edge == 0.0

    # confidence = 0.95 -> factor 1.0
    alpha_high = compute_effective_alpha(base_alpha=0.2, word_count=15, avg_asr_confidence=0.95)
    assert pytest.approx(alpha_high, abs=1e-5) == 0.2


def test_update_band_insufficient_confidence_skips_update():
    user_id = "test_user_insufficient"
    res = update_band(
        user_id=user_id,
        raw_score=9.0,
        word_count=4,
        avg_asr_confidence=0.9,
        base_alpha=0.2,
        consecutive_skip_count=0,
    )
    assert res["updated"] is False
    assert res["new_band"] == 6.0
    assert res["consecutive_skip_count"] == 1
    assert res["effective_alpha"] == 0.0


def test_update_band_out_of_bounds_clamping():
    user_id = "test_user_clamp"
    # Extremely high raw score 15.0 -> clamped to BAND_MAX (9.0)
    res_high = update_band(
        user_id=user_id,
        raw_score=15.0,
        word_count=15,
        avg_asr_confidence=0.95,
        base_alpha=0.2,
        consecutive_skip_count=0,
    )
    assert res_high["updated"] is True
    assert BAND_MIN <= res_high["new_band"] <= BAND_MAX
    # 6.0 * 0.8 + 9.0 * 0.2 = 6.6
    assert res_high["new_band"] == 6.6

    # Extremely low raw score 1.0 -> clamped to BAND_MIN (4.0)
    res_low = update_band(
        user_id="test_user_clamp_low",
        raw_score=1.0,
        word_count=15,
        avg_asr_confidence=0.95,
        base_alpha=0.2,
        consecutive_skip_count=0,
    )
    assert res_low["updated"] is True
    assert BAND_MIN <= res_low["new_band"] <= BAND_MAX
    # 6.0 * 0.8 + 4.0 * 0.2 = 5.6
    assert res_low["new_band"] == 5.6


def test_update_band_consecutive_skips_floor_alpha():
    user_id = "test_user_floor_alpha"
    # When consecutive_skip_count >= 5 and effective_alpha would be 0.0, floor alpha is applied
    res = update_band(
        user_id=user_id,
        raw_score=8.0,
        word_count=2,  # effective_alpha = 0.0 normally
        avg_asr_confidence=0.5,  # effective_alpha = 0.0 normally
        base_alpha=0.2,
        consecutive_skip_count=5,
    )
    assert res["updated"] is True
    assert res["effective_alpha"] == FLOOR_ALPHA
    assert res["consecutive_skip_count"] == 0
    # 6.0 * 0.95 + 8.0 * 0.05 = 5.7 + 0.4 = 6.1
    assert res["new_band"] == 6.1


def test_update_band_with_sub_scores_and_db_persistence():
    user_id = "test_user_subscores"
    sub_scores = {
        "fluency": 7.5,
        "lexical": 8.0,
        "grammar": 6.5,
        "pronunciation": 7.0,
    }
    res = update_band(
        user_id=user_id,
        raw_score=7.25,
        word_count=12,
        avg_asr_confidence=0.95,
        base_alpha=0.2,
        consecutive_skip_count=0,
        sub_scores=sub_scores,
    )

    assert res["updated"] is True
    assert "fluency" in res["sub_scores"]
    assert res["sub_scores"]["fluency"] == 6.3  # 6.0 * 0.8 + 7.5 * 0.2 = 6.3
    assert res["sub_scores"]["lexical"] == 6.4  # 6.0 * 0.8 + 8.0 * 0.2 = 6.4

    # Verify persistence in DB
    profile = get_user_profile(user_id)
    assert profile["band_estimate_overall"] == res["new_band"]
    assert profile["band_fluency"] == 6.3
    assert profile["band_lexical"] == 6.4
    assert profile["band_grammar"] == 6.1
    assert profile["band_pronunciation"] == 6.2
