# TASK EXECUTION PLAN
# Task TASK-003: Xây dựng Inngest Async Background Job cho Đánh giá Chuyên sâu

> **Trạng thái:** COMPLETED | **Ngày:** 2026-09-06

---

## 🎯 Task Goal
Tích hợp Inngest Async Background Worker SDK vào ứng dụng FastAPI (`app_id: haku-hakus-api`) để xử lý quá trình đánh giá sâu (AI Deep Scoring, IELTS/DET rubric) dưới dạng background job không gây nghẽn HTTP thread:
1. Endpoint `POST /api/exams/{session_id}/evaluate-async` phản hồi HTTP 202 Accepted trong `<1s` kèm `job_id` và `status_url`.
2. Endpoint `GET /api/jobs/{job_id}/status` hỗ trợ status polling trả về `pending`, `processing`, `done` (kèm kết quả) hoặc `failed`.
3. Inngest function `evaluate-speaking-exam` thực thi từng `step.run` và lưu kết quả vào database/state store với retry backoff (tối đa 2 retries).
4. Endpoint `/api/inngest` được mount trên FastAPI app.

---

## 📋 Atomic Steps

### [x] Step 1: Database Job Storage & Inngest Background Service (`app/storage/db.py`, `app/services/background_job_service.py`)
- Tạo bảng `evaluation_jobs` trong SQLite DB (`data/custom_topics.db` qua `app/storage/db.py`) và bổ sung helper functions (`create_evaluation_job`, `update_evaluation_job_status`, `get_evaluation_job`).
- Khởi tạo Inngest client (`id: haku-hakus-api`) trong `app/services/background_job_service.py`.
- Định nghĩa Inngest function `evaluate-speaking-exam` (trigger `exam/completed`, `retries=2`) thực thi các bước `step.run` (`ai-deep-scoring`, `phonetics-analysis`) và cập nhật tiến trình vào DB.

### [x] Step 2: REST API Router & Inngest Mount (`app/api/routers/jobs_router.py`, `app/main.py`)
- Định nghĩa router `jobs_router` với các endpoints:
  - `POST /api/exams/{session_id}/evaluate-async`: Phản hồi 202 Accepted trong `<1s` kèm `job_id` và `status_url`.
  - `GET /api/jobs/{job_id}/status`: Trả về trạng thái tiến độ job hoặc 404.
- Mount endpoint `/api/inngest` thông qua `inngest.fast_api.serve(app, inngest_client, [evaluate_speaking_exam])` và mount `jobs_router` vào `app/main.py`.

### [x] Step 3: Integration Tests (`tests/test_background_jobs.py`)
- Viết test suite trong `tests/test_background_jobs.py` kiểm định:
  - `POST /api/exams/{session_id}/evaluate-async` trả về 202 Accepted `<1s`.
  - `GET /api/jobs/{job_id}/status` phản hồi đúng chuyển trạng thái từ `pending` sang `done` kèm kết quả.
  - Test helper database & endpoint `/api/inngest`.

### [x] Step 4: Verification (`python3 pipeline/scripts/verify.py`)
- Chạy `pytest tests/test_background_jobs.py` và `python3 pipeline/scripts/verify.py` kiểm định toàn bộ Ruff, Mypy (trên service/router), Bandit, Pytest đạt PASS 100%.
