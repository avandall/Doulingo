# BOUNDARIES
# Giới hạn quyền hạn — Những gì AI được và không được làm

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-09-06
>
> ✏️ **HUMAN FILLS THIS FILE.** AI phải đọc và tuân thủ nghiêm ngặt.
>
> ⚠️ **CRITICAL:** Đây là "hợp đồng" ranh giới giữa bạn và AI. AI sẽ dừng lại và hỏi nếu thao tác vượt quá scope.

---

## 1. Phạm vi File (File Scope)

### AI được phép đọc và sửa:
```
✅ app/**                               (Router, Services, Schemas, Templates)
✅ tests/**                              (Unit & Integration test suites)
✅ reports/**, output/**                 (Thư mục lưu PDF và output artifacts)
✅ pipeline/docs/context/Tasks_list.md   (Cập nhật tiến độ task [ ] -> [/] -> [x])
✅ pipeline/docs/runtime/**              (Logs, status, plans của harness)
✅ requirements.txt, pyproject.toml      (Thêm packages cần thiết: playwright, inngest, jinja2)
✅ .gitignore                            (Đảm bảo bỏ qua reports/, *.db, __pycache__)
```

### AI KHÔNG được chạm vào:
```
❌ .env                                  (File chứa secrets / production API keys)
❌ pipeline/docs/core/**                 (Bộ quy chuẩn cốt lõi cố định của pipeline)
❌ pipeline/engine/**                    (Core engine của harness)
❌ static/index.html (ngoại trừ bổ sung nút download PDF / event listener nếu có task yêu cầu)
```

---

## 2. Database Permissions

```
READ:    ✅ Được phép đọc custom_topics.db, dictionary.db, reports.db
WRITE:   ✅ Được phép ghi test data, records báo cáo exam_reports và background_jobs
MIGRATE: ✅ Được phép tạo mới bảng trong reports.db hoặc custom_topics.db (CREATE TABLE IF NOT EXISTS)
DROP:    ❌ KHÔNG BAO GIỜ được phép DROP DB hoặc DROP các bảng từ điển chính

Môi trường:
  - Local DB:    ✅ Quyền đọc/ghi/tạo bảng trên DB local (data/*.db)
  - Production:  ❌ Không có access trực tiếp
```

---

## 3. External Services & APIs

```
Được phép gọi:
✅ Inngest Local Dev Server (http://localhost:8288)
✅ Playwright Local Headless Browser (Chromium)
✅ Local FastAPI Endpoints (http://localhost:8000)

KHÔNG được phép gọi:
❌ Production Inngest Cloud keys
❌ Bất kỳ dịch vụ nào tốn phí thực tế không có mock/test mode
```

---

## 4. Quyền Kiến trúc (Architecture Decisions)

### AI có thể tự quyết định:
```
✅ Cấu trúc file bên trong app/services/ (pdf_report_service.py, background_job_service.py)
✅ Thiết kế HTML/CSS template cho bản in PDF (đáp ứng đúng chuẩn A4, @page margin, break-inside: avoid)
✅ Schema Pydantic cho DTOs request/response của report và job status
✅ Thuật toán kiểm tra Idempotency (theo session_id và ngày hiện tại)
✅ Cấu hình retry & exponential backoff trong worker functions
```

### Phải hỏi human trước:
```
❓ Thay đổi cấu trúc core audio streaming / STT / TTS đang hoạt động ổn định
❓ Xóa bỏ các routes hiện có trong app/main.py
```

### KHÔNG được làm dù có lý do:
```
❌ Hardcode credentials, API keys vào source code
❌ Trả trực tiếp binary PDF dạng base64 trong JSON response (vi phạm Store & Link)
❌ Tắt validation hoặc bỏ qua kiểm tra lỗi
❌ Run unbounded blocking subprocesses/browser instances without timeout limits
```

---

## 5. Rollback & Git Permissions

```
AI được phép:
✅ Commit theo đúng quy chuẩn: [TASK-ID] <type>(<scope>): <mô tả ngắn> — CHỈ khi task [x] DONE
✅ Luôn chạy git thông qua WSL theo quy tắc toàn cục

KHÔNG bao giờ:
❌ git push --force
❌ Chạy git.exe của Windows trên ổ Z:\
```

