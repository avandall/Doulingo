# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-07 00:04

---

## 🎯 Task Spec: TASK-004
### 📌 TASK-004: Xây dựng Cron Job Tự động Dọn dẹp Audio Cache

#### Metadata
```
Task ID:         TASK-004
Task Name:       Xây dựng Cron Job Tự động Dọn dẹp Audio Cache
Phase:           Phase 2
Task Type:       feat
Priority:        P1-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Các file audio TTS tạm thời trong quá trình luyện nói tích tụ chiếm dung lượng lưu trữ trên server.
- **What:** Tạo scheduled cron job `cleanup-audio-cache` (chạy hàng ngày hoặc định kỳ qua Inngest `inngest.TriggerCron(cron="0 3 * * *")` hoặc async background scheduler), quét và xóa các file audio tạm thời có thời gian tạo $> 24$ giờ.

#### Acceptance Criteria
- [ ] Cron function quét thư mục audio cache/temp mà không gây crash server nếu thư mục rỗng.
- [ ] Chỉ xóa file audio cũ hơn 24 giờ, giữ lại file mới tạo.
- [ ] Ghi log số lượng file đã xóa và dung lượng đã giải phóng.

#### Scope
- **Files được sửa/tạo:** `app/services/cron_service.py`, `app/services/background_job_service.py`, `tests/test_background_jobs.py`

#### Verification Commands
```bash
pytest tests/test_background_jobs.py -k "test_cron_cleanup"
```

---

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime:          Python 3.10+ (WSL Linux Ubuntu / CPython) Framework:        FastAPI >= 0.115.0,Web Server:       Uvicorn (ASGI) Validation:       Pydantic v2,API Protocol:     RESTful JSON API + Binary File Streams (FileResponse) PDF Engine:       Playwright Headless Chromium + Jinja2 Templates + Print CSS,Background Engine: Inngest Python SDK / FastAPI BackgroundTasks + Async IO
- **Scope Boundaries:** ```,✅ app/**                               (Router, Services, Schemas, Templates) ✅ tests/**                              (Unit & Integration test suites),✅ reports/**, output/**                 (Thư mục lưu PDF và output artifacts) ✅ pipeline/docs/context/Tasks_list.md   (Cập nhật tiến độ task [ ] -> [/] -> [x]),✅ pipeline/docs/runtime/**              (Logs, status, plans của harness) ✅ requirements.txt, pyproject.toml      (Thêm packages cần thiết: playwright, inngest, jinja2),✅ .gitignore                            (Đảm bảo bỏ qua reports/, *.db, __pycache__)
- **Last Synced:** 2026-09-07 00:04:05
