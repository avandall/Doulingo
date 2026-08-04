# 📌 docs/WORK_BOARD.md — Multi-Agent Kanban Work Board

This board tracks task progression across human engineers, coding agents, and scheduled reviewer agents (*Tip 29: Add a Work Board*; *Tip 26: Schedule Reviewer Agents*; *Tip 27: Make Two Agents Argue*).

---

## 🟢 DONE (Verified in Production / Live Code)
* [x] **LLM Vietnamese Translation Engine**: Replaced Google Translate scraping with Groq/Gemini LLM (`app/ai_engine.py:L26`).
* [x] **20-Level CEFR Difficulty System**: Granular constraints from Pre-A1 to C2 (`app/ai_engine.py:L47`).
* [x] **In-Memory 0ms Word Cache & SQLite Dictionary**: `TRANSLATION_CACHE` in `app/main.py:L31-34` + SQLite storage in `app/db.py:L25`.
* [x] **Duolingo UI Design System**: `#58CC02` Primary Green, 3D feather buttons, card layouts (`static/index.html`).
* [x] **Custom Scenario Builder**: `/api/custom_scenarios` endpoint with IELTS exam mode (`app/main.py:L91`).
* [x] **TTS Neural Voice Audio Pipeline**: Synthesize expressive voices with `edge-tts` and `gTTS` fallback (`app/tts_service.py:L27`).
* [x] **Multi-Turn Context Truncation Guard**: Rolling-window context truncation and summarization guard for conversations > 15 exchanges (`app/ai_engine.py:L533`).
* [x] **Scenario Sharing & Export JSON API**: Export custom scenarios for sharing between learners (`app/main.py:L121`).

---

## 🟣 READY FOR REVIEW (For Reviewer Agents — *Tip 26*)
* *No items currently awaiting automated code review.*

---

## 🟡 IN PROGRESS (Assigned to Active Agent Session)
* *No items currently in progress. Select an item from TODO for a fresh session (*Tip 15*).*

---

## 🔴 TODO (Backlog / Up Next)
* [ ] **Streaming Speech Audio Buffering**: Chunked MP3 streaming in `app/tts_service.py` for <300ms audio playback start.
* [ ] **XP Rewards & Streak Celebration Animation**: Confetti burst and XP reward card popup upon scenario completion in `static/index.html`.
* [ ] **Vocabulary Flashcard Practice Mode**: Duolingo-style interactive flashcard modal for `/api/saved_words`.

---

## 🛑 BLOCKED (*Tip 16*)
* *No blocked tasks. See [`docs/BLOCKED.md`] for handbrake log.*

---

## ⚖️ Architectural Debate Log (*Tip 27: Make Two Agents Argue*)

When proposing major architectural changes, two subagents (Proposer vs. Critic) must document their consensus here before editing `docs/specs.md`:

| Proposal | Proposer Agent Argument | Critic Agent Counter-Argument | Final Human Decision (*Tip 1*) |
| :--- | :--- | :--- | :--- |
| *e.g., Streaming Audio* | Use WebSockets for bi-directional streaming STT/TTS | WebSockets complicate PWA mobile Safari connection stability | Keep REST API + chunked HTTP response streaming |

---
---

# [VI] 📌 docs/WORK_BOARD.md — Bảng Quản Lý Công Việc Kanban Đa Agent

Bảng này theo dõi tiến độ thực hiện nhiệm vụ giữa kỹ sư, coding agent và reviewer agent theo lịch (*Tip 29: Add a Work Board*; *Tip 26: Schedule Reviewer Agents*; *Tip 27: Make Two Agents Argue*).

---

## 🟢 DONE (Đã Kiểm Thử Hoàn Thành / Code Hoạt Động)
* [x] **Động Cơ Dịch Thuật Tiếng Việt LLM**: Thay thế scraping Google Translate bằng Groq/Gemini LLM (`app/ai_engine.py:L26`).
* [x] **Hệ Thống 20 Cấp Độ Khó CEFR**: Các ràng buộc chính xác từ Pre-A1 đến C2 (`app/ai_engine.py:L47`).
* [x] **Cache RAM 0ms & Từ Điển SQLite**: `TRANSLATION_CACHE` tại `app/main.py:L31-34` + CSDL SQLite tại `app/db.py:L25`.
* [x] **Design System Duolingo UI**: Màu `#58CC02`, nút bo 3D, giao diện thẻ bo góc (`static/index.html`).
* [x] **Bộ Tạo Kịch Bản Tùy Chỉnh**: Endpoint `/api/custom_scenarios` hỗ trợ chế độ luyện thi IELTS (`app/main.py:L91`).
* [x] **Luồng Tổng Hợp Giọng Nói TTS**: Sinh giọng nói truyền cảm bằng `edge-tts` có dự phòng gTTS (`app/tts_service.py:L27`).
* [x] **Bộ Lọc Cắt Gọn Ngữ Cảnh Dài**: Tích hợp tóm tắt cửa sổ trượt trong `app/ai_engine.py` cho hội thoại > 15 lượt (`app/ai_engine.py:L533`).
* [x] **API Export & Chia Sẻ Kịch Bản JSON**: Xuất kịch bản tùy chỉnh để học viên chia sẻ với nhau (`app/main.py:L121`).

---

## 🟣 READY FOR REVIEW (Chờ Reviewer Agent — *Tip 26*)
* *Hiện không có mục nào đang chờ code review tự động.*

---

## 🟡 IN PROGRESS (Đang Thực Hiện Trong Phiên Active)
* *Hiện không có mục nào đang thực hiện. Hãy chọn một mục từ TODO cho phiên làm việc mới (*Tip 15*).*

---

## 🔴 TODO (Backlog / Kế Hoạch Tiếp Theo)
* [ ] **Truyền Phát Âm Thanh Theo Gói**: Streaming chia nhỏ MP3 trong `app/tts_service.py` giúp phát thanh dưới <300ms.
* [ ] **Hiệu Ứng Nhận Thưởng XP & Chúc Mừng Streak**: Pháo giấy và hộp thoại nhận XP khi hoàn thành kịch bản trong `static/index.html`.
* [ ] **Chế Độ Luyện Tập Flashcard**: Modal flashcard tương tác chuẩn Duolingo cho `/api/saved_words`.

---

## 🛑 BLOCKED (*Tip 16*)
* *Không có tác vụ nào bị cản trở. Xem [`docs/BLOCKED.md`] để biết nhật ký phanh khẩn cấp.*

---

## ⚖️ Nhật Ký Tranh Luận Kiến Trúc (*Tip 27: Make Two Agents Argue*)

Khi đề xuất các thay đổi kiến trúc lớn, hai subagent (Đề Xuất vs. Phản Biện) phải ghi nhận sự đồng thuận tại đây trước khi sửa đổi `docs/specs.md`:

| Đề Xuất | Lập Luận Của Agent Đề Xuất | Phản Biện Của Agent Chỉ Trích | Quyết Định Cuối Cùng Của Con Người (*Tip 1*) |
| :--- | :--- | :--- | :--- |
| *Ví dụ: Streaming Audio* | Dùng WebSocket để stream STT/TTS hai chiều | WebSocket làm phức tạp độ ổn định kết nối trên Safari PWA mobile | Giữ nguyên REST API + chunked HTTP response streaming |
