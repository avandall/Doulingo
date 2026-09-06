# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-06 23:20

---

## 🎯 Task Spec: TASK-003
### 📌 TASK-003: Xây dựng Inngest Async Background Job cho Đánh giá Chuyên sâu

#### Metadata
```
Task ID:         TASK-003
Task Name:       Xây dựng Inngest Async Background Job cho Đánh giá Chuyên sâu
Phase:           Phase 2
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Quá trình đánh giá sâu (AI Deep Scoring, ngữ âm, IELTS/DET rubric) mất nhiều thời gian ($>10\text{s}$). Cần chuyển sang Background Worker để API phản hồi ngay lập tức (202 Accepted).
- **What:** Tích hợp `inngest` Python SDK vào FastAPI app:
  - Tạo `app/services/background_job_service.py` với Inngest client (`id: haku-hakus-api`) và function `evaluate-speaking-exam` (trigger `exam/completed`, có retry backoff).
  - Mount endpoint `/api/inngest` trên FastAPI app.
  - Endpoint `POST /api/exams/{session_id}/evaluate-async`: phản hồi 202 Accepted trong $<1\text{s}$ kèm `job_id` và `status_url`.
  - Endpoint `GET /api/jobs/{job_id}/status`: trả về `pending`, `processing`, `done` (kèm kết quả) hoặc `failed`.

#### Acceptance Criteria
- [ ] `POST /api/exams/{session_id}/evaluate-async` trả về 202 Accepted trong $<1\text{s}$.
- [ ] Inngest function thực thi từng step (step.run) và lưu kết quả vào database/state store.
- [ ] Status polling endpoint `GET /api/jobs/{job_id}/status` phản hồi đúng tiến độ chuyển trạng thái từ `pending` sang `done`.
- [ ] Lỗi tạm thời của AI service được tự động retry (tối đa 2 retries với exponential backoff).

#### Scope
- **Files được sửa/tạo:** `app/services/background_job_service.py`, `app/api/routers/reports_router.py` (hoặc `app/api/routers/jobs_router.py`), `app/main.py`, `requirements.txt`

#### Verification Commands
```bash
pytest tests/test_background_jobs.py -k "test_async_evaluation"
```

---

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime:          Python 3.10+ (WSL Linux Ubuntu / CPython) Framework:        FastAPI >= 0.115.0,Web Server:       Uvicorn (ASGI) Validation:       Pydantic v2,API Protocol:     RESTful JSON API + Binary File Streams (FileResponse) PDF Engine:       Playwright Headless Chromium + Jinja2 Templates + Print CSS,Background Engine: Inngest Python SDK / FastAPI BackgroundTasks + Async IO
- **Scope Boundaries:** ```,✅ app/**                               (Router, Services, Schemas, Templates) ✅ tests/**                              (Unit & Integration test suites),✅ reports/**, output/**                 (Thư mục lưu PDF và output artifacts) ✅ pipeline/docs/context/Tasks_list.md   (Cập nhật tiến độ task [ ] -> [/] -> [x]),✅ pipeline/docs/runtime/**              (Logs, status, plans của harness) ✅ requirements.txt, pyproject.toml      (Thêm packages cần thiết: playwright, inngest, jinja2),✅ .gitignore                            (Đảm bảo bỏ qua reports/, *.db, __pycache__)
- **Last Synced:** 2026-09-06 23:20:07
