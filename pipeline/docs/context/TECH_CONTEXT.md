# TECH CONTEXT
# Bối cảnh kỹ thuật — Stack, Môi trường và Kiến trúc Kỹ thuật

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-09-06
>
> ✏️ **HUMAN FILLS THIS FILE.** File này quy định chi tiết kỹ thuật, công nghệ, cấu trúc code và API contracts.

---

## 1. Tech Stack & Environment

### Language & Framework
```
Runtime:          Python 3.10+ (WSL Linux Ubuntu / CPython)
Framework:        FastAPI >= 0.115.0
Web Server:       Uvicorn (ASGI)
Validation:       Pydantic v2
API Protocol:     RESTful JSON API + Binary File Streams (FileResponse)
PDF Engine:       Playwright Headless Chromium + Jinja2 Templates + Print CSS
Background Engine: Inngest Python SDK / FastAPI BackgroundTasks + Async IO
Cron Engine:      Inngest TriggerCron / Async Schedule
```

### Database & Storage
```
Primary DB:       SQLite / LibSQL (custom_topics.db, dictionary.db, reports.db)
Data Isolation:   Session-based & User-based isolation (session_id, user_id)
Artifact Storage: Disk-backed storage at `reports/` and `output/` (Store & Link)
```

### Testing Framework
```
Test Runner:      Pytest + Pytest-Asyncio
Static Analysis:  Ruff, Mypy
Pipeline Check:   python3 pipeline/scripts/verify.py
```

---

## 2. Cấu trúc Thư mục Dự án (Directory Structure)

```
Doulingo/
├── app/
│   ├── main.py                           # Application entry point & router mounting
│   ├── api/
│   │   └── routers/
│   │       ├── reports_router.py         # [NEW] /api/reports (Generate, Status, Download File)
│   │       ├── chat_router.py            # Chat & realtime roleplay endpoints
│   │       ├── feedback_router.py        # Speaking evaluation & feedback endpoints
│   │       └── ...
│   ├── services/
│   │   ├── pdf_report_service.py         # [NEW] Playwright PDF Renderer & Page-break styling
│   │   ├── background_job_service.py     # [NEW] Inngest client, events & durable job execution
│   │   ├── cron_service.py               # [NEW] Scheduled audio cache cleanup
│   │   └── ...
│   ├── templates/
│   │   └── reports/
│   │       └── speaking_report.html      # [NEW] Jinja2 HTML/CSS Template for IELTS/DET scorecards
│   └── data/                             # SQLite DB files
├── reports/                              # Generated PDF files (.gitignore)
├── pipeline/
│   └── docs/context/                     # Context docs for agent harness
└── tests/
    ├── test_pdf_reporting.py             # Unit/Integration tests for PDF generation
    └── test_background_jobs.py           # Tests for background events & status endpoints
```

---

## 3. Database Schema & Data Models

```sql
-- Bảng lưu trữ metadata báo cáo PDF (reports.db)
CREATE TABLE IF NOT EXISTS exam_reports (
    id TEXT PRIMARY KEY,                  -- UUID or hash (e.g. rep_xxx)
    session_id TEXT NOT NULL,             -- Mã bài thi IELTS/DET
    topic_title TEXT NOT NULL,            -- Chủ đề bài thi
    overall_score REAL NOT NULL,          -- Điểm tổng kết (e.g. 7.5 IELTS / 120 DET)
    cefr_level TEXT NOT NULL,             -- B1, B2, C1, C2
    pdf_path TEXT NOT NULL,               -- Đường dẫn file PDF trên đĩa (reports/{id}.pdf)
    file_size_bytes INTEGER NOT NULL,     -- Dung lượng file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_date TEXT NOT NULL            -- YYYY-MM-DD (dùng cho Idempotency check)
);

-- Bảng theo dõi trạng thái Background Jobs
CREATE TABLE IF NOT EXISTS background_jobs (
    id TEXT PRIMARY KEY,                  -- job_xxx
    job_type TEXT NOT NULL,               -- 'deep_evaluation', 'pdf_generation', 'cleanup'
    status TEXT NOT NULL,                 -- 'pending', 'processing', 'done', 'failed'
    progress_pct INTEGER DEFAULT 0,
    result_json TEXT,                     -- Kết quả JSON khi hoàn tất
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. API Contracts & Specifications

### 1. Endpoint: `POST /api/reports/speaking/{session_id}/generate`
- **Mục tiêu:** Sinh báo cáo PDF từ kết quả bài thi Speaking (có kiểm tra Idempotency).
- **Request Body:**
  ```json
  {
    "force": false
  }
  ```
- **Response 201 Created (Tạo mới) / 200 OK (Đã tồn tại trong ngày):**
  ```json
  {
    "id": "rep_a1b2c3d4",
    "session_id": "sess_987654",
    "status": "ready",
    "download_url": "/api/reports/speaking/rep_a1b2c3d4/file",
    "created_at": "2026-09-06T20:00:00Z"
  }
  ```

### 2. Endpoint: `GET /api/reports/speaking/{report_id}/file`
- **Mục tiêu:** Tải file nhị phân PDF về máy (Header `Content-Type: application/pdf`).

### 3. Endpoint: `POST /api/exams/{session_id}/evaluate-async`
- **Mục tiêu:** Nhận yêu cầu chấm điểm chuyên sâu, phản hồi 202 Accepted ngay lập tức.
- **Response 202 Accepted:**
  ```json
  {
    "job_id": "job_eval_12345",
    "status": "pending",
    "status_url": "/api/jobs/job_eval_12345/status"
  }
  ```

### 4. Endpoint: `GET /api/jobs/{job_id}/status`
- **Mục tiêu:** Status polling trả về `pending`, `processing`, hoặc `done` + kết quả.

---

## 5. Environment & Dependencies

```bash
# Cài đặt Playwright Chromium
playwright install chromium

# Chạy server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Chạy deterministic test
python3 pipeline/scripts/verify.py
```

---

## 6. Execution Timeouts & Subprocess Guidelines

- **Playwright Headless Engine:** Playwright Chromium MUST run in headless mode (`headless=True`) with explicit navigation/rendering timeouts (e.g. `timeout=30000` ms) to prevent browser lockups.
- **Subprocess & Test Timeout Bounds:** All verification commands executed via `verify.py` enforce a default 60-second timeout per tool.
- **CLI Print Timeout Prevention:** To avoid CLI print timeouts (`Error: timeout waiting for response`), AI agents must avoid running unbounded, blocking tasks without timeouts. For rapid iterative turns, use `python3 pipeline/scripts/verify.py --quick` or `--test-target tests/test_xxx.py`.
- **Workspace Path Integrity & Dynamic Root Anchoring:** All absolute file URLs and markdown links generated in runtime logs and reports must anchor dynamically to the active workspace project directory (`/home/avandall/project/Doulingo/`), strictly prohibiting hardcoded obsolete template strings (e.g. `boilerplate`).
- **Log Analysis False-Positive Filtering:** Log analyzers (`ralph-analyze.mjs`) filter out status enum descriptions (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`) to avoid mistaking status listings for runtime error occurrences.


