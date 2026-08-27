"""
app/core/grammar_validator.py
==============================
Grammar Structure Bank & CEFR Constraint Validator (TASK-008)

Replaces rigid rules with a flexible CEFR grammar structure catalog (introduced_at_level
and mastered_at_level) and verifies clause complexity (max_clauses) per level.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("grammar_validator")

# Standard CEFR Level hierarchy to numeric rank mapping (0-13)
CEFR_RANKS: dict[str, int] = {
    "PRE-A1": 0,
    "PRE_A1": 0,
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

# 20-level scale to CEFR rank mapping
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

# Clause boundary splitters regex: subordinating conjunctions, relative pronouns, punctuation, or coordinating conjunctions with subjects
CLAUSE_SPLITTER_REGEX = re.compile(
    r"\b(?:because|although|though|even\s+though|if|when|while|after|before|since|unless|until|where|which|that|who|whom|whose)\b|[,;:]\s*(?:and|but|or|so)?|\b(?:and|but|or|so)\s+(?:i|you|he|she|it|we|they|this|that|there|here)\b",
    re.IGNORECASE,
)


@dataclass
class GrammarCheckResult:
    """Dataclass holding evaluation results from GrammarValidator."""

    is_valid: bool
    target_level: str | int
    target_rank: int
    max_clauses_allowed: int
    detected_max_clauses: int
    clause_violation: bool
    detected_structures: list[str] = field(default_factory=list)
    disallowed_structures: list[dict[str, Any]] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "target_level": str(self.target_level),
            "target_rank": self.target_rank,
            "max_clauses_allowed": self.max_clauses_allowed,
            "detected_max_clauses": self.detected_max_clauses,
            "clause_violation": self.clause_violation,
            "detected_structures": self.detected_structures,
            "disallowed_structures": self.disallowed_structures,
            "violations": self.violations,
        }


class GrammarValidator:
    """CEFR Grammar Structure & Clause Constraint Validator Engine."""

    def __init__(self, grammar_bank_path: str | Path | None = None) -> None:
        """Initialize validator with grammar bank data."""
        if grammar_bank_path is None:
            grammar_bank_path = Path(__file__).parent.parent / "data" / "grammar_bank.json"

        self.bank_path = Path(grammar_bank_path)
        self.level_constraints: dict[str, dict[str, Any]] = {}
        self.structures: list[dict[str, Any]] = []

        self._load_grammar_bank()

    def _load_grammar_bank(self) -> None:
        """Load grammar structures and level constraints from JSON bank file."""
        if not self.bank_path.exists():
            logger.warning("Grammar bank file not found at %s. Using default empty bank.", self.bank_path)
            return

        try:
            with open(self.bank_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.level_constraints = data.get("level_constraints", {})
            self.structures = data.get("grammar_structures", [])
            logger.info(
                "Loaded grammar bank successfully with %d structures.", len(self.structures)
            )
        except Exception as e:
            logger.error("Failed to load grammar bank: %s", e)

    def get_level_rank(self, level: str | int) -> int:
        """Map CEFR string level or integer 1-20 level to numeric rank 0-13."""
        if isinstance(level, int):
            return INT_LEVEL_TO_RANK.get(level, 1)

        level_str = str(level).strip().upper()
        if level_str.isdigit():
            return INT_LEVEL_TO_RANK.get(int(level_str), 1)

        return CEFR_RANKS.get(level_str, 1)

    def get_level_constraints(self, level: str | int) -> dict[str, Any]:
        """Get constraints dict for a given CEFR level or integer level."""
        rank = self.get_level_rank(level)
        for info in self.level_constraints.values():
            if info.get("rank") == rank:
                return info

        # Fallback constraints if rank not directly matched in dict keys
        default_max_clauses = min(2 + (rank // 2), 8)
        return {"rank": rank, "max_clauses": default_max_clauses, "max_sentence_words": 20}

    def count_clauses_in_sentence(self, sentence: str) -> int:
        """Calculate number of clauses in a single sentence using clause boundary segmentation."""
        clean_sentence = sentence.strip()
        if not clean_sentence:
            return 0

        # Split sentence by clause boundary markers
        segments = [s.strip() for s in CLAUSE_SPLITTER_REGEX.split(clean_sentence) if s and s.strip()]

        # Filter out empty or whitespace-only segments
        valid_segments = [s for s in segments if len(s.split()) >= 1]
        return max(1, len(valid_segments))

    def count_clauses(self, text: str) -> int:
        """Calculate maximum clause count across all sentences in the text."""
        sentences = re.split(r"[.!?]+", text)
        max_clauses = 0
        for s in sentences:
            s_clean = s.strip()
            if s_clean:
                clauses = self.count_clauses_in_sentence(s_clean)
                max_clauses = max(max_clauses, clauses)

        return max(1, max_clauses) if text.strip() else 0

    def detect_structures(self, text: str) -> list[str]:
        """Identify grammar structures present in text via regex pattern matching."""
        detected = []
        for struct in self.structures:
            struct_id = struct.get("id")
            patterns = struct.get("patterns", [])
            for pattern in patterns:
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        if struct_id and struct_id not in detected:
                            detected.append(struct_id)
                        break
                except re.error as err:
                    logger.warning("Invalid regex pattern '%s' for structure %s: %s", pattern, struct_id, err)

        return detected

    def validate_grammar(self, text: str, target_level: str | int) -> GrammarCheckResult:
        """
        Validate text against CEFR grammar ceiling constraints and maximum clause limit.

        Args:
            text: AI response text to evaluate.
            target_level: Target CEFR level string (e.g. 'A1', 'B2') or integer (1..20).

        Returns:
            GrammarCheckResult containing pass status, clause metrics, and violations.
        """
        target_rank = self.get_level_rank(target_level)
        constraints = self.get_level_constraints(target_level)
        max_clauses_allowed = constraints.get("max_clauses", 2)

        # 1. Clause count verification
        detected_max_clauses = self.count_clauses(text)
        clause_violation = detected_max_clauses > max_clauses_allowed

        # 2. Grammar structure ceiling check
        detected_structures = self.detect_structures(text)
        disallowed_structures = []
        violations = []

        if clause_violation:
            violations.append(
                f"Sentence clause count ({detected_max_clauses}) exceeds maximum allowed "
                f"clauses ({max_clauses_allowed}) for level '{target_level}'."
            )

        for struct_id in detected_structures:
            struct_info = next((s for s in self.structures if s.get("id") == struct_id), None)
            if not struct_info:
                continue

            intro_level = struct_info.get("introduced_at_level", "PRE-A1")
            intro_rank = self.get_level_rank(intro_level)

            if intro_rank > target_rank:
                disallowed_entry = {
                    "id": struct_id,
                    "name": struct_info.get("name", struct_id),
                    "introduced_at_level": intro_level,
                    "introduced_rank": intro_rank,
                    "target_rank": target_rank,
                }
                disallowed_structures.append(disallowed_entry)
                violations.append(
                    f"Grammar structure '{struct_info.get('name')}' (introduced at '{intro_level}') "
                    f"exceeds ceiling for target level '{target_level}'."
                )

        is_valid = not clause_violation and (len(disallowed_structures) == 0)

        return GrammarCheckResult(
            is_valid=is_valid,
            target_level=target_level,
            target_rank=target_rank,
            max_clauses_allowed=max_clauses_allowed,
            detected_max_clauses=detected_max_clauses,
            clause_violation=clause_violation,
            detected_structures=detected_structures,
            disallowed_structures=disallowed_structures,
            violations=violations,
        )
