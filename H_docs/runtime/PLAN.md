# PLAN
# Kế hoạch thực thi — TASK-002: Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-002
Task Name:  Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`)
Spec:       Viết toàn bộ unit test suite trong tests/test_material_bank.py cho app/material_bank.py để kiểm tra việc parse 5 file DB markdown, indexing, case-insensitive retrieval, topic listing, và singleton behavior.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Test case 1: Nạp cả 5 file DB (`docs/DB1_*.md` -> `docs/DB5_*.md`) kiểm tra số lượng Topic > 0 (161 topics).
- [ ] Test case 2: Kiểm tra các Topic parsed có đủ Persona pool, Question pool và Vocabulary pool.
- [ ] Test case 3: Kiểm tra `get_topic(topic_id)` hoạt động chính xác không phân biệt hoa thường và dấu gạch nối (`shopping-mall`, `SHOPPING_MALL`, `Shopping Mall`).
- [ ] Test case 4: Kiểm tra truy vấn topic không tồn tại trả về `None`.
- [ ] Test case 5: Kiểm tra `list_topics()` trả về đầy đủ metadata summary của tất cả các topics.
- [ ] Test case 6: Kiểm tra hàm `get_material_bank()` trả về singleton instance của `MaterialBank`.
- [ ] Test case 7: Kiểm tra parse custom markdown block cô lập.
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.

### Verification Commands
```bash
pytest tests/test_material_bank.py
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Create `tests/test_material_bank.py`
- **Mục tiêu:** Viết unit test suite với 100% pass rate bao phủ đầy đủ các case.
- **Files tạo/sửa:** `tests/test_material_bank.py`
- **Exit condition:** `pytest tests/test_material_bank.py` chạy 100% PASS.

### Step 2: Verification (Tier 1 & Tier 2)
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit). Thực hiện Tier 2 Cognitive Review dựa trên `git diff` và ghi log vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` pass 100%, `DEBATE_LOG.md` result APPROVED.

### Step 3: Documentation & State Update
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-002` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, và thực hiện atomic git commit.
- **Files tạo/sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`
- **Exit condition:** Git commit thành công.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 3
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-002 |
