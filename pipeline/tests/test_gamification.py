"""Tests for Gamification and Monotonic Streak Bounded Context."""

import datetime

import pytest

from pipeline.src.gamification.outbox import OutboxEventStatus, TransactionalOutbox
from pipeline.src.gamification.streak_engine import StreakEngine


class TestStreakEngine:
    def test_first_activity_starts_streak_at_1(self):
        engine = StreakEngine()
        user_id = "learner_001"
        res = engine.process_activity(user_id=user_id, earned_xp=20)

        assert res.streak_incremented is True
        assert res.current_streak == 1
        assert res.same_day_duplicate is False
        assert res.total_xp == 20

    def test_same_day_duplicate_does_not_increment_streak(self):
        # Invariant 1: Exactly-once streak increment per calendar day
        engine = StreakEngine()
        user_id = "learner_002"
        now = datetime.datetime.now(datetime.timezone.utc)

        # First turn today
        res1 = engine.process_activity(
            user_id=user_id, earned_xp=10, activity_timestamp=now
        )
        assert res1.streak_incremented is True
        assert res1.current_streak == 1

        # Second turn today (e.g. 1 hour later)
        later_same_day = now + datetime.timedelta(hours=2)
        res2 = engine.process_activity(
            user_id=user_id, earned_xp=15, activity_timestamp=later_same_day
        )

        assert res2.streak_incremented is False
        assert res2.same_day_duplicate is True
        assert res2.current_streak == 1  # Streak stayed 1!
        assert res2.total_xp == 25  # XP still awarded!

    def test_consecutive_day_increments_streak(self):
        engine = StreakEngine()
        user_id = "learner_003"
        day1 = datetime.datetime(2026, 10, 27, 20, 0, 0, tzinfo=datetime.timezone.utc)
        day2 = datetime.datetime(2026, 10, 28, 20, 0, 0, tzinfo=datetime.timezone.utc)

        res1 = engine.process_activity(
            user_id=user_id, earned_xp=10, activity_timestamp=day1
        )
        assert res1.current_streak == 1

        res2 = engine.process_activity(
            user_id=user_id, earned_xp=10, activity_timestamp=day2
        )
        assert res2.streak_incremented is True
        assert res2.current_streak == 2

    def test_streak_freeze_protection_on_missed_day(self):
        engine = StreakEngine()
        user_id = "learner_004"
        day1 = datetime.datetime(2026, 10, 25, 20, 0, 0, tzinfo=datetime.timezone.utc)
        day3 = datetime.datetime(
            2026, 10, 27, 20, 0, 0, tzinfo=datetime.timezone.utc
        )  # Missed Oct 26

        engine.process_activity(user_id=user_id, earned_xp=10, activity_timestamp=day1)
        res_after_freeze = engine.process_activity(
            user_id=user_id, earned_xp=10, activity_timestamp=day3
        )

        assert res_after_freeze.freeze_used is True
        assert res_after_freeze.streak_incremented is True
        assert res_after_freeze.current_streak == 2

    def test_streak_resets_if_gap_exceeds_freeze(self):
        engine = StreakEngine()
        user_id = "learner_005"
        user = engine.get_or_create_user(user_id)
        user.freeze_count = 0  # No freezes

        day1 = datetime.datetime(2026, 10, 20, 20, 0, 0, tzinfo=datetime.timezone.utc)
        day4 = datetime.datetime(2026, 10, 24, 20, 0, 0, tzinfo=datetime.timezone.utc)

        engine.process_activity(user_id=user_id, earned_xp=10, activity_timestamp=day1)
        res_reset = engine.process_activity(
            user_id=user_id, earned_xp=10, activity_timestamp=day4
        )

        assert res_reset.current_streak == 1  # Reset to 1


class TestTransactionalOutbox:
    def test_record_and_publish_event(self):
        outbox = TransactionalOutbox()
        event = outbox.record_event(
            event_type="PronunciationEvaluated",
            payload={"user_id": "u1", "score": 95},
        )
        assert event.status == OutboxEventStatus.PENDING

        pending = outbox.get_pending_events()
        assert len(pending) == 1
        assert pending[0].event_id == event.event_id

        outbox.mark_published(event.event_id)
        assert event.status == OutboxEventStatus.PUBLISHED
        assert len(outbox.get_pending_events()) == 0
