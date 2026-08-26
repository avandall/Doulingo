"""
app/core/heuristic_checker.py
==============================
Vocabulary Bank & Heuristic Level Checker Engine (TASK-002)

Provides ultra-fast (<5ms) non-LLM heuristic checking for AI response quality:
1. Validates text vocabulary against CEFR level ceiling target.
2. Calculates sentence length, sentence count, and average word count per sentence.
3. Identifies specific violating words exceeding the target CEFR ceiling.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("heuristic_checker")

# CEFR Level hierarchy to numeric rank mapping
CEFR_RANKS: dict[str, int] = {
    "PRE-A1": 0,
    "A1": 1,
    "A1+": 2,
    "A2": 3,
    "A2+": 4,
    "B1-": 5,
    "B1": 6,
    "B1+": 7,
    "B2": 8,
    "B2+": 9,
    "C1": 10,
    "C1+": 11,
    "C2": 12,
    "C2+": 13,
}

# 20-level scale to CEFR rank mapping (from Level 1 Pre-A1 to Level 20 C2+)
INT_LEVEL_TO_RANK: dict[int, int] = {
    1: 0,   # Pre-A1
    2: 1,   # A1
    3: 1,   # A1
    4: 2,   # A1+
    5: 3,   # A2
    6: 3,   # A2
    7: 4,   # A2+
    8: 5,   # B1-
    9: 6,   # B1
    10: 6,  # B1
    11: 7,  # B1+
    12: 8,  # B2
    13: 8,  # B2
    14: 9,  # B2+
    15: 10, # C1
    16: 10, # C1
    17: 11, # C1+
    18: 12, # C2
    19: 12, # C2
    20: 13, # C2+
}

# Common English stop words / pronouns / contractions ignored during ceiling check
COMMON_BASE_WORDS: set[str] = {
    "a", "an", "the", "i", "me", "my", "myself", "we", "us", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these",
    "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "having", "do", "does", "did", "doing", "would", "should", "could", "ought",
    "i'm", "you're", "he's", "she's", "it's", "we're", "they're", "i've", "you've",
    "we've", "they've", "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll",
    "you'll", "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't",
    "weren't", "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't", "won't",
    "wouldn't", "can't", "cannot", "couldn't", "mustn't", "let's", "that's", "who's",
    "what's", "here's", "there's", "when's", "where's", "why's", "how's", "yes", "no",
    "not", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at",
    "by", "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "now", "d", "ll", "m",
    "o", "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", "hasn",
    "haven", "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", "wasn",
    "weren", "won", "wouldn"
}


@dataclass
class HeuristicCheckResult:
    """Dataclass holding evaluation results from HeuristicChecker."""

    is_violated: bool
    violating_words: list[str] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    execution_time_ms: float = 0.0

    def __getitem__(self, item: str) -> Any:
        """Allow dictionary-like indexing for compatibility."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(f"Invalid key: {item}")

    def __iter__(self) -> Any:
        """Allow tuple unpacking: is_violated, violating_words = res."""
        yield self.is_violated
        yield self.violating_words

    def to_dict(self) -> dict[str, Any]:
        """Convert result object to dictionary."""
        return {
            "is_violated": self.is_violated,
            "violating_words": self.violating_words,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "avg_sentence_length": round(self.avg_sentence_length, 2),
            "execution_time_ms": round(self.execution_time_ms, 3),
        }


class HeuristicChecker:
    """
    Ultra-fast heuristic level ceiling checker & sentence analyzer.

    Reads app/data/vocab_bank.json and verifies if an input text stays within
    the target CEFR level vocabulary ceiling in <5ms.
    """

    def __init__(self, vocab_bank_path: str | Path | None = None) -> None:
        """
        Initialize HeuristicChecker with vocabulary bank mapping.

        Args:
            vocab_bank_path: Optional path to vocab_bank.json file.
        """
        if vocab_bank_path is None:
            # Fallback path discovery relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent
            vocab_bank_path = base_dir / "app" / "data" / "vocab_bank.json"

        self.vocab_bank_path = Path(vocab_bank_path)
        self.word_level_map: dict[str, str] = {}
        self.word_rank_map: dict[str, int] = {}
        self._load_vocab_bank()

    def _load_vocab_bank(self) -> None:
        """Load vocab_bank.json and construct word level & rank lookup indexes."""
        if not self.vocab_bank_path.exists():
            logger.warning(f"Vocab bank file not found at {self.vocab_bank_path}. Using empty bank.")
            return

        try:
            with open(self.vocab_bank_path, encoding="utf-8") as f:
                vocab_data = json.load(f)

            for item in vocab_data:
                word = item.get("word", "").strip().lower()
                level = item.get("level", "A1").strip().upper()
                if not word:
                    continue

                rank = self.get_cefr_rank(level)
                # Keep the minimum level/rank if word has multiple entries
                if word not in self.word_rank_map or rank < self.word_rank_map[word]:
                    self.word_rank_map[word] = rank
                    self.word_level_map[word] = level

            logger.info(f"Loaded {len(self.word_rank_map)} vocabulary words from {self.vocab_bank_path}")
        except Exception as e:
            logger.error(f"Failed to load vocab_bank.json: {e}")

    @staticmethod
    def get_cefr_rank(level: str | int) -> int:
        """
        Convert level representation (CEFR string or 20-level integer) to numeric rank.

        Args:
            level: Level identifier (e.g. "A1", "A2", "B1", 1, 5, 10).

        Returns:
            Integer rank (higher rank means more advanced vocabulary).
        """
        if isinstance(level, int):
            return INT_LEVEL_TO_RANK.get(level, 1)

        level_str = str(level).strip().upper()
        if level_str in CEFR_RANKS:
            return CEFR_RANKS[level_str]

        # Handle numbers formatted as string e.g. "5"
        if level_str.isdigit():
            return INT_LEVEL_TO_RANK.get(int(level_str), 1)

        # Fallback partial matching e.g. "A1-BASIC" -> "A1"
        for key in ["PRE-A1", "A1+", "A1", "A2+", "A2", "B1+", "B1-", "B1", "B2+", "B2", "C1+", "C1", "C2+", "C2"]:
            if key in level_str:
                return CEFR_RANKS[key]

        return 1  # Default fallback rank for A1

    def count_words(self, text: str) -> int:
        """Count total words in text."""
        words = re.findall(r"\b[a-zA-Z']+\b", text)
        return len(words)

    def calculate_sentence_length(self, text: str) -> dict[str, Any]:
        """
        Analyze text sentence structure and length.

        Returns:
            Dictionary containing word_count, sentence_count, avg_sentence_length, sentences.
        """
        raw_sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        total_words = self.count_words(text)
        sentence_count = max(1, len(sentences))
        avg_len = total_words / sentence_count

        return {
            "word_count": total_words,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_len, 2),
            "sentences": sentences,
        }

    def _normalize_word(self, word: str) -> str:
        """Normalize word for lookup (lowercase, strip trailing punctuation/possessives)."""
        w = word.lower().strip(" '\".,!?:;()")
        w = w.removesuffix("'s")
        return w

    def _stem_candidates(self, word: str) -> list[str]:
        """Generate candidate root forms for simple morphological suffixes."""
        candidates = [word]
        if word.endswith("s") and len(word) > 3:
            candidates.append(word[:-1])
        if word.endswith("es") and len(word) > 4:
            candidates.append(word[:-2])
        if word.endswith("ed") and len(word) > 4:
            candidates.append(word[:-2])
            candidates.append(word[:-1])  # e.g. liked -> like
        if word.endswith("ing") and len(word) > 5:
            candidates.append(word[:-3])
            candidates.append(word[:-3] + "e")  # e.g. making -> make
        if word.endswith("ly") and len(word) > 4:
            candidates.append(word[:-2])
        return candidates

    def find_violating_words(
        self, text: str, target_level: str | int, strict_unknown: bool = False
    ) -> list[str]:
        """
        Find unique words in text that exceed the target CEFR level ceiling.

        Args:
            text: Input response text to check.
            target_level: Target CEFR ceiling (e.g. "A1", "A2", "B1" or level 1..20).
            strict_unknown: If True, unknown non-stop words not in vocab bank are also flagged.

        Returns:
            List of unique violating word strings.
        """
        target_rank = self.get_cefr_rank(target_level)
        tokens = re.findall(r"\b[a-zA-Z']+\b", text)
        violating: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            norm = self._normalize_word(token)
            if not norm or norm in COMMON_BASE_WORDS or norm in seen:
                continue

            # 1. Lookup direct word or morphological stem candidates
            matched_rank: int | None = None
            for candidate in self._stem_candidates(norm):
                if candidate in self.word_rank_map:
                    matched_rank = self.word_rank_map[candidate]
                    break

            if matched_rank is not None:
                if matched_rank > target_rank:
                    violating.append(token)
                    seen.add(norm)
            elif strict_unknown and target_rank <= CEFR_RANKS.get("A2", 3) and len(norm) > 4:
                # If word is unknown and not in stop words, flag if target level is low (e.g. A1/A2)
                violating.append(token)
                seen.add(norm)

        return violating

    def check_level_ceiling(
        self, text: str, target_level: str | int, strict_unknown: bool = False
    ) -> HeuristicCheckResult:
        """
        Check if text violates target CEFR level ceiling in < 5ms.

        Args:
            text: Response text string.
            target_level: CEFR level ("A1", "A2", "B1" or level 1..20).
            strict_unknown: Flag unknown words if True.

        Returns:
            HeuristicCheckResult object containing violation status and metrics.
        """
        start_time = time.perf_counter()

        violating_words = self.find_violating_words(text, target_level, strict_unknown=strict_unknown)
        is_violated = len(violating_words) > 0

        len_analysis = self.calculate_sentence_length(text)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return HeuristicCheckResult(
            is_violated=is_violated,
            violating_words=violating_words,
            word_count=len_analysis["word_count"],
            sentence_count=len_analysis["sentence_count"],
            avg_sentence_length=len_analysis["avg_sentence_length"],
            execution_time_ms=elapsed_ms,
        )
