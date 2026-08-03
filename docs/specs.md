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
- [ ] **SPEC-TEST-01:** Tạo script smoke test (`tests/test_smoke.py` hoặc script python) để tự động kiểm thử nhanh các endpoint `/api/chat`, `/api/scenarios`, và `/api/tts` mà không cần bật trình duyệt, phục vụ tự động hóa Ralph Loop.

---

## Giai Đoạn 5: Hệ Thống Trace Log, Theo Dõi Quota & Cải Tiến Chất Lượng Dịch Thuật (Logging, Quota & Localization Quality)

- [ ] **SPEC-LOG-01 (Trace Log & Key Usage Tracking):** Xây dựng hệ thống ghi log chi tiết (Trace Logging) trong `app/ai_engine.py` và `app/main.py`. Mỗi lần gọi LLM API (Groq, Gemini, OpenAI, Anthropic) cần ghi rõ vào file log (`logs/api_trace.log`) và console: provider nào được gọi, model nào, **API key nào được sử dụng (masked key, ví dụ `gsk_...9aB` hoặc `AIza...x8A9`)**, thời gian phản hồi (latency) và trạng thái HTTP status code.
- [ ] **SPEC-LOG-02 (Quota Checking & Automated Key Rotation):** Xây dựng cơ chế theo dõi quota và xử lý lỗi hạn mức (Rate Limit / Quota Exhaustion).
  - Kiểm tra mã phản hồi (HTTP 429 Too Many Requests, 403, 500 hoặc `Quota exceeded` từ response error message).
  - Khi một API key hết quota hoặc bị lỗi, tự động ghi log cảnh báo `"[TRACE] API Key [MASKED_KEY] exhausted/rate-limited"`, lập tức chuyển sang (rotate) API key tiếp theo trong danh sách và ghi nhận sự kiện chuyển key.
  - Bổ sung endpoint `/api/trace` hoặc `/api/health/quota` để tra cứu nhanh lịch sử gọi API, danh sách key đang hoạt động và tình trạng quota.
- [ ] **SPEC-TRANS-01 (Khắc phục nguyên nhân dịch sát nghĩa/word-by-word):** Tối ưu hóa tham số cho hàm `_professional_vietnamese_localization` trong `app/ai_engine.py`. Nâng `temperature` từ `0.15` lên `0.35 - 0.40` để LLM có đủ độ linh hoạt diễn đạt tự nhiên theo văn ngôn người Việt thay vì dịch thô cứng sát nghĩa từng từ.
- [ ] **SPEC-TRANS-02 (Cải tiến System Prompt Dịch Thuật Văn Nói - Spoken Vietnamese Few-Shot):** Nâng cấp nội dung system prompt của hàm `_professional_vietnamese_localization` với các yêu cầu:
  - **Xưng hô ngữ cảnh (Roleplay Pronouns):** Bắt buộc chọn đại từ xưng hô tự nhiên (*em - anh, tớ - cậu, mình - bạn*) phù hợp mối quan hệ giữa nhân vật Duolingo và người học, tuyệt đối không dùng toàn bộ *tôi - bạn* kiểu dịch máy.
  - **Từ đệm văn nói (Vietnamese Particles):** Nhận diện văn cảnh để thêm các từ đệm tự nhiên (*nhé, nha, đấy, đi, cơ mà, chứ, nè, vậy*) ở cuối câu.
  - **Few-Shot Examples (Ví dụ so sánh Dở vs. Hay):** Thêm trực tiếp vào prompt các ví dụ mẫu:
    - *Bad (Literal):* "Tôi muốn bạn làm điều này cho tôi ngay bây giờ." -> *Good (Spoken):* "Cậu giúp tớ việc này luôn nhé!"
    - *Bad (Literal):* "Chúng ta có sự gia tăng giá thuê nhà." -> *Good (Spoken):* "Đợt này tiền nhà lại tăng rồi cậu ạ."
- [ ] **SPEC-TRANS-03 (Kiểm thử tự động Trace Log & Dịch Thuật):** Viết script kiểm thử tự động `tests/test_localization_trace.py` để:
  - Xác thực hàm `_professional_vietnamese_localization` dịch thoại tự nhiên, không chứa dấu ngoặc kép thừa hoặc từ ngữ dịch máy thô cứng.
  - Xác thực hệ thống Trace Log hoạt động đúng, ghi log đầy đủ thông tin Masked Key, Status Code và tự động chuyển key khi gặp lỗi giả lập (Mock 429 Quota Exceeded).
