"""Gamification and User Progress Bounded Context.

Enforces:
- Timezone-aware monotonic streak calculations
- Invariant 1: Exactly-once daily activity recording
- Transactional Outbox pattern for asynchronous event consistency
"""

from .outbox import OutboxEvent, OutboxEventStatus, TransactionalOutbox
from .streak_engine import StreakEngine, StreakState, StreakUpdateResult

__all__ = [
    "OutboxEvent",
    "OutboxEventStatus",
    "StreakEngine",
    "StreakState",
    "StreakUpdateResult",
    "TransactionalOutbox",
]
