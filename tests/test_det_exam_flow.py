"""
test_det_exam_flow.py — Verification & Integration tests for IELTS Exam Read-Then-Speak Flow (TASK-005)
"""

import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.ai_engine import ai_engine
from app.main import app

client = TestClient(app)

@pytest.fixture
def dummy_scenario() -> dict[str, Any]:
    return {
        "id": "det_childhood_memory",
        "title": "Childhood Memory",
        "category": "Descriptive",
        "description": "Describe a memorable event from your childhood in detail.",
        "question_card": {
            "prompt": "Describe a memorable event from your childhood.",
            "bullet_points": [
                "What the event was",
                "When and where it took place",
                "Who was with you",
                "Why it remains memorable"
            ]
        }
    }

def test_evaluate_det_speech_short_input(dummy_scenario: dict[str, Any]) -> None:
    async def _run():
        return await ai_engine.evaluate_det_speech(
            scenario=dummy_scenario,
            user_speech="I loved playing football.",
            duration_seconds=30,
            mode="read_then_speak",
            wpm=100,
            pause_count=1,
            filler_count=0
        )
    result = asyncio.run(_run())
    assert result["det_score"] <= 35
    assert "chỉ có" in result["examiner_critique"] or "quá ngắn" in result["examiner_critique"]
    assert "acoustic_metrics" in result
    assert result["acoustic_metrics"]["wpm"] == 100

def test_evaluate_det_speech_full_input(dummy_scenario: dict[str, Any]) -> None:
    long_speech = (
        "When I was around eight years old, my family took a unforgettable summer trip to the mountains. "
        "We stayed in a small wooden cabin near a pine forest. Every morning, we went hiking along pristine streams, "
        "and at night we sat around a campfire sharing stories and roasting marshmallows. "
        "This experience left a profound impression on me because it taught me to appreciate nature and brought our family closer."
    )
    async def _run():
        return await ai_engine.evaluate_det_speech(
            scenario=dummy_scenario,
            user_speech=long_speech,
            duration_seconds=90,
            mode="read_then_speak",
            wpm=120,
            pause_count=2,
            filler_count=1
        )
    result = asyncio.run(_run())
    assert result["det_score"] >= 80
    assert "cefr_level" in result
    assert "fluency_score" in result
    assert "grammar_score" in result
    assert "vocabulary_score" in result
    assert "examiner_critique" in result

def test_api_det_evaluate_speech_endpoint() -> None:
    response = client.post(
        "/api/det/evaluate_speech",
        json={
            "scenario_id": "det_childhood_memory",
            "user_speech": "One of my favorite childhood memories is learning to ride a bicycle with my grandfather.",
            "duration_seconds": 60,
            "mode": "read_then_speak",
            "wpm": 110,
            "pause_count": 1,
            "filler_count": 0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "det_score" in data
    assert "cefr_level" in data
    assert "examiner_critique" in data
    assert "acoustic_metrics" in data

def test_api_det_evaluate_speech_404_invalid_scenario() -> None:
    response = client.post(
        "/api/det/evaluate_speech",
        json={
            "scenario_id": "non_existent_det_scenario_id_999",
            "user_speech": "Hello world speech",
            "duration_seconds": 30,
            "mode": "read_then_speak"
        }
    )
    assert response.status_code == 404
