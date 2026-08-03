# 🏗️ Kiến Trúc Hệ Thống (Architecture Documentation) - Duolingo Speak Clone

Tài liệu này xác định kiến trúc kỹ thuật, cấu trúc module và luồng dữ liệu cho **Duolingo Speak** (ứng dụng luyện nói hội thoại ngữ cảnh dài - Long-Context Roleplay Conversation với giao diện chuẩn Duolingo).

> **Nguyên tắc Harness Engineering (Tip 4 & 5 - Don't describe code, point to it):**
> Các agent tự động (Ralph Loop) khi thực hiện code cần làm theo đúng các module, đường dẫn file và cấu trúc dữ liệu được quy định tại đây, không tự ý sáng tạo kiến trúc mới.

---

## 1. Cấu Trúc Thư Mục & Vai Trò Các Module

```
/home/avandall/project/Doulingo_Speak/Doulingo/
├── app/                      # Backend FastAPI Application
│   ├── main.py               # API Router, endpoints (/api/chat, /api/tts, /api/scenarios...) & static serving
│   ├── ai_engine.py          # LLM Roleplay Engine (OpenAI / Gemini / Mock fallback) & Speech Evaluator
│   ├── scenarios.py          # Dữ liệu kịch bản hội thoại dài (Scenarios catalogue)
│   ├── characters.py         # Danh sách nhân vật Duolingo (Duo, Lily, Oscar...) & system prompt cá tính
│   ├── tts_service.py        # Dịch vụ Text-to-Speech (Edge-TTS / gTTS / Web Audio fallback)
│   └── db.py                 # SQLite/Memory database lưu tiến độ, XP, Streak của người học
├── static/                   # Frontend Web UI (Vanilla JS + CSS chuẩn Duolingo DNA)
│   ├── index.html            # Single Page Application (SPA) layout
│   ├── css/                  # Styling chuẩn Duolingo (Colors, 3D Feather buttons, Animations)
│   ├── js/                   # UI logic, Web Speech API (STT), Audio Waveform visualizer, API calls
│   └── *.mp3                 # Mẫu giọng nói nhân vật
├── docs/                     # Harness Engineering Documentation (Ralph Loop harness)
│   ├── architecture.md       # (File này) Kiến trúc hệ thống
│   ├── rules.md              # Quy tắc kỹ thuật & chuẩn coding cho Agent
│   ├── specs.md              # Backlog chi tiết các task kiểm thử được (Checklist [ ] -> [x])
│   ├── prompt.md             # System prompt cho từng lặp lại của Ralph Loop
│   └── ralph_loop_guide.md   # Hướng dẫn thực hành chạy Ralph Loop qua đêm
├── main.py                   # Root entry point cho Uvicorn / Render deploy
└── pyproject.toml / uv.lock  # Quản lý phụ thuộc bằng UV
```

---

## 2. Luồng Xử Lý Chính (Core Data Flow)

### 2.1 Luồng Hội Thoại Ngữ Cảnh Dài (Long-Context Roleplay Flow)
1. **Nhận giọng nói (Voice Input):**
   - Người dùng nhấn nút Micro trên giao diện (`static/js/`).
   - Sóng âm (Audio Waveform) hiển thị thời gian thực theo giọng nói.
   - Frontend sử dụng **Web Speech API / Whisper STT** chuyển âm thanh thành văn bản (Speech-to-Text).
2. **Xử lý Ngôn ngữ Tự nhiên (LLM Engine):**
   - Văn bản STT gửi lên endpoint `/api/chat` tại `app/main.py`.
   - `app/ai_engine.py` nạp lịch sử hội thoại của tình huống (Scenario History), áp dụng System Prompt theo nhân vật (`app/characters.py`).
   - LLM sinh phản hồi ngữ cảnh (Next Response) + Đánh giá độ trôi chảy & gợi ý cách diễn đạt tự nhiên hơn (Native Phrasing Feedback).
3. **Phát âm AI (TTS Output):**
   - Văn bản phản hồi từ LLM được gửi tới `app/tts_service.py` (sử dụng `edge-tts` hoặc `gTTS`).
   - Trả về luồng âm thanh/base64 mp3 cho frontend phát ngữ điệu tự nhiên.
4. **Cập nhật Tiến độ & Gamification:**
   - Cập nhật số lượt thoại thành công, cộng XP và cập nhật Progress Bar trong `app/db.py`.

---

## 3. Duolingo Design Tokens & UI Component System

Hệ thống UI frontend (`static/`) bắt buộc áp dụng **Duolingo Design DNA**:
* **Bảng Màu Chính (Palette Tokens):**
  * `--duo-green-primary: #58CC02` (Màu xanh nhận diện thương hiệu)
  * `--duo-green-shadow: #46A302` (Màu đổ bóng nút 3D)
  * `--duo-blue-accent: #1CB0F6` (Màu xanh dương điểm nhấn / Gợi ý ngữ pháp)
  * `--duo-yellow-xp: #FFC800` (Màu vàng thưởng XP / Streak)
  * `--duo-coral-error: #FF4B4B` (Màu cảnh báo lỗi)
  * `--duo-bg-light: #F7F7F7` (Nền sáng) / `--duo-bg-dark: #131F24` (Nền tối)
* **3D Feather Buttons (Nút bấm 3D):**
  - Sử dụng bo góc `border-radius: 16px`, viền dưới `border-bottom: 4px solid var(--duo-green-shadow)`.
  - Khi `active/click`, nút chuyển dịch xuống 2px và giảm độ dày viền đáy (`border-bottom: 2px`).
* **Phản Hồi Trực Quan (Instant Feedback Cards):**
  - Modal feedback xuất hiện bên dưới sau mỗi lượt nói: màu xanh lá (nói tốt) hoặc xanh dương (gợi ý cách nói hay hơn của người bản xứ).

---

## 4. Hướng Dẫn Tích Hợp Kỹ Thuật Cho Agent

- **Tham chiếu Backend Endpoints:** Luôn kiểm tra và giữ tương thích API spec trong `app/main.py`.
- **Quản lý Dependencies:** Chỉ sử dụng `uv` để cài đặt thư viện (`uv pip install ...` hoặc khai báo trong `pyproject.toml`).
- **Xử lý ngoại lệ AI API:** Luôn duy trì cơ chế Mock Fallback trong `app/ai_engine.py` và `app/tts_service.py` để hệ thống vẫn chạy mượt mà ngay cả khi không có API Key của OpenAI/Gemini/Edge-TTS.

---

## 5. Kiến Trúc Trace Log, Theo Dõi Quota & Dịch Thuật Văn Nói (Logging, Quota & Localization DNA)

### 5.1 Hệ Thống Trace Log & Quota Key Rotation (`app/ai_engine.py` & `app/main.py`)
- **Mục tiêu:** Giám sát thời gian thực các cuộc gọi tới AI Provider (Groq, Gemini, OpenAI, Anthropic), nhận diện API Key nào đang được gọi và kiểm soát hạn mức (Quota/Rate limit).
- **Cơ chế hoạt động:**
  1. **Masked Key Logging:** Trước mỗi request, ghi log đầy đủ thông tin vào file `logs/api_trace.log`:
     `[TRACE] Provider=Groq | Model=llama-3.3-70b-versatile | Key=gsk_...9aB | Status=PENDING`
  2. **Quota Checking & Automated Failover:**
     - Kiểm tra HTTP Status Code (`200`, `429 Too Many Requests`, `403 Forbidden`, `500...`) và Error Message (`Quota exceeded`, `Rate limit reached`).
     - Khi phát hiện Key hết quota hoặc bị lỗi 429, tự động log:
       `[WARN] Key=gsk_...9aB quota exhausted (HTTP 429). Rotating to next available key...`
     - Tự động chuyển đổi sang API Key tiếp theo trong danh sách (`self.groq_keys`, `self.gemini_keys`) mà không làm ngắt quãng trải nghiệm người dùng.
  3. **Health & Quota Endpoint:** Cung cấp API `/api/trace` hoặc `/api/health/quota` để tra cứu nhanh danh sách key, trạng thái hoạt động và lịch sử lỗi.

### 5.2 Phân Tích & Nâng Cấp Chất Lượng Dịch Thuật (`_professional_vietnamese_localization`)
- **Nguyên nhân gốc rễ lỗi dịch sát nghĩa (Root Cause Analysis):**
  - Hàm `_professional_vietnamese_localization` hiện đang đặt `temperature = 0.15`. Nhiệt độ quá thấp làm suy giảm khả năng diễn đạt linh hoạt, khiến LLM dịch thô cứng theo từng từ (word-for-word).
  - Prompt thiếu chỉ dẫn về hệ thống đại từ xưng hô trong tiếng Việt và các từ đệm cảm xúc văn nói.
- **Chuẩn Dịch Thuật Văn Nói Tự Nhiên (Spoken Vietnamese Localization Standard):**
  1. **Nhiệt độ tối ưu:** Nâng `temperature` lên `0.35 - 0.40` để câu văn mềm mại, đậm chất hội thoại.
  2. **Xưng hô nhân vật (Roleplay Pronouns):** Luôn xác định mối quan hệ để dùng *em - anh, tớ - cậu, mình - bạn*, tuyệt đối không dịch rập khuôn *tôi - bạn* ở mọi tình huống.
  3. **Từ đệm văn nói (Vietnamese Particles):** Tự nhiên hóa câu thoại bằng các từ đệm *nhé, nha, đấy, đi, cơ mà, chứ, nè, vậy*.
  4. **Few-Shot Contrast Prompting:** Nhúng trực tiếp các cặp ví dụ so sánh (Dở - dịch từng từ vs. Hay - dịch văn nói) vào system prompt.
