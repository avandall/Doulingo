# 📋 docs/specs.md — Functional Specifications & Visible Done Checklists

This document is the master specification for **Duolingo Speak**. It breaks all features down into **Logical Units** (*Tip 14*) with **Visible Done Checklists** (`[ ]`, `[/]`, `[x]`) (*Tip 13*).

---

## 1. Core AI Roleplay Conversational Engine (`app/ai_engine.py`)

### Acceptance Criteria
- [x] **LLM Conversational Continuation**: Generate context-aware AI roleplay responses in English based on `scenario_id`, `character_id`, and `conversation_history`.
- [x] **Natural Vietnamese Translation**: Provide fluent, non-machine Vietnamese translations for AI responses using Groq/Gemini LLM (`ai_engine.py:L26`).
- [x] **Meaning-Preserving Grammatical Correction**: Evaluate user speech, correct grammar errors gently, and suggest native-speaker phrasing.
- [x] **Dynamic Scenario Angle Randomizer**: Invalidate repetitive scripts by selecting from `SCENARIO_ANGLES` presets (`ai_engine.py:L27-35`).
- [x] **20-Level CEFR Constraints (`LEVEL_CONFIGS`)**: Enforce per-level word limits (`sentence_words`, `max_words`) and allowed grammar whitelists (`ai_engine.py:L47`).
- [x] **Multi-Turn Context Truncation Guard**: Automatically summarize or prune conversation turns older than 15 exchanges to prevent prompt overflow without losing scenario context.

---

## 2. Text-to-Speech & Speech-to-Text Pipeline (`app/tts_service.py`, `static/js/speech.js`)

### Acceptance Criteria
- [x] **Neural Speech Synthesis (`edge-tts`)**: Synthesize high-quality neural voice audio per character persona (`tts_service.py:L27`).
- [x] **TTS Fallback Mechanism**: Automatically downgrade to `gTTS` if `edge-tts` fails or times out.
- [x] **Web Speech API Audio Recording**: Capture speech via microphone in `static/js/speech.js` with audio waveform visualizer animation.
- [x] **Mobile PWA Speech Recognition Fix**: Support complete transcript capture on iOS Safari and Android PWAs without clipping.
- [x] **Streaming Speech Audio Buffering**: Implement chunked MP3 streaming so audio playback begins within <300ms of LLM response.

---

## 3. Duolingo UI/UX & Gamification Frontend (`static/index.html`)

### Acceptance Criteria
- [x] **Duolingo Design System Integration**: Apply `--duo-primary-green` (`#58CC02`), 3D feather buttons, and rounded card layouts.
- [x] **Interactive Scenario Selection Grid**: Display preset scenarios with emojis, category badges, and CEFR level tags.
- [x] **Character Avatar Selection**: Allow users to switch between conversational partners (Duo, Rajesh, Lily, Oscar, etc.).
- [x] **Speaking Turn Progress Bar**: Show completion progress across a multi-turn roleplay session.
- [x] **Instant Corrections Modal**: Display native phrasing suggestions and grammar scores after each turn without interrupting speech.
- [x] **XP Rewards & Streak Celebration Animation**: Implement animated XP popup and confetti burst upon scenario completion.

---

## 4. 0ms Vocabulary Book & Permanent Dictionary (`app/db.py`, `app/main.py`)

### Acceptance Criteria
- [x] **L1 In-Memory Cache (`TRANSLATION_CACHE`)**: Store translated words in RAM for instant 0ms lookup (`main.py:L31-34`).
- [x] **L2 SQLite Word Dictionary**: Persist vocabulary entries and IPA transcriptions to local SQLite storage (`db.py:L25`).
- [x] **Saved Vocabulary Book API**: Provide `/api/saved_words` endpoint to retrieve, save, and manage bookmarked words.
- [x] **Vocabulary Flashcard Practice Mode**: Add UI modal to review bookmarked words using interactive Duolingo-style flashcards.

---

## 5. Custom Scenario Creation (`app/db.py`)

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
- [x] **Truyền Phát Âm Thanh Theo Gói (Streaming Audio)**: Thực hiện chia gói MP3 streaming để bắt đầu phát âm thanh ngay dưới <300ms kể từ khi LLM trả lời.

---

## 3. Giao Diện Duolingo UI/UX & Gamification (`static/index.html`)

### Tiêu Chí Nghiệm Thu
- [x] **Tích Hợp Design System Duolingo**: Áp dụng mã màu `--duo-primary-green` (`#58CC02`), nút bo góc 3D và bố cục thẻ bo tròn.
- [x] **Lưới Lựa Chọn Kịch Bản Tương Tác**: Hiển thị danh sách kịch bản với emoji, nhãn danh mục và thẻ cấp độ CEFR rõ ràng.
- [x] **Lựa Chọn Avatar Nhân Vật**: Cho phép người học tự do đổi bạn đồng hành (Duo, Rajesh, Lily, Oscar, v.v.).
- [x] **Thanh Tiến Trình Lượt Nói**: Cập nhật thanh tiến độ liên tục trong suốt buổi nhập vai hội thoại.
- [x] **Modal Sửa Lỗi Tức Thì**: Hiển thị mẹo diễn đạt bản ngữ và điểm ngữ pháp sau mỗi câu nói mà không ngắt quãng người dùng.
- [x] **Hiệu Ứng Nhận Thưởng XP & Chúc Mừng Streak**: Tích hợp hoạt ảnh pháo giấy và hộp thoại thưởng XP khi hoàn thành bài tập.

---

## 4. Sổ Từ Vựng 0ms & Từ Điển Vĩnh Viễn (`app/db.py`, `app/main.py`)

### Tiêu Chí Nghiệm Thu
- [x] **L1 RAM Cache (`TRANSLATION_CACHE`)**: Lưu từ vựng đã dịch trong RAM để tra cứu ngay lập tức 0ms (`main.py:L31-34`).
- [x] **L2 Từ Điển SQLite**: Lưu trữ vĩnh viễn từ vựng và phiên âm IPA trên cơ sở dữ liệu SQLite cục bộ (`db.py:L25`).
- [x] **API Sổ Từ Vựng Đã Lưu**: Cung cấp endpoint `/api/saved_words` để lấy, lưu và quản lý từ vựng yêu thích.
- [x] **Chế Độ Luyện Tập Flashcard**: Thêm giao diện modal ôn tập từ đã lưu bằng thẻ flashcard tương tác mang phong cách Duolingo.

---

## 5. Tạo Kịch Bản Tùy Chỉnh (`app/db.py`)

### Tiêu Chí Nghiệm Thu
- [x] **Endpoint Kịch Bản Tùy Chỉnh (`/api/custom_scenarios`)**: Cho phép người dùng tự tạo chủ đề giao tiếp với mục tiêu và từ vựng riêng (`main.py:L91`).
- [x] **Hỗ Trợ Chế Độ Luyện Thi IELTS / DET**: Hỗ trợ tiếp đầu ngữ mô phỏng đề thi thực tế (`det_custom_`).
- [x] **Xuất & Chia Sẻ Kịch Bản**: Cho phép xuất kịch bản tùy chỉnh sang file JSON để chia sẻ giữa các học viên (`app/main.py:L121`).

## 6. Chỉnh sửa chức năng
- [x] **Trong các phần nói, hãy bỏ giao diện nhập text hẳn ra. Chỉ để lại hình micro để bấm vào nói. Kể cả với phần IELTS EXAM, khi bấm start recording thì xuất hiện 1 micro và 1 hình sóng âm để khi người dùng nói nó sẽ nhảy sóng âm biểu thị đã ghi nhận đoạn nói cho user biết.**
- [x] **Kiểm tra lại tính năng tự chuyển API key tiếp theo trong list API lấy từ env có hoạt động đúng ko hay 1 API exhausted thì nó ngưng và fallback luôn**
- [x] **Bạn là 1 kỹ sư từng làm ra app Doulingo, giờ bạn quay lại làm app này, hãy test app bằng MCP chrome devtool, bật giao diện, test như 1 real user xem lỗi gì đang có, AI phản hồi có tốt ko, có đúng level cho real user ko ? Còn lỗi hay violation nào ko, nếu có thì phản biện lại để AI implement sửa và hand-out cho bạn check**