# PLAN
# Kế hoạch thực thi — TASK-001: Crawl & Seed Initial Datasets (CEFR Vocab & Dialogue Exemplars)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Cập nhật:** 2026-08-26

---

## Task Reference

```
Task ID:    TASK-001
Task Name:  Crawl & Seed Initial Datasets (CEFR Vocab & Dialogue Exemplars)
Spec:       Viết script scripts/seed_data.py tự động cào/tổng hợp từ vựng CEFR mở (Cambridge EVP/Oxford) và sinh ngân hàng câu thoại mẫu khởi tạo theo (level, persona, topic, dialogue_act).
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Script `python3 scripts/seed_data.py` chạy thành công không lỗi.
- [ ] Sinh ra file `app/data/vocab_bank.json` thô với > 1000 từ vựng A1-B1.
- [ ] Sinh ra file `app/data/sample_dialogue_bank.json` thô với > 100 câu thoại mẫu khởi tạo.
- [ ] Tier 1 verification (`verify.py`) pass 100%.

### Verification Commands
```bash
python3 scripts/seed_data.py
python3 pipeline/scripts/verify.py
```

---

## Execution Steps

### Step 1: Set up plan & runtime state
- **Mục tiêu:** Cập nhật PLAN.md, STATUS.md, PROGRESS_LOG.md sang trạng thái EXECUTING cho TASK-001.
- **Files tạo/sửa:** `pipeline/docs/runtime/PLAN.md`, `pipeline/docs/runtime/STATUS.md`, `pipeline/docs/runtime/PROGRESS_LOG.md`
- **Exit condition:** Các file status được ghi thành công trên disk.

### Step 2: Implement `scripts/seed_data.py` and generate dataset files
- **Mục tiêu:** Viết script seed_data.py để tự động tổng hợp bộ từ vựng CEFR A1-B1 (>1000 từ) xuất ra `app/data/vocab_bank.json` và bộ câu thoại mẫu (>100 câu) xuất ra `app/data/sample_dialogue_bank.json`.
- **Files tạo/sửa:** `scripts/seed_data.py`, `app/data/vocab_bank.json`, `app/data/sample_dialogue_bank.json`
- **Exit condition:** Lệnh `python3 scripts/seed_data.py` chạy không lỗi, `app/data/vocab_bank.json` chứa > 1000 items, `app/data/sample_dialogue_bank.json` chứa > 100 items.

### Step 3: Verify execution and run Tier 1 verification engine
- **Mục tiêu:** Kiểm tra kết quả output của seed_data.py và chạy `python3 pipeline/scripts/verify.py` để đảm bảo code quality & static checks.
- **Exit condition:** `verify.py` hoàn thành và không vi phạm static analysis.

### Step 4: Mark Task DONE and sync status
- **Mục tiêu:** Cập nhật `pipeline/docs/context/Tasks_list.md` chuyển TASK-001 sang `[x] DONE`, cập nhật STATUS.md & PROGRESS_LOG.md.
- **Exit condition:** Task-001 đánh dấu [x] DONE.
