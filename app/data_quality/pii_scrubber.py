"""
app/data_quality/pii_scrubber.py — PII Scrubbing Module for Data Quality & Flywheel

Provides standalone check_pii(text) functionality to detect personally identifiable
information (PII) including names, locations, organizations, phone numbers, and emails.
Enforces a strict REJECT-FIRST policy (passed=False if any PII is detected).
"""

from __future__ import annotations

import re
from typing import Any

PII_ENTITY_TYPES: set[str] = {"PERSON", "GPE", "LOC", "ORG", "FAC", "NORP"}

# Regex patterns for contact information
PHONE_REGEX: re.Pattern[str] = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}|\+?\d[\d\-\s]{7,}\d"
)
EMAIL_REGEX: re.Pattern[str] = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

# Common title patterns, names, and locations for fallback NER when spaCy is absent
NAME_TITLE_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|Sir|Madam)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
COMMON_LOCATIONS: set[str] = {
    "london",
    "new york",
    "paris",
    "tokyo",
    "hanoi",
    "ho chi minh",
    "california",
    "vietnam",
    "america",
    "england",
    "uk",
    "usa",
}
COMMON_NAMES: set[str] = {
    "john",
    "smith",
    "alice",
    "bob",
    "david",
    "michael",
    "sarah",
    "tom",
    "jessica",
    "alexander",
    "emily",
    "daniel",
    "james",
    "robert",
    "william",
}

_SPACY_NLP: Any = None
_SPACY_ATTEMPTED: bool = False


def _get_spacy_model() -> Any:
    """Lazy load spaCy model if available."""
    global _SPACY_NLP, _SPACY_ATTEMPTED
    if not _SPACY_ATTEMPTED:
        _SPACY_ATTEMPTED = True
        try:
            import spacy

            for model_name in ["en_core_web_trf", "en_core_web_sm", "en_core_web_md"]:
                try:
                    _SPACY_NLP = spacy.load(model_name)
                    break
                except Exception:
                    continue
        except ImportError:
            _SPACY_NLP = None
    return _SPACY_NLP


def check_pii(text: str) -> tuple[bool, list[str]]:
    """
    Check input text for Personally Identifiable Information (PII).

    Args:
        text: Input text string to be evaluated.

    Returns:
        tuple[bool, list[str]]:
            - passed (bool): True if NO PII was detected, False if ANY PII detected.
            - entities_found (list[str]): List of detected PII descriptions.
    """
    if not text or not text.strip():
        return True, []

    entities_found: list[str] = []

    # 1. Regex checks for Email & Phone Pattern
    if EMAIL_REGEX.search(text):
        entities_found.append("EMAIL_PATTERN")

    if PHONE_REGEX.search(text):
        entities_found.append("PHONE_PATTERN")

    # 2. NER checks via spaCy if available, otherwise heuristic fallback
    nlp = _get_spacy_model()
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in PII_ENTITY_TYPES:
                entities_found.append(f"{ent.label_}:{ent.text}")
    else:
        # Heuristic NER fallback when spaCy model is not installed
        for match in NAME_TITLE_PATTERN.finditer(text):
            entities_found.append(f"PERSON:{match.group(0)}")

        words = re.findall(r"\b[A-Za-z]+\b", text)
        for word in words:
            word_lower = word.lower()
            if word_lower in COMMON_NAMES and word[0].isupper():
                entities_found.append(f"PERSON:{word}")
            elif word_lower in COMMON_LOCATIONS and word[0].isupper():
                entities_found.append(f"GPE:{word}")

    # Enforce REJECT-FIRST policy: any detected entity results in passed=False
    passed = len(entities_found) == 0
    return passed, entities_found
