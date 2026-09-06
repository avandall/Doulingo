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
