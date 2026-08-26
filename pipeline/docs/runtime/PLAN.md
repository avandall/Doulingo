# PLAN: TASK-004 — Implement Structured Output CoT & Heuristic Validation Loop Engine

> **Task ID:** TASK-004  
> **Phase:** Phase 1 (Core Execution)  
> **Priority:** P0-Critical  
> **Target Files:** `app/core/ai_engine.py`, `app/core/prompt_factory.py`, `tests/test_ai_engine.py`

---

## 🎯 Goal & Acceptance Criteria
- [ ] Call 1 requests LLM to generate Structured Output JSON CoT (`natural_draft`, `vocab_check`, `final_response`).
- [ ] Heuristic Check validates `final_response`: if PASS, returns result immediately (1 API call).
- [ ] If Heuristic Check FAILS, system automatically feeds back specific violating words to LLM in a retry loop until PASS.
- [ ] Pytest suite for `tests/test_ai_engine.py` passes 100% and Tier 1 verification (`python3 pipeline/scripts/verify.py`) passes 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Update Prompt Factory & Structured Output CoT Schema
- Create `app/core/prompt_factory.py` re-exporting `PromptFactory` & `get_prompt_factory` from `app.rag.prompt_factory` while adding CoT prompt helpers.
- Update `_build_token_efficient_prompt` and prompt templates in `app/core/ai_engine.py` to request Call 1 JSON CoT output containing `natural_draft`, `vocab_check`, `final_response`, and `user_feedback`.
- Update `_parse_json_response` to extract `natural_draft`, `vocab_check`, and `final_response`.

### Step 2: Implement Heuristic Validation & Feedback Retry Loop in AI Engine
- Integrate `HeuristicChecker` from `app.core.heuristic_checker` into `AIEngine`.
- In `process_turn`:
  1. Call 1 LLM request with CoT prompt.
  2. Parse output to extract `final_response`.
  3. Run `heuristic_checker.check_level_ceiling(final_response, target_level)`.
  4. If PASS -> Return result immediately.
  5. If FAIL -> Extract `violating_words`, enter retry loop (up to 2 retries) with targeted feedback instructing LLM to downgrade vocabulary to level ceiling.

### Step 3: Add Pytest Suite & Run Verification
- Write tests in `tests/test_ai_engine.py` testing:
  - CoT fields (`natural_draft`, `vocab_check`, `final_response`) parsing.
  - Single-call PASS path.
  - Heuristic check failure & retry feedback loop execution.
- Run `pytest tests/test_ai_engine.py` and `python3 pipeline/scripts/verify.py` until 100% PASS.
