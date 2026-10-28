"""Unified Pronunciation & Dialogue Gateway.

Coordinates:
- Ingestion Context (Payload validator & Idempotency filter)
- Resilience & Dialogue Context (ModelMeshRouter with FSM fallback)
- Gamification Context (StreakEngine & TransactionalOutbox)

Engineered for Render Free Tier: memory footprint remains < 50MB RAM.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

from ..ingestion.idempotency import IdempotencyStore
from ..ingestion.validator import AudioPayloadValidator
from ..dialogue.fsm_engine import DialogueFSMEngine
from ..dialogue.phonetic_evaluator import PhoneticEvaluator, EvaluationResult
from ..resilience.circuit_breaker import CircuitBreaker
from ..resilience.model_mesh import ModelMeshRouter, ModelProvider, ExecutionResult
from ..gamification.streak_engine import StreakEngine, StreakUpdateResult
from ..gamification.outbox import TransactionalOutbox


@dataclass(slots=True)
class SubmissionRequest:
    """Input payload for a speaking exercise submission."""

    user_id: str
    exercise_id: str
    scenario_id: str
    current_node_id: Optional[str]
    idempotency_key: str
    audio_bytes: bytes
    reported_duration: Optional[float] = None
    transcribed_text: Optional[str] = None
    target_phonemes: list[tuple[str, str]] = field(default_factory=list)
    detected_phonemes: list[Optional[str]] = field(default_factory=list)


@dataclass(slots=True)
class SubmissionResponse:
    """Output payload returned to the client."""

    status: str
    overall_score: int
    accuracy_score: int
    fluency_score: int
    integrity_score: int
    ai_reply_text: str
    provider_used: str
    is_fallback: bool
    streak_count: int
    streak_incremented: bool
    total_xp: int
    total_latency_ms: float
    idempotency_hit: bool = False
    phoneme_feedback: list[dict[str, Any]] = field(default_factory=list)


class UnifiedPronunciationGateway:
    """High-concurrency, low-latency API orchestrator for language learning submissions."""

    def __init__(
        self,
        idempotency_store: Optional[IdempotencyStore] = None,
        fsm_engine: Optional[DialogueFSMEngine] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        model_mesh_router: Optional[ModelMeshRouter] = None,
        streak_engine: Optional[StreakEngine] = None,
        outbox: Optional[TransactionalOutbox] = None,
    ) -> None:
        self.idempotency_store = idempotency_store or IdempotencyStore(max_records=10_000)
        self.fsm_engine = fsm_engine or DialogueFSMEngine()
        self.circuit_breaker = circuit_breaker or CircuitBreaker(cool_down_seconds=10.0)
        self.model_mesh_router = model_mesh_router or ModelMeshRouter(
            fsm_engine=self.fsm_engine,
            circuit_breaker=self.circuit_breaker,
        )
        self.streak_engine = streak_engine or StreakEngine()
        self.outbox = outbox or TransactionalOutbox()

    def process_submission(
        self,
        request: SubmissionRequest,
        cloud_caller: Optional[Callable[[str, str], str]] = None,
    ) -> SubmissionResponse:
        """Executes the complete submission workflow within p95 <= 2,200ms."""
        t0 = time.time()

        # Step 1: Pre-flight payload validation (<15ms)
        AudioPayloadValidator.validate_all(
            request.audio_bytes,
            reported_duration=request.reported_duration,
        )

        # Step 2: Idempotency deduplication check (<50ms SLO)
        audio_hash = IdempotencyStore.compute_audio_hash(request.audio_bytes)
        is_hit, cached_payload = self.idempotency_store.check_or_lock(
            user_id=request.user_id,
            idempotency_key=request.idempotency_key,
            audio_hash=audio_hash,
        )

        if is_hit and cached_payload is not None:
            # Idempotency Cache Hit: return immediately (< 50ms)
            latency_ms = (time.time() - t0) * 1000.0
            return SubmissionResponse(
                status="success",
                overall_score=cached_payload["overall_score"],
                accuracy_score=cached_payload["accuracy_score"],
                fluency_score=cached_payload["fluency_score"],
                integrity_score=cached_payload["integrity_score"],
                ai_reply_text=cached_payload["ai_reply_text"],
                provider_used=cached_payload["provider_used"],
                is_fallback=cached_payload["is_fallback"],
                streak_count=cached_payload["streak_count"],
                streak_incremented=False,  # Duplicate never re-increments streak
                total_xp=cached_payload["total_xp"],
                total_latency_ms=latency_ms,
                idempotency_hit=True,
                phoneme_feedback=cached_payload.get("phoneme_feedback", []),
            )

        try:
            # Step 3: Phonetic evaluation & acoustic alignment
            user_text = request.transcribed_text or "hello"
            eval_result: EvaluationResult = PhoneticEvaluator.evaluate_utterance(
                target_phonemes=request.target_phonemes,
                detected_phonemes=request.detected_phonemes,
            )

            # Step 4: Dialogue continuation (Cloud LLM or In-Memory FSM fallback)
            exec_result: ExecutionResult = self.model_mesh_router.route_turn(
                scenario_id=request.scenario_id,
                current_node_id=request.current_node_id,
                user_text=user_text,
                cloud_caller=cloud_caller,
            )

            # Step 5: Gamification progression (Atomic Streak & XP Update)
            streak_result: StreakUpdateResult = self.streak_engine.process_activity(
                user_id=request.user_id,
                earned_xp=15,
            )

            # Step 6: Transactional Outbox Event Publication
            self.outbox.record_event(
                event_type="PronunciationEvaluated",
                payload={
                    "user_id": request.user_id,
                    "exercise_id": request.exercise_id,
                    "score": eval_result.overall_score,
                    "provider": exec_result.provider.value,
                    "streak_count": streak_result.current_streak,
                },
            )

            total_latency_ms = (time.time() - t0) * 1000.0

            # Step 7: Serialize phoneme feedback
            feedback_serialized = [
                {
                    "word": fb.word,
                    "target_phoneme": fb.target_phoneme,
                    "detected_phoneme": fb.detected_phoneme,
                    "error_type": fb.error_type.value,
                    "guidance": fb.guidance,
                }
                for fb in eval_result.phoneme_feedback
            ]

            response_data = {
                "overall_score": eval_result.overall_score,
                "accuracy_score": eval_result.accuracy_score,
                "fluency_score": eval_result.fluency_score,
                "integrity_score": eval_result.integrity_score,
                "ai_reply_text": exec_result.reply_text,
                "provider_used": exec_result.provider.value,
                "is_fallback": exec_result.is_fallback,
                "streak_count": streak_result.current_streak,
                "total_xp": streak_result.total_xp,
                "phoneme_feedback": feedback_serialized,
            }

            # Cache in Idempotency Store
            self.idempotency_store.complete(
                user_id=request.user_id,
                idempotency_key=request.idempotency_key,
                response_payload=response_data,
            )

            return SubmissionResponse(
                status="success",
                overall_score=eval_result.overall_score,
                accuracy_score=eval_result.accuracy_score,
                fluency_score=eval_result.fluency_score,
                integrity_score=eval_result.integrity_score,
                ai_reply_text=exec_result.reply_text,
                provider_used=exec_result.provider.value,
                is_fallback=exec_result.is_fallback,
                streak_count=streak_result.current_streak,
                streak_incremented=streak_result.streak_incremented,
                total_xp=streak_result.total_xp,
                total_latency_ms=total_latency_ms,
                idempotency_hit=False,
                phoneme_feedback=feedback_serialized,
            )

        except Exception:
            # On failure, release pending lock so user can retry
            self.idempotency_store.fail(request.user_id, request.idempotency_key)
            raise
