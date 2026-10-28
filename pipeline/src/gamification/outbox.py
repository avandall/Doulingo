"""Transactional Outbox Pattern Implementation.

Ensures eventual consistency without 2PC by persisting domain events
atomically with entity mutations before streaming them to downstream consumers.
"""

from __future__ import annotations

import collections
import enum
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


class OutboxEventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


@dataclass(slots=True)
class OutboxEvent:
    """Represents a domain event stored in the transactional outbox."""

    event_id: str
    event_type: str
    payload: dict[str, Any]
    status: OutboxEventStatus = OutboxEventStatus.PENDING
    created_at: float = field(default_factory=time.time)
    published_at: float | None = None
    retry_count: int = 0


class TransactionalOutbox:
    """In-memory transactional outbox manager."""

    def __init__(self, max_retained_events: int = 10_000) -> None:
        self.max_retained_events = max_retained_events
        self._lock = threading.RLock()
        self._events: collections.OrderedDict[str, OutboxEvent] = (
            collections.OrderedDict()
        )

    def record_event(self, event_type: str, payload: dict[str, Any]) -> OutboxEvent:
        """Atomically inserts an event into the outbox buffer."""
        event_id = str(uuid.uuid4())
        event = OutboxEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=OutboxEventStatus.PENDING,
        )

        with self._lock:
            while len(self._events) >= self.max_retained_events:
                self._events.popitem(last=False)
            self._events[event_id] = event
            return event

    def get_pending_events(self, limit: int = 50) -> list[OutboxEvent]:
        """Retrieves uncommitted or pending events for publication."""
        with self._lock:
            return [
                e
                for e in self._events.values()
                if e.status == OutboxEventStatus.PENDING
            ][:limit]

    def mark_published(self, event_id: str) -> None:
        """Marks an event as successfully published to the message broker."""
        with self._lock:
            if event_id in self._events:
                event = self._events[event_id]
                event.status = OutboxEventStatus.PUBLISHED
                event.published_at = time.time()

    def size(self) -> int:
        with self._lock:
            return len(self._events)
