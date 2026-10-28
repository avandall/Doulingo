"""FastAPI Production Server for Render Free Tier.

Exposes REST endpoints:
- GET /health: Healthcheck and memory usage monitor (<50MB).
- GET /scenarios: List available CEFR dialogue scenarios.
- POST /api/submit: Unified speaking submission endpoint.
"""

from __future__ import annotations

import base64
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pipeline.src.gateway.app import (
    UnifiedPronunciationGateway,
    SubmissionRequest,
    SubmissionResponse,
)
from pipeline.src.dialogue.cefr_catalog import CEFRScenarioCatalog
from pipeline.src.ingestion.validator import ValidationError

app = FastAPI(
    title="Resilient Pronunciation & Dialogue API",
    version="2.0.0",
    description="High-throughput, low-latency language learning platform optimized for Render Free Tier.",
)

gateway = UnifiedPronunciationGateway()


class SubmitRequestBody(BaseModel):
    user_id: str
    exercise_id: str
    scenario_id: str
    current_node_id: Optional[str] = None
    idempotency_key: str
    audio_base64: str = Field(description="Base64 encoded Opus or WAV 16kHz audio")
    reported_duration: Optional[float] = None
    transcribed_text: Optional[str] = None
    target_phonemes: list[tuple[str, str]] = Field(default_factory=list)
    detected_phonemes: list[Optional[str]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "pronunciation-dialogue-gateway",
        "version": "2.0.0",
        "idempotency_records": gateway.idempotency_store.size(),
        "outbox_events": gateway.outbox.size(),
    }


@app.get("/scenarios")
def list_scenarios() -> list[str]:
    return CEFRScenarioCatalog.list_scenarios()


@app.post("/api/submit")
def submit_speaking(body: SubmitRequestBody) -> dict[str, Any]:
    try:
        audio_bytes = base64.b64decode(body.audio_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 audio payload: {e}") from e

    req = SubmissionRequest(
        user_id=body.user_id,
        exercise_id=body.exercise_id,
        scenario_id=body.scenario_id,
        current_node_id=body.current_node_id,
        idempotency_key=body.idempotency_key,
        audio_bytes=audio_bytes,
        reported_duration=body.reported_duration,
        transcribed_text=body.transcribed_text,
        target_phonemes=body.target_phonemes,
        detected_phonemes=body.detected_phonemes,
    )

    try:
        res: SubmissionResponse = gateway.process_submission(req)
        return {
            "status": res.status,
            "overall_score": res.overall_score,
            "accuracy_score": res.accuracy_score,
            "fluency_score": res.fluency_score,
            "integrity_score": res.integrity_score,
            "ai_reply_text": res.ai_reply_text,
            "provider_used": res.provider_used,
            "is_fallback": res.is_fallback,
            "streak_count": res.streak_count,
            "streak_incremented": res.streak_incremented,
            "total_xp": res.total_xp,
            "total_latency_ms": res.total_latency_ms,
            "idempotency_hit": res.idempotency_hit,
            "phoneme_feedback": res.phoneme_feedback,
        }
    except ValidationError as ve:
        raise HTTPException(status_code=ve.status_code, detail=str(ve)) from ve
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Internal processing error: {err}") from err


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
