# PLAN
# Kế hoạch thực thi — TASK-001: Material Bank Data Models & Markdown Parser (`app/material_bank.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-001
Task Name:  Material Bank Data Models & Markdown Parser (`app/material_bank.py`)
Spec:       Tạo module app/material_bank.py chứa Pydantic models (Persona, Question, VocabularyItem, GrammarPattern, TopicBank) và lớp MaterialBank tự động parse tất cả 5 file markdown (DB1_*.md -> DB5_*.md) tại startup.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] File `app/material_bank.py` được tạo với các Pydantic models chuẩn hóa (`Persona`, `Question`, `VocabularyItem`, `GrammarPattern`, `TopicBank`).
- [ ] Lớp `MaterialBank` có phương thức `load_all(docs_dir)` đọc thành công cả 5 file `DB1_*.md` đến `DB5_*.md`.
- [ ] Parser bóc tách chính xác các section: Persona Pool, Question Pool (by Band), Vocab Pool (by Band), Grammar Patterns.
- [ ] Hỗ trợ chuẩn hóa `topic_id` và các phương thức `get_topic(topic_id)` (case-insensitive, dash/underscore insensitive) và `list_topics()` trả về dữ liệu nhanh chóng từ RAM.
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.

### Verification Commands
```bash
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Implement `app/material_bank.py`
- **Mục tiêu:** Định nghĩa Pydantic models và class `MaterialBank` tự động parse 5 file markdown trong `docs/`.
- **Files tạo/sửa:** `app/material_bank.py`
- **Exit condition:** `app/material_bank.py` import thành công, `MaterialBank().load_all('docs')` nạp > 0 topics.

### Step 2: Verification (Tier 1 & Tier 2)
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit). Thực hiện Tier 2 Cognitive Review dựa trên `git diff` và ghi log vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` pass 100%, `DEBATE_LOG.md` result APPROVED.

### Step 3: Documentation & State Update
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-001` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, và thực hiện atomic git commit.
- **Files tạo/sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`
- **Exit condition:** Git commit thành công.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 2
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-001 |
