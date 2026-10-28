"""Timezone-Aware Monotonic Streak Engine.

Strictly enforces:
- Invariant 1: Exactly-once streak increment per user per local calendar day.
- Invariant 5: Timezone-aware date calculations immune to server UTC drift.
"""

from __future__ import annotations

import datetime
import threading
from dataclasses import dataclass, field
from typing import Optional
from zoneinfo import ZoneInfo


@dataclass(slots=True)
class StreakState:
    """Represents a user's persistent streak status."""

    user_id: str
    current_streak: int = 0
    last_completed_date: Optional[datetime.date] = None
    user_timezone: str = "Asia/Ho_Chi_Minh"
    freeze_count: int = 1
    total_xp: int = 0
    version: int = 1


@dataclass(slots=True)
class StreakUpdateResult:
    """Outcome of an activity evaluation on a user's streak."""

    streak_incremented: bool
    current_streak: int
    freeze_used: bool
    same_day_duplicate: bool
    calendar_date: datetime.date
    total_xp: int


class StreakEngine:
    """In-memory atomic gamification store and streak progression engine."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._user_streaks: dict[str, StreakState] = {}
        # Stores composite constraint: set of (user_id, calendar_date)
        self._daily_activities: set[tuple[str, datetime.date]] = set()

    def get_or_create_user(self, user_id: str, timezone_str: str = "Asia/Ho_Chi_Minh") -> StreakState:
        with self._lock:
            if user_id not in self._user_streaks:
                self._user_streaks[user_id] = StreakState(
                    user_id=user_id,
                    user_timezone=timezone_str,
                )
            return self._user_streaks[user_id]

    @staticmethod
    def calculate_local_date(timestamp: Optional[datetime.datetime], timezone_str: str) -> datetime.date:
        """Converts UTC or native timestamp to user's localized calendar date."""
        dt = timestamp or datetime.datetime.now(datetime.timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        try:
            tz = ZoneInfo(timezone_str)
        except Exception:
            tz = ZoneInfo("UTC")
        return dt.astimezone(tz).date()

    def process_activity(
        self,
        user_id: str,
        earned_xp: int = 10,
        activity_timestamp: Optional[datetime.datetime] = None,
    ) -> StreakUpdateResult:
        """Processes qualifying activity and evaluates streak state transitions.

        Enforces Invariant 1: Exactly-once streak transition per calendar day.
        Enforces Invariant 5: Monotonic progression according to localized calendar date.
        """
        with self._lock:
            user = self.get_or_create_user(user_id)
            current_local_date = self.calculate_local_date(activity_timestamp, user.user_timezone)

            # Invariant 1 check: Duplicate submission for the same user and calendar day
            activity_key = (user_id, current_local_date)
            if activity_key in self._daily_activities:
                # Same day activity: award XP, but do NOT increment streak again!
                user.total_xp += earned_xp
                return StreakUpdateResult(
                    streak_incremented=False,
                    current_streak=user.current_streak,
                    freeze_used=False,
                    same_day_duplicate=True,
                    calendar_date=current_local_date,
                    total_xp=user.total_xp,
                )

            # Mark daily activity
            self._daily_activities.add(activity_key)
            user.total_xp += earned_xp

            if user.last_completed_date is None:
                # First ever completion
                user.current_streak = 1
                user.last_completed_date = current_local_date
                user.version += 1
                return StreakUpdateResult(
                    streak_incremented=True,
                    current_streak=1,
                    freeze_used=False,
                    same_day_duplicate=False,
                    calendar_date=current_local_date,
                    total_xp=user.total_xp,
                )

            day_diff = (current_local_date - user.last_completed_date).days

            if day_diff == 0:
                # Same day duplicate
                return StreakUpdateResult(
                    streak_incremented=False,
                    current_streak=user.current_streak,
                    freeze_used=False,
                    same_day_duplicate=True,
                    calendar_date=current_local_date,
                    total_xp=user.total_xp,
                )

            if day_diff == 1:
                # Consecutive calendar day: increment streak!
                user.current_streak += 1
                user.last_completed_date = current_local_date
                user.version += 1
                return StreakUpdateResult(
                    streak_incremented=True,
                    current_streak=user.current_streak,
                    freeze_used=False,
                    same_day_duplicate=False,
                    calendar_date=current_local_date,
                    total_xp=user.total_xp,
                )

            if day_diff == 2 and user.freeze_count > 0:
                # Missed 1 day, but user has a Streak Freeze shield!
                user.freeze_count -= 1
                user.current_streak += 1  # Streak protected and incremented
                user.last_completed_date = current_local_date
                user.version += 1
                return StreakUpdateResult(
                    streak_incremented=True,
                    current_streak=user.current_streak,
                    freeze_used=True,
                    same_day_duplicate=False,
                    calendar_date=current_local_date,
                    total_xp=user.total_xp,
                )

            # Missed more than 1 day or no freeze available: streak resets to 1
            user.current_streak = 1
            user.last_completed_date = current_local_date
            user.version += 1
            return StreakUpdateResult(
                streak_incremented=True,
                current_streak=1,
                freeze_used=False,
                same_day_duplicate=False,
                calendar_date=current_local_date,
                total_xp=user.total_xp,
            )
