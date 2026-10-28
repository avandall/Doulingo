"""Tests for Resilience and Non-Sticky Circuit Breaker Bounded Context."""

import time
import pytest
from pipeline.src.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenException,
)
from pipeline.src.resilience.model_mesh import (
    ModelMeshRouter,
    ModelProvider,
    ExecutionResult,
)


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_trip_to_open_after_repeated_failures(self):
        cb = CircuitBreaker(failure_rate_threshold=0.5, sliding_window_size=6, min_calls_to_evaluate=4)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_half_open_transition_after_cooldown(self):
        cb = CircuitBreaker(cool_down_seconds=0.05, min_calls_to_evaluate=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Sleep past cool-down
        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.can_execute() is True

    def test_non_sticky_probe_success_resets_to_closed(self):
        cb = CircuitBreaker(cool_down_seconds=0.05, min_calls_to_evaluate=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN

        # Successful probe call resets state to CLOSED!
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


class TestModelMeshRouter:
    def test_exact_model_names_preserved(self):
        # Invariant check: Verify model names match exact system constants
        assert "qwen/qwen3.8-27b" in ModelMeshRouter.GROQ_MODELS
        assert "openai/gpt-oss-120b" in ModelMeshRouter.GROQ_MODELS
        assert "gemini-3.5-flash-lite" in ModelMeshRouter.GEMINI_MODELS
        assert "gemini-3.1-flash-lite" in ModelMeshRouter.GEMINI_MODELS

    def test_successful_cloud_execution(self):
        router = ModelMeshRouter()

        def mock_caller(model: str, prompt: str) -> str:
            return f"Mock reply from {model} for '{prompt}'"

        res = router.route_turn(
            scenario_id="cafe_order",
            current_node_id="order_drink",
            user_text="I want a latte",
            cloud_caller=mock_caller,
            preferred_provider=ModelProvider.GROQ,
        )
        assert res.is_fallback is False
        assert res.provider == ModelProvider.GROQ
        assert "qwen/qwen3.8-27b" in res.model_name
        assert "latte" in res.reply_text

    def test_per_request_non_sticky_fallback_flow(self):
        cb = CircuitBreaker(cool_down_seconds=0.05, min_calls_to_evaluate=1)
        router = ModelMeshRouter(circuit_breaker=cb)

        # 1. Turn 1: Cloud provider throws error -> Falls back to FSM
        def failing_caller(model: str, prompt: str) -> str:
            raise ConnectionError("Cloud LLM endpoint 503 unavailable")

        res_turn_1 = router.route_turn(
            scenario_id="cafe_order",
            current_node_id="order_drink",
            user_text="I would like a coffee",
            cloud_caller=failing_caller,
        )
        assert res_turn_1.is_fallback is True
        assert res_turn_1.provider == ModelProvider.LOCAL_FSM
        assert "coffee" in res_turn_1.reply_text

        # 2. Wait for cool-down
        time.sleep(0.06)

        # 3. Turn 2: Cloud provider is restored -> Immediately uses Cloud LLM (never sticky to FSM!)
        def healthy_caller(model: str, prompt: str) -> str:
            return "Sure! Would you like a small or large coffee?"

        res_turn_2 = router.route_turn(
            scenario_id="cafe_order",
            current_node_id="select_size",
            user_text="A large one please",
            cloud_caller=healthy_caller,
        )
        assert res_turn_2.is_fallback is False
        assert res_turn_2.provider == ModelProvider.GROQ
        assert cb.state == CircuitState.CLOSED
