"""Non-Sticky Self-Healing Circuit Breaker.

Maintains 3 distinct states:
- CLOSED: Requests route to primary cloud providers normally.
- OPEN: Tripped after high failure rate (>= 50%); immediately diverts to FSM with 0ms network delay.
- HALF-OPEN: After a 10s cool-down window, allows a probe request to verify provider recovery.
  If the probe succeeds, state immediately resets to CLOSED (never sticking to FSM).
"""

from __future__ import annotations

import collections
import enum
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when an execution is attempted while the circuit breaker is OPEN."""


class CircuitBreaker:
    """Sliding-window circuit breaker with non-sticky self-healing capability."""

    def __init__(
        self,
        failure_rate_threshold: float = 0.5,
        cool_down_seconds: float = 10.0,
        sliding_window_size: int = 10,
        min_calls_to_evaluate: int = 4,
    ) -> None:
        self.failure_rate_threshold = failure_rate_threshold
        self.cool_down_seconds = cool_down_seconds
        self.sliding_window_size = sliding_window_size
        self.min_calls_to_evaluate = min_calls_to_evaluate

        self._state: CircuitState = CircuitState.CLOSED
        self._lock = threading.RLock()
        self._window: collections.deque[bool] = collections.deque(
            maxlen=sliding_window_size
        )
        self._opened_at: float = 0.0
        self._half_open_in_flight: bool = False

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN and time.time() - self._opened_at >= self.cool_down_seconds:
                self._state = CircuitState.HALF_OPEN
                self._half_open_in_flight = False
            return self._state

    def record_success(self) -> None:
        """Records a successful call."""
        with self._lock:
            self._window.append(True)
            if self._state == CircuitState.HALF_OPEN:
                # Probe succeeded -> immediately heal back to CLOSED!
                self._state = CircuitState.CLOSED
                self._half_open_in_flight = False
                self._window.clear()

    def record_failure(self) -> None:
        """Records a failed call and transitions state if threshold is exceeded."""
        with self._lock:
            self._window.append(False)
            if self._state == CircuitState.HALF_OPEN:
                # Probe failed -> trip right back to OPEN
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                self._half_open_in_flight = False
                return

            if self._state == CircuitState.CLOSED and len(self._window) >= self.min_calls_to_evaluate:
                failures = sum(1 for success in self._window if not success)
                failure_rate = failures / len(self._window)
                if failure_rate >= self.failure_rate_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.time()

    def can_execute(self) -> bool:
        """Returns True if a request is allowed through; False if circuit is OPEN."""
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            with self._lock:
                return not self._half_open_in_flight
        return False

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes a function protected by the circuit breaker."""
        with self._lock:
            if not self.can_execute():
                raise CircuitBreakerOpenException(
                    "Circuit is OPEN; fast-failing to fallback"
                )
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_in_flight = True

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise

    def force_open(self) -> None:
        """For testing or manual intervention: force the circuit to OPEN."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._opened_at = time.time()

    def force_close(self) -> None:
        """For testing or manual intervention: force the circuit to CLOSED."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._window.clear()
            self._half_open_in_flight = False
