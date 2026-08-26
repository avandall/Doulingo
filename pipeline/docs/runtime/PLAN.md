# PLAN
# Kế hoạch thực thi — TASK-002: Build Vocabulary Bank & Heuristic Level Checker

> **Trạng thái:** COMPLETED | **Tạo bởi:** AI | **Cập nhật:** 2026-08-26

---

## Task Reference

```
Task ID:    TASK-002
Task Name:  Build Vocabulary Bank & Heuristic Level Checker
Spec:       Đọc dữ liệu từ app/data/vocab_bank.json và viết module app/core/heuristic_checker.py đếm từ, tính độ dài câu, tra từ vựng vượt trần.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [x] Module `HeuristicChecker.check_level_ceiling(text, target_level)` trả về `is_violated: bool` và danh sách từ vi phạm trong < 5ms.
- [x] Pytest cho `HeuristicChecker` pass 100%.

### Scope
- **Files được sửa/tạo:** `app/core/heuristic_checker.py`, `tests/test_heuristic_checker.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

### Verification Commands
```bash
pytest tests/test_heuristic_checker.py
python3 pipeline/scripts/verify.py --test-target tests/test_heuristic_checker.py
```

---

## Execution Steps

### Step 1: Create `app/core/heuristic_checker.py` [DONE]
- **Mục tiêu:** Xây dựng class `HeuristicChecker` đọc `app/data/vocab_bank.json`, phân tích độ dài câu, đếm từ, và thực hiện kiểm tra trần từ vựng `check_level_ceiling(text, target_level)` trong < 5ms.
- **Result:** Module hoàn thành, độ trễ trung bình < 0.5ms.

### Step 2: Implement comprehensive tests in `tests/test_heuristic_checker.py` [DONE]
- **Mục tiêu:** Viết bộ test suite kiểm tra tính đúng đắn của HeuristicChecker.
- **Result:** 8/8 tests passed 100%.

### Step 3: Run Tier 1 Verification (`python3 pipeline/scripts/verify.py`) [DONE]
- **Mục tiêu:** Đảm bảo toàn bộ ruff, mypy, pytest pass 100%.
- **Result:** Verification Report: PASS 100%.

### Step 4: Mark TASK-002 DONE and update progress logs [DONE]
- **Mục tiêu:** Cập nhật `pipeline/docs/context/Tasks_list.md` chuyển TASK-002 sang `[x] DONE`.
- **Result:** Cập nhật file thành công.
