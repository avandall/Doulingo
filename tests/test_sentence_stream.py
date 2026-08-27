"""
Unit and integration tests for Sentence-Level Streaming & Direct Chunked Audio Synthesis (TASK-013).
"""

import asyncio

from fastapi.testclient import TestClient

from app.audio import split_sentences, stream_sentence_level_tts
from app.audio.tts_streamer import stream_sentence_audio_response
from app.main import app

client = TestClient(app)


def test_split_sentences_basic():
    """Verify split_sentences tokenizes text by sentence boundary delimiters (. ! ? \\n)."""
    text = "Hello there! How are you doing today? I am fine. Thanks!"
    sentences = split_sentences(text)
    assert len(sentences) == 4
    assert sentences[0] == "Hello there!"
    assert sentences[1] == "How are you doing today?"
    assert sentences[2] == "I am fine."
    assert sentences[3] == "Thanks!"


def test_split_sentences_single_and_empty():
    """Verify split_sentences behavior on single sentence and empty input."""
    assert split_sentences("") == []
    assert split_sentences("   ") == []
    assert split_sentences("Just one single sentence.") == ["Just one single sentence."]


def test_split_sentences_newlines():
    """Verify split_sentences handles multiline paragraphs correctly."""
    text = "First paragraph sentence.\nSecond line sentence."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    assert sentences[0] == "First paragraph sentence."
    assert sentences[1] == "Second line sentence."


def test_stream_sentence_level_tts_yields_chunks():
    """Verify stream_sentence_level_tts yields non-empty audio chunks for each sentence."""
    async def _run():
        text = "Hello welcome to Duolingo Speak. How can I help you today?"
        chunks = []
        async for chunk in stream_sentence_level_tts(text=text, char_id="lily"):
            chunks.append(chunk)
            if len(chunks) >= 2:
                break
        return chunks

    chunks = asyncio.run(_run())
    assert len(chunks) > 0, "stream_sentence_level_tts should yield at least one audio chunk"
    assert isinstance(chunks[0], bytes), "Yielded chunk must be bytes"
    assert len(chunks[0]) > 0, "Audio chunk must not be empty"


def test_api_tts_stream_endpoint():
    """Verify GET /api/tts/stream endpoint streams audio/mpeg content."""
    response = client.get("/api/tts/stream", params={"text": "Hello world. Nice to meet you.", "character_id": "lily"})
    assert response.status_code == 200
    assert "audio/mpeg" in response.headers.get("content-type", "")
    assert len(response.content) > 100, "Streamed audio content should be non-empty"


def test_api_tts_query_stream_param_endpoint():
    """Verify GET /api/tts with stream=true parameter streams audio/mpeg content."""
    response = client.get("/api/tts", params={"text": "Testing sentence level stream query.", "char_id": "lily", "stream": "true"})
    assert response.status_code == 200
    assert "audio/mpeg" in response.headers.get("content-type", "")
    assert len(response.content) > 100, "Streamed audio content should be non-empty"


def test_stream_sentence_audio_response_streamer():
    """Verify convenience streamer function yields audio chunks."""
    async def _run():
        chunks = []
        async for chunk in stream_sentence_audio_response(text="Greeting sentence.", char_id="lily"):
            chunks.append(chunk)
            if len(chunks) >= 1:
                break
        return chunks

    chunks = asyncio.run(_run())
    assert len(chunks) > 0, "stream_sentence_audio_response should yield audio chunks"
    assert isinstance(chunks[0], bytes)
