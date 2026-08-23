"""
tests/test_anti_repetition.py
==============================
Unit and Integration Tests for Embedding Anti-Repetition Engine (TASK-016).
"""

import time

import pytest

from app.core.anti_repetition import (
    check_repetition,
    check_user_repetition,
    cosine_similarity,
    fallback_text_embedding,
    fetch_user_history_utterances,
    get_embedding,
)
from app.storage.db import get_db_connection, init_db


def test_cosine_similarity_edge_cases():
    """Test cosine similarity calculations on edge cases."""
    # Identical vectors -> 1.0
    vec_a = [0.5, 0.5, 0.5, 0.5]
    assert pytest.approx(cosine_similarity(vec_a, vec_a), abs=1e-4) == 1.0

    # Orthogonal vectors -> 0.0
    vec_b = [1.0, 0.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0, 0.0]
    assert pytest.approx(cosine_similarity(vec_b, vec_c), abs=1e-4) == 0.0

    # Zero vectors -> 0.0
    vec_zero = [0.0, 0.0, 0.0, 0.0]
    assert cosine_similarity(vec_a, vec_zero) == 0.0
    assert cosine_similarity(vec_zero, vec_zero) == 0.0

    # Dimension mismatch -> 0.0
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0

    # Empty vectors -> 0.0
    assert cosine_similarity([], []) == 0.0


def test_fallback_text_embedding_format():
    """Test fallback text embedding dimensions and normalization."""
    emb = fallback_text_embedding("Hello world, this is a test utterance.")
    assert len(emb) == 384
    # Zero text
    assert len(fallback_text_embedding("")) == 384


def test_check_repetition_empty_history():
    """Test check_repetition with empty history."""
    res = check_repetition(candidate_utterance="Where do you live?", history_utterances=[])
    assert res.is_repetitive is False
    assert res.max_similarity == 0.0
    assert res.matched_utterance is None
    assert res.re_generation_directive is None


def test_check_repetition_identical_match():
    """Test check_repetition with exact duplicate utterance."""
    target = "Do you prefer living in an apartment or a house?"
    history = [
        "What is your favorite food?",
        "Do you prefer living in an apartment or a house?",
        "Tell me about your job.",
    ]
    res = check_repetition(
        candidate_utterance=target,
        history_utterances=history,
        similarity_threshold=0.85,
    )
    assert res.is_repetitive is True
    assert res.max_similarity >= 0.85
    assert res.matched_utterance == target
    assert res.re_generation_directive is not None
    assert "trùng lặp motif" in res.re_generation_directive


def test_check_repetition_distinct_content():
    """Test check_repetition with completely distinct content."""
    candidate = "I enjoy astrophysics and studying distant black holes."
    history = [
        "How do I cook spaghetti carbonara?",
        "What is the weather like in London today?",
    ]
    res = check_repetition(
        candidate_utterance=candidate,
        history_utterances=history,
        similarity_threshold=0.85,
    )
    assert res.is_repetitive is False
    assert res.max_similarity < 0.85
    assert res.re_generation_directive is None


def test_check_repetition_precomputed_embeddings():
    """Test check_repetition with pre-computed candidate and history embeddings."""
    cand_vec = [1.0, 0.0, 0.0]
    hist_vecs = [
        [0.0, 1.0, 0.0],
        [0.9, 0.1, 0.0],
    ]
    history = ["Text A", "Text B"]

    res = check_repetition(
        candidate_utterance="Dummy",
        history_utterances=history,
        candidate_embedding=cand_vec,
        history_embeddings=hist_vecs,
        similarity_threshold=0.8,
    )
    assert res.is_repetitive is True
    assert res.matched_utterance == "Text B"
    assert res.max_similarity > 0.8


def test_check_repetition_performance_speed():
    """Test that embedding anti-repetition check runs fast (<15ms per check)."""
    candidate = "What kind of music do you like listening to?"
    history = [f"Sample dialogue sentence number {i} for testing speed." for i in range(10)]

    # Compute candidate vector once
    cand_vec = get_embedding(candidate)
    hist_vecs = [get_embedding(h) for h in history]

    start = time.perf_counter()
    res = check_repetition(
        candidate_utterance=candidate,
        history_utterances=history,
        candidate_embedding=cand_vec,
        history_embeddings=hist_vecs,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert elapsed_ms < 15.0
    assert res.execution_time_ms < 15.0


def test_db_user_history_integration(monkeypatch):
    """Test fetch_user_history_utterances and check_user_repetition with SQLite DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    import uuid

    user_id = f"test_usr_{uuid.uuid4().hex[:8]}"
    cu_id = f"test_cu_{uuid.uuid4().hex[:8]}"
    sd_id = f"test_sd_{uuid.uuid4().hex[:8]}"
    exp_id = f"test_exp_{uuid.uuid4().hex[:8]}"

    try:
        # Insert test user profile
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_profile (user_id, band_estimate_overall)
            VALUES (?, 6.0)
            """,
            (user_id,),
        )

        # Insert test content unit
        cursor.execute(
            """
            INSERT OR REPLACE INTO content_units (id, template_type, title)
            VALUES (?, 'band_ladder', 'Repetition Test Unit')
            """,
            (cu_id,),
        )

        # Insert test sample dialogue
        cursor.execute(
            """
            INSERT OR REPLACE INTO sample_dialogues (id, content_unit_id, band_level, ai_line, user_model_answer)
            VALUES (?, ?, 6.0, 'What is your favorite leisure activity on weekends?', 'I like swimming.')
            """,
            (sd_id, cu_id),
        )

        # Insert user exposure record
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_content_exposure (id, user_id, sample_dialogue_id)
            VALUES (?, ?, ?)
            """,
            (exp_id, user_id, sd_id),
        )
        conn.commit()

        # Test fetching history
        history = fetch_user_history_utterances(user_id, conn=conn)
        assert len(history) >= 1
        assert "What is your favorite leisure activity on weekends?" in history

        # Test user repetition check with identical candidate
        res = check_user_repetition(
            user_id=user_id,
            candidate_utterance="What is your favorite leisure activity on weekends?",
            conn=conn,
        )
        assert res.is_repetitive is True
        assert res.matched_utterance == "What is your favorite leisure activity on weekends?"

    finally:
        conn.close()
