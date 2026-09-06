# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-06 23:12

---

## 🎯 Task Spec: TASK-002
### 📌 TASK-002: Xây dựng Endpoint Xuất Báo Cáo PDF & Idempotent Caching

#### Metadata
```
Task ID:         TASK-002
Task Name:       Xây dựng Endpoint Xuất Báo Cáo PDF & Idempotent Caching
Phase:           Phase 1
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Cung cấp API cho Frontend gọi tạo và tải PDF, đồng thời tuân thủ nguyên tắc "Store & Link" và chống tạo file trùng lặp khi người dùng bấm nút nhiều lần (Idempotency).
- **What:** Tạo bảng `exam_reports` trong SQLite DB (`data/custom_topics.db` hoặc `data/reports.db`), tạo router `app/api/routers/reports_router.py` với các endpoints:
  - `POST /api/reports/speaking/{session_id}/generate` (hỗ trợ body `{"force": false}`)
  - `GET /api/reports/speaking/{report_id}/file` (trả về `FileResponse` application/pdf)
  - `GET /api/reports/speaking/{report_id}` (trả về metadata và URL tải)

#### Acceptance Criteria
- [ ] `POST /api/reports/speaking/{session_id}/generate` lần đầu trả về 201 Created kèm download link.
- [ ] Gọi lại lần 2 trong cùng ngày với cùng session_id trả về 200 OK với report_id cũ, không sinh thêm file PDF mới.
- [ ] Gọi kèm `{"force": true}` bỏ qua cache và sinh report mới (201 Created).
- [ ] `GET /api/reports/speaking/{report_id}/file` tải về đúng file PDF nhị phân. ID lạ trả về 404.

#### Scope
- **Files được sửa/tạo:** `app/api/routers/reports_router.py`, `app/main.py`, `app/services/pdf_report_service.py`, `tests/test_pdf_reporting.py`

#### Verification Commands
```bash
pytest tests/test_pdf_reporting.py
```

---

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime:          Python 3.10+ (WSL Linux Ubuntu / CPython) Framework:        FastAPI >= 0.115.0,Web Server:       Uvicorn (ASGI) Validation:       Pydantic v2,API Protocol:     RESTful JSON API + Binary File Streams (FileResponse) PDF Engine:       Playwright Headless Chromium + Jinja2 Templates + Print CSS,Background Engine: Inngest Python SDK / FastAPI BackgroundTasks + Async IO
- **Scope Boundaries:** ```,✅ app/**                               (Router, Services, Schemas, Templates) ✅ tests/**                              (Unit & Integration test suites),✅ reports/**, output/**                 (Thư mục lưu PDF và output artifacts) ✅ pipeline/docs/context/Tasks_list.md   (Cập nhật tiến độ task [ ] -> [/] -> [x]),✅ pipeline/docs/runtime/**              (Logs, status, plans của harness) ✅ requirements.txt, pyproject.toml      (Thêm packages cần thiết: playwright, inngest, jinja2),✅ .gitignore                            (Đảm bảo bỏ qua reports/, *.db, __pycache__)
- **Last Synced:** 2026-09-06 23:12:31
