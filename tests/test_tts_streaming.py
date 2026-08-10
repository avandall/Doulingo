"""
Unit and integration tests for Streaming Speech Audio Buffering in app/tts_service.py and app/main.py.
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.tts_service import stream_tts_mp3_chunks

client = TestClient(app)

def test_stream_tts_mp3_chunks_yields_bytes():
    """Verify stream_tts_mp3_chunks yields non-empty audio chunks asynchronously."""
    async def _run():
        chunks = []
        async for chunk in stream_tts_mp3_chunks(text="Hello welcome to Duolingo Speak", char_id="lily"):
            chunks.append(chunk)
            if len(chunks) >= 2:
                break
        return chunks

    chunks = asyncio.run(_run())
    assert len(chunks) > 0, "stream_tts_mp3_chunks should yield at least one audio chunk"
    assert isinstance(chunks[0], bytes), "Yielded chunk must be bytes"
    assert len(chunks[0]) > 0, "Audio chunk must not be empty"

def test_api_tts_streaming_endpoint():
    """Verify GET /api/tts endpoint streams audio/mpeg content."""
    response = client.get("/api/tts", params={"text": "Hello world", "char_id": "lily"})
    assert response.status_code == 200
    assert "audio/mpeg" in response.headers.get("content-type", "")
    assert len(response.content) > 100, "Streamed audio content should be non-empty"
