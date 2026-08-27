"""
TTS Audio Output Streamer (`app/tts_streamer.py`)

Module providing high-level audio synthesis streaming and buffer generation
for Conversational Agent responses (`ai_utterance`). Wraps underlying multi-provider
TTS infrastructure with explicit `text_only_mode` fallback capabilities and error resilience.
"""

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from app.audio.tts_service import (
    generate_tts_mp3,
    stream_sentence_level_tts,
    stream_tts_mp3_chunks,
)

logger = logging.getLogger("duolingo_speak.tts_streamer")


@dataclass
class TTSStreamResult:
    """Dataclass holding complete synthesized audio output or text-only fallback state."""

    audio_bytes: bytes | None = None
    content_type: str = "audio/mpeg"
    text_only_mode: bool = False
    error_message: str | None = None


class TTSStreamer:
    """High-level TTS streaming controller for generating audio responses."""

    def __init__(self, default_char_id: str = "lily", default_text_only: bool = False) -> None:
        self.default_char_id = default_char_id
        self.default_text_only = default_text_only

    def generate_audio(
        self,
        text: str,
        char_id: str | None = None,
        text_only_mode: bool | None = None,
    ) -> TTSStreamResult:
        """Synthesize complete MP3 audio buffer from text string.

        If text_only_mode is enabled or if audio synthesis fails, returns a result
        marked text_only_mode=True without throwing an exception.
        """
        is_text_only = self.default_text_only if text_only_mode is None else text_only_mode
        character = char_id or self.default_char_id

        if is_text_only or not text or not text.strip():
            logger.info("TTS skipped (text_only_mode=True or empty text)")
            return TTSStreamResult(
                audio_bytes=None,
                content_type="audio/mpeg",
                text_only_mode=True,
                error_message=None,
            )

        try:
            mp3_fp = generate_tts_mp3(text=text, char_id=character)
            raw_bytes = mp3_fp.getvalue() if mp3_fp else b""
            if not raw_bytes:
                logger.warning("TTS returned empty bytes, falling back to text-only mode")
                return TTSStreamResult(
                    audio_bytes=None,
                    content_type="audio/mpeg",
                    text_only_mode=True,
                    error_message="Empty audio payload generated",
                )
            return TTSStreamResult(
                audio_bytes=raw_bytes,
                content_type="audio/mpeg",
                text_only_mode=False,
                error_message=None,
            )
        except Exception as err:
            logger.error("TTS generation error in generate_audio: %s", err, exc_info=True)
            return TTSStreamResult(
                audio_bytes=None,
                content_type="audio/mpeg",
                text_only_mode=True,
                error_message=str(err),
            )

    async def stream_audio_chunks(
        self,
        text: str,
        char_id: str | None = None,
        text_only_mode: bool | None = None,
    ) -> AsyncGenerator[bytes]:
        """Asynchronously stream MP3 audio chunks for low-latency playback.

        If text_only_mode is enabled or synthesis fails, yields nothing.
        """
        is_text_only = self.default_text_only if text_only_mode is None else text_only_mode
        character = char_id or self.default_char_id

        if is_text_only or not text or not text.strip():
            logger.info("TTS streaming skipped (text_only_mode=True or empty text)")
            return

        try:
            async for chunk in stream_tts_mp3_chunks(text=text, char_id=character):
                if chunk:
                    yield chunk
        except Exception as err:
            logger.error("Error during TTS chunk streaming: %s", err, exc_info=True)
            return

    async def stream_sentence_audio_chunks(
        self,
        text: str,
        char_id: str | None = None,
        text_only_mode: bool | None = None,
    ) -> AsyncGenerator[bytes]:
        """Asynchronously stream MP3 audio chunks sentence-by-sentence for <1.0s TTFA playback."""
        is_text_only = self.default_text_only if text_only_mode is None else text_only_mode
        character = char_id or self.default_char_id

        if is_text_only or not text or not text.strip():
            logger.info("Sentence TTS streaming skipped (text_only_mode=True or empty text)")
            return

        try:
            async for chunk in stream_sentence_level_tts(text=text, char_id=character):
                if chunk:
                    yield chunk
        except Exception as err:
            logger.error("Error during sentence TTS chunk streaming: %s", err, exc_info=True)
            return


# Module-level convenience functions
def generate_audio_response(
    text: str,
    char_id: str = "lily",
    text_only_mode: bool = False,
) -> TTSStreamResult:
    """Convenience function to synthesize audio buffer for a given response."""
    streamer = TTSStreamer()
    return streamer.generate_audio(text=text, char_id=char_id, text_only_mode=text_only_mode)


async def stream_audio_response(
    text: str,
    char_id: str = "lily",
    text_only_mode: bool = False,
) -> AsyncGenerator[bytes]:
    """Convenience async generator to stream audio chunks for a given response."""
    streamer = TTSStreamer()
    async for chunk in streamer.stream_audio_chunks(
        text=text, char_id=char_id, text_only_mode=text_only_mode
    ):
        yield chunk


async def stream_sentence_audio_response(
    text: str,
    char_id: str = "lily",
    text_only_mode: bool = False,
) -> AsyncGenerator[bytes]:
    """Convenience async generator to stream sentence-level audio chunks for low latency."""
    streamer = TTSStreamer()
    async for chunk in streamer.stream_sentence_audio_chunks(
        text=text, char_id=char_id, text_only_mode=text_only_mode
    ):
        yield chunk

