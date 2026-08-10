# PLAN
# Kế hoạch thực thi — TASK-003: Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-003
Task Name:  Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)
Spec:       Xây dựng module app/prompt_factory.py chứa class PromptFactory để sample ngẫu nhiên nguyên liệu từ MaterialBank (Persona, Vocab, Questions, Grammar) và lắp ráp System Prompt linh hoạt kết hợp thông tin AI Character và User Level.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Implement `app/prompt_factory.py` chứa class `PromptFactory`.
- [ ] Implement `sample_materials(topic_id, level)` sample 1 Persona, 3-4 Vocab items, 1-2 Questions, và Grammar patterns theo target level.
- [ ] Implement `build_system_prompt(topic_id, level, character_id, user_history)` lắp ráp thành công System Prompt hoàn chỉnh.
- [ ] Fallback an toàn nếu `topic_id` không tồn tại trong `MaterialBank` hoặc khi `MaterialBank` không có đủ nguyên liệu.
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.
- [ ] Tier 2 Cognitive Review đạt `APPROVED` trong `H_docs/runtime/DEBATE_LOG.md`.

### Verification Commands
```bash
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Implement `app/prompt_factory.py`
- **Mục tiêu:** Tạo module `app/prompt_factory.py` với class `PromptFactory` và helper factory methods.
- **Files tạo/sửa:** `app/prompt_factory.py`
- **Exit condition:** `python3 -c "import app.prompt_factory"` chạy không lỗi.

### Step 2: Verification (Tier 1 & Tier 2)
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit). Thực hiện Tier 2 Cognitive Review dựa trên `git diff` và ghi log vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` pass 100%, `DEBATE_LOG.md` result APPROVED.

### Step 3: Documentation & State Update
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-003` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, `H_docs/runtime/ITERATIONS/iter_004.md`, và thực hiện atomic git commit.
- **Files tạo/sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, `H_docs/runtime/ITERATIONS/iter_004.md`
- **Exit condition:** Git commit thành công.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 5
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-003 |
