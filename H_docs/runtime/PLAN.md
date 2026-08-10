# PLAN
# Kế hoạch thực thi — TASK-004: Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-004
Task Name:  Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`)
Spec:       Viết bộ unit test comprehensive cho PromptFactory trong `tests/test_prompt_factory.py`. Đảm bảo kiểm chứng tốc độ dựng prompt (< 5ms), tính đa dạng không lặp lại giữa các lần sample, và các trường hợp fallback (topic không tồn tại, bank thiếu dữ liệu).
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Implement `tests/test_prompt_factory.py` với pytest fixtures và test cases chi tiết.
- [ ] Benchmark test: Chứng minh thời gian dựng prompt trung bình (`build_system_prompt`) < 5ms over 100+ iterations.
- [ ] Diversity test: Gọi `build_system_prompt` 5 lần liên tiếp trên cùng 1 topic và xác nhận thu được các prompt có sự khác biệt ở Vocab/Persona/Question.
- [ ] Fallback test: Kiểm tra `build_system_prompt` và `sample_materials` với topic_id không tồn tại hoặc level không khớp hoạt động an toàn không ném exception.
- [ ] Target Level & Character test: Kiểm tra đúng character definitions (Lily, etc.) và target levels được nhúng vào System Prompt.
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.
- [ ] Tier 2 Cognitive Review đạt `APPROVED` trong `H_docs/runtime/DEBATE_LOG.md`.

### Verification Commands
```bash
pytest tests/test_prompt_factory.py
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Implement `tests/test_prompt_factory.py`
- **Mục tiêu:** Viết file `tests/test_prompt_factory.py` chứa test suite đầy đủ cho `PromptFactory`.
- **Files tạo/sửa:** `tests/test_prompt_factory.py`
- **Exit condition:** `pytest tests/test_prompt_factory.py` chạy qua 100% pass.

### Step 2: Verification (Tier 1 & Tier 2)
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit). Thực hiện Tier 2 Cognitive Review dựa trên `git diff` và ghi log vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` pass 100%, `DEBATE_LOG.md` result APPROVED.

### Step 3: Documentation & State Update
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-004` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, `H_docs/runtime/ITERATIONS/iter_005.md`, và thực hiện atomic git commit.
- **Files tạo/sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, `H_docs/runtime/ITERATIONS/iter_005.md`
- **Exit condition:** Git commit thành công.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 6
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-004 |
