"""
Unit tests for app/asr_processor.py (TASK-004)
Testing Streaming ASR Ingestion, Cumulative Sample Timestamps, Wall-clock Independence, and Audio Buffer.
"""

import time

import pytest

from app.audio.asr_processor import ASRChunkResult, StreamingSessionState, WordTimestamp


def generate_dummy_pcm(duration_sec: float, sample_rate: int = 16000, sample_width: int = 2) -> bytes:
    """Generate silent raw PCM audio bytes of specified duration."""
    num_samples = int(duration_sec * sample_rate)
    return b"\x00" * (num_samples * sample_width)


def test_non_uniform_chunks_offset_calculation() -> None:
    """Test 3 non-uniform consecutive audio chunks and verify cumulative offset calculation."""
    session = StreamingSessionState(sample_rate=16000)

    # Chunk 1: 1.0s audio (16,000 samples = 32,000 bytes)
    chunk1_bytes = generate_dummy_pcm(1.0)
    asr1 = ASRChunkResult(
        transcript="Hello",
        words=[WordTimestamp(word="Hello", start_time=0.1, end_time=0.5, confidence=0.95)],
    )
    words1 = session.process_chunk(chunk1_bytes, asr1)

    assert len(words1) == 1
    assert words1[0].start_time == pytest.approx(0.1, abs=1e-3)
    assert words1[0].end_time == pytest.approx(0.5, abs=1e-3)
    assert session.cumulative_offset_sec == pytest.approx(1.0, abs=1e-3)

    # Chunk 2: 2.5s audio (40,000 samples = 80,000 bytes)
    chunk2_bytes = generate_dummy_pcm(2.5)
    asr2 = ASRChunkResult(
        transcript="world today",
        words=[
            WordTimestamp(word="world", start_time=0.2, end_time=0.7, confidence=0.90),
            WordTimestamp(word="today", start_time=1.0, end_time=1.8, confidence=0.88),
        ],
    )
    words2 = session.process_chunk(chunk2_bytes, asr2)

    assert len(words2) == 2
    assert words2[0].start_time == pytest.approx(1.2, abs=1e-3)  # 0.2 + 1.0
    assert words2[0].end_time == pytest.approx(1.7, abs=1e-3)  # 0.7 + 1.0
    assert words2[1].start_time == pytest.approx(2.0, abs=1e-3)  # 1.0 + 1.0
    assert words2[1].end_time == pytest.approx(2.8, abs=1e-3)  # 1.8 + 1.0
    assert session.cumulative_offset_sec == pytest.approx(3.5, abs=1e-3)  # 1.0 + 2.5

    # Chunk 3: 0.5s audio
    chunk3_bytes = generate_dummy_pcm(0.5)
    asr3 = ASRChunkResult(
        transcript="again",
        words=[WordTimestamp(word="again", start_time=0.1, end_time=0.4, confidence=0.92)],
    )
    words3 = session.process_chunk(chunk3_bytes, asr3)

    assert words3[0].start_time == pytest.approx(3.6, abs=1e-3)  # 0.1 + 3.5
    assert session.cumulative_offset_sec == pytest.approx(4.0, abs=1e-3)  # 3.5 + 0.5


def test_network_delay_independence() -> None:
    """Test that artificial network delays do NOT alter timestamp offset calculations."""
    session = StreamingSessionState(sample_rate=16000)

    chunk_bytes = generate_dummy_pcm(1.5)
    asr_res = ASRChunkResult(
        transcript="test delay",
        words=[WordTimestamp(word="test", start_time=0.1, end_time=0.6, confidence=0.9)],
    )

    # Simulate network delay before processing chunk
    time.sleep(0.05)
    words = session.process_chunk(chunk_bytes, asr_res)

    assert words[0].start_time == pytest.approx(0.1, abs=1e-3)
    assert words[0].end_time == pytest.approx(0.6, abs=1e-3)
    assert session.cumulative_offset_sec == pytest.approx(1.5, abs=1e-3)


def test_silence_and_empty_chunks() -> None:
    """Test that silence or empty chunks advance cumulative offset without creating false words."""
    session = StreamingSessionState(sample_rate=16000)

    # Silent chunk with 1.0s audio
    silent_bytes = generate_dummy_pcm(1.0)
    empty_asr = ASRChunkResult(transcript="", words=[])

    words = session.process_chunk(silent_bytes, empty_asr)

    assert len(words) == 0
    assert session.cumulative_offset_sec == pytest.approx(1.0, abs=1e-3)
    assert session.is_silence_chunk(silent_bytes) is True


def test_total_session_duration_accuracy() -> None:
    """Test that total accumulated duration matches total audio sample duration (< 10ms error margin)."""
    session = StreamingSessionState(sample_rate=16000)

    durations = [0.8, 1.25, 0.45, 2.1]
    total_expected = sum(durations)

    for d in durations:
        pcm = generate_dummy_pcm(d)
        session.process_chunk(pcm, ASRChunkResult(transcript="a", words=[]))

    assert session.get_total_duration() == pytest.approx(total_expected, abs=1e-4)
    assert session.cumulative_offset_sec == pytest.approx(total_expected, abs=1e-4)


def test_audio_buffer_accumulation_and_reset() -> None:
    """Test that raw audio bytes buffer accumulates properly and reset clears all state."""
    session = StreamingSessionState(sample_rate=16000)

    b1 = b"\x01\x02" * 8000  # 0.5s
    b2 = b"\x03\x04" * 8000  # 0.5s

    session.process_chunk(b1, ASRChunkResult(transcript="one", words=[]))
    session.process_chunk(b2, ASRChunkResult(transcript="two", words=[]))

    buf = session.get_audio_buffer()
    assert len(buf) == len(b1) + len(b2)
    assert buf == b1 + b2
    assert session.get_transcript() == "one two"

    # Test reset
    session.reset()
    assert session.cumulative_offset_sec == 0.0
    assert len(session.get_word_timestamps()) == 0
    assert len(session.get_audio_buffer()) == 0
    assert session.get_transcript() == ""
