"""
Unit tests for app/retrieval.py (TASK-005 & TASK-015)
RAG Retrieval Layer v1
"""

import logging
import sqlite3

import pytest

from app.retrieval import (
    blob_to_floats,
    compute_band_window,
    cosine_similarity,
    log_exposure,
    retrieve_adaptive_dialogues,
    retrieve_dialogues,
)
from scripts import generate_embeddings, insert_turso


@pytest.fixture
def temp_db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(insert_turso.SCHEMA_SQL)
    conn.execute("PRAGMA foreign_keys = ON;")
    yield conn
    conn.close()


def test_compute_band_window():
    assert compute_band_window(6.0, "increase") == (6.0, 7.5)
    assert compute_band_window(6.0, "decrease") == (4.5, 6.0)
    assert compute_band_window(6.0, "hold") == (5.5, 7.0)
    assert compute_band_window(6.0, "unknown") == (5.5, 7.0)
    assert compute_band_window(6.0, "") == (5.5, 7.0)


def test_blob_to_floats_and_cosine_similarity():
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]

    assert pytest.approx(cosine_similarity(vec1, vec2)) == 1.0
    assert pytest.approx(cosine_similarity(vec1, vec3)) == 0.0
    assert cosine_similarity([], vec1) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0

    blob = generate_embeddings.floats_to_blob([0.5, -0.2, 0.9])
    floats = blob_to_floats(blob)
    assert len(floats) == 3
    assert pytest.approx(floats[0]) == 0.5
    assert pytest.approx(floats[1]) == -0.2
    assert pytest.approx(floats[2]) == 0.9
    assert blob_to_floats(b"") == []
    assert blob_to_floats(b"123") == []


def test_log_exposure(temp_db_conn):
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title)
        VALUES ('cu_exp_test', 'band_ladder', 'Exp Test')
        """
    )
    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
        VALUES
            ('sd_1', 'cu_exp_test', 6.0, 'Q1', 'A1'),
            ('sd_2', 'cu_exp_test', 6.0, 'Q2', 'A2')
        """
    )
    temp_db_conn.commit()

    user_id = "user_test_exp"
    dialogue_ids = ["sd_1", "sd_2"]

    ids = log_exposure(user_id, dialogue_ids, conn=temp_db_conn)
    assert len(ids) == 2

    cur = temp_db_conn.cursor()
    cur.execute("SELECT sample_dialogue_id FROM user_content_exposure WHERE user_id = ?", (user_id,))
    rows = [r[0] for r in cur.fetchall()]
    assert set(rows) == {"sd_1", "sd_2"}


def test_retrieve_dialogues_basic(temp_db_conn):
    # Insert content_unit
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags, target_band_min, target_band_max)
        VALUES ('cu_hometown', 'band_ladder', 'Hometown Topic', '["hometown", "travel"]', 5.0, 8.0)
        """
    )
    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, turn_type, function_tag, ai_line, user_model_answer)
        VALUES
            ('sd_ht_60', 'cu_hometown', 6.0, 'standalone', 'desc', 'Where is your hometown?', 'It is in Hanoi.'),
            ('sd_ht_65', 'cu_hometown', 6.5, 'standalone', 'desc', 'What do you like about it?', 'I love the food.'),
            ('sd_ht_75', 'cu_hometown', 7.5, 'standalone', 'desc', 'How has it changed?', 'It has modernized quickly.')
        """
    )
    temp_db_conn.commit()

    results = retrieve_dialogues(
        user_id="user_123",
        topic_tags=["hometown"],
        band_min=5.5,
        band_max=7.0,
        conn=temp_db_conn,
        auto_log_exposure=True,
    )

    assert len(results) == 2
    assert results[0].id in {"sd_ht_60", "sd_ht_65"}
    assert results[1].id in {"sd_ht_60", "sd_ht_65"}

    # Verify exposure was recorded
    cur = temp_db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_content_exposure WHERE user_id = 'user_123'")
    assert cur.fetchone()[0] == 2


def test_retrieve_dialogues_exposure_exclusion(temp_db_conn):
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags)
        VALUES ('cu_food', 'band_ladder', 'Food Topic', '["food"]')
        """
    )
    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
        VALUES
            ('sd_food_1', 'cu_food', 6.0, 'Favorite food?', 'Pho.'),
            ('sd_food_2', 'cu_food', 6.0, 'Cooking skills?', 'I can cook basic dishes.'),
            ('sd_food_3', 'cu_food', 6.0, 'Eating out?', 'I prefer local eateries.')
        """
    )
    # Mark sd_food_1 as exposed
    log_exposure("user_exp", ["sd_food_1"], conn=temp_db_conn)

    results = retrieve_dialogues(
        user_id="user_exp",
        topic_tags=["food"],
        band_min=5.5,
        band_max=6.5,
        conn=temp_db_conn,
        auto_log_exposure=False,
    )

    result_ids = [r.id for r in results]
    assert "sd_food_1" not in result_ids
    assert "sd_food_2" in result_ids
    assert "sd_food_3" in result_ids


def test_retrieve_dialogues_fallback_cascade(temp_db_conn, caplog):
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags)
        VALUES ('cu_rare', 'band_ladder', 'Rare Topic', '["rare_topic"]')
        """
    )
    # Only 1 dialogue for rare_topic at band 8.5
    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
        VALUES ('sd_rare_1', 'cu_rare', 8.5, 'Rare question?', 'Rare answer.')
        """
    )
    # Another dialogue under a different topic at band 6.0
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags)
        VALUES ('cu_common', 'band_ladder', 'Common Topic', '["common"]')
        """
    )
    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
        VALUES ('sd_common_1', 'cu_common', 6.0, 'Common question?', 'Common answer.')
        """
    )
    temp_db_conn.commit()

    with caplog.at_level(logging.WARNING):
        # Querying for "rare_topic" at band 5.5-6.5 (strict returns 0 items)
        results = retrieve_dialogues(
            user_id="user_fallback",
            topic_tags=["rare_topic"],
            band_min=5.5,
            band_max=6.5,
            conn=temp_db_conn,
            auto_log_exposure=False,
        )

    assert len(results) >= 1
    # Fallback stage log warning should be emitted
    assert "Retrieval fallback stage" in caplog.text or "fallback" in caplog.text.lower()


def test_retrieve_dialogues_empty_db(temp_db_conn, caplog):
    with caplog.at_level(logging.ERROR):
        results = retrieve_dialogues(
            user_id="user_empty",
            topic_tags=["non_existent"],
            band_min=5.0,
            band_max=7.0,
            conn=temp_db_conn,
        )

    assert results == []
    assert "Retrieval fallback exhausted" in caplog.text


def test_retrieve_dialogues_with_vector_embedding(temp_db_conn):
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags)
        VALUES ('cu_vec', 'band_ladder', 'Vector Topic', '["music"]')
        """
    )
    # Insert 2 dialogues with embeddings
    vec_a = [1.0, 0.0, 0.0] + [0.0] * 381
    vec_b = [0.0, 1.0, 0.0] + [0.0] * 381

    blob_a = generate_embeddings.floats_to_blob(vec_a)
    blob_b = generate_embeddings.floats_to_blob(vec_b)

    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer, embedding)
        VALUES
            ('sd_music_a', 'cu_vec', 6.0, 'Song A?', 'Answer A.', ?),
            ('sd_music_b', 'cu_vec', 6.0, 'Song B?', 'Answer B.', ?)
        """,
        (blob_a, blob_b),
    )
    temp_db_conn.commit()

    query_vec = [0.99, 0.01, 0.0] + [0.0] * 381

    results = retrieve_dialogues(
        user_id="user_vec",
        topic_tags=["music"],
        band_min=5.5,
        band_max=6.5,
        query_embedding=query_vec,
        conn=temp_db_conn,
        auto_log_exposure=False,
    )

    assert len(results) == 2
    assert results[0].id == "sd_music_a"
    assert results[0].score > results[1].score


def test_retrieve_adaptive_dialogues(temp_db_conn):
    temp_db_conn.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags)
        VALUES ('cu_adapt', 'band_ladder', 'Adaptive Topic', '["adapt"]')
        """
    )
    temp_db_conn.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
        VALUES
            ('sd_easy', 'cu_adapt', 5.0, 'Easy Q?', 'Easy A.'),
            ('sd_mid', 'cu_adapt', 6.0, 'Mid Q?', 'Mid A.'),
            ('sd_hard', 'cu_adapt', 7.2, 'Hard Q?', 'Hard A.')
        """
    )
    temp_db_conn.commit()

    # Test "increase": base 6.0 -> (6.0, 7.5) -> matches sd_mid (6.0) and sd_hard (7.2)
    results_inc = retrieve_adaptive_dialogues(
        user_id="user_inc",
        topic_tags=["adapt"],
        base_band=6.0,
        difficulty_signal="increase",
        conn=temp_db_conn,
        auto_log_exposure=False,
    )
    inc_ids = {r.id for r in results_inc}
    assert "sd_hard" in inc_ids or "sd_mid" in inc_ids

    # Test "decrease": base 6.0 -> (4.5, 6.0) -> matches sd_easy (5.0) and sd_mid (6.0)
    results_dec = retrieve_adaptive_dialogues(
        user_id="user_dec",
        topic_tags=["adapt"],
        base_band=6.0,
        difficulty_signal="decrease",
        conn=temp_db_conn,
        auto_log_exposure=False,
    )
    dec_ids = {r.id for r in results_dec}
    assert "sd_easy" in dec_ids

    # Test "hold": base 6.0 -> (5.5, 7.0) -> matches sd_mid (6.0)
    results_hold = retrieve_adaptive_dialogues(
        user_id="user_hold",
        topic_tags=["adapt"],
        base_band=6.0,
        difficulty_signal="hold",
        conn=temp_db_conn,
        auto_log_exposure=False,
    )
    hold_ids = {r.id for r in results_hold}
    assert "sd_mid" in hold_ids

