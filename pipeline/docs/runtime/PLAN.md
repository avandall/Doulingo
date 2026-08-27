# PLAN: TASK-008 — Build Grammar Structure Bank & CEFR Constraint Validator

> **Task ID:** TASK-008  
> **Phase:** Phase 3 (Advanced Validation)  
> **Priority:** P2-Medium  
> **Target Files:** `app/data/grammar_bank.json`, `app/core/grammar_validator.py`, `tests/test_grammar_validator.py`

---

## 🎯 Goal & Acceptance Criteria
- [x] Create `app/data/grammar_bank.json` containing CEFR grammar structures categorized with `introduced_at_level`, `mastered_at_level`, regex patterns, and level constraints (`max_clauses`).
- [x] Implement `app/core/grammar_validator.py` with `GrammarValidator` class that:
  - Detects maximum clause count (`max_clauses`) in sentences.
  - Identifies grammar structures present in AI responses via regex pattern matching.
  - Validates detected structures against the allowed CEFR ceiling (`introduced_at_level`) for a target level.
  - Returns structured `GrammarCheckResult`.
- [x] Create unit tests in `tests/test_grammar_validator.py` covering clause counting, grammar structure detection, level constraint checks, and edge cases.
- [x] Pass `pytest tests/test_grammar_validator.py` and `python3 pipeline/scripts/verify.py` 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Create `app/data/grammar_bank.json` [x]
- Define level constraints (mapping CEFR levels Pre-A1 to C2+ and levels 1-20 to `max_clauses` and rank boundaries).
- Define CEFR grammar structure catalog (Present Simple, Present Continuous, Past Simple, Future going to, Present Perfect, Modals, Conditionals, Passive Voice, Subjunctive) with `introduced_at_level`, `mastered_at_level`, and regex patterns.

### Step 2: Implement `app/core/grammar_validator.py` [x]
- Define dataclass `GrammarCheckResult`.
- Implement `GrammarValidator` class:
  - Level rank resolution (converting string level `"A1"` or int level `2` to rank 0..13).
  - Sentence segmentation and clause counting heuristic algorithm (`count_clauses`).
  - Grammar structure matching (`detect_structures`).
  - Constraint validation logic (`validate_grammar(text, target_level)`).

### Step 3: Implement `tests/test_grammar_validator.py` & Verification [x]
- Test level rank mapping and constraint lookup.
- Test sentence clause counting (single clause, compound sentences, complex sentences).
- Test detection of allowed vs disallowed grammar structures for target levels (e.g. A1 vs B2 vs C1).
- Test full validation workflow returning `GrammarCheckResult`.
- Run `pytest tests/test_grammar_validator.py` and `python3 pipeline/scripts/verify.py`.
