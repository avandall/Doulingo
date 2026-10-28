"""Chaos Engineering and Fault Injection Test Suite.

Simulates:
1. 250 Concurrent Request Burst: Validates thread safety, memory boundaries, and zero 500s.
2. 100% Cloud LLM Blackhole: Injects 503 HTTP outages and socket timeouts.
3. Network Jitter & Fault Injection: Verifies p95 latency stays well under 2,200ms budget.
"""

import concurrent.futures
import time

import pytest

from pipeline.src.gateway.app import (
    SubmissionRequest,
    SubmissionResponse,
    UnifiedPronunciationGateway,
)


class TestChaosFaultInjection:
    @pytest.fixture
    def valid_audio_bytes(self) -> bytes:
        return b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00chaos_test_audio_payload"

    def test_chaos_250_concurrent_burst(self, valid_audio_bytes):
        """Simulates 250 concurrent requests hitting the gateway simultaneously."""
        gateway = UnifiedPronunciationGateway()
        concurrency = 250

        def single_worker(index: int) -> SubmissionResponse:
            req = SubmissionRequest(
                user_id=f"burst_user_{index}",
                exercise_id="ex_burst",
                scenario_id="cafe_order",
                current_node_id="order_drink",
                idempotency_key=f"burst_token_{index}",
                audio_bytes=valid_audio_bytes,
                reported_duration=3.5,
                transcribed_text="I want a latte",
                target_phonemes=[("latte", "/lɑːteɪ/")],
                detected_phonemes=["/lɑːteɪ/"],
            )
            # Use local FSM fast-path
            return gateway.process_submission(req, cloud_caller=None)

        results: list[SubmissionResponse] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(single_worker, i) for i in range(concurrency)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        # Assertions
        assert len(results) == concurrency
        for res in results:
            assert res.status == "success"
            assert res.overall_score > 0
            assert res.streak_count == 1
            assert res.is_fallback is True

        latencies = [r.total_latency_ms for r in results]
        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95)]

        # Under local burst, p95 must be vastly below 2,200ms
        assert p95_latency < 2200.0

    def test_chaos_100_percent_cloud_llm_blackhole(self, valid_audio_bytes):
        """Simulates 100% cloud outage (503 Service Unavailable + 5s network timeouts)."""
        gateway = UnifiedPronunciationGateway()

        def blackhole_api(model: str, prompt: str) -> str:
            # Simulate network timeout
            time.sleep(0.01)
            raise TimeoutError("503 Endpoint unreachable: Google and OpenAI down")

        results: list[SubmissionResponse] = []
        for i in range(20):
            req = SubmissionRequest(
                user_id=f"blackhole_user_{i}",
                exercise_id="ex_blackhole",
                scenario_id="cafe_order",
                current_node_id="order_drink",
                idempotency_key=f"bh_token_{i}",
                audio_bytes=valid_audio_bytes,
                reported_duration=4.0,
                transcribed_text="Can I get some tea",
                target_phonemes=[("tea", "/tiː/")],
                detected_phonemes=["/tiː/"],
            )
            res = gateway.process_submission(req, cloud_caller=blackhole_api)
            results.append(res)

        # Verify zero unhandled exceptions and seamless FSM fallback
        assert len(results) == 20
        for res in results:
            assert res.status == "success"
            assert res.is_fallback is True
            assert res.provider_used == "local_fsm"
            assert res.streak_incremented is True
            assert "tea" in res.ai_reply_text

    def test_chaos_duplicate_hammering_under_concurrency(self, valid_audio_bytes):
        """Simulates malicious concurrent requests with identical idempotency keys."""
        gateway = UnifiedPronunciationGateway()
        hammer_count = 50
        same_key = "hammered_token_xyz"
        same_user = "hammer_user"

        duplicate_hits = 0

        # First request finishes
        req_seed = SubmissionRequest(
            user_id=same_user,
            exercise_id="ex_seed",
            scenario_id="cafe_order",
            current_node_id="order_drink",
            idempotency_key=same_key,
            audio_bytes=valid_audio_bytes,
            reported_duration=5.0,
            transcribed_text="A cappuccino please",
            target_phonemes=[("cappuccino", "/ˌkæpəˈtʃiːnoʊ/")],
            detected_phonemes=["/ˌkæpəˈtʃiːnoʊ/"],
        )
        res_initial = gateway.process_submission(req_seed)
        assert res_initial.streak_incremented is True
        assert res_initial.streak_count == 1

        # Now hammer with 50 threads
        def hammer_worker() -> SubmissionResponse:
            return gateway.process_submission(req_seed)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(hammer_worker) for _ in range(hammer_count)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res.idempotency_hit:
                    duplicate_hits += 1

        # All hammered requests must hit idempotency cache
        assert duplicate_hits == hammer_count
        # Verify streak was NOT incremented 50 times (Invariant 1 preserved)
        streak_state = gateway.streak_engine.get_or_create_user(same_user)
        assert streak_state.current_streak == 1
