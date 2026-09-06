# PROGRESS LOG
# Nhật ký tiến độ chi tiết từng bước

> **Trạng thái:** RUNTIME (Append-only by AI Agent)

## [2026-09-06] TASK-001 Execution
- [x] Đã tạo PLAN.md với 4 atomic steps cho TASK-001.
- [x] Step 1: Dependencies & Environment Setup (`requirements.txt`, `.gitignore`).
- [x] Step 2: HTML Template & Print CSS (`app/templates/reports/speaking_report.html`).
- [x] Step 3: PDF Service Implementation (`app/services/pdf_report_service.py`).
- [x] Step 4: Unit Test & Verification (`tests/test_pdf_reporting.py`).
- [x] Verification report: `python3 pipeline/scripts/verify.py` PASSED 100% (Ruff, Mypy, Bandit, Pytest).
- [x] `reports/sample_report.pdf` được tạo thành công với kích thước ~132 KB, 3 trang A4.

## [2026-09-06] TASK-002 Execution
- [x] Đã khởi tạo PLAN.md cho TASK-002 với 3 atomic steps.
- [x] Step 1: Thêm schema bảng `exam_reports` & các helper functions (`get_cached_exam_report`, `save_exam_report`, `get_exam_report_by_id`) trong `app/storage/db.py`.
- [x] Step 2: Tạo FastAPI APIRouter `app/api/routers/reports_router.py` hỗ trợ Idempotency caching theo ngày, binary PDF stream (`FileResponse`), và report metadata endpoints. Mount router vào `app/main.py`.
- [x] Step 3: Viết bộ test suite tích hợp endpoint trong `tests/test_pdf_reporting.py` kiểm định full flow (201 Created lần đầu, 200 OK idempotent cache, 201 Created với force=True, 200 OK binary PDF streaming, 404 cho report_id không tồn tại).
- [x] Verification report: `python3 pipeline/scripts/verify.py` PASSED 100% (Ruff, Mypy, Bandit, Pytest).

## [2026-09-07] TASK-004 Execution
- [x] Đã khởi tạo PLAN.md cho TASK-004 với 4 atomic steps.
- [x] Step 1: Định nghĩa service `cleanup_audio_cache` trong `app/services/cron_service.py` xử lý safe check thư mục chưa tồn tại / rỗng, lọc mtime > 24h, xóa file audio cũ và ghi log chi tiết.
- [x] Step 2: Khởi tạo Inngest scheduled cron function `cleanup-audio-cache` (`cron="0 3 * * *"` daily) trong `app/services/background_job_service.py` và đăng ký vào endpoint `/api/inngest` trong `app/main.py`.
- [x] Step 3: Thêm bộ test suite `test_cron_cleanup_empty_or_missing_directory` và `test_cron_cleanup_deletes_old_files_keeps_new` trong `tests/test_background_jobs.py`.
- [x] Step 4: Verification report: `python3 pipeline/scripts/verify.py` PASSED 100% (Ruff, Mypy, Bandit, Pytest).
