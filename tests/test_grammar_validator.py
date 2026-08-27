"""
tests/test_grammar_validator.py
================================
Unit tests for Grammar Structure Bank & CEFR Constraint Validator (TASK-008).
"""

import pytest

from app.core.grammar_validator import GrammarCheckResult, GrammarValidator


@pytest.fixture
def validator():
    """Fixture providing initialized GrammarValidator instance."""
    return GrammarValidator()


def test_level_rank_mapping(validator):
    """Test CEFR level string and integer level to rank resolution."""
    assert validator.get_level_rank("Pre-A1") == 0
    assert validator.get_level_rank("A1") == 1
    assert validator.get_level_rank("A2") == 3
    assert validator.get_level_rank("B1") == 6
    assert validator.get_level_rank("B2") == 8
    assert validator.get_level_rank("C1") == 10
    assert validator.get_level_rank("C2") == 12

    # Integer levels (1 to 20)
    assert validator.get_level_rank(1) == 0
    assert validator.get_level_rank(2) == 1
    assert validator.get_level_rank(5) == 3
    assert validator.get_level_rank(9) == 6
    assert validator.get_level_rank(12) == 8


def test_clause_counting(validator):
    """Test heuristic sentence clause count calculation."""
    # Simple single clause sentence
    assert validator.count_clauses("I eat rice every day.") == 1

    # Two clauses connected by 'because'
    assert validator.count_clauses("I eat rice because I am hungry.") == 2

    # Three clauses connected by conjunctions
    assert validator.count_clauses("I woke up early, but I was tired because I slept late.") >= 3


def test_detect_structures(validator):
    """Test detection of grammar structures via regex patterns."""
    # Present simple
    structs_a1 = validator.detect_structures("I live in London and I eat lunch at home.")
    assert "present_simple_basic" in structs_a1

    # Present continuous
    structs_cont = validator.detect_structures("She is working on her project right now.")
    assert "present_continuous" in structs_cont

    # Past simple
    structs_past = validator.detect_structures("Yesterday we visited a famous museum.")
    assert "past_simple" in structs_past

    # Second conditional
    structs_cond2 = validator.detect_structures("If I were rich, I would travel the world.")
    assert "second_conditional" in structs_cond2

    # Passive voice
    structs_passive = validator.detect_structures("The bridge was built in 1920.")
    assert "passive_voice" in structs_passive


def test_validate_grammar_pass_for_target_level(validator):
    """Test simple response passing A1 target level constraints."""
    text = "I eat lunch at home. I like coffee very much."
    result = validator.validate_grammar(text, target_level="A1")

    assert isinstance(result, GrammarCheckResult)
    assert result.is_valid is True
    assert result.clause_violation is False
    assert len(result.disallowed_structures) == 0
    assert len(result.violations) == 0


def test_validate_grammar_disallowed_structure_violation(validator):
    """Test response containing B2 second conditional failing A1 target level."""
    text = "If I won the lottery, I would buy a large house."
    result = validator.validate_grammar(text, target_level="A1")

    assert result.is_valid is False
    assert len(result.disallowed_structures) > 0
    disallowed_ids = [d["id"] for d in result.disallowed_structures]
    assert "second_conditional" in disallowed_ids
    assert any("second_conditional" in v or "Second Conditional" in v for v in result.violations)


def test_validate_grammar_clause_count_violation(validator):
    """Test complex multi-clause sentence violating A1 max_clauses limit."""
    text = "I went to the store, and I bought apples, but I forgot my wallet because I was in a rush."
    result = validator.validate_grammar(text, target_level="A1")

    # A1 max_clauses is 2
    assert result.max_clauses_allowed == 2
    assert result.detected_max_clauses > 2
    assert result.clause_violation is True
    assert result.is_valid is False
    assert any("clause count" in v.lower() for v in result.violations)


def test_validate_grammar_advanced_level_passes(validator):
    """Test advanced conditional passing when target level is set to B2/C1."""
    text = "If I won the lottery, I would buy a house."
    result_b2 = validator.validate_grammar(text, target_level="B2")

    assert result_b2.is_valid is True
    assert result_b2.clause_violation is False
    assert len(result_b2.disallowed_structures) == 0
