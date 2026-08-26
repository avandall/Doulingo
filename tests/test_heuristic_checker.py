"""
tests/test_heuristic_checker.py
================================
Unit tests and performance benchmarks for HeuristicChecker (TASK-002).
"""

import json
import time

import pytest

from app.core.heuristic_checker import HeuristicChecker, HeuristicCheckResult


@pytest.fixture
def checker():
    """Fixture providing initialized HeuristicChecker instance."""
    return HeuristicChecker()


def test_initialization(checker):
    """Verify HeuristicChecker initializes and loads vocab bank."""
    assert len(checker.word_rank_map) > 0
    assert len(checker.word_level_map) > 0
    # Common words in vocab bank
    assert "about" in checker.word_rank_map
    assert "apple" in checker.word_rank_map


def test_level_rank_conversion():
    """Test get_cefr_rank conversions for string and integer levels."""
    assert HeuristicChecker.get_cefr_rank("A1") == 1
    assert HeuristicChecker.get_cefr_rank("A2") == 3
    assert HeuristicChecker.get_cefr_rank("B1") == 6
    assert HeuristicChecker.get_cefr_rank("B2") == 8
    assert HeuristicChecker.get_cefr_rank("C1") == 10
    assert HeuristicChecker.get_cefr_rank("C2") == 12

    # Integer level scale
    assert HeuristicChecker.get_cefr_rank(1) == 0   # Pre-A1
    assert HeuristicChecker.get_cefr_rank(2) == 1   # A1
    assert HeuristicChecker.get_cefr_rank(6) == 3   # A2
    assert HeuristicChecker.get_cefr_rank(9) == 6   # B1


def test_sentence_length_calculation(checker):
    """Test word count and sentence length calculation."""
    text = "Hello! I like coffee very much. Do you eat at home?"
    analysis = checker.calculate_sentence_length(text)

    assert analysis["word_count"] == 11
    assert analysis["sentence_count"] == 3
    assert analysis["avg_sentence_length"] == round(11 / 3, 2)


def test_check_level_ceiling_pass(checker):
    """Test that text within level ceiling passes without violations."""
    # A1 basic sentences
    text = "I eat lunch at home every day. I like rice and apples."
    res = checker.check_level_ceiling(text, target_level="A1")

    assert isinstance(res, HeuristicCheckResult)
    assert res.is_violated is False
    assert len(res.violating_words) == 0
    assert res.word_count > 0
    assert res.execution_time_ms < 5.0


def test_check_level_ceiling_violation(checker):
    """Test that text containing higher-level words flags violations."""
    # "abandon" / "academic" / "abstract" are B1/B2 level words in vocab_bank
    text_b1 = "The academic project was an abstract effort."

    # When target is A1, B1 words should be flagged
    res_a1 = checker.check_level_ceiling(text_b1, target_level="A1")
    assert res_a1.is_violated is True
    assert len(res_a1.violating_words) > 0

    # Check that specific higher-level word is in violating_words list
    violating_lower = [w.lower() for w in res_a1.violating_words]
    assert any(w in violating_lower for w in ["academic", "abstract", "effort"])


def test_check_level_ceiling_performance(checker):
    """Benchmark test verifying check_level_ceiling completes in under 5ms."""
    sample_text = (
        "I really enjoy spending time with my family on weekends. "
        "Last Saturday, we went to a beautiful park near our home and had a nice picnic. "
        "The weather was warm and sunny. What do you usually do on Saturdays?"
    )

    # Warmup
    checker.check_level_ceiling(sample_text, target_level="A2")

    # Measure 50 iterations
    start_time = time.perf_counter()
    iterations = 50
    for _ in range(iterations):
        res = checker.check_level_ceiling(sample_text, target_level="A2")
        assert res.execution_time_ms < 5.0

    total_time_ms = ((time.perf_counter() - start_time) * 1000.0) / iterations
    assert total_time_ms < 5.0, f"Average execution time {total_time_ms:.3f}ms exceeded 5ms limit!"


def test_result_unpacking_and_indexing(checker):
    """Verify HeuristicCheckResult supports tuple unpacking and dict indexing."""
    text = "I like apples."
    res = checker.check_level_ceiling(text, target_level="A1")

    # Dict indexing
    assert res["is_violated"] is False
    assert isinstance(res["violating_words"], list)
    assert res["word_count"] == 3

    # Tuple unpacking
    is_violated, violating = res
    assert is_violated is False
    assert violating == []


def test_custom_vocab_bank(tmp_path):
    """Test initializing HeuristicChecker with a custom vocab bank file."""
    custom_data = [
        {"word": "simple", "level": "A1"},
        {"word": "complex", "level": "B2"},
    ]
    bank_file = tmp_path / "custom_vocab.json"
    bank_file.write_text(json.dumps(custom_data), encoding="utf-8")

    custom_checker = HeuristicChecker(vocab_bank_path=bank_file)
    assert "simple" in custom_checker.word_rank_map
    assert custom_checker.word_level_map["complex"] == "B2"

    res = custom_checker.check_level_ceiling("This is complex", target_level="A1")
    assert res.is_violated is True
    assert "complex" in res.violating_words
