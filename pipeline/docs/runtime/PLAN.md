# PLAN: TASK-009 — Implement ASR Adaptive Level Detector (IRT Model)

> **Task ID:** TASK-009  
> **Phase:** Phase 3 (Advanced Adaptive Engine)  
> **Priority:** P2-Medium  
> **Target Files:** `app/core/adaptive_level_detector.py`, `tests/test_adaptive_level.py`

---

## 🎯 Goal & Acceptance Criteria
- [x] Implement `app/core/adaptive_level_detector.py` with IRT (Item Response Theory) model analyzing ASR transcripts (speech rate/WPM, sentence length/MLU, vocabulary complexity/diversity, filler density).
- [x] Maintain rolling history of spoken turns to dynamically estimate user's actual CEFR level (Level 1-20 / Pre-A1 to C2+) and emit difficulty adjustments (`increase`, `hold`, `decrease`).
- [x] Provide integration interface `get_effective_level` for `AIEngine` to automatically adjust difficulty based on measured level instead of static selection.
- [x] Implement comprehensive unit tests in `tests/test_adaptive_level.py`.
- [x] Pass `pytest tests/test_adaptive_level.py` and `python3 pipeline/scripts/verify.py` 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Implement `app/core/adaptive_level_detector.py` [x]
- Implement `ASRFeatureExtractor` to compute WPM, MLU, lexical diversity (TTR/MTLD), filler density, and vocabulary complexity from ASR transcripts.
- Implement `IRTLevelModel` (1PL/2PL Rasch model) converting theta $\theta \in [-3.0, +3.0]$ to CEFR level (1-20), CEFR code (Pre-A1 to C2+), and band estimate (4.0 - 9.0).
- Implement `AdaptiveLevelDetector` class managing multi-turn rolling state, IRT updates $\theta_{new} = \theta_{old} + \eta(S - P)$, persistence in SQLite (`user_adaptive_level`), and adjustment signals.
- Provide `get_effective_level` helper for AI Engine dynamic difficulty adjustment.

### Step 2: Implement `tests/test_adaptive_level.py` [x]
- Test feature extraction algorithms (WPM, MLU, filler density, vocabulary complexity).
- Test IRT mathematical mapping (theta to level, level to theta, success probability $P(\theta, \beta)$).
- Test multi-turn adaptive level updates, dynamic level increases/decreases, and persistence.
- Test `get_effective_level` integration.

### Step 3: Run Deterministic Verification & Finalize [x]
- Run `pytest tests/test_adaptive_level.py`.
- Run `python3 pipeline/scripts/verify.py`.
- Ensure Ruff, Mypy, Bandit, and Pytest pass 100%.
- Update `STATUS.md`, `PROGRESS_LOG.md`, `PLAN.md`, and mark `[x] DONE` in `Tasks_list.md`.
