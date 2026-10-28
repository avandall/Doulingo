"""Ingestion and Idempotency Bounded Context.

Handles pre-flight payload validation, magic-byte inspection,
and sub-50ms idempotency deduplication under strict memory constraints (<15MB RAM).
"""

from .idempotency import IdempotencyRecord, IdempotencyStatus, IdempotencyStore
from .validator import AudioPayloadValidator, ValidationError

__all__ = [
    "IdempotencyStore",
    "IdempotencyRecord",
    "IdempotencyStatus",
    "AudioPayloadValidator",
    "ValidationError",
]
