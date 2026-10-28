"""Gateway Bounded Context.

Unified lightweight orchestrator (<50MB RAM footprint) coordinating
Ingestion, Resilience, Dialogue FSM, and Gamification contexts.
"""

from .app import SubmissionRequest, SubmissionResponse, UnifiedPronunciationGateway

__all__ = [
    "SubmissionRequest",
    "SubmissionResponse",
    "UnifiedPronunciationGateway",
]
