# TASK EXECUTION PLAN
# Task TASK-002: Xây dựng Endpoint Xuất Báo Cáo PDF & Idempotent Caching

> **Trạng thái:** COMPLETED | **Ngày:** 2026-09-06

---

## 🎯 Task Goal
Cung cấp REST API router `/api/reports/speaking/...` cho phép tạo báo cáo PDF theo `session_id`, lưu vết trong database SQLite (`exam_reports`), hỗ trợ Idempotent caching theo ngày (gọi lại lần 2 trả về HTTP 200 OK với report_id cũ, truyền `{"force": true}` ép sinh lại PDF với HTTP 201 Created), đồng thời hỗ trợ tải file PDF nhị phân và tra cứu metadata báo cáo.

---

## 📋 Atomic Steps

### [x] Step 1: Database Table & Service Layer Helper
- Tạo bảng `exam_reports` trong SQLite (`data/custom_topics.db` qua `app/storage/db.py`).
- Cung cấp các helper functions trong `app/storage/db.py` (`get_cached_exam_report`, `save_exam_report`, `get_exam_report_by_id`) để tìm kiếm cached report theo `session_id` trong cùng ngày, lưu vết report mới, và lấy thông tin report theo `report_id`.

### [x] Step 2: REST API Router & Application Mount (`app/api/routers/reports_router.py`, `app/main.py`)
- Định nghĩa router FastAPI `app/api/routers/reports_router.py` với các endpoints:
  - `POST /api/reports/speaking/{session_id}/generate`: Idempotent endpoint, nhận `{"force": false}`, trả 201 Created (lần đầu / force) hoặc 200 OK (cache).
  - `GET /api/reports/speaking/{report_id}/file`: Trả về `FileResponse` binary PDF (application/pdf) hoặc 404.
  - `GET /api/reports/speaking/{report_id}`: Trả về metadata chi tiết và `download_url`.
- Mount `reports_router` vào `app/main.py` và cập nhật `app/api/routers/__init__.py`.

### [x] Step 3: Unit & Integration Tests & Verification (`tests/test_pdf_reporting.py`)
- Thêm test suite kiểm định trong `tests/test_pdf_reporting.py`:
  - Lần đầu generate trả về 201 Created kèm download link.
  - Gọi lại lần 2 trong ngày trả về 200 OK với report_id cũ.
  - Gọi kèm `{"force": true}` sinh PDF mới trả về 201 Created.
  - Tải file nhị phân qua `GET /file` hoạt động chuẩn, ID giả trả về 404.
  - Tra cứu metadata qua `GET /{report_id}` trả về 200 / 404 đúng chuẩn.
- Chạy `python3 pipeline/scripts/verify.py` đạt PASS 100%.
