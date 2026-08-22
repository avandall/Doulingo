"""
Unit & Integration Tests for Instant Conversational Fillers & Natural TTS Tuning (TASK-004)
"""

import os

from fastapi.testclient import TestClient

from app.main import app
from app.tts_service import (
    CHARACTER_FILLER_MAP,
    CHARACTER_VOICE_MAP,
    get_character_filler_path,
)

client = TestClient(app)


def test_character_voice_map_natural_tuning():
    """Verify that all characters in CHARACTER_VOICE_MAP use natural rate (+0%) and pitch (+0Hz)."""
    assert len(CHARACTER_VOICE_MAP) >= 10
    for char_id, profile in CHARACTER_VOICE_MAP.items():
        assert profile["rate"] == "+0%", f"Character '{char_id}' rate is not +0%"
        assert profile["pitch"] == "+0Hz", f"Character '{char_id}' pitch is not +0Hz"


def test_character_filler_map_existence():
    """Verify that filler phrases and audio file mappings exist for all key virtual characters."""
    expected_chars = ["duo", "lily", "oscar", "viktor", "chanel", "kaelen", "colt", "zarina", "scarlet", "luigi"]
    for char_id in expected_chars:
        assert char_id in CHARACTER_FILLER_MAP
        rel_path = get_character_filler_path(char_id)
        assert os.path.exists(rel_path), f"Filler audio file for '{char_id}' missing at {rel_path}"


def test_api_filler_endpoint():
    """Test the /api/fillers/{character_id} endpoint returns valid audio response."""
    response = client.get("/api/fillers/lily")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert len(response.content) > 100


def test_api_filler_fallback_character():
    """Test /api/fillers with default or unknown character fallback."""
    response = client.get("/api/fillers/unknown_char")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")


def test_api_tts_fallback_natural_voice():
    """Test /api/tts endpoint works with natural tuned character settings."""
    response = client.get("/api/tts?text=Hello+world&character_id=lily")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert len(response.content) > 500
