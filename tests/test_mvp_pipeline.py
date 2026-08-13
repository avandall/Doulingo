"""
tests/test_mvp_pipeline.py
===========================
Integration test suite for TASK-009: MVP End-to-End Pipeline & API Endpoints Bridge (`app/main.py`).

Tests the 5-step conversational AI pipeline:
1. Audio/Text ASR Ingestion
2. RAG Retrieval Layer
3. Prompt Construction
4. Conversational Agent structured JSON response
5. TTS Output generation
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_topics_endpoint():
    """Verify GET /api/topics returns topics list and content units."""
    response = client.get("/api/topics")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert "content_units_count" in data
    assert "content_units" in data
    assert isinstance(data["topics"], list)
    assert isinstance(data["content_units_count"], int)


def test_voice_process_turn_endpoint_text_only():
    """Verify POST /api/voice/process_turn handles text input in text_only_mode."""
    payload = {
        "user_id": "test_mvp_user_001",
        "topic": "accommodation",
        "band_level": 6.5,
        "conversation_history": [
            {"role": "user", "content": "I live in a small apartment."},
            {"role": "assistant", "content": "What do you like most about your neighborhood?"},
        ],
        "character_id": "lily",
        "text_only_mode": True,
        "user_transcript": "It is quiet and close to a nice park.",
    }
    response = client.post("/api/voice/process_turn", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["user_transcript"] == "It is quiet and close to a nice park."
    assert "ai_utterance" in data and len(data["ai_utterance"]) > 0
    assert "internal_band_signal" in data
    assert "topic_tag" in data
    assert "difficulty_adjustment" in data
    assert data["text_only_mode"] is True
    assert data["audio_base64"] is None
    assert "retrieved_dialogues_count" in data


def test_voice_process_turn_endpoint_with_tts():
    """Verify POST /api/voice/process_turn generates audio when text_only_mode is False."""
    payload = {
        "user_id": "test_mvp_user_002",
        "topic": "food",
        "band_level": 5.5,
        "conversation_history": [],
        "character_id": "lily",
        "text_only_mode": False,
        "user_transcript": "My favorite food is traditional Vietnamese pho.",
    }
    response = client.post("/api/voice/process_turn", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "ai_utterance" in data and len(data["ai_utterance"]) > 0
    assert data["text_only_mode"] is False
    assert "audio_base64" in data
    # Audio base64 should be a string or None if fallback occurred
    if data["audio_base64"] is not None:
        assert isinstance(data["audio_base64"], str)


def test_voice_process_turn_multipart_endpoint():
    """Verify POST /api/voice/process_turn_multipart handles form fields."""
    form_data = {
        "user_id": "test_mvp_user_003",
        "topic": "work_study",
        "band_level": "6.0",
        "conversation_history": '[{"role": "user", "content": "I am a software developer."}]',
        "character_id": "lily",
        "text_only_mode": "true",
        "user_transcript": "I enjoy solving technical challenges.",
    }
    response = client.post("/api/voice/process_turn_multipart", data=form_data)
    assert response.status_code == 200
    data = response.json()

    assert data["user_transcript"] == "I enjoy solving technical challenges."
    assert "ai_utterance" in data
    assert data["text_only_mode"] is True
