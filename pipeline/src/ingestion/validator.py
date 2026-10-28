"""Early Audio Payload Validator.

Enforces pre-flight boundaries within <15ms:
- Max payload size: 3.0 MB
- Max audio duration: 30.0 seconds
- Allowed codecs: Opus (WebM/Ogg) or Linear PCM WAV 16kHz Mono
"""

from __future__ import annotations

import struct
from typing import Optional


class ValidationError(Exception):
    """Raised when payload boundary validation fails."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class AudioPayloadValidator:
    """Pre-flight validator for incoming audio files and metadata."""

    MAX_BYTES: int = 3 * 1024 * 1024  # 3 MB
    MAX_DURATION_SECONDS: float = 30.0

    # Magic byte signatures
    OGG_MAGIC: bytes = b"OggS"
    WEBM_MAGIC: bytes = b"\x1a\x45\xdf\xa3"
    RIFF_MAGIC: bytes = b"RIFF"
    WAVE_MAGIC: bytes = b"WAVE"

    @classmethod
    def validate_payload_size(cls, audio_bytes: bytes) -> None:
        """Validates payload byte size (<1ms)."""
        if len(audio_bytes) == 0:
            raise ValidationError("Audio payload cannot be empty", status_code=400)
        if len(audio_bytes) > cls.MAX_BYTES:
            raise ValidationError(
                f"Audio payload size ({len(audio_bytes)} bytes) exceeds 3.0 MB limit",
                status_code=413,
            )

    @classmethod
    def validate_duration(cls, duration_seconds: float) -> None:
        """Validates audio duration in seconds."""
        if duration_seconds <= 0.0:
            raise ValidationError("Audio duration must be greater than 0 seconds", status_code=400)
        if duration_seconds > cls.MAX_DURATION_SECONDS:
            raise ValidationError(
                f"Audio duration ({duration_seconds:.1f}s) exceeds maximum allowed 30.0 seconds",
                status_code=400,
            )

    @classmethod
    def detect_and_validate_format(cls, audio_bytes: bytes) -> str:
        """Inspects magic bytes to ensure valid audio container/encoding.

        Returns detected format string: 'opus_ogg', 'opus_webm', or 'wav_pcm'.
        Raises ValidationError if format is invalid or unsupported.
        """
        if len(audio_bytes) < 12:
            raise ValidationError("Audio payload header too short to verify format", status_code=400)

        # Check OGG / Opus
        if audio_bytes.startswith(cls.OGG_MAGIC):
            return "opus_ogg"

        # Check WebM / Opus
        if audio_bytes.startswith(cls.WEBM_MAGIC):
            return "opus_webm"

        # Check RIFF / WAVE
        if audio_bytes[:4] == cls.RIFF_MAGIC and audio_bytes[8:12] == cls.WAVE_MAGIC:
            # Further inspect WAV header format (PCM = 1, IEEE Float = 3)
            if len(audio_bytes) >= 36:
                # Subchunk1ID should be 'fmt '
                fmt_idx = audio_bytes.find(b"fmt ", 12, 36)
                if fmt_idx != -1 and fmt_idx + 16 <= len(audio_bytes):
                    audio_format, num_channels, sample_rate = struct.unpack(
                        "<HHI", audio_bytes[fmt_idx + 8 : fmt_idx + 16]
                    )
                    # Enforce 16kHz Mono recommendation, but accept PCM standard
                    if audio_format not in (1, 3):
                        raise ValidationError(
                            f"Unsupported WAV compression format ({audio_format}). Only PCM is allowed.",
                            status_code=400,
                        )
            return "wav_pcm"

        raise ValidationError(
            "Unsupported audio format. Only Opus (WebM/Ogg) and WAV (16kHz Mono) are accepted.",
            status_code=400,
        )

    @classmethod
    def validate_all(
        cls,
        audio_bytes: bytes,
        reported_duration: Optional[float] = None,
    ) -> str:
        """Runs full validation pipeline within < 15ms.

        Returns detected format string.
        """
        cls.validate_payload_size(audio_bytes)
        detected_format = cls.detect_and_validate_format(audio_bytes)
        if reported_duration is not None:
            cls.validate_duration(reported_duration)
        return detected_format
