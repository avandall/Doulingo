"""Gamification and User Progress Bounded Context.

Enforces:
- Timezone-aware monotonic streak calculations
- Invariant 1: Exactly-once daily activity recording
- Transactional Outbox pattern for asynchronous event consistency
"""

from .streak_engine import StreakEngine, StreakState, StreakUpdateResult
from .outbox import TransactionalOutbox, OutboxEvent, OutboxEventStatus

__all__ = [
    "StreakEngine",
    "StreakState",
    "StreakUpdateResult",
    "TransactionalOutbox",
    "OutboxEvent",
    "OutboxEventStatus",
]
