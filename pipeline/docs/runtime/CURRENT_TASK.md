# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-07 00:10

---

## 🎯 Task Spec: TASK-005
### 📌 TASK-005: Test Suite Tích hợp & Deterministic Verification

#### Metadata
```
Task ID:         TASK-005
Task Name:       Test Suite Tích hợp & Deterministic Verification
Phase:           Phase 3
Task Type:       test
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Đảm bảo toàn bộ hệ thống (PDF Reporting, Idempotency, Async Background Jobs, Cron Cleanup) hoạt động ổn định và vượt qua bộ kiểm tra chất lượng tự động của Harness (`verify.py`).
- **What:** Viết đầy đủ unit & integration tests trong `tests/test_pdf_reporting.py` và `tests/test_background_jobs.py`, cấu hình `.gitignore` chuẩn và chạy `verify.py` kiểm tra tĩnh + runtime.

#### Acceptance Criteria
- [ ] `tests/test_pdf_reporting.py` pass 100%.
- [ ] `tests/test_background_jobs.py` pass 100%.
- [ ] `python3 pipeline/scripts/verify.py` pass 100% (Tier 1 deterministic check).
- [ ] Git status sạch sẽ, `reports/*.pdf` và file database tạm thời không bị lọt vào Git.

#### Scope
- **Files được sửa/tạo:** `tests/**`, `.gitignore`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py
```

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime:          Python 3.10+ (WSL Linux Ubuntu / CPython) Framework:        FastAPI >= 0.115.0,Web Server:       Uvicorn (ASGI) Validation:       Pydantic v2,API Protocol:     RESTful JSON API + Binary File Streams (FileResponse) PDF Engine:       Playwright Headless Chromium + Jinja2 Templates + Print CSS,Background Engine: Inngest Python SDK / FastAPI BackgroundTasks + Async IO
- **Scope Boundaries:** ```,✅ app/**                               (Router, Services, Schemas, Templates) ✅ tests/**                              (Unit & Integration test suites),✅ reports/**, output/**                 (Thư mục lưu PDF và output artifacts) ✅ pipeline/docs/context/Tasks_list.md   (Cập nhật tiến độ task [ ] -> [/] -> [x]),✅ pipeline/docs/runtime/**              (Logs, status, plans của harness) ✅ requirements.txt, pyproject.toml      (Thêm packages cần thiết: playwright, inngest, jinja2),✅ .gitignore                            (Đảm bảo bỏ qua reports/, *.db, __pycache__)
- **Last Synced:** 2026-09-07 00:10:13
