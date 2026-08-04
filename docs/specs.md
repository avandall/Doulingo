# 📋 Đặc Tả Kỹ Thuật & Danh Sách Công Việc (Specs & Tasks - Ralph Loop Backlog)

Tài liệu này chứa toàn bộ các yêu cầu kỹ thuật có thể kiểm chứng được (Testable Specifications) cho dự án **Duolingo Speak Clone** dưới dạng danh sách việc cần làm (`- [ ]`).

> **Quy Tắc Cho Ralph Loop Agent:**
> - Tìm mục đầu tiên có dấu `- [ ]`.
> - Thực hiện ĐÚNG 01 mục đó theo quy tắc trong `docs/rules.md` và kiến trúc trong `docs/architecture.md`.
> - Chạy kiểm thử tự động để xác nhận không lỗi.
> - Đổi `- [ ]` thành `- [x]` sau khi hoàn thành và commit code.

---

## Giai Đoạn 1: Cấu Trúc & Nền Tảng UI/UX Duolingo (Frontend Standard)

- [x] **SPEC-UI-01:** Xác thực và đồng bộ hóa các biến CSS chuẩn Duolingo (`--duo-green-primary: #58CC02`, `--duo-green-shadow: #46A302`, `--duo-blue-accent: #1CB0F6`, `--duo-yellow-xp: #FFC800`) trong `static/index.html` và file CSS liên quan.
- [x] **SPEC-UI-02:** Chuẩn hóa toàn bộ các nút bấm tương tác theo phong cách **3D Feather Button** (`border-radius: 16px`, `border-bottom: 4px solid var(--duo-green-shadow)`, chuyển vị trí 2px khi click/active).
- [x] **SPEC-UI-03:** Cải thiện Thanh Tiến Trình (Lesson Progress Bar) trong màn hình luyện nói, hiển thị chính xác tỷ lệ hoàn thành kịch bản với animation mượt mà.
- [x] **SPEC-UI-04:** Xác thực hiệu ứng chuyển động sóng âm (Audio Waveform Visualizer) trong `static/js/` hiển thị trạng thái sinh động khi người dùng bật Microphone.

---

## Giai Đoạn 2: Tối Ưu Hóa API Backend & LLM Engine (FastAPI & Long-Context Roleplay)

- [x] **SPEC-BE-01:** Xác thực cơ chế Mock Fallback trong `app/ai_engine.py` đảm bảo trả về câu thoại hội thoại mẫu hợp lý, điểm Fluency và lời khuyên bản xứ (Native Phrasing) khi không có API Key của OpenAI/Gemini.
- [x] **SPEC-BE-02:** Kiểm tra và hoàn thiện bộ nhớ ngữ cảnh dài (Long-Context History Management) cho hội thoại 5-15 lượt nói trong `app/scenarios.py` và `app/ai_engine.py`.
- [x] **SPEC-BE-03:** Đảm bảo endpoint `/api/chat` trong `app/main.py` xử lý mượt mà dữ liệu đầu vào STT từ người dùng và trả về phản hồi theo định dạng JSON chuẩn:
  ```json
  {
    "response": "...",
    "audio_url": "...",
    "fluency_score": 95,
    "native_suggestion": "...",
    "is_completed": false,
    "xp_gained": 10
  }
  ```

---

## Giai Đoạn 3: Dịch Vụ Âm Thanh (Speech-to-Text & Text-to-Speech)

- [x] **SPEC-AUDIO-01:** Kiểm tra dịch vụ TTS trong `app/tts_service.py` đảm bảo phát âm các giọng nhân vật Duolingo (Duo, Lily, Oscar...) ổn định và có cơ chế fallback về gTTS/Web Speech khi `edge-tts` gặp sự cố mạng.
- [x] **SPEC-AUDIO-02:** Chuẩn hóa endpoint `/api/tts` để hỗ trợ stream âm thanh nhanh nhất cho Frontend.

---

## Giai Đoạn 4: Gamification & Hoàn Thiện Trải Nghiệm Người Học

- [x] **SPEC-GAME-01:** Xác thực hệ thống tính điểm XP và Streak Counter trong `app/db.py`, đảm bảo cập nhật tiến độ khi người học hoàn thành từng lượt thoại và toàn bộ kịch bản.
- [x] **SPEC-GAME-02:** Đảm bảo modal phản hồi (Instant Feedback Modal) hiển thị đúng màu sắc (xanh lá cho lời nói trôi chảy, xanh dương cho gợi ý sửa lỗi ngữ pháp nhẹ) theo chuẩn Duolingo UI.
- [x] **SPEC-TEST-01:** Tạo script smoke test (`tests/test_smoke.py` hoặc script python) để tự động kiểm thử nhanh các endpoint `/api/chat`, `/api/scenarios`, và `/api/tts` mà không cần bật trình duyệt, phục vụ tự động hóa Ralph Loop.

---

## Giai Đoạn 5: Hệ Thống Trace Log, Theo Dõi Quota & Cải Tiến Chất Lượng Dịch Thuật (Logging, Quota & Localization Quality)

<<<<<<< HEAD
- [x] **SPEC-LOG-01 (Trace Log & Key Usage Tracking):** Xây dựng hệ thống ghi log chi tiết (Trace Logging) trong `app/ai_engine.py` và `app/main.py`. Mỗi lần gọi LLM API (Groq, Gemini, OpenAI, Anthropic) cần ghi rõ vào file log (`logs/api_trace.log`) và console: provider nào được gọi, model nào, **API key nào được sử dụng (masked key, ví dụ `gsk_...9aB` hoặc `AIza...x8A9`)**, thời gian phản hồi (latency) và trạng thái HTTP status code.
- [x] **SPEC-LOG-02 (Quota Checking & Automated Key Rotation):** Xây dựng cơ chế theo dõi quota và xử lý lỗi hạn mức (Rate Limit / Quota Exhaustion).
  - Kiểm tra mã phản hồi (HTTP 429 Too Many Requests, 403, 500 hoặc `Quota exceeded` từ response error message).
  - Khi một API key hết quota hoặc bị lỗi, tự động ghi log cảnh báo `"[TRACE] API Key [MASKED_KEY] exhausted/rate-limited"`, lập tức chuyển sang (rotate) API key tiếp theo trong danh sách và ghi nhận sự kiện chuyển key.
  - Bổ sung endpoint `/api/trace` hoặc `/api/health/quota` để tra cứu nhanh lịch sử gọi API, danh sách key đang hoạt động và tình trạng quota.
- [x] **SPEC-TRANS-01 (Khắc phục nguyên nhân dịch sát nghĩa/word-by-word):** Tối ưu hóa tham số cho hàm `_professional_vietnamese_localization` trong `app/ai_engine.py`. Nâng `temperature` từ `0.15` lên `0.35 - 0.40` để LLM có đủ độ linh hoạt diễn đạt tự nhiên theo văn ngôn người Việt thay vì dịch thô cứng sát nghĩa từng từ.
- [x] **SPEC-TRANS-02 (Cải tiến System Prompt Dịch Thuật Văn Nói - Spoken Vietnamese Few-Shot):** Nâng cấp nội dung system prompt của hàm `_professional_vietnamese_localization` với các yêu cầu:
  - **Xưng hô ngữ cảnh (Roleplay Pronouns):** Bắt buộc chọn đại từ xưng hô tự nhiên (*em - anh, tớ - cậu, mình - bạn*) phù hợp mối quan hệ giữa nhân vật Duolingo và người học, tuyệt đối không dùng toàn bộ *tôi - bạn* kiểu dịch máy.
  - **Từ đệm văn nói (Vietnamese Particles):** Nhận diện văn cảnh để thêm các từ đệm tự nhiên (*nhé, nha, đấy, đi, cơ mà, chứ, nè, vậy*) ở cuối câu.
  - **Few-Shot Examples (Ví dụ so sánh Dở vs. Hay):** Thêm trực tiếp vào prompt các ví dụ mẫu:
    - *Bad (Literal):* "Tôi muốn bạn làm điều này cho tôi ngay bây giờ." -> *Good (Spoken):* "Cậu giúp tớ việc này luôn nhé!"
    - *Bad (Literal):* "Chúng ta có sự gia tăng giá thuê nhà." -> *Good (Spoken):* "Đợt này tiền nhà lại tăng rồi cậu ạ."
- [x] **SPEC-TRANS-03 (Kiểm thử tự động Trace Log & Dịch Thuật):** Viết script kiểm thử tự động `tests/test_localization_trace.py` để:
  - Xác thực hàm `_professional_vietnamese_localization` dịch thoại tự nhiên, không chứa dấu ngoặc kép thừa hoặc từ ngữ dịch máy thô cứng.
  - Xác thực hệ thống Trace Log hoạt động đúng, ghi log đầy đủ thông tin Masked Key, Status Code và tự động chuyển key khi gặp lỗi giả lập (Mock 429 Quota Exceeded).
=======
### Acceptance Criteria
- [x] **Custom Scenario Endpoint (`/api/custom_scenarios`)**: Create custom user-defined speaking topics with custom objectives and vocabulary (`main.py:L91`).
- [x] **IELTS / DET Exam Mode Support**: Support specialized exam simulation prefixes (`det_custom_`).
- [x] **Scenario Sharing & Export**: Allow exporting custom scenarios as JSON files for sharing between learners (`app/main.py:L121`).

---
---

# [VI] 📋 docs/specs.md — Đặc Tả Kỹ Thuật & Danh Sách Hoàn Thành Trực Quan

Tài liệu này là bản đặc tả tổng thể cho **Duolingo Speak**. Các tính năng được phân chia thành **Đơn Vị Logic (Logical Units)** (*Tip 14*) cùng **Checklist Hoàn Thành Trực Quan** (`[ ]`, `[/]`, `[x]`) (*Tip 13*).

---

## 1. Động Cơ Nhập Vai Hội Thoại AI (`app/ai_engine.py`)

### Tiêu Chí Nghiệm Thu
- [x] **Duy Trì Hội Thoại LLM**: Sinh phản hồi nhập vai tiếng Anh theo ngữ cảnh dựa trên `scenario_id`, `character_id` và `conversation_history`.
- [x] **Dịch Tiếng Việt Tự Nhiên**: Cung cấp bản dịch trôi chảy, không mang văn phong máy móc cho các câu trả lời của AI bằng Groq/Gemini LLM (`ai_engine.py:L26`).
- [x] **Sửa Ngữ Pháp Giữ Nguyên Ý**: Đánh giá câu nói của học viên, sửa lỗi nhẹ nhàng và gợi ý cách nói chuẩn bản ngữ.
- [x] **Bộ Đổi Góc Độ Kịch Bản Ngẫu Nhiên**: Xóa bỏ rập khuôn bằng cách chọn ngẫu nhiên các hướng hội thoại từ danh sách `SCENARIO_ANGLES` (`ai_engine.py:L27-35`).
- [x] **Ràng Buộc 20 Cấp Độ CEFR (`LEVEL_CONFIGS`)**: Kiểm soát chặt chẽ số từ từng câu (`sentence_words`, `max_words`) và danh sách ngữ pháp được phép theo từng cấp độ (`ai_engine.py:L47`).
- [x] **Bộ Lọc Cắt Gọn Ngữ Cảnh Dài**: Tự động tóm tắt hoặc cắt bớt các lượt thoại cũ hơn 15 lần trao đổi để tránh tràn prompt mà không làm mất ngữ cảnh cốt lõi.

---

## 2. Luồng Xử Lý Âm Thanh TTS & STT (`app/tts_service.py`, `static/js/speech.js`)

### Tiêu Chí Nghiệm Thu
- [x] **Tổng Hợp Giọng Nói Trí Tuệ Nhân Tạo (`edge-tts`)**: Tạo âm thanh truyền cảm sắc nét cho từng nhân vật (`tts_service.py:L27`).
- [x] **Cơ Chế TTS Dự Phòng**: Tự động chuyển xuống `gTTS` nếu `edge-tts` gặp sự cố hoặc quá thời gian chờ.
- [x] **Ghi Âm Web Speech API**: Thu âm giọng nói qua microphone trong `static/js/speech.js` kèm hiệu ứng sóng âm sống động.
- [x] **Tối Ưu Nhận Diện Trên Mobile PWA**: Đảm bảo ghi nhận trọn vẹn câu nói trên iOS Safari và Android PWA mà không bị mất chữ đầu/cuối.
- [ ] **Truyền Phát Âm Thanh Theo Gói (Streaming Audio)**: Thực hiện chia gói MP3 streaming để bắt đầu phát âm thanh ngay dưới <300ms kể từ khi LLM trả lời.

---

## 3. Giao Diện Duolingo UI/UX & Gamification (`static/index.html`)

### Tiêu Chí Nghiệm Thu
- [x] **Tích Hợp Design System Duolingo**: Áp dụng mã màu `--duo-primary-green` (`#58CC02`), nút bo góc 3D và bố cục thẻ bo tròn.
- [x] **Lưới Lựa Chọn Kịch Bản Tương Tác**: Hiển thị danh sách kịch bản với emoji, nhãn danh mục và thẻ cấp độ CEFR rõ ràng.
- [x] **Lựa Chọn Avatar Nhân Vật**: Cho phép người học tự do đổi bạn đồng hành (Duo, Rajesh, Lily, Oscar, v.v.).
- [x] **Thanh Tiến Trình Lượt Nói**: Cập nhật thanh tiến độ liên tục trong suốt buổi nhập vai hội thoại.
- [x] **Modal Sửa Lỗi Tức Thì**: Hiển thị mẹo diễn đạt bản ngữ và điểm ngữ pháp sau mỗi câu nói mà không ngắt quãng người dùng.
- [ ] **Hiệu Ứng Nhận Thưởng XP & Chúc Mừng Streak**: Tích hợp hoạt ảnh pháo giấy và hộp thoại thưởng XP khi hoàn thành bài tập.

---

## 4. Sổ Từ Vựng 0ms & Từ Điển Vĩnh Viễn (`app/db.py`, `app/main.py`)

### Tiêu Chí Nghiệm Thu
- [x] **L1 RAM Cache (`TRANSLATION_CACHE`)**: Lưu từ vựng đã dịch trong RAM để tra cứu ngay lập tức 0ms (`main.py:L31-34`).
- [x] **L2 Từ Điển SQLite**: Lưu trữ vĩnh viễn từ vựng và phiên âm IPA trên cơ sở dữ liệu SQLite cục bộ (`db.py:L25`).
- [x] **API Sổ Từ Vựng Đã Lưu**: Cung cấp endpoint `/api/saved_words` để lấy, lưu và quản lý từ vựng yêu thích.
- [ ] **Chế Độ Luyện Tập Flashcard**: Thêm giao diện modal ôn tập từ đã lưu bằng thẻ flashcard tương tác mang phong cách Duolingo.

---

## 5. Tạo Kịch Bản Tùy Chỉnh (`app/db.py`)

### Tiêu Chí Nghiệm Thu
- [x] **Endpoint Kịch Bản Tùy Chỉnh (`/api/custom_scenarios`)**: Cho phép người dùng tự tạo chủ đề giao tiếp với mục tiêu và từ vựng riêng (`main.py:L91`).
- [x] **Hỗ Trợ Chế Độ Luyện Thi IELTS / DET**: Hỗ trợ tiếp đầu ngữ mô phỏng đề thi thực tế (`det_custom_`).
- [x] **Xuất & Chia Sẻ Kịch Bản**: Cho phép xuất kịch bản tùy chỉnh sang file JSON để chia sẻ giữa các học viên (`app/main.py:L121`).
>>>>>>> 633bd73 (feat(custom-scenarios): add custom scenario export and import endpoints for scenario sharing)
