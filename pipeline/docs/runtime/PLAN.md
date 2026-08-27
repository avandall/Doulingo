# PLAN: TASK-007 — Implement Response Rating API & Continuous Feedback Logger

> **Task ID:** TASK-007  
> **Phase:** Phase 2 (Continuous Improvement)  
> **Priority:** P1-High  
> **Target Files:** `app/api/feedback_router.py`, `app/services/feedback_service.py`, `app/data/feedback_log.json`, `tests/test_feedback.py`

---

## 🎯 Goal & Acceptance Criteria
- [x] Endpoint `POST /api/v1/feedback/rate-response` ghi log thành công vào `app/data/feedback_log.json`.
- [x] Câu bị đánh giá "Sáo rỗng" (`hollow`) hoặc "Sai ngữ cảnh" (`out_of_context`) sẽ bị hạ điểm `quality_score` hoặc đưa vào blacklist không dùng lại trong Exemplar RAG.
- [x] Câu được đánh giá "Tốt" (`good`) với điểm cao tự động được cân nhắc đưa vào Dialogue Exemplar Bank.
- [x] Pytest cho feedback router & service pass 100% (`pytest tests/test_feedback.py`) và `python3 pipeline/scripts/verify.py` PASS 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Implement `app/services/feedback_service.py` & update RAG filter [x]
- Create `FeedbackService` class managing feedback logging and dialogue bank updates.
- Save structured feedback rating entries to `app/data/feedback_log.json`.
- For `hollow` or `out_of_context` ratings: lower `quality_score` in `sample_dialogue_bank.json` and flag `is_blacklisted = True` if score drops below threshold (<= 2.0).
- For `good` ratings: boost `quality_score` for existing matching exemplars or automatically create and add new high-scoring exemplar entries into `sample_dialogue_bank.json`.
- Update `app/core/exemplar_rag.py` to exclude blacklisted/low-quality exemplars during retrieval.

### Step 2: Implement `app/api/feedback_router.py` & initialize feedback log [x]
- Define Pydantic request/response models: `RateResponseRequest` (`response_text`, `rating`, `dialogue_id`, `context`, `user_id`, `comments`) and `RateResponseResponse`.
- Create router endpoint `POST /api/v1/feedback/rate-response` in `app/api/feedback_router.py`.
- Ensure `app/data/feedback_log.json` exists as `[]` if missing.
- Register router in `app/api/routers/__init__.py` and include in `app/main.py`.

### Step 3: Write `tests/test_feedback.py` & Verify 100% PASS [x]
- Write comprehensive unit tests in `tests/test_feedback.py`:
  1. API endpoint validation (`rating` value validation, empty text handling).
  2. Logging ratings into `app/data/feedback_log.json`.
  3. Quality score reduction and blacklisting for `hollow` / `out_of_context`.
  4. Exemplar auto-addition / score boost for `good` rating.
  5. Exemplar RAG filtering of blacklisted exemplars.
- Run `pytest tests/test_feedback.py` and `python3 pipeline/scripts/verify.py`.
