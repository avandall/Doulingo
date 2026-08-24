"""
Unit tests for Cold-Start Diagnostic Probe System (TASK-014)
"""

import pytest

import app.storage.db as db_module
from app.scoring.cold_start import (
    COLD_START_ALPHA,
    COLD_START_TURNS,
    STANDARD_ALPHA,
    ColdStartManager,
    get_alpha,
    get_diagnostic_probes,
    is_cold_start,
    process_cold_start_turn,
)
from app.storage.db import get_user_profile


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    test_db_path = str(tmp_path / "test_cold_start.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db_path)
    monkeypatch.setenv("TURSO_DATABASE_URL", "")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "")
    db_module.init_db()
    conn = db_module.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profile")
    conn.commit()
    conn.close()


def test_is_cold_start_detection():
    assert COLD_START_TURNS == 3
    assert is_cold_start(0) is True
    assert is_cold_start(1) is True
    assert is_cold_start(2) is True
    assert is_cold_start(3) is False
    assert is_cold_start(10) is False


def test_get_alpha_switching():
    assert get_alpha(0) == COLD_START_ALPHA
    assert get_alpha(1) == COLD_START_ALPHA
    assert get_alpha(2) == COLD_START_ALPHA
    assert get_alpha(3) == STANDARD_ALPHA
    assert get_alpha(5) == STANDARD_ALPHA


def test_get_diagnostic_probes_fallback():
    probes = get_diagnostic_probes(limit=3)
    assert len(probes) == 3
    for p in probes:
        assert "id" in p
        assert "question" in p
        assert "topic_tag" in p
        assert "turn_type" in p
        assert p["turn_type"] == "opening"


def test_process_cold_start_turn_initial_turns():
    user_id = "cold_start_user_1"

    # Turn 0: Cold start active (alpha = 0.5)
    res_turn0 = process_cold_start_turn(
        user_id=user_id,
        turn_count=0,
        raw_score=8.0,
        word_count=12,
        avg_asr_confidence=0.95,
    )
    assert res_turn0["is_cold_start"] is True
    assert res_turn0["applied_base_alpha"] == 0.5
    # 6.0 * 0.5 + 8.0 * 0.5 = 7.0
    assert res_turn0["new_band"] == 7.0

    profile = get_user_profile(user_id)
    assert profile["band_estimate_overall"] == 7.0


def test_process_cold_start_turn_transition_to_standard():
    user_id = "cold_start_user_2"

    # Turn 2: Cold start last turn (alpha = 0.5)
    res_turn2 = process_cold_start_turn(
        user_id=user_id,
        turn_count=2,
        raw_score=8.0,
        word_count=12,
        avg_asr_confidence=0.95,
    )
    assert res_turn2["is_cold_start"] is True
    assert res_turn2["applied_base_alpha"] == 0.5

    # Turn 3: Transition to standard alpha (0.2)
    res_turn3 = process_cold_start_turn(
        user_id=user_id,
        turn_count=3,
        raw_score=8.0,
        word_count=12,
        avg_asr_confidence=0.95,
    )
    assert res_turn3["is_cold_start"] is False
    assert res_turn3["applied_base_alpha"] == 0.2


def test_cold_start_manager_class():
    manager = ColdStartManager(cold_start_turns=2, cold_start_alpha=0.6, standard_alpha=0.15)
    assert manager.is_cold_start(0) is True
    assert manager.is_cold_start(1) is True
    assert manager.is_cold_start(2) is False

    assert manager.get_alpha(0) == 0.6
    assert manager.get_alpha(2) == 0.15

    probes = manager.get_probes(limit=2)
    assert len(probes) == 2

    user_id = "cs_manager_user"
    res = manager.process_turn(
        user_id=user_id,
        turn_count=0,
        raw_score=8.0,
        word_count=10,
        avg_asr_confidence=0.95,
    )
    assert res["applied_base_alpha"] == 0.6
