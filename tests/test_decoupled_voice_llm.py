"""
tests/test_decoupled_voice_llm.py
=================================
Unit & Integration Test Suite for TASK-011:
Decoupled Fast Voice LLM & Background Evaluation Pipeline.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.ai_engine import AIEngine, get_background_evaluation
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_llm_providers(monkeypatch):
    """Mock LLM provider calls for fast, deterministic testing without external API timeouts."""
    def fake_call_llm_providers(self, prompt: str, temp: float = 0.8):
        if "Respond naturally and directly" in prompt:
            return {"ai_response": "That sounds wonderful! What else do you like to cook?"}
        return {
            "natural_draft": "Draft answer for practice.",
            "vocab_check": "Level 1 vocab verified.",
            "final_response": "That sounds wonderful! What else do you like to cook?",
            "ai_response": "That sounds wonderful! What else do you like to cook?",
            "ai_response_vi": "Điều đó nghe thật tuyệt vời! Bạn còn thích nấu món gì nữa?",
            "user_feedback": {
                "corrected_text": "I enjoy cooking pasta for my family.",
                "grammar_status": "Clean & Clear",
                "native_phrasing": "I enjoy cooking pasta for my family.",
                "fluency_score": 95,
                "grammar_score": 96,
                "overall_score": 95,
                "duo_reaction": "happy",
                "xp_earned": 10
            }
        }

    monkeypatch.setattr(AIEngine, "_call_llm_providers", fake_call_llm_providers)


def test_process_turn_fast_unit():
    """Unit test for AIEngine.process_turn_fast()."""
    engine = AIEngine()
    result = engine.process_turn_fast(
        scenario_id="everyday_chat",
        character_id="lily",
        user_transcript="I enjoy cooking pasta for my family on weekends.",
        conversation_history=[],
        level=1,
    )

    assert "ai_response" in result
    assert len(result["ai_response"]) > 0
    assert result["status"] == "fast_voice_ready"
    assert result["latency_mode"] == "fast_voice"


def test_evaluate_turn_background_unit():
    """Unit test for AIEngine.evaluate_turn_background()."""
    engine = AIEngine()
    turn_id = "test_turn_12345"

    eval_result = engine.evaluate_turn_background(
        turn_id=turn_id,
        scenario_id="everyday_chat",
        character_id="lily",
        user_transcript="I goes to school every day.",
        conversation_history=[],
        ai_response="That is nice! What is your favorite subject?",
        level=1,
        speech_metrics={"wpm": 110, "pauses": 1, "pronunciation_score": 88.0},
    )

    assert eval_result["turn_id"] == turn_id
    assert eval_result["status"] == "completed"
    assert "user_feedback" in eval_result
    fb = eval_result["user_feedback"]
    assert "fluency_score" in fb
    assert "grammar_score" in fb
    assert "overall_score" in fb

    stored = get_background_evaluation(turn_id)
    assert stored is not None
    assert stored["turn_id"] == turn_id
    assert stored["user_feedback"]["fluency_score"] == fb["fluency_score"]


def test_api_process_turn_fast_endpoint():
    """Integration test for POST /api/process_turn_fast."""
    payload = {
        "turn_id": "api_turn_fast_999",
        "scenario_id": "everyday_chat",
        "character_id": "lily",
        "user_transcript": "I love playing guitar and singing songs.",
        "conversation_history": [],
        "level": 1,
    }

    response = client.post("/api/process_turn_fast", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["turn_id"] == "api_turn_fast_999"
    assert "ai_response" in data
    assert len(data["ai_response"]) > 0
    assert data["status"] == "processing_eval"
    assert data["latency_mode"] == "fast_voice"


def test_api_turn_evaluation_endpoint():
    """Integration test for GET /api/turn_evaluation/{turn_id}."""
    turn_id = "eval_poll_001"

    # 1. Poll non-existent / pending turn
    pending_resp = client.get(f"/api/turn_evaluation/{turn_id}")
    assert pending_resp.status_code == 200
    pending_data = pending_resp.json()
    assert pending_data["status"] == "pending"

    # 2. Trigger background evaluation
    engine = AIEngine()
    engine.evaluate_turn_background(
        turn_id=turn_id,
        scenario_id="everyday_chat",
        character_id="lily",
        user_transcript="Learning English is fun.",
        conversation_history=[],
        ai_response="I agree! What method do you use?",
        level=1,
    )

    # 3. Poll completed turn
    completed_resp = client.get(f"/api/turn_evaluation/{turn_id}")
    assert completed_resp.status_code == 200
    completed_data = completed_resp.json()
    assert completed_data["status"] == "completed"
    assert "user_feedback" in completed_data
