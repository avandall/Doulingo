# PLAN
# Kế hoạch thực thi — TASK-007: End-to-End Test Suite & MCP Browser Interactive Testing (<10 Calls)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Cập nhật:** 2026-08-22 20:02

---

## Task Reference

```
Task ID:    TASK-007
Task Name:  End-to-End Test Suite & MCP Browser Interactive Testing (<10 Calls)
Phase:      Phase 7 (E2E Verification & Browser QA)
Spec:       Viết E2E test suite kiểm thử toàn bộ 5 kịch bản tích hợp của ứng dụng Duolingo Speak AI (Roleplay Empathy, IELTS Exam Flow, Topic Explorer, API Trace Logging, TTS & Audio Fillers). Giới hạn gọi API <10 calls. Pass 100% verify.py.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [x] Xây dựng test file E2E `tests/test_e2e_conversational_system.py` bao phủ 5 use cases chính.
- [x] Chạy `pytest tests/test_e2e_conversational_system.py -v` thành công 100%.
- [x] Chạy `python3 pipeline/scripts/verify.py` pass 100% (Ruff, Mypy, Bandit, Pytest).
- [x] Giới hạn tổng API calls thực nghiệm < 10 calls.

### Verification Commands
```bash
pytest tests/test_e2e_conversational_system.py -v
python3 pipeline/scripts/verify.py
```

---

## Execution Steps

### [x] Step 1: Create Comprehensive E2E Test Suite (`tests/test_e2e_conversational_system.py`)
- **Mục tiêu:**
  - Viết `tests/test_e2e_conversational_system.py` sử dụng Starlette TestClient / pytest fixture để test toàn bộ ứng dụng FastApi + AI Engine.
  - Test 1: Full conversation turn với AI Engine (Roleplay, Topic shift detection, Empathy response, Anti-repetition context memory).
  - Test 2: IELTS Read-Then-Speak exam submission & DET scoring report API endpoints.
  - Test 3: Topic explorer scenario provider bridge, categories, and keyword searching.
  - Test 4: Real-time API trace log file update (`logs/api_trace.log`), quota endpoint `/api/health/quota`, trace endpoint `/api/trace`.
  - Test 5: TTS service voice mapping, rate/pitch natural tuning, instant filler sound endpoint & character mapping.
- **Files tạo/sửa:** `tests/test_e2e_conversational_system.py`
- **Exit condition:** `pytest tests/test_e2e_conversational_system.py -v` pass 100%.

### [x] Step 2: Run Tier 1 Verification (`python3 pipeline/scripts/verify.py`) & Fix any issues
- **Mục tiêu:** Run full deterministic quality checks (`verify.py`), ensuring Ruff lint, Mypy type-checking, Bandit security, and all Pytest test suites pass cleanly.
- **Files tạo/sửa:** `tests/test_e2e_conversational_system.py` (if any linting/typing tweaks needed)
- **Exit condition:** `python3 pipeline/scripts/verify.py` status is PASS.

### [x] Step 3: Update System Runtime Docs & Mark Task DONE (`Phase 7 REPORT`)
- **Mục tiêu:**
  - Update `pipeline/docs/runtime/STATUS.md` with TASK-007 completion details and system status.
  - Update `pipeline/docs/runtime/PROGRESS_LOG.md` appending iteration log.
  - Update `pipeline/docs/runtime/PROOF_OF_SOLUTION.md` with test evidence.
  - Update `pipeline/docs/context/Tasks_list.md` marking `TASK-007` as `[x] DONE`.
- **Files tạo/sửa:** `pipeline/docs/runtime/STATUS.md`, `pipeline/docs/runtime/PROGRESS_LOG.md`, `pipeline/docs/runtime/PROOF_OF_SOLUTION.md`, `pipeline/docs/context/Tasks_list.md`, `pipeline/docs/runtime/PLAN.md`
- **Exit condition:** Runtime docs updated on filesystem, task marked `[x] DONE` in `Tasks_list.md`. Stop execution without committing git (Reviewer will handle Tier 2 cognitive review & git commit).

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      3
Context refresh at:   Iteration 3
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-22 | Khởi tạo plan cho TASK-007 |
