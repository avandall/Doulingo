# Implementation Plan — TASK-018: Weekly Performance Reporting Engine & Hidden Scoring UI (`app/reporting.py`)

## Goal
Build `app/reporting.py` to aggregate weekly performance reports across 4 IELTS axes (Fluency, Lexical, Grammar, Pronunciation) using Tier 2 evaluation history (`TASK-012`) and overall profile bands (`TASK-013`). Ensure the main conversation UI hides real-time per-sentence band scores (Hidden Scoring UI) to reduce exam pressure for learners while providing rich weekly analytics via `/api/reports/weekly`.

## Spec & Acceptance Criteria
- [ ] DB Schema Update (`app/db.py`):
  - Add `tier2_evaluations` table to log Tier 2 deep evaluations (`id`, `user_id`, `fluency_score`, `lexical_score`, `grammar_score`, `pronunciation_score`, `raw_score`, `created_at`).
  - Add helper functions `save_tier2_evaluation_record` and `get_tier2_evaluations_history`.
- [ ] Weekly Performance Reporting Engine (`app/reporting.py`):
  - Implement `save_tier2_evaluation(user_id: str, score_result: Any, conn: Any = None) -> dict`.
  - Implement `generate_weekly_report(user_id: str, days: int = 7, conn: Any = None) -> dict[str, Any]`:
    - Summarizes evaluation count and 4-axis scores (Fluency, Lexical, Grammar, Pronunciation).
    - Retrieves overall band estimate and recurring errors from `user_profile`.
    - Generates actionable recommendations and strengths/weaknesses summary.
- [ ] API Endpoint (`app/main.py`):
  - `GET /api/reports/weekly` (or `GET /api/reporting/weekly`): Query parameter `user_id` (default "user_demo") & `days` (default 7).
- [ ] Hidden Scoring UI (`static/js/app.js` & `static/index.html`):
  - Ensure main conversation view does not render per-turn band score badges.
  - Provide UI hooks/modal for weekly report viewing.
- [ ] Unit Tests (`tests/test_reporting.py`):
  - Test saving Tier 2 evaluation history to DB.
  - Test `generate_weekly_report` with populated and empty evaluation history.
  - Test API endpoint `/api/reports/weekly`.
- [ ] Phase 4 Verification (`python3 H_docs/scripts/verify.py`):
  - Passes 100% (Ruff, Mypy, Bandit, Pytest).

## Steps
- [ ] Step 0: ORIENT & SPEC — Prepare task plan and update context.
- [ ] Step 1: Add `tier2_evaluations` table & helpers in `app/db.py` and implement `app/reporting.py`.
- [ ] Step 2: Add API endpoint `/api/reports/weekly` in `app/main.py` and update UI for hidden scoring / weekly report.
- [ ] Step 3: Implement test suite `tests/test_reporting.py`.
- [ ] Step 4: Run Phase 4 Verification (`python3 H_docs/scripts/verify.py`) and fix any issues until 100% PASS.

## Status
- **Current Phase:** PHASE 3 (EXECUTE)
- **Iteration:** 46
- **Result:** IN_PROGRESS
