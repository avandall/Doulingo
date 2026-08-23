"""
tests/test_error_journal.py
============================
Unit & Integration Tests for Personal Error Journal & Interleaved Practice Weaver (TASK-020).
"""

import uuid

import pytest

from app.storage.db import get_user_profile, init_db
from app.analytics.error_journal import (
    ErrorJournalManager,
    get_recurring_errors,
    record_error,
    weave_interleaved_practice_directives,
)
from app.rag.prompt_constructor import PromptContext, construct_system_prompt
from app.analytics.reporting import generate_weekly_report


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is initialized before each test."""
    init_db()


def test_record_new_error():
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    entry = record_error(
        user_id=user_id,
        error_type="grammar",
        error_detail="Subject-verb agreement (e.g., 'she go')",
        context="She go to school yesterday",
    )

    assert entry["error_type"] == "grammar"
    assert entry["error_detail"] == "Subject-verb agreement (e.g., 'she go')"
    assert entry["count"] == 1
    assert entry["context"] == "She go to school yesterday"

    profile = get_user_profile(user_id)
    assert len(profile["recurring_errors"]) == 1
    assert profile["recurring_errors"][0]["count"] == 1


def test_record_duplicate_error_increments_count():
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    error_detail = "Incorrect past tense irregular verb"

    entry1 = record_error(user_id, "grammar", error_detail, "I buyed a car")
    assert entry1["count"] == 1

    entry2 = record_error(user_id, "grammar", error_detail, "He runned away")
    assert entry2["count"] == 2

    entry3 = record_error(user_id, "grammar", error_detail, "They flied high")
    assert entry3["count"] == 3

    profile = get_user_profile(user_id)
    assert len(profile["recurring_errors"]) == 1
    assert profile["recurring_errors"][0]["count"] == 3


def test_get_recurring_errors_threshold():
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Record error A 3 times
    for _ in range(3):
        record_error(user_id, "grammar", "Preposition mismatch", "depend of")

    # Record error B 1 time
    record_error(user_id, "vocabulary", "Collocation error", "make a photo")

    # Default threshold=2 should return only error A
    recurring_2 = get_recurring_errors(user_id, threshold=2)
    assert len(recurring_2) == 1
    assert recurring_2[0]["error_detail"] == "Preposition mismatch"

    # Threshold=1 should return both errors
    recurring_1 = get_recurring_errors(user_id, threshold=1)
    assert len(recurring_1) == 2


def test_weave_interleaved_practice_directives():
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # Initially no errors
    directives_empty = weave_interleaved_practice_directives(user_id)
    assert directives_empty["has_directives"] is False
    assert directives_empty["directives_text"] == ""

    # Record errors
    record_error(user_id, "grammar", "Article omission", "in morning")
    record_error(user_id, "grammar", "Article omission", "in morning")

    directives = weave_interleaved_practice_directives(user_id, current_topic="daily_routine")
    assert directives["has_directives"] is True
    assert "INTERLEAVED PRACTICE DIRECTIVES" in directives["directives_text"]
    assert "Article omission" in directives["directives_text"]


def test_prompt_constructor_integration():
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    manager = ErrorJournalManager()

    manager.record_error(user_id, "grammar", "Third person -s", "he like")
    manager.record_error(user_id, "grammar", "Third person -s", "he like")

    directives_res = manager.weave_interleaved_practice_directives(user_id)

    ctx = PromptContext(
        user_id=user_id,
        band_estimate=6.5,
        topic_tag="hobbies",
        interleaved_directives=directives_res["directives_text"],
    )

    prompt = construct_system_prompt(ctx)
    assert "### INTERLEAVED PRACTICE DIRECTIVES" in prompt
    assert "Third person -s" in prompt


def test_reporting_with_dict_errors():
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    record_error(user_id, "grammar", "Tense inconsistency", "I was go")
    record_error(user_id, "grammar", "Tense inconsistency", "I was go")

    report = generate_weekly_report(user_id, days=7)
    assert "recurring_errors" in report
    assert isinstance(report["recurring_errors"], list)
    assert len(report["recurring_errors"]) == 1
