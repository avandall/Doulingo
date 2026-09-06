# PROJECT BRIEF
# Tóm tắt dự án — Haku Haku's IELTS & DET AI Speaking Platform

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-09-06
>
> ✏️ **HUMAN FILLS THIS FILE.** File này định nghĩa bức tranh tổng thể, mục tiêu và phạm vi dự án thực tế.

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:          Haku Haku's - Unlimited AI Roleplays
Mô tả ngắn:        Nền tảng luyện thi và đánh giá kỹ năng Speaking (IELTS & Duolingo English Test - DET) tương tác AI thời gian thực với xuất báo cáo chứng nhận PDF và xử lý tác vụ nền bất đồng bộ.
Repo Name:         Doulingo
Track / Domain:    AI Speaking Assistant / Backend API / Fullstack EdTech
Độ khó:             Medium-Hard
Thời gian ước tính: 15-20 giờ
Tech Stack:        Python 3.10+, FastAPI, Playwright (Chromium), Inngest / Async Worker, SQLite/LibSQL, Google GenAI, Edge-TTS
```

---

## 2. Mục tiêu Kinh doanh & Vấn đề Cốt lõi

### Vấn đề cần giải quyết
1. **Trải nghiệm chờ đợi khi chấm điểm sâu (Latency Bottleneck):** Các tác vụ AI phân tích phát âm, ngữ pháp, từ vựng và rubric CEFR chi tiết sau bài thi nói mất từ 10-25 giây. Nếu xử lý đồng bộ trong HTTP request thông thường sẽ gây timeout, khóa giao diện hoặc khiến người dùng bối rối tưởng app bị treo.
2. **Thiếu tài liệu báo cáo kết quả chuyên nghiệp (Tangible Proof):** Học viên sau khi thi thử IELTS/DET cần một bảng điểm chi tiết (Speaking Report Card / Certificate) đẹp mắt ở định dạng PDF để lưu trữ, chia sẻ hoặc theo dõi tiến trình học tập.
3. **Quản lý rác dữ liệu & tài nguyên (Resource Waste):** Các file âm thanh tạm thời (TTS audio chunks) sinh ra trong các buổi luyện nói tích tụ chiếm dung lượng đĩa nếu không có cron dọn dẹp định kỳ.

### Giải pháp & Mục tiêu Thực tế (Áp dụng W6 & W7)
1. **Module PDF Report Generator (Áp dụng W7):** Xây dựng pipeline tự động trích xuất dữ liệu bài thi $\rightarrow$ tổng hợp số liệu (Fluency, Lexical, Grammar, Pronunciation, Band Score) $\rightarrow$ render qua HTML template với Print CSS chống cắt dòng $\rightarrow$ xuất PDF chất lượng cao bằng Headless Chromium (Playwright) $\rightarrow$ lưu trữ theo nguyên tắc "Store & Link" và chống sinh trùng lặp (Idempotency).
2. **Module Async Background Worker & Cron Jobs (Áp dụng W6):** Tách tác vụ đánh giá chuyên sâu sang Background Worker với cơ chế **Accept fast (202 Accepted) $\rightarrow$ Background Execution $\rightarrow$ Status Polling / Eventual Consistency** kèm cơ chế tự động thử lại (Exponential Backoff Retries) và Cron Jobs dọn dẹp cache audio định kỳ.

---

## 3. Ground Rules & Constraints (Quy tắc & Giới hạn)

| Quy tắc | Chi tiết bắt buộc |
|---------|-------------------|
| **1. Dedicated Storage** | Mọi file PDF sinh ra lưu tại thư mục `reports/` hoặc `output/` (được gitignore), DB lưu tại `data/`. |
| **2. Store & Link** | API không bao giờ trả bytes PDF trong JSON; chỉ trả URL link tải (`/api/reports/.../file`) phục vụ qua `FileResponse`. |
| **3. Idempotent Generation** | Gọi tạo báo cáo nhiều lần cho cùng một session chỉ sinh đúng 1 file PDF và trả về bản ghi có sẵn (mã 200 OK), trừ khi có cờ `force: true` (mã 201 Created). |
| **4. Fast Door Response** | Tác vụ nặng (AI Deep Evaluation) phải phản hồi 202 Accepted trong $< 1$ giây, đẩy việc vào background queue. |
| **5. Secrets & Safety** | Không commit file `.env`, credentials, secrets vào Git. |

---

## 4. Phạm vi Dự án (Project Scope) & Modules Thực tế

### Core Features / Modules
- **Module 1: Speaking Exam PDF Report Card Generator (W7)**
  - Thu thập số liệu chấm điểm IELTS / DET (Sub-scores, CEFR Level, WPM, Duration, Vocabulary tier, Turn transcript).
  - Jinja2/HTML template chuyên nghiệp với Print CSS (`tr { break-inside: avoid; }`, `@page { size: A4; margin: 15mm; }`, `thead` lặp lại).
  - Playwright Headless Chromium PDF renderer.
  - Endpoint `POST /api/reports/speaking/{session_id}/generate` & `GET /api/reports/speaking/{session_id}/file`.
- **Module 2: Async Background Job & Evaluation Engine (W6)**
  - Tích hợp Inngest / Async Worker cho sự kiện `exam/completed`.
  - Endpoint `POST /api/exams/{session_id}/evaluate` $\rightarrow$ 202 Accepted $\rightarrow$ Background evaluation $\rightarrow$ Status Polling `GET /api/jobs/{job_id}/status`.
  - Cấu hình retry 2 lần với backoff khi dịch vụ AI gặp sự cố tạm thời.
- **Module 3: Automated Audio Cache Cleanup Cron Job (W6)**
  - Cron Job định kỳ dọn dẹp các file audio TTS tạm thời đã quá hạn ($>24\text{h}$) để tối ưu dung lượng bộ nhớ.

---

## 5. Kiến trúc Hệ thống (Architecture Overview)

```
[ Web Client / IELTS Learner ]
               │
       ┌───────┴────────────────────────────────┐
       ▼ (Instant 202 Accepted)                 ▼ (Direct PDF Download)
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  FastAPI Async Entry Point   │        │ GET /reports/:id/file        │
└──────────────┬───────────────┘        └──────────────┬───────────────┘
               │                                       │
       (Dispatches Event)                              │ (Serves binary file)
               ▼                                       ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  Inngest / Async Worker      │        │      Disk Storage            │
│  - Deep CEFR Evaluation      │───────▶│      (reports/*.pdf)         │
│  - Playwright PDF Renderer   │        └──────────────────────────────┘
│  - Scheduled Cleanup Cron    │                       ▲
└──────────────┬───────────────┘                       │
               │                                       │
               ▼ (Saves Metadata & Paths)              │
┌──────────────────────────────────────────────────────┴───────┐
│              SQLite / LibSQL Database Layer                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Definition of Done Checklist (Tiêu chí Hoàn thành)

- [ ] PDF Report Card xuất ra đúng chuẩn A4, hiển thị đầy đủ điểm số IELTS/DET, biểu đồ phân tích và bảng turn transcript.
- [ ] Bảng điểm nhiều trang không bị cắt đôi dòng text (nhờ Print CSS `break-inside: avoid`).
- [ ] Chống bấm đúp (Idempotency) hoạt động chính xác: 2 lần gọi tạo PDF cùng session trả về cùng ID và chỉ sinh 1 file trên đĩa.
- [ ] Endpoint chấm điểm sâu phản hồi 202 Accepted trong $<1\text{s}$ và chuyển việc cho background worker.
- [ ] Cron job dọn dẹp audio cache chạy tự động và an toàn.
- [ ] Automated tests pass 100% (`python3 pipeline/scripts/verify.py`).
