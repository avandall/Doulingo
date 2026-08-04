# 🛠️ docs/TECH_DEBT.md — Technical Debt & Legacy Limitations Ledger

This document tracks known technical debt, refactoring needs, and non-blocking architectural improvements (*Tip 6: Track Tech Debt in Its Own File*; *Tip 11: Fix a Bug Older Than You*). 

> [!IMPORTANT]
> When executing a spec item in autonomous loops (`Ralph Loop`), **do not get distracted** by fixing items in this file unless explicitly tasked. Record new technical debt here instead of refactoring on the fly.

---

## 1. Backend API (`app/main.py`)
- `[MEDIUM]` **Async Route Blocking**: Currently, some LLM calls in route handlers execute synchronously or wait on blocking HTTP requests. Refactor to Pydantic/FastAPI `asyncio` thread pools or asynchronous HTTP clients (`httpx`) to improve concurrency under multi-user load.
- `[LOW]` **Global Cache Eviction**: `TRANSLATION_CACHE` and `IPA_CACHE` in `app/main.py:L31-34` grow indefinitely in memory. Implement an LRU cache eviction policy (e.g., `@lru_cache(maxsize=5000)`) to prevent unbounded RAM usage.

---

## 2. AI & LLM Engine (`app/ai_engine.py`)
- `[HIGH]` **Conversation History Overflow**: Long conversations (>15 turns) pass the full conversation history to the LLM. Add token counting and rolling window summarization to truncate older turns while retaining core scenario context.
- `[MEDIUM]` **Prompt Caching**: Groq and Gemini calls re-send system prompts and scenario instructions on every turn. Adopt LLM prompt caching headers where supported to reduce latency and token costs.

---

## 3. Audio Pipeline (`app/tts_service.py`, `static/js/speech.js`)
- `[HIGH]` **TTS Audio Latency**: `edge-tts` generates full MP3 files before returning bytes to the browser. Implement streaming audio chunks so playback starts instantaneously.
- `[MEDIUM]` **Safari iOS Audio Permission Drops**: Safari PWAs occasionally drop microphone permissions after long pauses. Implement proactive Web Speech API re-initialization hooks in `static/js/speech.js`.

---

## 4. SQLite Storage (`app/db.py`)
- `[LOW]` **SQLite Write Lock Concurrency**: High-frequency vocabulary saves under concurrent load can trigger SQLite database lock contention. Enable WAL (Write-Ahead Logging) mode in SQLite connection initialization (`PRAGMA journal_mode=WAL;`).

---
---

# [VI] 🛠️ docs/TECH_DEBT.md — Sổ Theo Dõi Nợ Kỹ Thuật & Giới Hạn Hệ Thống Cũ

Tài liệu này theo dõi nợ kỹ thuật hiện có, nhu cầu tái cấu trúc và các cải tiến kiến trúc không cản trở công việc hiện tại (*Tip 6: Track Tech Debt in Its Own File*; *Tip 11: Fix a Bug Older Than You*).

> [!IMPORTANT]
> Khi thực thi một mục tính năng trong vòng lặp tự động (`Ralph Loop`), **không được mất tập trung** bằng cách tự ý sửa các mục trong file này trừ khi được chỉ định rõ ràng. Hãy ghi lại nợ kỹ thuật mới vào đây thay vì tái cấu trúc tùy tiện trong lúc code.

---

## 1. Backend API (`app/main.py`)
- `[MEDIUM]` **Nghẽn Luồng Trong Route Async**: Hiện tại một số lời gọi LLM trong handler được thực hiện đồng bộ hoặc chờ yêu cầu HTTP chặn luồng. Cần tái cấu trúc sang sử dụng thread pool `asyncio` của FastAPI hoặc thư viện HTTP bất đồng bộ (`httpx`) để cải thiện hiệu năng khi có nhiều người dùng đồng thời.
- `[LOW]` **Đuổi Bộ Nhớ Đệm Toàn Cục**: `TRANSLATION_CACHE` và `IPA_CACHE` tại `app/main.py:L31-34` hiện tăng vô hạn trong RAM. Cần áp dụng cơ chế giải phóng bộ nhớ đệm LRU (ví dụ: `@lru_cache(maxsize=5000)`) để tránh tràn RAM.

---

## 2. Động Cơ AI & LLM (`app/ai_engine.py`)
- `[HIGH]` **Tràn Lịch Sử Hội Thoại**: Các cuộc trò chuyện dài (>15 lượt) gửi toàn bộ lịch sử trò chuyện đến LLM. Cần tích hợp bộ đếm token và tóm tắt lịch sử theo cửa sổ trượt (rolling window) để thu gọn các lượt cũ mà vẫn giữ được bối cảnh kịch bản.
- `[MEDIUM]` **Cache Prompt LLM**: Các lời gọi Groq/Gemini hiện gửi lại toàn bộ system prompt và hướng dẫn kịch bản trong mỗi lượt. Cần tận dụng header cache prompt của nhà cung cấp để giảm độ trễ và tiết kiệm token.

---

## 3. Luồng Âm Thanh (`app/tts_service.py`, `static/js/speech.js`)
- `[HIGH]` **Độ Trễ Tạo Audio TTS**: `edge-tts` hiện sinh toàn bộ tập tin MP3 trước khi trả dữ liệu về trình duyệt. Cần thực hiện truyền phát dữ liệu âm thanh theo từng gói (streaming chunk) để âm thanh bắt đầu phát lập tức.
- `[MEDIUM]` **Mất Quyền Microphone Trên Safari iOS**: Ứng dụng PWA trên Safari đôi khi mất quyền truy cập microphone sau khoảng nghỉ dài. Cần tích hợp cơ chế tự động tái khởi tạo Web Speech API trong `static/js/speech.js`.

---

## 4. Lưu Trữ SQLite (`app/db.py`)
- `[LOW]` **Tranh Chấp Khóa Ghi SQLite**: Các thao tác lưu từ vựng tần suất cao có thể gây xung đột khóa ghi (database lock contention). Cần kích hoạt chế độ WAL (Write-Ahead Logging) khi khởi tạo kết nối SQLite (`PRAGMA journal_mode=WAL;`).
