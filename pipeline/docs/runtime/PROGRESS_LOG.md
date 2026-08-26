# PROGRESS LOG
# Nhật ký tiến độ chi tiết — Ghi lại toàn bộ lịch sử thao tác & phát sinh

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** 2026-08-26 21:27

---

## 📅 Lịch sử thực thi

### [2026-08-26 21:21] — Khởi tạo TASK-001
- **Task ID:** TASK-001 (Crawl & Seed Initial Datasets)
- **Hành động:** 
  - Khởi tạo PLAN.md và STATUS.md cho TASK-001.
  - Phân tích bối cảnh và yêu cầu cho `scripts/seed_data.py`, `app/data/vocab_bank.json` (>1000 từ vựng A1-B1) và `app/data/sample_dialogue_bank.json` (>100 câu thoại mẫu).

### [2026-08-26 21:22] — Hoàn thành TASK-001
- **Hành động:**
  - Viết `scripts/seed_data.py` tự động tích hợp nguồn từ vựng Oxford/Cambridge CEFR A1-B1 kết hợp dữ liệu từ `data/dictionary.db`.
  - Sinh thành công `app/data/vocab_bank.json` với **2,445 từ vựng** (yêu cầu > 1000).
  - Sinh thành công `app/data/sample_dialogue_bank.json` với **150 câu thoại mẫu** phân loại theo level, persona, topic, dialogue_act (yêu cầu > 100).
  - Kiểm định static analysis (Ruff & Mypy) pass 100%.
  - Cập nhật trạng thái `TASK-001` thành `[x] DONE` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-26 21:26] — Khởi tạo TASK-002
- **Task ID:** TASK-002 (Build Vocabulary Bank & Heuristic Level Checker)
- **Hành động:**
  - Tạo `PLAN.md` 4 bước và cập nhật `STATUS.md` cho TASK-002.

### [2026-08-26 21:27] — Hoàn thành TASK-002
- **Hành động:**
  - Viết module `app/core/heuristic_checker.py` thực hiện:
    1. Đọc dữ liệu `app/data/vocab_bank.json` và ánh xạ rank level CEFR (Pre-A1 -> C2) và 20-level integer scale.
    2. Đếm từ, đếm câu, và tính độ dài câu trung bình.
    3. Tra từ vựng vượt trần `check_level_ceiling(text, target_level)` với thời gian thực thi siêu nhanh **< 0.5ms** (đạt yêu cầu < 5ms).
  - Viết bộ test `tests/test_heuristic_checker.py` gồm 8 test cases kiểm tra initialization, sentence analysis, level ceiling pass/violate, integer level mapping, benchmarking, tuple unpacking & dict indexing.
  - Sửa lỗi linting import/SIM102 và chạy `python3 pipeline/scripts/verify.py --test-target tests/test_heuristic_checker.py` đạt **PASS 100%** (Ruff, Mypy, Bandit, Pytest đều PASS).
  - Đánh dấu `[x] DONE` cho `TASK-002` trong `pipeline/docs/context/Tasks_list.md`.
