# PLAN
# Kế hoạch thực thi — TASK-013

> **Task:** `TASK-013` Sentence-Level Streaming & Direct Chunked Audio Synthesis
> **Trạng thái:** COMPLETED | **Cập nhật:** 2026-08-27

---

## 🎯 Task Spec Overview
Triển khai cơ chế Sentence-Level Streaming và Direct Chunked Audio Synthesis để giảm Time-To-First-Audio (TTFA) xuống dưới 1.0 giây từ khi người dùng dứt lời. Tách response thành các câu độc lập (theo ranh giới `.`, `!`, `?`), lập tức tổng hợp và stream audio cho câu 1 ngay khi có sẵn, cho phép trình duyệt phát ngay chunk audio đầu tiên trong khi các câu tiếp theo tiếp tục được tổng hợp song song.

---

## 📌 Implementation Steps (Atomic Steps)

- [x] **Step 1: Implement Sentence Splitting & Sentence-Level Audio Streaming (`app/audio/tts_service.py` & `app/audio/tts_streamer.py`)**
  - Implement `split_sentences(text: str) -> list[str]` to intelligently tokenize response into sentence boundaries while handling abbreviations and punctuation.
  - Implement `stream_sentence_level_tts(text: str, char_id: str, tld: str)` async generator yielding chunked MP3 audio sentence-by-sentence for fast TTFA.
  - Update `TTSStreamer` in `app/audio/tts_streamer.py` with sentence-level streaming helper `stream_sentence_audio_chunks`.

- [x] **Step 2: Update Audio API Routers for Sentence-Level Streaming (`app/api/routers/audio.py`)**
  - Update `GET /api/tts` endpoint to support `stream=true` parameter or direct sentence streaming via `/api/tts/stream`.
  - Configure `StreamingResponse` headers (`audio/mpeg`, chunked transfer, cache-control) to support instant audio playback.

- [x] **Step 3: Update Frontend App for Direct Native Audio Streaming (`static/js/app.js`)**
  - Refactor `playTTS` in `static/js/app.js` to utilize streaming audio (`audio.src = url`) rather than waiting for full `res.blob()`.
  - Ensure smooth audio playback transition without stuttering.

- [x] **Step 4: Create Comprehensive Test Suite & Verify 100% (`tests/test_sentence_stream.py`)**
  - Create `tests/test_sentence_stream.py` to test sentence splitter, sentence audio streaming generator, and streaming API endpoints.
  - Run `python3 pipeline/scripts/verify.py` and verify all tests pass 100%.
  - Update `STATUS.md`, `PROGRESS_LOG.md`, `PLAN.md`, and mark `[x] DONE` line TASK-013 in `Tasks_list.md`.
