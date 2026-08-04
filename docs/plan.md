# 🦉 Kế Hoạch Triển Khai Ứng Dụng Luyện Nói Ngữ Cảnh Dài (Duolingo Speak Clone)

> [!NOTE]
> **Harness Engineering Documentation Hub**: This is the original Vietnamese project plan and design DNA reference. For active development, specifications, and AI agent execution rules, please refer to:
> - Root Hub: [`README.md`](file:///home/avandall1999/Projects/Doulingo_speak/README.md) & [`AGENTS.md`](file:///home/avandall1999/Projects/Doulingo_speak/AGENTS.md)
> - Architecture & Live Code: [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md) | Coding Rules: [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md)
> - Specs & Work Board: [`docs/specs.md`] | [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md)
> - Tech Debt & Handbrake: [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md) | [`docs/BLOCKED.md`] | [`docs/RALPH_LOOP.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/RALPH_LOOP.md)

## 1. Tổng Quan Dự Án (Project Overview)
Ứng dụng **Duolingo Speak** là giải pháp luyện nói chuyên sâu, kết hợp phong cách thiết kế UI/UX & Gamification đặc trưng của Duolingo với công nghệ AI thoại hội thoại ngữ cảnh dài (Long-Context Roleplay Conversation). 

Mục tiêu chính: Giúp người học thực hành **nói liên tục, tự nhiên trong các tình huống kéo dài** (hội thoại 5-15 lượt nói/kịch bản) thay vì chỉ phát âm từng câu ngắn đơn lẻ.

---

## 2. Phân Tích Đặc Trưng Duolingo (Duolingo Design & Feature DNA)

### 2.1 UI/UX Design System
* **Bảng màu đặc trưng (Duolingo Color Palette):**
  * Primary Green: `#58CC02` (Màu xanh thương hiệu)
  * Secondary Green: `#46A302` (Đổ bóng nút 3D)
  * Accent Blue: `#1CB0F6` / Accent Yellow: `#FFC800` / Accent Coral: `#FF4B4B`
  * Background: `#F7F7F7` (Light Mode) / `#131F24` (Dark Mode)
* **Nút bấm 3D (Feather Button Style):** Nút bo góc tròn (`border-radius: 16px`), hiệu ứng nhấn chìm xuống khi click (`box-shadow` / `border-bottom: 4px solid`).
* **Linh vật Duo & Animation:** Biểu cảm tương tác của linh vật Duo (vui mừng khi nói tốt, cổ vũ khi ngập ngừng, bất ngờ trước câu trả lời hay).
* **Phản hồi âm thanh & Hình ảnh (Audio-Visual Feedback):** Âm thanh "Ding!" rộn ràng khi hoàn thành lượt nói tốt, hiệu ứng confetti mừng hoàn thành kịch bản.

### 2.2 Gamification & Tâm Lý Học Người Học
* **Thanh tiến trình (Lesson Progress Bar):** Đoạn đường hoàn thành kịch bản nói.
* **Hệ thống XP & Streak:** Nhận điểm thưởng sau mỗi câu nói và sau mỗi scenario.
* **Instant Corrections:** Phản hồi tức thì về lỗi ngữ pháp/từ vựng nhưng không ngắt lời, chỉ hiển thị gợi ý sau khi kết thúc lượt nói.

---

## 3. Kiến Trúc Kỹ Thuật (Technical Architecture)

```
[ Frontend: Web App UI (Duolingo Aesthetic) ]
          │ 
          ├── 1. Speech Input (Web Audio / Web Speech API / Recorder)
          ├── 2. Waveform Audio Visualizer (Hiệu ứng sóng âm khi nói)
          └── 3. Duolingo UI Components (Progress, Duo Character, Feedback Cards)
          │
[ Backend: FastAPI (Python + UV Package Manager) ]
          │
          ├── A. STT Engine (Speech-to-Text): Whisper API / Web Speech API
          ├── B. LLM Engine (Long-Context Roleplay): OpenAI / Gemini API
          │      └── System Prompt & Conversation History Management
          ├── C. TTS Engine (Text-to-Speech): Edge-TTS / gTTS / Web Speech API
          └── D. Speech Evaluator (Phân tích độ trôi chảy & Ngữ pháp)
```

---

## 4. Luồng Trải Nghiệm Người Dùng (User Flow)

1. **Chọn Kịch Bản Luyện Nói (Scenario Selection):**
   * Người dùng chọn kịch bản: *Gọi món ở nhà hàng, Phỏng vấn xin việc, Tâm sự với bạn bè, Tranh luận chủ đề biến đổi khí hậu...*
2. **AI Khởi Tạo Tình Huống (AI Initiation):**
   * AI (đóng vai nhân vật) mở đầu bằng giọng nói TTS sống động + hiển thị lời thoại.
3. **Thực Hành Nói Liên Tục (Continuous User Speaking):**
   * Người dùng bấm nút **Mic** (có sóng âm chuyển động).
   * Hệ thống ghi âm & nhận diện STT theo thời gian thực.
4. **Phân Tích & Phản Hồi Tức Thì (Instant Feedback):**
   * **Đánh giá câu nói:** Chấm điểm độ tự nhiên (Fluency), phát hiện lỗi ngữ pháp nhẹ.
   * **Gợi ý Nâng Cấp (Better Phrasing):** Đưa ra cách diễn đạt tự nhiên hơn của người bản xứ (Native Speaker Version).
5. **Duy Trì Hội Thoại Ngữ Cảnh Dài (Long-Context Continuation):**
   * AI ghi nhớ toàn bộ nội dung đã nói trước đó, đưa ra câu phản hồi tiếp theo hợp lý, đặt câu hỏi mở để kích thích người dùng tiếp tục nói.
6. **Tổng Kết Kịch Bản (Scenario Summary & Rewards):**
   * Hiển thị bảng tổng kết: XP nhận được, danh sách từ vựng hay đã dùng, các câu cần cải thiện.

---

## 5. Kế Hoạch Triển Khai (Implementation Plan)

### Giai Đoạn 1: Xây Dựng UI/UX chuẩn Duolingo (Design System & Frontend)
- [ ] Thiết lập HTML/CSS/JS frontend với Duolingo theme tokens (Colors, Typography, 3D Buttons, Card Components).
- [ ] Tạo màn hình chính chọn Scenarios & màn hình Speaking Interface.
- [ ] Tích hợp Audio Waveform Visualizer khi người dùng bật Microphone.

### Giai Đoạn 2: Xây Dựng Backend & Tích Hợp AI Engines
- [ ] Xây dựng REST API / WebSocket bằng FastAPI (`uv`).
- [ ] Triển khai STT (Speech-to-Text) ghi nhận giọng nói người dùng.
- [ ] Triển khai LLM Engine với Memory Management (Lưu giữ lịch sử hội thoại dài).
- [ ] Triển khai TTS (Text-to-Speech) phát âm phản hồi của AI.

### Giai Đoạn 3: Đánh Giá Phát Âm & Phản Hồi Ngữ Cảnh (Grammar & Fluency Feedback)
- [ ] Xây dựng prompt đánh giá & so sánh câu gốc người dùng nói vs câu bản xứ (Native phrasing).
- [ ] Thiết kế Feedback Modal chuẩn Duolingo (Màu xanh dương/xanh lá, hiển thị điểm & mẹo diễn đạt).

### Giai Đoạn 4: Gamification & Hoàn Thiện Trải Nghiệm
- [ ] Tích hợp hiệu ứng âm thanh (Correct sound, Complete sound).
- [ ] Thêm thanh tiến trình (Progress Bar), Streak count, XP rewards & Confetti animation khi xong bài.
- [ ] Kiểm thử & Tối ưu độ trễ (Latency optimization cho luồng Voice-to-Voice).

---

## 6. Xác Nhận Kịch Bản Mẫu Dự Kiến (Sample Scenarios)
1. ☕ **At the Coffee Shop (Sơ cấp - 5 lượt nói):** Gọi đồ uống, yêu cầu điều chỉnh đường/đá, thanh toán.
2. 🧳 **Checking into a Hotel (Trung cấp - 8 lượt nói):** Phàn nàn về phòng thiếu tiện nghi, đổi phòng.
3. 💼 **Job Interview (Cao cấp - 10-15 lượt nói):** Trả lời câu hỏi phỏng vấn kéo dài, đưa ra ví dụ kinh nghiệm thực tế.

/goal Hãy đọc hệ thống tài liệu trong docs/prompt.md, docs/rules.md và docs/specs.md. Hãy thực hiện trọn bộ nhiệm vụ chưa hoàn thành (- [ ]) theo đúng mô hình Harness Engineering (đóng 2 vai Coder - Reviewer đối chất mã nguồn trước khi test cú pháp). Không dừng lại cho đến khi 100% checkbox trong docs/specs.md hoàn tất!
