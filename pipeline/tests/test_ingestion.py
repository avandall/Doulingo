"""Tests for Ingestion and Idempotency Bounded Context."""

import time

import pytest

from pipeline.src.ingestion.idempotency import IdempotencyStatus, IdempotencyStore
from pipeline.src.ingestion.validator import AudioPayloadValidator, ValidationError


class TestAudioPayloadValidator:
    def test_validate_valid_wav_header(self):
        # Construct valid minimal WAV PCM header
        # RIFF + length + WAVE + fmt + size(16) + format(1=PCM) + channels(1=mono) + sample_rate(16000) + byte_rate + block_align + bits_per_sample(16) + data
        header = bytearray(
            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        )
        fmt = AudioPayloadValidator.validate_all(bytes(header), reported_duration=5.0)
        assert fmt == "wav_pcm"

    def test_validate_valid_ogg_opus(self):
        header = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00fake_opus_content_data"
        fmt = AudioPayloadValidator.validate_all(header, reported_duration=12.5)
        assert fmt == "opus_ogg"

    def test_validate_valid_webm(self):
        header = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01fake_webm"
        fmt = AudioPayloadValidator.validate_all(header, reported_duration=29.9)
        assert fmt == "opus_webm"

    def test_reject_oversized_payload_3mb(self):
        oversized = b"OggS" + (b"\x00" * (3 * 1024 * 1024 + 1))
        t0 = time.time()
        with pytest.raises(ValidationError) as exc_info:
            AudioPayloadValidator.validate_all(oversized)
        latency_ms = (time.time() - t0) * 1000.0

        assert exc_info.value.status_code == 413
        assert "exceeds 3.0 MB limit" in str(exc_info.value)
        # Verify early rejection is well under 15ms
        assert latency_ms < 15.0

    def test_reject_duration_over_30s(self):
        header = b"OggS" + (b"\x00" * 100)
        with pytest.raises(ValidationError) as exc_info:
            AudioPayloadValidator.validate_all(header, reported_duration=30.5)
        assert exc_info.value.status_code == 400
        assert "exceeds maximum allowed 30.0 seconds" in str(exc_info.value)

    def test_reject_invalid_audio_format(self):
        fake_binary = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
        with pytest.raises(ValidationError) as exc_info:
            AudioPayloadValidator.validate_all(fake_binary)
        assert exc_info.value.status_code == 400
        assert "Unsupported audio format" in str(exc_info.value)


class TestIdempotencyStore:
    def test_check_or_lock_and_sub_50ms_hit(self):
        store = IdempotencyStore(max_records=100)
        user_id = "user_42"
        key = "req_token_abc123"
        audio_hash = "sha256_mock_hash_xyz"

        # First attempt: acquire lock
        is_hit, cached = store.check_or_lock(user_id, key, audio_hash)
        assert is_hit is False
        assert cached is None

        # Complete request with payload
        expected_response = {
            "score": 92,
            "streak_count": 15,
            "transcription": "Hello world",
        }
        store.complete(user_id, key, expected_response)

        # Second attempt: Idempotency Hit (must return in < 50ms)
        t0 = time.time()
        is_hit_2, cached_2 = store.check_or_lock(user_id, key, audio_hash)
        latency_ms = (time.time() - t0) * 1000.0

        assert is_hit_2 is True
        assert cached_2 == expected_response
        assert latency_ms < 50.0  # Idempotency SLO requirement

    def test_concurrent_pending_request_rejection(self):
        store = IdempotencyStore(max_records=10)
        user_id = "user_99"
        key = "req_in_flight"
        audio_hash = "mock_hash_99"

        # First request locks it
        store.check_or_lock(user_id, key, audio_hash)

        # Simultaneous second request before complete() raises error
        with pytest.raises(RuntimeError) as exc_info:
            store.check_or_lock(user_id, key, audio_hash)
        assert "Concurrent request in progress" in str(exc_info.value)

    def test_lru_eviction_under_memory_bound(self):
        # Test capacity cap
        store = IdempotencyStore(max_records=3)
        for i in range(5):
            store.check_or_lock("user", f"key_{i}", f"hash_{i}")
            store.complete("user", f"key_{i}", {"res": i})

        assert store.size() == 3
        # Earliest keys (key_0, key_1) should be evicted
        is_hit, _ = store.check_or_lock("user", "key_0", "hash_0")
        assert is_hit is False  # Re-registered as new lock because evicted
