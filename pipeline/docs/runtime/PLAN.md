# PLAN: TASK-011 — Decoupled Fast Voice LLM & Background Evaluation Pipeline

> **Task ID:** TASK-011  
> **Phase:** Phase 4 (Ultra-Low-Latency & Real-Time Voice Streaming Optimization)  
> **Priority:** P0-Critical  
> **Target Files:** `app/core/ai_engine.py`, `app/api/routers/chat.py`, `tests/test_decoupled_voice_llm.py`

---

## 🎯 Goal & Acceptance Criteria
- [x] Implement `process_turn_fast()` in `app/core/ai_engine.py` generating fast plain text AI responses (~30-40 tokens) with latency < 400ms.
- [x] Implement `evaluate_turn_background()` in `app/core/ai_engine.py` and `BACKGROUND_EVAL_STORE` for async evaluation (grammar analysis, scores, error journal, native phrasing, translation).
- [x] Add `POST /api/process_turn_fast` and `GET /api/turn_evaluation/{turn_id}` in `app/api/routers/chat.py` leveraging FastAPI `BackgroundTasks`.
- [x] Write unit & integration tests in `tests/test_decoupled_voice_llm.py` verifying fast voice generation & background evaluation polling.
- [x] Pass `pytest tests/test_decoupled_voice_llm.py` and `python3 pipeline/scripts/verify.py` 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Implement Fast Voice Generation & Background Evaluation in `app/core/ai_engine.py` [x]
- Add `process_turn_fast()` method to `AIEngine` for lightweight utterance generation without heavy JSON CoT/feedback overhead.
- Add `evaluate_turn_background()` method and `BACKGROUND_EVAL_STORE` dictionary to compute detailed feedback, scores, Error Journal recording, and Vietnamese translation in background.

### Step 2: Implement Decoupled Router Endpoints in `app/api/routers/chat.py` [x]
- Add `FastTurnRequest` schema.
- Add `POST /api/process_turn_fast` endpoint to immediately return `ai_response` and schedule `evaluate_turn_background` via `BackgroundTasks`.
- Add `GET /api/turn_evaluation/{turn_id}` endpoint to retrieve background evaluation results.

### Step 3: Create Tests `tests/test_decoupled_voice_llm.py` [x]
- Test fast voice generation method.
- Test background evaluation worker & storage.
- Test `POST /api/process_turn_fast` and `GET /api/turn_evaluation/{turn_id}` API flow.

### Step 4: Run Verification & Update Documentation [x]
- Execute `pytest tests/test_decoupled_voice_llm.py`.
- Execute `python3 pipeline/scripts/verify.py`.
- Update `STATUS.md`, `PROGRESS_LOG.md`, `PLAN.md`, and mark `[x] DONE` in `Tasks_list.md`.
