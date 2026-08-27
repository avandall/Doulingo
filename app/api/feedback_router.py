"""
app/api/feedback_router.py
===========================
FastAPI Router for Response Rating API & Continuous Feedback Logger (TASK-007).
Exposes POST /api/v1/feedback/rate-response.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.feedback_service import FeedbackService

logger = logging.getLogger("duolingo_speak.api.feedback")

router = APIRouter(tags=["Feedback & Continuous Improvement"])


class RateResponseRequest(BaseModel):
    """Payload schema for rating an AI response."""

    response_text: str = Field(..., description="AI response text being evaluated")
    rating: str = Field(
        ..., description="Rating grade: 'hollow', 'out_of_context', or 'good'"
    )
    dialogue_id: str | None = Field(
        None, description="Optional ID of exemplar if from RAG sample dialogue bank"
    )
    context: dict[str, Any] | None = Field(
        default_factory=dict, description="Metadata context (level, persona, topic, etc.)"
    )
    user_id: str | None = Field(None, description="Optional user ID submitting feedback")
    comments: str | None = Field(None, description="Optional feedback comment")


class RateResponseResponse(BaseModel):
    """Response schema for rating submission."""

    status: str = Field(..., description="Status string e.g. 'success'")
    message: str = Field(..., description="Human-readable status message")
    feedback_id: str = Field(..., description="Unique generated feedback ID")
    rating: str = Field(..., description="Normalized rating value")
    bank_action: str | None = Field(
        None, description="Action taken on dialogue bank (penalized, boosted, added_new)"
    )
    dialogue_id: str | None = Field(
        None, description="ID of affected or created dialogue exemplar"
    )
    new_quality_score: float | None = Field(
        None, description="Updated or initial quality score"
    )
    is_blacklisted: bool = Field(
        False, description="Whether exemplar is blacklisted from RAG retrieval"
    )


@router.post("/api/v1/feedback/rate-response", response_model=RateResponseResponse)
def rate_response(payload: RateResponseRequest) -> dict[str, Any]:
    """
    Endpoint: POST /api/v1/feedback/rate-response
    Logs user rating into app/data/feedback_log.json and updates dialogue bank quality score.
    """
    service = FeedbackService()
    try:
        result = service.rate_response(
            response_text=payload.response_text,
            rating=payload.rating,
            dialogue_id=payload.dialogue_id,
            context=payload.context,
            user_id=payload.user_id,
            comments=payload.comments,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing feedback: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal feedback server error: {e!s}")
