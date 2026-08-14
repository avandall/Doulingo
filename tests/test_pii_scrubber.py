"""
tests/test_pii_scrubber.py — Unit test suite for app/data_quality/pii_scrubber.py
"""

from __future__ import annotations

from app.data_quality.pii_scrubber import check_pii


def test_check_pii_clean_text() -> None:
    text = "I enjoy reading books about history and science in my free time."
    passed, entities = check_pii(text)
    assert passed is True
    assert entities == []


def test_check_pii_empty_text() -> None:
    passed1, entities1 = check_pii("")
    assert passed1 is True
    assert entities1 == []

    passed2, entities2 = check_pii("   \n\t  ")
    assert passed2 is True
    assert entities2 == []


def test_check_pii_email() -> None:
    text = "Please contact me at user.example@domain.com for more info."
    passed, entities = check_pii(text)
    assert passed is False
    assert "EMAIL_PATTERN" in entities


def test_check_pii_phone() -> None:
    text = "Call my cell number +1-555-123-4567 anytime."
    passed, entities = check_pii(text)
    assert passed is False
    assert "PHONE_PATTERN" in entities


def test_check_pii_person_name() -> None:
    text = "I spoke with John yesterday about the new project proposal."
    passed, entities = check_pii(text)
    assert passed is False
    assert any("PERSON" in entity or "John" in entity for entity in entities)


def test_check_pii_location() -> None:
    text = "I lived in London for three years during university."
    passed, entities = check_pii(text)
    assert passed is False
    assert any("GPE" in entity or "LOC" in entity or "London" in entity for entity in entities)


def test_check_pii_reject_first_policy_fictional_name() -> None:
    # Reject-first policy test: even narrative/fictional names must trigger reject (passed=False)
    text = "Once upon a time, Mr. Smith went to the market."
    passed, entities = check_pii(text)
    assert passed is False
    assert len(entities) > 0


def test_check_pii_multiple_pii() -> None:
    text = "Contact Alice at alice@example.com or call +15559876543."
    passed, entities = check_pii(text)
    assert passed is False
    assert "EMAIL_PATTERN" in entities
    assert "PHONE_PATTERN" in entities
