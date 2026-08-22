# PLAN
# Kế hoạch thực thi — TASK-001: Comprehensive Real-Time API Trace & Diagnostic Logging System

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Cập nhật:** 2026-08-22

---

## Task Reference

```
Task ID:    TASK-001
Task Name:  Comprehensive Real-Time API Trace & Diagnostic Logging System
Phase:      Phase 1 (Observability & Logging)
Spec:       Nâng cấp và đồng bộ hệ thống trace logging cho STT, LLM, TTS ra console và file logs/api_trace.log. Cập nhật endpoint /api/trace & /api/health/quota.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [x] Console in ra rõ ràng mỗi khi có request: `[TRACE] Step=... | Provider=... | Key=... | Status=... | Latency=...ms`.
- [x] Khi ElevenLabs hết quota hoặc lỗi, có log ghi rõ nguyên nhân và provider fallback tiếp theo (Edge-TTS).
- [x] File `logs/api_trace.log` được cập nhật liên tục với đầy đủ timestamp và masked keys (`gsk_...`, `xi_...`, `AIza...`).
- [x] Endpoint `/api/trace` và `/api/health/quota` phản ánh đúng trạng thái real-time.
- [x] Unit test `pytest tests/test_logging_trace.py -v` chạy PASS 100%.

### Verification Commands
```bash
pytest tests/test_logging_trace.py -v
python3 pipeline/scripts/verify.py
```

---

## Execution Steps

### [x] Step 1: Nâng cấp `log_api_trace()` và bổ sung logging cho STT/LLM trong `app/ai_engine.py`
- **Mục tiêu:** Thêm tham số `step` vào `log_api_trace()`, định dạng log console chuẩn `[TRACE] Step=... | Provider=... | Key=... | Status=... | Latency=...ms`, và tích hợp log_api_trace vào `transcribe_audio()` (Groq Whisper & Gemini Audio & Browser Fallback).
- **Files tạo/sửa:** `app/ai_engine.py`
- **Exit condition:** `log_api_trace()` ghi log đầy đủ thông tin step, provider, masked key, status, latency và error ra console & file `logs/api_trace.log`.

### [x] Step 2: Tích hợp Real-Time Logging & Auto-Rotation trong `app/tts_service.py`
- **Mục tiêu:** Gọi `log_api_trace()` trong `generate_elevenlabs_tts_single()`, `generate_elevenlabs_tts_multi_key()`, `generate_tts_mp3()`, và `stream_tts_mp3_chunks()` khi xử lý TTS ElevenLabs, Edge-TTS fallback, và gTTS.
- **Files tạo/sửa:** `app/tts_service.py`
- **Exit condition:** ElevenLabs 429/402 quota error và Edge-TTS fallback được ghi nhận minh bạch vào log trace.

### [x] Step 3: Đảm bảo Endpoints `/api/trace` và `/api/health/quota` trong `app/main.py`
- **Mục tiêu:** Kiểm tra endpoints trả về `key_statuses`, `recent_trace_logs` và active key counts chính xác.
- **Files tạo/sửa:** `app/main.py`
- **Exit condition:** GET `/api/trace` và GET `/api/health/quota` trả dữ liệu JSON hợp lệ chứa trạng thái key và log trace mới nhất.

### [x] Step 4: Tạo Unit Test Suite `tests/test_logging_trace.py` & Verification
- **Mục tiêu:** Xây dựng unit test suite kiểm tra toàn bộ tiêu chí của TASK-001 và chạy `python3 pipeline/scripts/verify.py`.
- **Files tạo/sửa:** `tests/test_logging_trace.py`
- **Exit condition:** `pytest tests/test_logging_trace.py -v` và `verify.py` pass 100%.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      3
Context refresh at:   Iteration 3
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-22 | Khởi tạo plan cho TASK-001 |
