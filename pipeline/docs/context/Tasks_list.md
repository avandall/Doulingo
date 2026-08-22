# TASKS LIST
# Danh sách tác vụ & Queue thực thi — Duolingo Speak AI Conversational Engine & Pro Frontend

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.**
> 🤖 **AI EXECUTION RULE:** AI sẽ đọc danh sách này từ trên xuống dưới, tìm task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS` để thực thi. Khi hoàn thành task, AI đánh dấu `[x] DONE` và chuyển sang task tiếp theo.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Ghi chú / Blocker |
|---------|----------|-------|---------|------------|-------------------|
| `TASK-001` | Comprehensive Real-Time API Trace & Diagnostic Logging System | Phase 1 | P0 | `[x] DONE` | In log chi tiết provider, key, status, latency, fallback, quota |
| `TASK-002` | Dynamic Anti-Repetition Fallback Engine with Topic-Shift & Memory | Phase 2 | P0 | `[x] DONE` | Xóa bỏ hoàn toàn lặp câu, ngân hàng 30+ câu, đổi chủ đề, ghi nhớ lịch sử |
| `TASK-003` | Empathetic Prompting & ASR Phonetic Clarification Pipeline | Phase 3 | P1 | `[x] DONE` | Active listening, phản chiếu cảm xúc, xử lý từ phát âm sai (did you mean X?) |
| `TASK-004` | Instant Conversational Fillers (<100ms) & Natural TTS Tuning | Phase 4 | P1 | `[x] DONE` | Phát audio "Hmm... let me see" tức thì câu giờ + đưa Edge-TTS về tần số chuẩn |
| `TASK-005` | Fix IELTS EXAM Read-Then-Speak Recording & Submission Flow | Phase 5 | P0 | `[ ] TODO` | Khắc phục race condition bất đồng bộ ASR khiến Submit bị báo "please record" |
| `TASK-006` | Modern Curated Roleplay Hub (<11 Featured Topics & Categorized Explorer) | Phase 6 | P1 | `[ ] TODO` | Giữ <11 topics tinh tuyển trên trang chủ + Modal All Topics có tìm kiếm & filters |
| `TASK-007` | End-to-End Test Suite & MCP Browser Interactive Testing (<10 Calls) | Phase 7 | P0 | `[ ] TODO` | Test như real user qua MCP, kiểm tra toàn bộ luồng, giới hạn < 10 API calls |

---

## 2. Chi tiết các Tasks (Task Specs)

---

### 📌 TASK-001: Comprehensive Real-Time API Trace & Diagnostic Logging System

#### Metadata
```
Task ID:         TASK-001
Task Name:       Comprehensive Real-Time API Trace & Diagnostic Logging System
Phase:           Phase 1 (Observability & Logging)
Task Type:       feature / logging
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Khi chạy ứng dụng, developer và người dùng cần biết chính xác API nào đang được gọi, gọi có thành công không, key nào bị 429/401, khi nào chuyển sang fallback hay xoay vòng sang provider khác.
- **What:**
  1. Nâng cấp `log_api_trace()` trong `app/ai_engine.py` và `app/tts_service.py` để in log rõ ràng ra console có màu/prefix trực quan.
  2. Ghi nhật ký đầy đủ ra `logs/api_trace.log` cho mọi bước:
     - STT Ingestion (Groq Whisper / Gemini Audio / Browser fallback).
     - LLM Selection (Groq $\rightarrow$ Gemini $\rightarrow$ OpenAI $\rightarrow$ Ollama $\rightarrow$ Fallback), thời gian phản hồi (latency), HTTP status code.
     - Quota warning & Auto-rotation (khi 1 key hết hạn/429, log rõ: `[ElevenLabs] Key #1 (xi_...9A) hit 429 Quota -> Auto-rotating to Key #2`).
  3. Cập nhật endpoint `/api/trace` và `/api/health/quota` để trả về dữ liệu trạng thái real-time.

#### Acceptance Criteria
- [ ] Console in ra rõ ràng mỗi khi có request: `[TRACE] Step=... | Provider=... | Key=... | Status=... | Latency=...ms`.
- [ ] Khi ElevenLabs hết quota hoặc lỗi, có log ghi rõ nguyên nhân và provider fallback tiếp theo (Edge-TTS).
- [ ] File `logs/api_trace.log` được cập nhật liên tục với đầy đủ timestamp và masked keys.
- [ ] Unit test cho module logging chạy pass 100%.

#### Scope
- **Files được sửa/tạo:** `app/ai_engine.py`, `app/tts_service.py`, `app/main.py`, `tests/test_logging_trace.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_logging_trace.py -v
```

---

### 📌 TASK-002: Dynamic Anti-Repetition Fallback Engine with Topic-Shift & Context Memory

#### Metadata
```
Task ID:         TASK-002
Task Name:       Dynamic Anti-Repetition Fallback Engine with Topic-Shift & Context Memory
Phase:           Phase 2 (Fallback Overhaul)
Task Type:       feature / fallback
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Khi không có mạng hoặc tất cả LLM API keys đều hết quota, hệ thống hiện tại lặp đi lặp lại đúng 1 câu duy nhất. Fallback phải đủ thông minh, đa dạng, không bao giờ lặp lại câu trước và nhận biết được khi user đổi chủ đề.
- **What:**
  1. Viết lại hàm `_get_context_aware_fallback()` trong `app/ai_engine.py`:
     - Xây dựng ngân hàng 30+ câu mở (openers), câu kết nối (bodies) và câu hỏi mở (questions) phong phú chia theo level (1-20) và sắc thái cảm xúc (empathy, curious, cheerful, thoughtful).
     - Đọc `conversation_history` và kiểm tra độ tương đồng (Jaccard / N-gram) với 5 câu gần nhất của AI để **tuyệt đối không bao giờ chọn lại câu tương tự**.
     - Bổ sung bộ nhận diện chuyển chủ đề (Topic Shift Detector): Nếu user nói về "food", "travel", "movie", "weather", "change topic", fallback tự động bắt từ khóa và đặt câu hỏi về chủ đề mới thay vì tiếp tục bám vào `{title}` cũ.
     - Thay thế cơ chế nhồi từ cố định bằng việc lựa chọn ngẫu nhiên các câu mở rộng có nghĩa và phù hợp với độ dài Level.
  2. Đảm bảo `user_feedback` trong fallback vẫn cung cấp gợi ý sửa lỗi và chấm điểm hợp lý.

#### Acceptance Criteria
- [ ] Chạy thử nghiệm 10 turns liên tiếp ở chế độ Fallback không bao giờ xuất hiện 2 câu giống nhau.
- [ ] Khi user nói "Let's change topic to cooking", fallback phản hồi về cooking thay vì Career.
- [ ] Khi user than phiền buồn bã, fallback đưa ra phản hồi thấu cảm phù hợp, không dùng template neutral.
- [ ] Verification tests cho Fallback Engine chạy pass 100%.

#### Scope
- **Files được sửa/tạo:** `app/ai_engine.py`, `tests/test_fallback_engine.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_fallback_engine.py -v
```

---

### 📌 TASK-003: Empathetic Prompting & ASR Phonetic Clarification Pipeline

#### Metadata
```
Task ID:         TASK-003
Task Name:       Empathetic Prompting & ASR Phonetic Clarification Pipeline
Phase:           Phase 3 (Prompt & Intelligence)
Task Type:       feature / prompt-engineering
Priority:        P1-High
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** AI cần thông minh, thấu cảm, phản chiếu được cảm xúc và hiểu được lời nói của người học ngay cả khi phát âm chưa chuẩn hoặc bị ASR nhận diện sai âm.
- **What:**
  1. Nâng cấp System Prompt trong `app/ai_engine.py` và `app/prompt_factory.py`:
     - **Active Listening & Mirroring Directive:** Yêu cầu LLM trích xuất ít nhất 1 ý cụ thể/cảm xúc mà user vừa nói vào câu mở đầu trước khi đưa ra nhận định tiếp theo.
     - **ASR Phonetic Clarification Directive:** Khi user phát âm sai từ (ví dụ *'beach' $\rightarrow$ 'bitch'*, *'important' $\rightarrow$ 'in portal'*), AI không được chê trách hay nói "tôi không hiểu", mà phải lịch sự đoán ý và xác nhận nhẹ nhàng trong vai nhân vật (*"Oh, did you mean important? If so, I totally agree..."*).
     - **Open Question Mandate:** Mọi phản hồi của AI luôn kết thúc bằng 1 câu hỏi mở kích thích người học nói nhiều hơn.
  2. Bổ sung cơ chế ghi nhận feedback ngữ pháp thấu cảm (động viên người học, giải thích lỗi nhẹ nhàng).

#### Acceptance Criteria
- [x] AI phản hồi có chiều sâu, thể hiện sự lắng nghe và thấu cảm với cảm xúc của người dùng.
- [x] Khi thử nghiệm với các câu có từ vựng phát âm khó, AI tự động suy luận ra ý nghĩa chính xác của người học.
- [x] Tất cả câu trả lời của AI đều kết thúc bằng câu hỏi mở, không làm đứt đoạn cuộc trò chuyện.
- [x] Tests kiểm tra Prompt structure và Empathy logic pass 100%.

#### Scope
- **Files được sửa/tạo:** `app/ai_engine.py`, `app/prompt_factory.py`, `tests/test_empathy_prompt.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_empathy_prompt.py -v
```

---

### 📌 TASK-004: Instant Conversational Fillers (<100ms) & Natural TTS Fallback Tuning

#### Metadata
```
Task ID:         TASK-004
Task Name:       Instant Conversational Fillers (<100ms) & Natural TTS Fallback Tuning
Phase:           Phase 4 (Audio & Latency)
Task Type:       feature / audio-latency
Priority:        P1-High
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Trong giao tiếp thực tế, người bản xứ luôn có các từ đệm câu giờ (*"Hmm...", "Let me see...", "Well..."*) khi suy nghĩ. Cần có âm thanh phát ra ngay lập tức (<100ms) để che lấp độ trễ mạng gọi API LLM/TTS, đồng thời chỉnh giọng Edge-TTS không bị méo tiếng khi fallback.
- **What:**
  1. **Instant Filler Subsystem:**
     - Tạo/tích hợp sẵn bộ âm thanh filler ngắn (< 1s) cho từng nhân vật ảo (`lily`, `oscar`, `viktor`, `duo`) lưu trong `static/audio/fillers/` hoặc sinh tức thì qua Web Audio / Base64 cache.
     - Cập nhật `static/js/app.js`: Ngay khi user bấm gửi hoặc dứt lời, client lập tức phát 1 audio filler ngẫu nhiên phù hợp với nhân vật, đồng thời hiển thị hiệu ứng "AI is thinking...".
     - Khi âm thanh chính từ `/api/tts` tải về xong, chuyển tiếp mượt mà để phát câu trả lời chính của AI.
  2. **Natural Voice Fallback Tuning:**
     - Trong `app/tts_service.py`, chỉnh lại `pitch` và `rate` của `CHARACTER_VOICE_MAP` cho Edge-TTS về mức tự nhiên (`rate: "+0%"`, `pitch: "+0Hz"` thay vì `-10Hz`, `-10%`).
     - Đảm bảo khi ElevenLabs hết quota, giọng Microsoft Edge-TTS phát ra trong trẻo, ấm áp và tự nhiên.

#### Acceptance Criteria
- [ ] Khi user nói xong, audio filler phát trong vòng < 100ms, tạo cảm giác phản xạ tự nhiên.
- [ ] Luồng audio chính phát mượt mà sau khi filler kết thúc mà không bị chèn âm thanh.
- [ ] Giọng Edge-TTS fallback nghe tự nhiên, không bị trầm đục hay méo tiếng.
- [ ] Tests cho TTS Service và Filler mapping pass 100%.

#### Scope
- **Files được sửa/tạo:** `app/tts_service.py`, `static/js/app.js`, `static/audio/fillers/**`, `tests/test_tts_fillers.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_tts_fillers.py -v
```

---

### 📌 TASK-005: Fix IELTS EXAM Read-Then-Speak Recording & Submission Flow

#### Metadata
```
Task ID:         TASK-005
Task Name:       Fix IELTS EXAM Read-Then-Speak Recording & Submission Flow
Phase:           Phase 5 (Frontend Bugfix - IELTS Exam)
Task Type:       fix / frontend
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Khi người học vào phần thi IELTS Exam (Read-Then-Speak), bấm Start Recording nói xong bấm Submit, hệ thống bị chặn lại và báo lỗi "Please record before submitting" do race condition giữa Web Speech recognition, MediaRecorder và hàm submit.
- **What:**
  1. Trong `static/js/app.js` và `static/js/speech.js`:
     - Đồng bộ hóa biến `detSpeechAccumulated` với cả interim transcripts lẫn kết quả trả về từ `/api/transcribe_audio`.
     - Trong `submitDetSpeech()`: Nếu ASR đang xử lý hoặc chưa nhận xong text, chuyển nút submit sang trạng thái chờ `⏳ Transcribing & Evaluating...`, tự động đợi ASR hoàn tất thay vì chặn ngay lập tức.
     - Cho phép fallback gõ tay/review text trong trường hợp micro bị lỗi hoặc trình duyệt không bắt được âm thanh.
  2. Đảm bảo sau khi submit, modal chuyển sang hiển thị Bảng điểm DET Score Report (`det_report_score`, CEFR band, fluency, grammar, vocabulary, examiner critique) chính xác.

#### Acceptance Criteria
- [ ] Người dùng bấm Start Record $\rightarrow$ nói $\rightarrow$ bấm Submit: Hệ thống nộp bài thành công 100%, không xuất hiện toast lỗi "Please record before submitting".
- [ ] Bảng điểm đánh giá DET Score Report hiển thị đầy đủ các cột điểm và lời phê của giám khảo.
- [ ] Unit/Integration test cho flow IELTS Exam Evaluation pass 100%.

#### Scope
- **Files được sửa/tạo:** `static/js/app.js`, `static/js/speech.js`, `app/ai_engine.py`, `tests/test_det_exam_flow.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_det_exam_flow.py -v
```

---

### 📌 TASK-006: Modern Curated Roleplay Hub (<11 Featured Topics & Categorized Explorer)

#### Metadata
```
Task ID:         TASK-006
Task Name:       Modern Curated Roleplay Hub (<11 Featured Topics & Categorized Explorer)
Phase:           Phase 6 (Frontend UX Refactor)
Task Type:       feature / frontend-ui
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Giao diện hiện tại liệt kê hàng chục chủ đề tràn lan trên màn hình chính gây rối mắt. Cần tinh giản trang chủ chỉ giữ tối ưu <11 topics nổi bật, kèm nút mở "Topic Explorer" chuyên nghiệp có thanh Search, Filter tabs và phân vùng danh mục.
- **What:**
  1. **Trang chủ (Main Screen):**
     - Giới hạn hiển thị 8-10 topics thịnh hành nhất (Coffee Chat, Job Interview, Airport Travel, Hotel Check-in, Weekend Plans, Tech Talk, Doctor Visit, Shopping).
     - Thiết kế card hiện đại, tinh tế với icon 3D/emoji, badge level A1-C2 và hover animation mượt mà.
  2. **Topic Explorer Modal / Drawer:**
     - Nút hành động nổi bật: `📚 Explore All 30+ Topics` ở trang chủ.
     - Khi bấm, mở Explorer Modal toàn diện:
       - **Live Search Bar:** Tìm kiếm tức thì theo tên topic hoặc mô tả.
       - **Filter Tabs:** `All`, `Everyday Life ☕`, `Work & Career 💼`, `Travel & Adventure ✈️`, `Social & Culture 🎭`, `IELTS Prep 🎓`.
       - **Phân vùng gọn gàng:** Hiển thị số lượng topic theo từng category, click vào là vào thẳng phòng luyện nói.
  3. Cập nhật CSS trong `static/css/` đảm bảo giao diện responsive hoàn hảo trên Mobile, Tablet và Desktop.

#### Acceptance Criteria
- [ ] Màn hình chính Roleplay chỉ hiển thị tối đa 10 topics tiêu biểu + nút "Add Custom Topic" + nút "Explore All Topics".
- [ ] Topic Explorer Modal mở mượt mà, hỗ trợ tìm kiếm và lọc theo danh mục chuẩn xác.
- [ ] Responsive tốt, layout đẹp mắt chuẩn Production-level.

#### Scope
- **Files được sửa/tạo:** `static/index.html`, `static/css/**`, `static/js/app.js`, `app/scenarios/**`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_frontend_scenarios.py -v
```

---

### 📌 TASK-007: End-to-End Test Suite & MCP Browser Interactive Testing (<10 Calls)

#### Metadata
```
Task ID:         TASK-007
Task Name:       End-to-End Test Suite & MCP Browser Interactive Testing (<10 Calls)
Phase:           Phase 7 (E2E Verification & Browser QA)
Task Type:       test / verification
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-22
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Kiểm thử toàn bộ hệ thống như 1 real user trên giao diện thực tế bằng MCP Browser, đảm bảo tất cả chức năng hoạt động hoàn hảo, mượt mà và không bị crash, giới hạn tổng API calls < 10 lần.
- **What:**
  1. Viết bộ E2E Test Suite (`tests/test_e2e_conversational_system.py`) bao phủ toàn bộ các use cases:
     - Kịch bản 1: Roleplay thông minh, đổi chủ đề, thấu cảm, anti-repetition.
     - Kịch bản 2: IELTS Exam Read-Then-Speak ghi âm và nộp bài.
     - Kịch bản 3: Topic Explorer tìm kiếm và lọc danh mục.
     - Kịch bản 4: Tracing logs in ra console và file đầy đủ.
     - Kịch bản 5: Giọng đọc Edge-TTS tự nhiên khi không có ElevenLabs.
  2. Thực hiện kiểm thử tương tác qua MCP Browser, chụp screenshot xác nhận và kiểm tra log.
  3. Giới hạn nghiêm ngặt: Tổng số lần gọi API thử nghiệm thực tế < 10 lần.

#### Acceptance Criteria
- [ ] Tất cả 7 phases hoàn thành và verified pass 100%.
- [ ] Trải nghiệm UI/UX mượt mà, chuyên nghiệp như một sản phẩm Production sẵn sàng ra mắt.
- [ ] Tổng số API calls test được kiểm soát < 10 lần.

#### Scope
- **Files được sửa/tạo:** `tests/**`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/ -v
```
