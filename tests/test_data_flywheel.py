"""
tests/test_data_flywheel.py — Unit tests for High-Band User Answer Harvest Pipeline (TASK-023)
"""

import json
import sqlite3

import pytest

from app.analytics.data_flywheel import (
    TurnData,
    blob_to_floats,
    check_dedup,
    check_quality,
    check_rate_cap,
    cosine_similarity,
    harvest_candidate,
)


@pytest.fixture
def test_db():
    """In-memory SQLite connection fixture with schema initialized."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Schema setup for sample_dialogues, content_units, harvest_review_queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_units (
            id TEXT PRIMARY KEY,
            template_type TEXT NOT NULL,
            title TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample_dialogues (
            id TEXT PRIMARY KEY,
            content_unit_id TEXT NOT NULL,
            band_level REAL NOT NULL,
            turn_type TEXT,
            function_tag TEXT,
            ai_line TEXT NOT NULL,
            user_model_answer TEXT NOT NULL,
            embedding BLOB,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvest_review_queue (
            id TEXT PRIMARY KEY,
            candidate_ai_line TEXT NOT NULL,
            candidate_user_answer TEXT NOT NULL,
            source_user_id TEXT NOT NULL,
            source_turn_id TEXT NOT NULL,
            topic_tag TEXT DEFAULT '',
            tier2_scores TEXT NOT NULL,
            pii_check_passed INTEGER NOT NULL,
            pii_entities_found TEXT DEFAULT '[]',
            dedup_max_similarity REAL DEFAULT 0.0,
            dedup_status TEXT CHECK (dedup_status IN ('unique','similar_variant','duplicate_rejected')),
            review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending','approved','rejected')),
            reviewed_by TEXT DEFAULT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    yield conn
    conn.close()


def test_quality_verification():
    # Pass case: all axes >= 7.0, avg >= 7.5, confidence >= 0.85
    good_scores = {"fluency": 8.0, "lexical": 8.0, "grammar": 8.0, "pronunciation": 8.0}
    assert check_quality(good_scores, 0.90) is True

    # Fail case 1: low ASR confidence
    assert check_quality(good_scores, 0.80) is False

    # Fail case 2: one axis < 7.0 (e.g. pronunciation = 5.0)
    uneven_scores = {"fluency": 9.0, "lexical": 9.0, "grammar": 9.0, "pronunciation": 5.0}
    assert check_quality(uneven_scores, 0.95) is False

    # Fail case 3: average < 7.5 (all axes 7.1)
    low_avg_scores = {"fluency": 7.1, "lexical": 7.1, "grammar": 7.1, "pronunciation": 7.1}
    assert check_quality(low_avg_scores, 0.95) is False


def test_pii_scrubbing_rejection(test_db):
    # Candidate with email address PII
    turn = TurnData(
        user_transcript="My contact address is john.doe@example.com for further discussion.",
        ai_line="What is your email?",
        source_user_id="user_123",
        source_turn_id="turn_001",
        topic_tag="general",
        tier2_scores={"fluency": 8.5, "lexical": 8.5, "grammar": 8.5, "pronunciation": 8.5},
        avg_asr_confidence=0.95,
    )
    res = harvest_candidate(turn, conn=test_db)
    assert res == "rejected_pii"

    # Candidate with phone number PII
    turn_phone = TurnData(
        user_transcript="Call me at +1 555-123-4567 anytime.",
        ai_line="How can I reach you?",
        source_user_id="user_123",
        source_turn_id="turn_002",
        topic_tag="general",
        tier2_scores={"fluency": 8.5, "lexical": 8.5, "grammar": 8.5, "pronunciation": 8.5},
        avg_asr_confidence=0.95,
    )
    res_phone = harvest_candidate(turn_phone, conn=test_db)
    assert res_phone == "rejected_pii"


def test_rate_cap_rejection(test_db):
    cursor = test_db.cursor()
    # Insert 10 items for topic 'travel'
    for i in range(10):
        cursor.execute(
            """
            INSERT INTO harvest_review_queue (
                id, candidate_ai_line, candidate_user_answer, source_user_id, source_turn_id,
                topic_tag, tier2_scores, pii_check_passed
            ) VALUES (?, 'AI line', 'User answer', 'u1', ?, 'travel', '{}', 1)
            """,
            (f"hrq_prev_{i}", f"turn_{i}"),
        )
    test_db.commit()

    assert check_rate_cap("travel", conn=test_db) is False

    # Harvesting 11th candidate should return rejected_rate_cap
    turn = TurnData(
        user_transcript="I adore visiting historical monuments when traveling abroad.",
        ai_line="What do you enjoy when traveling?",
        source_user_id="user_123",
        source_turn_id="turn_011",
        topic_tag="travel",
        tier2_scores={"fluency": 8.0, "lexical": 8.0, "grammar": 8.0, "pronunciation": 8.0},
        avg_asr_confidence=0.90,
    )
    res = harvest_candidate(turn, conn=test_db)
    assert res == "rejected_rate_cap"


def test_vector_deduplication(test_db):
    cursor = test_db.cursor()
    cursor.execute("INSERT INTO content_units VALUES ('cu_1', 'band_ladder', 'Title')")
    cursor.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
        VALUES ('sd_1', 'cu_1', 8.0, 'AI line', 'I strongly prefer traveling by train because of the scenic routes.')
        """
    )
    test_db.commit()

    # Exact text match duplicate
    status, sim = check_dedup(
        candidate_embedding=None,
        candidate_answer="I strongly prefer traveling by train because of the scenic routes.",
        conn=test_db,
    )
    assert status == "duplicate_rejected"
    assert sim == 1.0

    turn_dup = TurnData(
        user_transcript="I strongly prefer traveling by train because of the scenic routes.",
        ai_line="How do you travel?",
        source_user_id="user_123",
        source_turn_id="turn_dup",
        topic_tag="transport",
        tier2_scores={"fluency": 8.5, "lexical": 8.5, "grammar": 8.5, "pronunciation": 8.5},
        avg_asr_confidence=0.95,
    )
    res = harvest_candidate(turn_dup, conn=test_db)
    assert res == "rejected_duplicate"


def test_successful_candidate_harvest(test_db):
    turn = TurnData(
        user_transcript="In my perspective, sustainable urban infrastructure plays a crucial role in enhancing public well-being.",
        ai_line="Why is urban planning important?",
        source_user_id="user_999",
        source_turn_id="turn_999",
        topic_tag="environment",
        tier2_scores={"fluency": 8.0, "lexical": 8.5, "grammar": 8.0, "pronunciation": 8.0},
        avg_asr_confidence=0.92,
    )

    res = harvest_candidate(turn, conn=test_db)
    assert res == "queued_for_review"

    # Verify database staging table
    cursor = test_db.cursor()
    cursor.execute("SELECT * FROM harvest_review_queue WHERE source_turn_id = 'turn_999'")
    row = cursor.fetchone()
    assert row is not None
    assert row["candidate_user_answer"] == turn.user_transcript
    assert row["review_status"] == "pending"
    assert row["pii_check_passed"] == 1
    scores = json.loads(row["tier2_scores"])
    assert scores["fluency"] == 8.0


def test_utility_functions():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(vec1, vec2) == 1.0

    vec3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(vec1, vec3) == 0.0

    # Test blob_to_floats
    floats_in = [0.1, 0.2, 0.3]
    parsed = blob_to_floats(floats_in)
    assert parsed == floats_in
