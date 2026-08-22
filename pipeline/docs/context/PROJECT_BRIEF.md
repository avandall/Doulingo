# PROJECT BRIEF
# Tóm tắt dự án — Duolingo Speak (Unlimited AI Roleplays & Empathy Speaking Engine)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.** File này định nghĩa bức tranh tổng thể, mục tiêu, kiến trúc và phạm vi nâng cấp hệ thống AI Generative Speaking & Frontend UX.

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:          Duolingo Speak - Empathy Conversational AI Engine & Pro Frontend UX
Mô tả ngắn:        Hệ thống luyện nói tiếng Anh tương tác thời gian thực với AI nhân vật ảo đa tính cách, thấu cảm, nhận diện phát âm ASR, thi thử IELTS Speaking (Read-Then-Speak), giao diện Roleplay Hub tinh gọn (<11 topics tiêu biểu) và tích hợp đa tầng LLM/TTS.
Repo Name:         Doulingo
Track / Domain:    AI Voice Assistant / EdTech / Conversational Agent / Fullstack Web PWA
Độ khó:             Hard
Tech Stack:        Python 3.11+, FastAPI, Uvicorn, Groq (Whisper + Llama 3.3), Google Gemini, ElevenLabs TTS, Edge-TTS, SQLite, HTML5 Audio, Vanilla JS/PWA
```

---

## 2. Mục tiêu Kinh doanh & Trải nghiệm Người dùng (Core Goals)

### Vấn đề cần giải quyết
1. **Lặp lại câu vô nghĩa khi lỗi mạng / thiếu key:** Khi LLM hết quota hoặc thiếu key, hệ thống rơi vào vòng lặp fallback tĩnh phát đúng 1 câu cố định, phớt lờ hoàn toàn lời nói của người dùng.
2. **AI thiếu thấu cảm & không hiểu ý người học:** Khi STT nhận diện sai âm tương tự (homophones) hoặc người học nói ngắt quãng, AI phản hồi lạc đề hoặc cụt hứng.
3. **Độ trễ phản hồi (Latency):** Người học phải chờ đợi trong im lặng vài giây khi backend gọi LLM/TTS mà không có phản hồi tự nhiên (filler cues).
4. **Giọng đọc méo tiếng khi fallback:** Khi ElevenLabs hết quota, Edge-TTS bị chỉnh pitch/rate âm trầm nhân tạo khiến giọng nghe kỳ quặc, cứng đơ.
5. **Thiếu khả năng giám sát (Observability/Logging):** Developer và user không biết được hệ thống đang gọi AI nào, API nào thành công, key nào hết quota.
6. **Lỗi nộp bài IELTS Exam (Read-Then-Speak):** Bấm Start Record nói xong bấm Submit thì bị chặn với thông báo "Please record before submitting" do race condition bất đồng bộ giữa STT ingestion và hàm submit.
7. **Giao diện Roleplay Topics bị tràn lan:** Hiển thị ồ ạt hàng chục chủ đề làm rối mắt. Cần giữ tối ưu <11 chủ đề tiêu biểu ở màn hình chính, kèm nút "Explore All Topics" mở drawer/modal chuyên nghiệp có tìm kiếm, bộ lọc danh mục và phân vùng rõ ràng.

### Giải pháp & Mục tiêu Hệ thống
1. **Real-Time API Tracing & Observability:** In log console và ghi file `logs/api_trace.log` chi tiết trạng thái từng key, latency, provider thành công, quota exhaustion.
2. **Instant Conversational Fillers (<100ms):** Tự động phát âm thanh đệm câu giờ tự nhiên (*"Hmm...", "Well, let me think...", "Uhm, okay..."*) ngay khi user vừa dứt lời.
3. **Dynamic Anti-Repetition Fallback Engine:** Ngân hàng 30+ câu mở & câu hỏi ngữ cảnh đa dạng, đọc `conversation_history` để không bao giờ lặp lại câu cũ, nhận diện đổi chủ đề (Topic Shift).
4. **Empathetic Prompting & ASR Correction:** Active Listening, phản chiếu cảm xúc (Sentiment Mirroring), tự động nhận diện từ phát âm sai theo ngữ cảnh (*"Did you mean X?"*).
5. **Natural Voice Fallback Tuning:** Tinh chỉnh Edge-TTS về tần số chuẩn (0Hz, 0%) để giữ chất giọng ấm áp, tự nhiên khi ElevenLabs hết lượt.
6. **Fix Triệt để IELTS Exam Submission Flow:** Xử lý bất đồng bộ ASR transcript, hỗ trợ buffer audio trực tiếp và fallback text ngay lập tức khi người học bấm Submit.
7. **Curated Roleplay Hub & Professional Topic Explorer:** Giữ 8-10 topics thịnh hành/tối ưu nhất trên trang chủ; tạo All Topics Explorer modal với thanh Search, Filter tabs (Everyday, Travel, Work, Exam, Social) và phân cấp danh mục gọn gàng.
8. **Frontend Testing via MCP:** Kiểm thử thực tế như real user cho từng tính năng, gọi API kiểm thử < 10 lần, không spam.

---

## 3. Ground Rules & Constraints

| Quy tắc | Chi tiết bắt buộc |
|---------|-------------------|
| **1. Môi trường & Bảo mật** | Mọi API Key nằm trong `.env`, không bao giờ hardcode secrets vào source code. Log chỉ in masked key (ví dụ: `gsk_...9aB`). |
| **2. Fallback Thông minh** | Tuyệt đối không bao giờ để hệ thống lặp lại 1 câu phản hồi cứng nhắc qua các lượt hội thoại. |
| **3. Tốc độ Phản hồi** | Instant filler phát trong < 100ms; tổng thời gian xử lý LLM + TTS cố gắng dưới 1.5s. |
| **4. Frontend Testing Quality** | Sử dụng MCP kiểm thử UI thực tế từng tính năng, giới hạn số lần gọi API < 10 lần. |
| **5. Ngôn ngữ & Độ tương thích** | Python backend trên FastAPI + Vanilla JS hiện đại, không làm vỡ các API contracts hiện tại. |

---

## 4. Kiến trúc Hệ thống (Architecture Overview)

```
[ User Microphone Audio / Text ]
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  Instant Conversational Filler (<100ms Audio "Hmm...")  │
└──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  ASR Layer (/api/transcribe_audio)                       │
│  - Groq Whisper Large V3 -> Gemini Audio -> Browser STT  │
│  - Async-Safe Transcript Accumulation (IELTS + Roleplay) │
└──────────────────────────────┬───────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│  Conversational Core (/api/process_turn, /api/det/eval)  │
│  - Token-Efficient Empathetic Prompt Construction       │
│  - Multi-Provider LLM Pool (Groq -> Gemini -> OpenAI)   │
│  - Dynamic Anti-Repetition Fallback Engine               │
│  - Real-Time API Trace & Log Subsystem                  │
└──────────────────────────────┬───────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────┐
│  TTS Voice Synthesis (/api/tts)                          │
│  - ElevenLabs Multi-Key Auto-Rotation Pool               │
│  - Microsoft Edge-TTS Natural Neural Fallback (0Hz/0%)   │
│  - gTTS Safety Fallback                                  │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Definition of Done Checklist

- [ ] Log trace in đầy đủ thông tin provider, model, latency, status code, key exhaustion ra console và `logs/api_trace.log`.
- [ ] Giao diện/Hệ thống có câu nói đệm (*"Hmm...", "Uhm..."*) phản hồi ngay lập tức để người dùng không cảm thấy lag/delay.
- [ ] Fallback engine không bao giờ lặp lại cùng một câu phản hồi trong suốt buổi luyện tập, tự động chuyển chủ đề khi user yêu cầu.
- [ ] Prompt AI có cơ chế thấu cảm, phản chiếu ý kiến của user và kết thúc bằng câu hỏi mở sâu sắc.
- [ ] Giọng đọc fallback Edge-TTS tự nhiên, không bị méo tiếng hoặc bè giọng.
- [ ] IELTS Exam (Read-Then-Speak) ghi âm và bấm Submit thành công 100%, không bị lỗi "please record before submitting".
- [ ] Trang chủ Roleplay hiển thị <11 chủ đề tinh tuyển; mở All Topics Explorer có đầy đủ filter danh mục, tìm kiếm và phân vùng gọn gàng.
- [ ] Được kiểm thử bằng MCP như real user trên UI, tổng API calls test < 10 lần.
- [ ] Toàn bộ automated tests pass 100%.
