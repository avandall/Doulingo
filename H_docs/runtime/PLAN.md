# PLAN
# Kế hoạch thực thi — TASK-007: End-to-End Integration Testing & Latency Benchmarks (`tests/test_integration_material_bank.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-007
Task Name:  End-to-End Integration Testing & Latency Benchmarks (`tests/test_integration_material_bank.py`)
Spec:       Tạo test suite mô phỏng full turn conversation từ FastAPI -> Prompt Factory -> LLM Engine -> Structured Output với MaterialBank topic_id, kiểm tra đầy đủ JSON response (ai_response, ai_response_vi, user_feedback, v.v.) và đo lường latency benchmark.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Tạo file integration test suite `tests/test_integration_material_bank.py` với `pytest` và `TestClient`.
- [ ] Test case 1: Full turn roleplay flow với `start_scenario` và `process_turn` cho MaterialBank `topic_id` (e.g. `work_job_interview`, `travel_booking`).
- [ ] Test case 2: Verification of structured JSON fields (`ai_response`, `ai_response_vi`, `user_feedback`, `grammar_corrections`, `pronunciation_tips`, `vocabulary_hints`, `suggested_replies`).
- [ ] Test case 3: Latency Benchmark - Đảm bảo response time của endpoint `/api/start_scenario` và `/api/process_turn` (khi mock hoặc integration) đáp ứng ngưỡng thời gian cho phép (< 50ms đối với prompt assembly / routing, và hợp lý với LLM).
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.
- [ ] Tier 2 Cognitive Review được ghi nhận trong `H_docs/runtime/DEBATE_LOG.md`.

### Verification Commands
```bash
pytest tests/test_integration_material_bank.py
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Create `tests/test_integration_material_bank.py`
- **Mục tiêu:** Viết các test cases kiểm thử end-to-end cho FastAPI client nạp MaterialBank scenarios, khởi tạo phiên thoại `/api/start_scenario`, thực hiện lượt thoại `/api/process_turn`, kiểm tra đầy đủ schema fields và benchmark latency.
- **Files tạo:** `tests/test_integration_material_bank.py`
- **Exit condition:** `pytest tests/test_integration_material_bank.py` pass 100%.

### Step 2: Tier 1 Verification
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit).
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`
- **Exit condition:** `verify.py` pass 100% không còn lỗi.

### Step 3: Tier 2 Cognitive Review
- **Mục tiêu:** Thực hiện Tier 2 Review trên `git diff` theo `H_docs/core/REVIEW_PROTOCOL.md` và ghi nhận vào `DEBATE_LOG.md`.
- **Files sửa:** `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** Review result APPROVED.

### Step 4: Documentation, State Update & Git Commit
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-007` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, và thực hiện atomic git commit.
- **Files sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`
- **Exit condition:** Git commit thành công.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 8
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-007 |
