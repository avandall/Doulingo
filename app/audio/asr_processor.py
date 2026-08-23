"""
Streaming ASR Ingestion & Chunk Processor (app/asr_processor.py)
TASK-004: Handles streaming audio chunks, cumulative timestamp offsets based on audio sample count,
word-level timestamp mapping, and raw audio buffer retention for Pronunciation GOP scoring.
"""

import struct
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WordTimestamp:
    """Represents a word with start and end timestamps (in seconds) and confidence score."""

    word: str
    start_time: float
    end_time: float
    confidence: float = 1.0


@dataclass
class ASRChunkResult:
    """Result returned by ASR engine for a single audio chunk.

    Words timestamps inside chunk are local (relative to start of chunk, 0.0s).
    """

    transcript: str
    words: list[WordTimestamp] = field(default_factory=list)


class StreamingSessionState:
    """Manages streaming session state for ASR ingestion and timestamp tracking.

    Offset calculation is strictly sample-count based to avoid time drift from network latency.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        sample_width: int = 2,
        channels: int = 1,
    ) -> None:
        """Initialize session state.

        Args:
            sample_rate: Audio sampling frequency in Hz (default: 16000).
            sample_width: Sample width in bytes for raw PCM (default: 2 bytes for 16-bit PCM).
            channels: Number of audio channels (default: 1 for mono).
        """
        self.sample_rate: int = sample_rate
        self.sample_width: int = sample_width
        self.channels: int = channels

        self.cumulative_offset_sec: float = 0.0
        self.all_words: list[WordTimestamp] = []
        self.transcripts: list[str] = []
        self._audio_buffer: bytearray = bytearray()
        self._total_samples: int = 0

    def calculate_chunk_duration(self, audio_chunk: bytes | bytearray | list[Any] | Any) -> float:
        """Calculate exact chunk duration in seconds based on sample count.

        Args:
            audio_chunk: Audio raw bytes, bytearray, list, or array-like object.

        Returns:
            Duration in seconds (float).
        """
        if isinstance(audio_chunk, (bytes, bytearray)):
            bytes_per_frame = self.sample_width * self.channels
            if bytes_per_frame <= 0:
                bytes_per_frame = 2
            num_samples = len(audio_chunk) // bytes_per_frame
        elif hasattr(audio_chunk, "__len__"):
            num_samples = len(audio_chunk)
        else:
            num_samples = 0

        if self.sample_rate <= 0:
            return 0.0

        return num_samples / float(self.sample_rate)

    def process_chunk(
        self,
        audio_chunk: bytes | bytearray | list[Any] | Any,
        asr_result: ASRChunkResult,
    ) -> list[WordTimestamp]:
        """Process an incoming audio chunk and map its local word timestamps to global session time.

        Args:
            audio_chunk: Raw audio chunk data.
            asr_result: ASR recognition output with local timestamps.

        Returns:
            List of new WordTimestamp objects with global timestamps for this chunk.
        """
        chunk_duration_sec = self.calculate_chunk_duration(audio_chunk)

        # Accumulate raw audio buffer
        if isinstance(audio_chunk, (bytes, bytearray)):
            self._audio_buffer.extend(audio_chunk)
            bytes_per_frame = self.sample_width * self.channels
            if bytes_per_frame > 0:
                self._total_samples += len(audio_chunk) // bytes_per_frame
        elif hasattr(audio_chunk, "__len__"):
            self._total_samples += len(audio_chunk)

        # Map local words to global timestamps
        chunk_words: list[WordTimestamp] = []
        for w in asr_result.words:
            global_word = WordTimestamp(
                word=w.word,
                start_time=round(w.start_time + self.cumulative_offset_sec, 4),
                end_time=round(w.end_time + self.cumulative_offset_sec, 4),
                confidence=w.confidence,
            )
            chunk_words.append(global_word)
            self.all_words.append(global_word)

        if asr_result.transcript and asr_result.transcript.strip():
            self.transcripts.append(asr_result.transcript.strip())

        # Advance cumulative offset AFTER mapping words of current chunk
        self.cumulative_offset_sec += chunk_duration_sec

        return chunk_words

    def get_transcript(self) -> str:
        """Return combined full transcript for the session."""
        return " ".join(self.transcripts)

    def get_word_timestamps(self) -> list[WordTimestamp]:
        """Return all global word timestamps across the session."""
        return list(self.all_words)

    def get_audio_buffer(self) -> bytes:
        """Return accumulated raw audio bytes for Pronunciation GOP scoring."""
        return bytes(self._audio_buffer)

    def get_total_duration(self) -> float:
        """Return total audio duration in seconds calculated from sample count."""
        if self.sample_rate <= 0:
            return 0.0
        return self._total_samples / float(self.sample_rate)

    def is_silence_chunk(self, audio_chunk: bytes | bytearray | list[Any] | Any, threshold: float = 0.01) -> bool:
        """Helper to check if audio chunk represents silence (useful for VAD).

        Args:
            audio_chunk: Audio raw bytes or sample list.
            threshold: Amplitude threshold for silence detection.

        Returns:
            True if chunk is silent or empty.
        """
        if not audio_chunk:
            return True

        if isinstance(audio_chunk, (bytes, bytearray)):
            if len(audio_chunk) == 0:
                return True
            sample_width = 2
            count = len(audio_chunk) // sample_width
            if count == 0:
                return True
            try:
                samples = struct.unpack(f"<{count}h", bytes(audio_chunk[: count * sample_width]))
                sum_sq = sum(s * s for s in samples)
                rms = (sum_sq / count) ** 0.5
                normalized_rms = rms / 32768.0
                return normalized_rms < threshold
            except Exception:
                return False
        return False

    def reset(self) -> None:
        """Reset session state to initial state."""
        self.cumulative_offset_sec = 0.0
        self.all_words.clear()
        self.transcripts.clear()
        self._audio_buffer.clear()
        self._total_samples = 0
