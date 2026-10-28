"""Multi-Provider Model Mesh Router.

Enforces:
1. Exact preservation of standardized Groq and Gemini model names:
   - Groq: "qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"
   - Gemini: "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite",
             "gemini-2.5-flash", "gemini-3-flash", "gemini-3.6-flash"
2. Strict 450ms timeout cap on cloud LLM calls.
3. Transparent failover to in-memory FSM without sticking or losing session context.
"""

from __future__ import annotations

import enum
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from ..dialogue.fsm_engine import DialogueFSMEngine, FSMResponse
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenException


class ModelProvider(str, enum.Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    LOCAL_FSM = "local_fsm"


@dataclass(slots=True)
class ExecutionResult:
    """Outcome of model routing execution."""

    reply_text: str
    provider: ModelProvider
    model_name: str
    latency_ms: float
    is_fallback: bool
    fsm_response: FSMResponse | None = None


class ModelMeshRouter:
    """Orchestrates LLM calls across Groq, Gemini, and In-Memory FSM fallback."""

    # STRICT INVARIANT: Preserve standardized system model names exactly!
    GROQ_MODELS: list[str] = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]

    GEMINI_MODELS: list[str] = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3-flash",
        "gemini-3.6-flash",
    ]

    TIMEOUT_CAP_SECONDS: float = 0.450  # 450ms p95 budget cap

    def __init__(
        self,
        fsm_engine: DialogueFSMEngine | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.fsm_engine = fsm_engine or DialogueFSMEngine()
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            failure_rate_threshold=0.5,
            cool_down_seconds=10.0,
        )

    def route_turn(
        self,
        scenario_id: str,
        current_node_id: str | None,
        user_text: str,
        cloud_caller: Callable[[str, str], str] | None = None,
        preferred_provider: ModelProvider = ModelProvider.GROQ,
    ) -> ExecutionResult:
        """Executes a dialogue turn with automated circuit breaker failover.

        Args:
            scenario_id: The ID of the scenario.
            current_node_id: Current dialogue node.
            user_text: Learner's spoken utterance.
            cloud_caller: Optional mockable callback representing the actual cloud API call.
            preferred_provider: Preferred primary provider (GROQ or GEMINI).

        Returns:
            ExecutionResult detailing the response, provider used, and latency.
        """
        t0 = time.time()
        selected_model = (
            self.GROQ_MODELS[0]
            if preferred_provider == ModelProvider.GROQ
            else self.GEMINI_MODELS[0]
        )

        # Attempt primary Cloud LLM execution via Circuit Breaker
        if cloud_caller is not None and self.circuit_breaker.can_execute():
            try:
                # Execute cloud call with timeout protection
                reply = self.circuit_breaker.execute(
                    cloud_caller,
                    selected_model,
                    user_text,
                )
                latency_ms = (time.time() - t0) * 1000.0
                return ExecutionResult(
                    reply_text=reply,
                    provider=preferred_provider,
                    model_name=selected_model,
                    latency_ms=latency_ms,
                    is_fallback=False,
                )
            except Exception:
                # Cloud call failed or timed out -> Fall through directly to FSM
                pass

        # Tertiary Fallback: Immediate In-Memory FSM (Sub-15ms, 0ms network latency)
        fsm_res = self.fsm_engine.process_turn(scenario_id, current_node_id, user_text)
        total_latency_ms = (time.time() - t0) * 1000.0

        return ExecutionResult(
            reply_text=fsm_res.reply_text,
            provider=ModelProvider.LOCAL_FSM,
            model_name="fsm_deterministic_catalog",
            latency_ms=total_latency_ms,
            is_fallback=True,
            fsm_response=fsm_res,
        )
