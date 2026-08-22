# TECH CONTEXT
# Bối cảnh kỹ thuật — Stack, Logging, Fallback, IELTS STT & Roleplay Hub UI

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.** File này quy định chi tiết kỹ thuật cho hệ thống Tracing Logs, Dynamic Fallback, Empathetic Prompting, IELTS Exam STT Submission Fix và Curated Roleplay Hub.

---

## 1. Tech Stack & Key Components

```
Runtime:          Python 3.11+ (.venv managed with uv / pip)
Web Framework:    FastAPI / Uvicorn (ASGI)
ASR Services:     1. Groq Whisper Large V3 (OpenAI client / requests)
                  2. Gemini Audio Inline ASR
                  3. Browser Web Speech API fallback
LLM Providers:    1. Groq API (llama-3.3-70b-versatile, llama-3.1-8b-instant)
                  2. Google Gemini API (gemini-2.5-flash, gemini-3.0-flash)
                  3. OpenAI API (gpt-4o-mini)
                  4. Ollama (local llama3, if available)
TTS Services:     1. ElevenLabs API (Multi-Key Auto-Rotation Pool)
                  2. Microsoft Edge-TTS (Free Azure Neural Voices)
                  3. gTTS (Google Translate TTS safety fallback)
Local Cache & DB: SQLite (custom_topics.db, saved_words, translation_cache) + In-memory RAM caches
Frontend:         Vanilla JavaScript (ES6+), HTML5 Web Audio API, PWA Service Worker, Responsive CSS Grid/Flexbox
Testing Tools:    pytest, Chrome DevTools MCP (navigate, click, type, screenshot)
```

---

## 2. Tracing & Logging Specification

### Log Output Format:
Console output và file `logs/api_trace.log` ghi theo định dạng chuẩn:
```text
[YYYY-MM-DD HH:MM:SS] [TRACE] Step=<STT|LLM|FALLBACK|TTS|EVAL> | Provider=<Groq|Gemini|ElevenLabs|EdgeTTS> | Model=<model_name> | Key=<masked_key> | Status=<200|429|500> | Latency=<ms> | Details=<Message>
```

### Log Scenarios:
- **LLM Success:** `[TRACE] Step=LLM | Provider=Groq | Model=llama-3.3-70b-versatile | Key=gsk_...7x9A | Status=200 | Latency=412.3ms | Details=Success`
- **LLM 429 Quota Exceeded (Auto-rotate):** `[TRACE] Step=LLM | Provider=Groq | Model=llama-3.3-70b-versatile | Key=gsk_...1a2B | Status=429 | Latency=120.0ms | Details=Quota limit hit, auto-rotating to Key #2`
- **All LLMs Down $\rightarrow$ Fallback:** `[TRACE] Step=FALLBACK | Provider=LocalEngine | Model=DynamicContextFallback | Status=200 | Latency=2.1ms | Details=All LLMs unavailable. Generated dynamic anti-repetition turn.`
- **ElevenLabs 429 $\rightarrow$ Edge-TTS Fallback:** `[TRACE] Step=TTS | Provider=ElevenLabs | Key=xi_...99F | Status=429 | Latency=85.0ms | Details=ElevenLabs pool exhausted, falling back to Microsoft Edge-TTS (en-GB-SoniaNeural)`

---

## 3. IELTS Exam Read-Then-Speak Fix Specification

### Root Cause Analysis:
1. `this.detSpeechAccumulated` bị reset hoặc không được cập nhật do `this.isDetRecording` bị đặt về `false` trong `stopDetMonologueTimer()` trước khi callback bất đồng bộ `onResult` từ `/api/transcribe_audio` hoàn tất.
2. Khi bấm Submit, hàm `submitDetSpeech()` đọc chuỗi rỗng và hiện toast lỗi ngay lập tức mà không đợi pipeline ASR hoàn thành.

### Technical Fix:
1. **Async-Aware Submission:** Trong `submitDetSpeech()`, nếu `detSpeechAccumulated` rỗng nhưng đang có audio ghi âm hoặc pending ASR, hàm sẽ chuyển sang trạng thái chờ `⏳ Transcribing & Evaluating...` và đợi tối đa 2s để nhận transcript.
2. **Immediate Local Text Buffer:** Lưu tạm transcript interim từ Web Speech API vào buffer `detInterimTranscript`. Khi Submit, tự động gộp cả interim text và final text.
3. **Graceful Fallback Evaluation:** Nếu ASR trả về text ngắn hoặc mạng rớt, cho phép user gõ/xem review hoặc tự động tạo đánh giá dựa trên thời lượng nói và các chỉ số âm thanh thực tế.

---

## 4. Curated Roleplay Hub & Topic Explorer Specification

### Giao diện Trang chủ:
1. **Featured Curated Grid (< 11 topics):**
   - Chỉ hiển thị 8-10 topics thịnh hành, hấp dẫn và phổ biến nhất (Coffee Chat, Job Interview, Travel Airport, Restaurant, Casual Hangout, Weekend Plans, Tech Talk, Doctor Visit).
   - Card thiết kế sang trọng, tối giản, có icon 3D/emoji bắt mắt, badge cấp độ (A1-C2) và màu sắc hài hòa.
2. **"Explore All Topics" Action Button & Explorer Drawer/Modal:**
   - Nút nổi bật: `📚 Explore All 30+ Topics` đặt ở cuối section hoặc header.
   - Khi bấm, mở một Topic Explorer Drawer/Modal toàn màn hình hoặc popup chuyên nghiệp:
     - **Thanh tìm kiếm (Live Search Bar):** Tìm kiếm tức thì theo tên topic hoặc từ khóa.
     - **Segmented Filter Tabs:** `All`, `Everyday Life ☕`, `Work & Career 💼`, `Travel & Adventure ✈️`, `Social & Culture 🎭`, `IELTS Prep 🎓`.
     - **Phân vùng gọn gàng (Categorized Sections):** Nhóm các topics theo danh mục rõ ràng, có bộ đếm số lượng topic trong từng mục.

---

## 5. Frontend MCP Real-User Testing Guidelines

```
1. Mở trang web ứng dụng qua MCP Browser (http://localhost:8000).
2. Test kịch bản 1: Màn hình chính -> Kiểm tra số lượng Roleplay topics (<11 thẻ) -> Mở All Topics Explorer -> Test Search & Filter Tabs -> Chọn 1 topic và vào Roleplay.
3. Test kịch bản 2: Vào IELTS Exam -> Chọn Read-Then-Speak -> Bấm Start Record -> Nói/Giả lập âm thanh -> Bấm Submit -> Xác nhận nộp bài thành công và hiển thị bảng điểm DET Report.
4. Test kịch bản 3: Kiểm tra Instant Filler âm thanh -> Kiểm tra log trace trong console và logs/api_trace.log.
5. Giới hạn số lần gọi API kiểm thử < 10 lần.
```
