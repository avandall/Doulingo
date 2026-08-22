# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.** Task đang sẵn sàng được giao cho vòng lặp `harness.sh`.

---

## Task đang thực hiện

```
Task ID:      TASK-001
Task Name:    Comprehensive Real-Time API Trace & Diagnostic Logging System
Phase:        Phase 1 (Observability & Logging)
Priority:     P0-Critical
Started:      2026-08-22
```

---

## Mục tiêu (Why & What)

**Tại sao cần làm task này?**
- Hệ thống cần có khả năng in log chi tiết và minh bạch ra console và file `logs/api_trace.log` để người dùng và developer biết rõ:
  - Khi nào gọi API thành công, gọi của provider nào (Groq, Gemini, OpenAI, ElevenLabs).
  - Khi nào bị hết quota (429), lỗi kết nối, hoặc tự động xoay vòng key.
  - Khi nào phải dùng fallback engine và lý do fallback.

**Cụ thể cần làm gì?**
- Tích hợp subsystem logging chuẩn hóa trong `app/ai_engine.py` và `app/tts_service.py`.
- In masked API key (`gsk_...9aB`) bảo mật, ghi nhận thời gian latency (ms) và status code.
- Cập nhật endpoint `/api/trace` và `/api/health/quota` phản ánh đúng trạng thái real-time.

---

## Acceptance Criteria (Tiêu chí hoàn thành)

Task được coi là DONE khi:
- [ ] Console in ra rõ ràng mỗi khi có request: `[TRACE] Step=... | Provider=... | Key=... | Status=... | Latency=...ms`.
- [ ] Khi ElevenLabs hết quota hoặc lỗi, có log ghi rõ nguyên nhân và provider fallback tiếp theo (Edge-TTS).
- [ ] File `logs/api_trace.log` được cập nhật liên tục với đầy đủ timestamp và masked keys.
- [ ] Unit test `pytest tests/test_logging_trace.py -v` chạy PASS 100%.

---

## Verification Commands

```bash
pytest tests/test_logging_trace.py -v
```
