"""
Unit tests for TTS Audio Output Streamer in app/tts_streamer.py.
"""

import asyncio
from unittest.mock import patch

from app.tts_streamer import (
    TTSStreamer,
    TTSStreamResult,
    generate_audio_response,
    stream_audio_response,
)


def test_generate_audio_success():
    """Verify batch audio generation returns valid TTSStreamResult."""
    streamer = TTSStreamer()
    result = streamer.generate_audio("Hello, welcome to Duolingo Speak!", char_id="lily")

    assert isinstance(result, TTSStreamResult)
    assert result.text_only_mode is False
    assert result.content_type == "audio/mpeg"
    assert result.audio_bytes is not None
    assert len(result.audio_bytes) > 0
    assert result.error_message is None


def test_generate_audio_text_only_mode():
    """Verify text_only_mode=True skips audio synthesis cleanly."""
    streamer = TTSStreamer()
    result = streamer.generate_audio(
        "Hello!", char_id="lily", text_only_mode=True
    )

    assert isinstance(result, TTSStreamResult)
    assert result.text_only_mode is True
    assert result.audio_bytes is None
    assert result.error_message is None


def test_generate_audio_empty_text():
    """Verify empty text string defaults to text_only_mode."""
    streamer = TTSStreamer()
    result = streamer.generate_audio("   ", char_id="lily")

    assert isinstance(result, TTSStreamResult)
    assert result.text_only_mode is True
    assert result.audio_bytes is None


def test_generate_audio_exception_fallback():
    """Verify exceptions during TTS synthesis log error and fallback to text_only_mode."""
    streamer = TTSStreamer()
    with patch("app.tts_streamer.generate_tts_mp3", side_effect=RuntimeError("TTS Provider Error")):
        result = streamer.generate_audio("Test audio failure", char_id="lily")

        assert isinstance(result, TTSStreamResult)
        assert result.text_only_mode is True
        assert result.audio_bytes is None
        assert "TTS Provider Error" in (result.error_message or "")


def test_stream_audio_chunks_success():
    """Verify async chunk streaming yields audio bytes."""
    async def _run():
        streamer = TTSStreamer()
        chunks = []
        async for chunk in streamer.stream_audio_chunks("Short phrase for streaming test"):
            chunks.append(chunk)
            if len(chunks) >= 2:
                break
        return chunks

    chunks = asyncio.run(_run())
    assert len(chunks) > 0
    assert isinstance(chunks[0], bytes)
    assert len(chunks[0]) > 0


def test_stream_audio_chunks_text_only_mode():
    """Verify async chunk streaming yields no chunks in text_only_mode."""
    async def _run():
        streamer = TTSStreamer()
        chunks = []
        async for chunk in streamer.stream_audio_chunks("Short phrase", text_only_mode=True):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_run())
    assert len(chunks) == 0


def test_stream_audio_chunks_exception_fallback():
    """Verify exception in stream_tts_mp3_chunks handles gracefully."""
    async def mock_failed_stream(*args, **kwargs):
        raise RuntimeError("Stream connection broken")
        yield b""  # unreachable yield to satisfy generator typing

    async def _run():
        streamer = TTSStreamer()
        chunks = []
        with patch("app.tts_streamer.stream_tts_mp3_chunks", side_effect=mock_failed_stream):
            async for chunk in streamer.stream_audio_chunks("Testing stream error"):
                chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_run())
    assert len(chunks) == 0


def test_convenience_functions():
    """Verify module-level convenience helper functions."""
    result = generate_audio_response("Convenience test", text_only_mode=True)
    assert isinstance(result, TTSStreamResult)
    assert result.text_only_mode is True

    async def _run_stream():
        chunks = []
        async for chunk in stream_audio_response("Convenience stream", text_only_mode=True):
            chunks.append(chunk)
        return chunks

    streamed = asyncio.run(_run_stream())
    assert len(streamed) == 0
