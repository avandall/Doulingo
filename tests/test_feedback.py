"""
tests/test_feedback.py
======================
Unit tests for Response Rating API & Continuous Feedback Logger (TASK-007).
Tests FeedbackService, RAG integration, and POST /api/v1/feedback/rate-response endpoint.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.core.exemplar_rag import ExemplarRAG
from app.main import app
from app.services.feedback_service import FeedbackService


@pytest.fixture(autouse=True)
def temp_feedback_env(tmp_path, monkeypatch):
    """Creates temporary JSON files for feedback log and dialogue bank and patches env vars."""
    log_file = tmp_path / "feedback_log.json"
    bank_file = tmp_path / "sample_dialogue_bank.json"

    log_file.write_text("[]", encoding="utf-8")

    initial_bank = [
        {
            "id": "ex_test_001",
            "level": "A1",
            "persona": "Alex",
            "persona_trait": "friendly",
            "topic": "daily_life",
            "dialogue_act": "greeting",
            "user_input_context": "Hello!",
            "ai_response": "Good morning! How are you doing today?",
            "text": "Good morning! How are you doing today?",
            "word_count": 7,
            "reviewed_by": "teacher",
            "quality_score": 4.5,
            "is_blacklisted": False,
        },
        {
            "id": "ex_test_002",
            "level": "A1",
            "persona": "Alex",
            "persona_trait": "friendly",
            "topic": "daily_life",
            "dialogue_act": "greeting",
            "user_input_context": "Hi there!",
            "ai_response": "Hello friend! Nice to meet you.",
            "text": "Hello friend! Nice to meet you.",
            "word_count": 6,
            "reviewed_by": "teacher",
            "quality_score": 4.8,
            "is_blacklisted": False,
        },
    ]
    bank_file.write_text(json.dumps(initial_bank, indent=2), encoding="utf-8")

    monkeypatch.setenv("FEEDBACK_LOG_PATH", str(log_file))
    monkeypatch.setenv("DIALOGUE_BANK_PATH", str(bank_file))

    return {
        "log_path": str(log_file),
        "bank_path": str(bank_file),
        "tmp_dir": tmp_path,
    }


def test_feedback_service_invalid_input(temp_feedback_env):
    """Tests that invalid ratings or empty texts raise ValueError."""
    service = FeedbackService(
        feedback_log_path=temp_feedback_env["log_path"],
        dialogue_bank_path=temp_feedback_env["bank_path"],
    )

    with pytest.raises(ValueError, match="response_text cannot be empty"):
        service.rate_response(response_text="", rating="good")

    with pytest.raises(ValueError, match="Invalid rating"):
        service.rate_response(response_text="Hello", rating="terrible")


def test_feedback_service_hollow_penalize_and_blacklist(temp_feedback_env):
    """Tests that rating 'hollow' penalizes quality_score and blacklists when score is low."""
    service = FeedbackService(
        feedback_log_path=temp_feedback_env["log_path"],
        dialogue_bank_path=temp_feedback_env["bank_path"],
    )

    # First hollow rating: 4.5 -> 3.0
    res1 = service.rate_response(
        response_text="Good morning! How are you doing today?",
        rating="hollow",
        dialogue_id="ex_test_001",
    )
    assert res1["status"] == "success"
    assert res1["bank_action"] == "penalized"
    assert res1["new_quality_score"] == 3.0
    assert res1["is_blacklisted"] is False

    # Second hollow rating: 3.0 -> 1.5 (<= 2.0, triggers blacklisting)
    res2 = service.rate_response(
        response_text="Good morning! How are you doing today?",
        rating="hollow",
        dialogue_id="ex_test_001",
    )
    assert res2["new_quality_score"] == 1.5
    assert res2["is_blacklisted"] is True

    # Verify log entry was written to log file
    with open(temp_feedback_env["log_path"], "r", encoding="utf-8") as f:
        logs = json.load(f)
        assert len(logs) == 2
        assert logs[0]["rating"] == "hollow"

    # Verify RAG engine excludes the blacklisted item
    rag = ExemplarRAG(data_path=temp_feedback_env["bank_path"])
    retrieved = rag.retrieve(level="A1", persona="Alex", top_k=5)
    retrieved_ids = [ex["id"] for ex in retrieved]
    assert "ex_test_001" not in retrieved_ids
    assert "ex_test_002" in retrieved_ids


def test_feedback_service_good_boost_and_unblacklist(temp_feedback_env):
    """Tests rating 'good' boosts quality_score and clears blacklist."""
    service = FeedbackService(
        feedback_log_path=temp_feedback_env["log_path"],
        dialogue_bank_path=temp_feedback_env["bank_path"],
    )

    # First penalize item to lower score and blacklist
    service.rate_response(
        response_text="Good morning! How are you doing today?",
        rating="out_of_context",
        dialogue_id="ex_test_001",
    )
    service.rate_response(
        response_text="Good morning! How are you doing today?",
        rating="hollow",
        dialogue_id="ex_test_001",
    )

    # Now rate good: boost 1.5 -> 2.0, clear blacklist
    res = service.rate_response(
        response_text="Good morning! How are you doing today?",
        rating="good",
        dialogue_id="ex_test_001",
    )
    assert res["bank_action"] == "boosted"
    assert res["new_quality_score"] == 2.0
    assert res["is_blacklisted"] is False


def test_feedback_service_auto_add_new_good_exemplar(temp_feedback_env):
    """Tests rating 'good' for a non-existing sentence automatically adds a new exemplar."""
    service = FeedbackService(
        feedback_log_path=temp_feedback_env["log_path"],
        dialogue_bank_path=temp_feedback_env["bank_path"],
    )

    new_sentence = "What a fascinating story! Tell me more about your adventures."
    ctx = {
        "level": "B1",
        "persona": "Oscar",
        "topic": "travel",
        "dialogue_act": "interest",
    }

    res = service.rate_response(
        response_text=new_sentence,
        rating="good",
        context=ctx,
        comments="Great question",
    )

    assert res["status"] == "success"
    assert res["bank_action"] == "added_new"
    assert res["new_quality_score"] == 4.8
    assert res["dialogue_id"].startswith("ex_auto_")

    # Verify newly added exemplar exists in bank file
    with open(temp_feedback_env["bank_path"], "r", encoding="utf-8") as f:
        bank = json.load(f)
        added = [item for item in bank if item.get("text") == new_sentence]
        assert len(added) == 1
        assert added[0]["persona"] == "Oscar"
        assert added[0]["level"] == "B1"


def test_api_rate_response_endpoint_success(temp_feedback_env):
    """Tests FastAPI POST /api/v1/feedback/rate-response with valid payload."""
    client = TestClient(app)

    payload = {
        "response_text": "Good day to you! How may I assist your learning today?",
        "rating": "good",
        "context": {
            "level": "A2",
            "persona": "Alex",
            "topic": "daily_life",
        },
        "user_id": "test_user_42",
        "comments": "Very friendly response",
    }

    response = client.post("/api/v1/feedback/rate-response", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["rating"] == "good"
    assert "feedback_id" in data
    assert data["feedback_id"].startswith("fb_")


def test_api_rate_response_endpoint_validation_errors(temp_feedback_env):
    """Tests FastAPI endpoint response for invalid rating or missing parameters."""
    client = TestClient(app)

    # Invalid rating grade
    bad_rating_payload = {
        "response_text": "Hello world",
        "rating": "invalid_grade",
    }
    resp = client.post("/api/v1/feedback/rate-response", json=bad_rating_payload)
    assert resp.status_code == 400
    assert "Invalid rating" in resp.json()["detail"]

    # Missing required field response_text
    missing_text_payload = {
        "rating": "good",
    }
    resp = client.post("/api/v1/feedback/rate-response", json=missing_text_payload)
    assert resp.status_code == 422
