"""Unit tests for AIEngine Circuit Breaker & Fine-Grained Rate Limit Telemetry."""
import time
import pytest
from app.core.ai_engine import (
    _RATE_LIMIT_COOLDOWNS,
    KEY_EXHAUSTED_CACHE,
    is_key_exhausted,
    is_model_key_rate_limited,
    record_model_key_exhausted,
)


@pytest.fixture(autouse=True)
def clean_circuit_breaker():
    """Clear cooldowns before and after each test."""
    _RATE_LIMIT_COOLDOWNS.clear()
    KEY_EXHAUSTED_CACHE.clear()
    yield
    _RATE_LIMIT_COOLDOWNS.clear()
    KEY_EXHAUSTED_CACHE.clear()


def test_circuit_breaker_rpm_trip():
    """RPM rate limit trips (model, key) for 60 seconds."""
    model = "gemini-3.1-flash-lite"
    key = "AIzaSyFakeKey1234567890"

    assert not is_model_key_rate_limited(model, key)

    # Simulate 429 RPM payload
    rpm_payload = '{"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota).", "details": [{"description": "Quota exceeded for quota metric requests per minute"}]}}'
    record_model_key_exhausted(model, key, 429, rpm_payload)

    # Must be rate limited immediately
    assert is_model_key_rate_limited(model, key)

    # Different model on the same key must NOT be rate limited!
    assert not is_model_key_rate_limited("gemini-3.5-flash-lite", key)

    # Different key on the same model must NOT be rate limited!
    assert not is_model_key_rate_limited(model, "AIzaSyOtherKey9876543210")


def test_circuit_breaker_rpd_trip():
    """RPD rate limit trips (model, key) for 12 hours (43,200s)."""
    model = "gemini-2.5-flash"
    key = "AIzaSyFakeKey1234567890"

    rpd_payload = '{"error": {"code": 429, "message": "Quota exceeded for quota metric \'Generate Content API requests per day\'."}}'
    record_model_key_exhausted(model, key, 429, rpd_payload)

    assert is_model_key_rate_limited(model, key)
    expiry = _RATE_LIMIT_COOLDOWNS.get((model, key))
    assert expiry is not None
    # Remaining cooldown should be around 43200 seconds (> 40000)
    assert (expiry - time.time()) > 40000


def test_circuit_breaker_auth_failure_global_lockout():
    """401 or 403 triggers global key lockout."""
    key = "AIzaSyInvalidKey12345678"
    model = "gemini-3.1-flash-lite"

    record_model_key_exhausted(model, key, 401, "API key not valid. Please pass a valid API key.")

    assert is_key_exhausted(key)
    # Any model on this key is now blocked
    assert is_model_key_rate_limited(model, key)
    assert is_model_key_rate_limited("gemini-2.5-flash", key)


def test_circuit_breaker_404_model_not_found():
    """404 locks the non-existent model for 24h on that key."""
    key = "AIzaSyFakeKey1234567890"
    model = "gemini-unknown-model"

    record_model_key_exhausted(model, key, 404, "models/gemini-unknown-model is not found for API version v1beta")

    assert is_model_key_rate_limited(model, key)
    expiry = _RATE_LIMIT_COOLDOWNS.get((model, key))
    assert expiry is not None
    assert (expiry - time.time()) > 80000


def test_circuit_breaker_pre_flight_latency():
    """Pre-flight check in memory must take less than 0.05ms (0.00005s)."""
    key = "AIzaSyFakeKey1234567890"
    model = "gemini-3.1-flash-lite"

    t0 = time.perf_counter()
    for _ in range(1000):
        _ = is_model_key_rate_limited(model, key)
    elapsed = time.perf_counter() - t0

    avg_per_check = elapsed / 1000
    assert avg_per_check < 0.00005, f"Check took {avg_per_check*1000:.4f}ms, expected < 0.05ms"
