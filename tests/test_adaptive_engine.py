"""
tests/test_adaptive_engine.py
==============================
Unit tests for Multi-Armed Bandit / Adaptive Spaced Repetition Engine (TASK-021).
"""

import sqlite3

import pytest

from app.adaptive_engine import (
    BanditDifficultyEngine,
    SpacedRepetitionEngine,
    recommend_adaptive_pool,
)


@pytest.fixture
def db_conn():
    """In-memory SQLite database connection fixture initialized with full schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    # Run init_db using in-memory connection
    # Execute DDL statements directly
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_units (
            id TEXT PRIMARY KEY, template_type TEXT NOT NULL, title TEXT NOT NULL,
            topic_tags TEXT NOT NULL DEFAULT '[]', target_band_min REAL, target_band_max REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample_dialogues (
            id TEXT PRIMARY KEY, content_unit_id TEXT NOT NULL, band_level REAL NOT NULL,
            turn_type TEXT, function_tag TEXT, ai_line TEXT NOT NULL, user_model_answer TEXT NOT NULL,
            embedding BLOB
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id TEXT PRIMARY KEY, band_estimate_overall REAL DEFAULT 6.0, recurring_errors TEXT DEFAULT '[]'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_content_exposure (
            id TEXT PRIMARY KEY, user_id TEXT, sample_dialogue_id TEXT, exposed_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_bandit_stats (
            user_id TEXT NOT NULL, arm_offset REAL NOT NULL, pull_count INTEGER DEFAULT 0,
            total_reward REAL DEFAULT 0.0, avg_reward REAL DEFAULT 0.0, updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, arm_offset)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_spaced_repetition (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, item_id TEXT NOT NULL, item_text TEXT NOT NULL,
            item_type TEXT DEFAULT 'vocabulary', easiness_factor REAL DEFAULT 2.5, interval_days INTEGER DEFAULT 1,
            repetitions INTEGER DEFAULT 0, next_review_at TEXT DEFAULT (datetime('now')), created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    yield conn
    conn.close()


def test_bandit_select_and_update(db_conn):
    user_id = "test_user_bandit"
    bandit = BanditDifficultyEngine(arms=[-1.0, 0.0, 1.0])

    # Initial selection should pick an unpulled arm
    arm, target_band = bandit.select_difficulty_arm(user_id, base_band=6.5, conn=db_conn)
    assert arm in [-1.0, 0.0, 1.0]
    assert 4.0 <= target_band <= 9.0

    # Record rewards for arm 1.0
    res = bandit.update_arm_reward(user_id, arm_offset=1.0, reward=0.9, conn=db_conn)
    assert res["pull_count"] == 1.0
    assert res["avg_reward"] == 0.9

    # Update again
    res2 = bandit.update_arm_reward(user_id, arm_offset=1.0, reward=0.7, conn=db_conn)
    assert res2["pull_count"] == 2.0
    assert abs(res2["avg_reward"] - 0.8) < 1e-4


def test_spaced_repetition_flow(db_conn):
    user_id = "test_user_sr"
    sr = SpacedRepetitionEngine()

    # Add item
    item = sr.add_item(user_id, item_id="vocab_001", item_text="resilient", item_type="vocabulary", conn=db_conn)
    assert item["item_id"] == "vocab_001"
    assert item["easiness_factor"] == 2.5

    # Get due items (initially next_review_at is now, so it should be due)
    due = sr.get_due_items(user_id, limit=5, conn=db_conn)
    assert len(due) >= 1
    assert due[0]["item_id"] == "vocab_001"

    # Record good performance (quality=4)
    perf = sr.record_performance(user_id, item_id="vocab_001", quality=4, conn=db_conn)
    assert perf["quality"] == 4
    assert perf["new_interval"] == 1
    assert perf["repetitions"] == 1
    assert perf["new_ef"] >= 2.5

    # Record bad performance (quality=1)
    perf_bad = sr.record_performance(user_id, item_id="vocab_001", quality=1, conn=db_conn)
    assert perf_bad["quality"] == 1
    assert perf_bad["new_interval"] == 1
    assert perf_bad["repetitions"] == 0


def test_recommend_adaptive_pool(db_conn):
    user_id = "test_user_pool"

    # Insert sample content_unit and sample_dialogue into DB
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO content_units (id, template_type, title, topic_tags, target_band_min, target_band_max)
        VALUES ('cu_01', 'band_ladder', 'Travel Discussion', '["travel"]', 5.0, 7.0)
    """)
    cursor.execute("""
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, turn_type, function_tag, ai_line, user_model_answer)
        VALUES ('sd_01', 'cu_01', 6.0, 'standalone', 'general', 'Where do you like to travel?', 'I prefer quiet places.')
    """)
    cursor.execute("""
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, turn_type, function_tag, ai_line, user_model_answer)
        VALUES ('sd_02', 'cu_01', 6.5, 'standalone', 'general', 'Why do you choose quiet places?', 'Because I want to relax.')
    """)
    db_conn.commit()

    rec = recommend_adaptive_pool(
        user_id=user_id,
        topic_tags=["travel"],
        base_band=6.0,
        limit=2,
        conn=db_conn,
    )

    assert rec["user_id"] == user_id
    assert "chosen_arm_offset" in rec
    assert "target_band" in rec
    assert "due_spaced_repetition_items" in rec
    assert len(rec["dialogues"]) > 0
    assert rec["dialogues"][0].ai_line != ""
