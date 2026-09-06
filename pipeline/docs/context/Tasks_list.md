# TASKS LIST
# Danh sách tác vụ & Queue thực thi — Haku Haku's Speaking Platform

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-09-06
>
> ✏️ **HUMAN FILLS THIS FILE.** Bạn có thể thêm 1 hoặc nhiều tasks vào danh sách này.
> 🤖 **AI EXECUTION RULE:** AI sẽ đọc danh sách này từ trên xuống dưới, tìm task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS` để thực thi. Khi hoàn thành task, AI đánh dấu `[x] DONE` và chuyển sang task tiếp theo.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Ghi chú / Blocker |
|---|---|---|---|---|---|
| `TASK-001` | Cài đặt Jinja2 Template & Playwright PDF Reporting Engine | Phase 1 | P0 | `[x] DONE` | HTML/CSS A4 + Page-break defense |
| `TASK-002` | Xây dựng Endpoint Xuất Báo Cáo PDF & Idempotent Caching | Phase 1 | P0 | `[x] DONE` | Store & Link (`/api/reports/.../file`) |
| `TASK-003` | Xây dựng Inngest Async Background Job cho Đánh giá Chuyên sâu | Phase 2 | P0 | `[x] DONE` | 202 Accepted + Retries + Polling |
| `TASK-004` | Xây dựng Cron Job Tự động Dọn dẹp Audio Cache | Phase 2 | P1 | `[ ] TODO` | Xóa audio chunks cũ > 24h |
| `TASK-005` | Test Suite Tích hợp & Deterministic Verification | Phase 3 | P0 | `[ ] TODO` | Pytest + verify.py pass 100% |

> **Trạng thái hợp lệ:**
> - `[ ] TODO`: Chưa làm, chờ AI chọn
> - `[/] IN_PROGRESS`: AI đang thực hiện
> - `[x] DONE`: Hoàn thành, đã verify & proof
> - `[!] BLOCKED`: Bị kẹt, cần human intervention

---

## 2. Chi tiết các Tasks (Task Specs)

---

### 📌 TASK-001: Cài đặt Jinja2 Template & Playwright PDF Reporting Engine

#### Metadata
```
Task ID:         TASK-001
Task Name:       Cài đặt Jinja2 Template & Playwright PDF Reporting Engine
Phase:           Phase 1
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Học viên sau bài thi IELTS/DET cần bảng điểm Speaking Report Card chi tiết, định dạng PDF chuẩn in ấn A4.
- **What:** Tạo `app/templates/reports/speaking_report.html` và `app/services/pdf_report_service.py` sử dụng Playwright Headless Chromium để render HTML sang PDF. Đảm bảo Print CSS có `@page { size: A4; margin: 12mm; }`, `tr { break-inside: avoid; }`, và `<thead>` tự động lặp lại trên mọi trang.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Thư viện `playwright` và `jinja2` sẵn sàng trong project.
- [x] Template HTML chứa: Header bài thi, Thẻ điểm CEFR / Overall Band, Bảng điểm thành phần (Fluency, Pronunciation, Grammar, Lexical), Bảng chi tiết toàn bộ lượt đối thoại (turn-by-turn).
- [x] Hàm `generate_speaking_pdf(report_data: dict, output_path: str)` xuất file PDF $\ge 2$ trang đẹp mắt, không cắt ngang dòng chữ.
- [x] Script test đơn lẻ xuất thử file `reports/sample_report.pdf` thành công.


#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/templates/reports/**`, `app/services/pdf_report_service.py`, `requirements.txt`, `reports/**`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 -c "import playwright; import jinja2; print('Dependencies OK')"
pytest tests/test_pdf_reporting.py -k "test_render_pdf"
```

---

### 📌 TASK-002: Xây dựng Endpoint Xuất Báo Cáo PDF & Idempotent Caching

#### Metadata
```
Task ID:         TASK-002
Task Name:       Xây dựng Endpoint Xuất Báo Cáo PDF & Idempotent Caching
Phase:           Phase 1
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-09-06
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Cung cấp API cho Frontend gọi tạo và tải PDF, đồng thời tuân thủ nguyên tắc "Store & Link" và chống tạo file trùng lặp khi người dùng bấm nút nhiều lần (Idempotency).
- **What:** Tạo bảng `exam_reports` trong SQLite DB (`data/custom_topics.db` hoặc `data/reports.db`), tạo router `app/api/routers/reports_router.py` với các endpoints:
  - `POST /api/reports/speaking/{session_id}/generate` (hỗ trợ body `{"force": false}`)
  - `GET /api/reports/speaking/{report_id}/file` (trả về `FileResponse` application/pdf)
  - `GET /api/reports/speaking/{report_id}` (trả về metadata và URL tải)

#### Acceptance Criteria
- [x] `POST /api/reports/speaking/{session_id}/generate` lần đầu trả về 201 Created kèm download link.
- [x] Gọi lại lần 2 trong cùng ngày với cùng session_id trả về 200 OK với report_id cũ, không sinh thêm file PDF mới.
- [x] Gọi kèm `{"force": true}` bỏ qua cache và sinh report mới (201 Created).
- [x] `GET /api/reports/speaking/{report_id}/file` tải về đúng file PDF nhị phân. ID lạ trả về 404.

#### Scope
- **Files được sửa/tạo:** `app/api/routers/reports_router.py`, `app/main.py`, `app/services/pdf_report_service.py`, `tests/test_pdf_reporting.py`

#### Verification Commands
```bash
pytest tests/test_pdf_reporting.py
```

---

### 📌 TASK-003: Xây dựng Inngest Async Background Job cho Đánh giá Chuyên sâu

#### Metadata
```
Task ID:         TASK-003
Task Name:       Xây dựng Inngest Async Background Job cho Đánh giá Chuyên sâu
Phase:           Phase 2
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [x] DONE
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
- [x] `POST /api/exams/{session_id}/evaluate-async` trả về 202 Accepted trong $<1\text{s}$.
- [x] Inngest function thực thi từng step (step.run) và lưu kết quả vào database/state store.
- [x] Status polling endpoint `GET /api/jobs/{job_id}/status` phản hồi đúng tiến độ chuyển trạng thái từ `pending` sang `done`.
- [x] Lỗi tạm thời của AI service được tự động retry (tối đa 2 retries với exponential backoff).

#### Scope
- **Files được sửa/tạo:** `app/services/background_job_service.py`, `app/api/routers/reports_router.py` (hoặc `app/api/routers/jobs_router.py`), `app/main.py`, `requirements.txt`

#### Verification Commands
```bash
pytest tests/test_background_jobs.py -k "test_async_evaluation"
```

---

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

