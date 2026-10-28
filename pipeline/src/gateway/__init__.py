"""Gateway Bounded Context.

Unified lightweight orchestrator (<50MB RAM footprint) coordinating
Ingestion, Resilience, Dialogue FSM, and Gamification contexts.
"""

from .app import UnifiedPronunciationGateway, SubmissionRequest, SubmissionResponse

__all__ = [
    "UnifiedPronunciationGateway",
    "SubmissionRequest",
    "SubmissionResponse",
]
