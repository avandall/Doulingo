"""Mutation Invariant Verification Suite.

Validates the 5 Vital Invariants against AST mutation testing:
- Invariant 1: Idempotency & Exactly-Once Streak State Transition.
- Invariant 2: Audio Payload Integrity & Boundary Validation.
- Invariant 3: Core Flow Survival (3rd-party LLM decoupling).
- Invariant 4: Non-Sticky, Self-Healing Circuit Breaker.
- Invariant 5: Timezone-Aware Monotonic Streak Progression.
"""

import datetime
import time

import pytest

from pipeline.src.gamification.streak_engine import StreakEngine
from pipeline.src.gateway.app import SubmissionRequest, UnifiedPronunciationGateway
from pipeline.src.ingestion.idempotency import IdempotencyStore
from pipeline.src.ingestion.validator import AudioPayloadValidator, ValidationError
from pipeline.src.resilience.circuit_breaker import CircuitBreaker, CircuitState


class TestMutationInvariants:
    @pytest.fixture
    def valid_audio_bytes(self) -> bytes:
        return b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00mock_opus_audio_bytes"

    def test_invariant_1_idempotency_streak_protection(self, valid_audio_bytes):
        """Invariant 1: A user can never increment their streak more than once per day,

        even if identical or concurrent requests are sent.
        """
        gateway = UnifiedPronunciationGateway()
        req = SubmissionRequest(
            user_id="mut_user_1",
            exercise_id="ex_1",
            scenario_id="cafe_order",
            current_node_id="order_drink",
            idempotency_key="key_token_inv1",
            audio_bytes=valid_audio_bytes,
            reported_duration=5.0,
            transcribed_text="I want a latte",
            target_phonemes=[("latte", "/lɑːteɪ/")],
            detected_phonemes=["/lɑːteɪ/"],
        )

        # First submission
        res1 = gateway.process_submission(req)
        assert res1.streak_count == 1
        assert res1.streak_incremented is True
        assert res1.idempotency_hit is False

        # Duplicate submission with same idempotency key (Sub-50ms hit)
        t0 = time.time()
        res2 = gateway.process_submission(req)
        latency_ms = (time.time() - t0) * 1000.0

        assert res2.idempotency_hit is True
        assert res2.streak_count == 1  # Streak remained 1!
        assert res2.streak_incremented is False
        assert latency_ms < 50.0  # Idempotency SLO <= 50ms

    def test_invariant_2_payload_boundary_rejection(self):
        """Invariant 2: Audio payloads exceeding 3MB or 30s must be rejected < 15ms."""
        # 3.01 MB payload
        oversized = b"OggS" + (b"\x00" * (3 * 1024 * 1024 + 10))
        t0 = time.time()
        with pytest.raises(ValidationError) as exc_info:
            AudioPayloadValidator.validate_all(oversized)
        latency_ms = (time.time() - t0) * 1000.0

        assert exc_info.value.status_code == 413
        assert latency_ms < 15.0

    def test_invariant_3_core_flow_survival_on_llm_outage(self, valid_audio_bytes):
        """Invariant 3: Complete 3rd-party LLM outage must not prevent scoring and streak."""
        gateway = UnifiedPronunciationGateway()

        def blackhole_llm(model: str, prompt: str) -> str:
            raise ConnectionError("503 Service Unavailable: OpenAI and Gemini down")

        req = SubmissionRequest(
            user_id="mut_user_3",
            exercise_id="ex_3",
            scenario_id="cafe_order",
            current_node_id="order_drink",
            idempotency_key="key_inv3",
            audio_bytes=valid_audio_bytes,
            reported_duration=4.0,
            transcribed_text="I want a coffee",
            target_phonemes=[("coffee", "/kɔːfi/")],
            detected_phonemes=["/kɔːfi/"],
        )

        res = gateway.process_submission(req, cloud_caller=blackhole_llm)

        # Core flow survived via in-memory FSM fallback
        assert res.status == "success"
        assert res.is_fallback is True
        assert res.provider_used == "local_fsm"
        assert res.streak_incremented is True
        assert res.streak_count == 1
        assert "coffee" in res.ai_reply_text

    def test_invariant_4_non_sticky_circuit_breaker(self):
        """Invariant 4: Circuit breaker fallback to FSM is strictly per-request and heals."""
        cb = CircuitBreaker(cool_down_seconds=0.05, min_calls_to_evaluate=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN

        # Probe success immediately resets to CLOSED
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_invariant_5_monotonic_timezone_progression(self):
        """Invariant 5: Streak progress is strictly monotonic across local calendar days."""
        engine = StreakEngine()
        user_id = "mut_user_5"

        # Monday 23:00 local time
        t_monday = datetime.datetime(
            2026, 10, 26, 16, 0, 0, tzinfo=datetime.timezone.utc
        )
        res_mon = engine.process_activity(user_id, activity_timestamp=t_monday)
        assert res_mon.current_streak == 1

        # Tuesday 01:00 local time (only 2 hours later, but next calendar day!)
        t_tuesday = datetime.datetime(
            2026, 10, 26, 18, 0, 0, tzinfo=datetime.timezone.utc
        )
        res_tue = engine.process_activity(user_id, activity_timestamp=t_tuesday)
        assert res_tue.current_streak == 2  # Monotonic increment verified!
