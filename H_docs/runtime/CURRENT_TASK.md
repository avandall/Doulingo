# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-13

---

## Task vừa hoàn thành

```
Task ID:      TASK-008
Task Name:    TTS Audio Output Streamer (`app/tts_streamer.py`)
Phase:        Phase 1 (MVP Pipeline)
Priority:     P0-Critical
Started:      2026-08-13
Completed:    2026-08-13
Status:       [x] DONE
```

---

## Task tiếp theo

```
Task ID:      TASK-009
Task Name:    MVP End-to-End Pipeline & API Endpoints Bridge (`app/main.py`)
Phase:        Phase 1 (MVP Pipeline)
Priority:     P0-Critical
Status:       [ ] TODO
```

---

## Acceptance Criteria (Đã kiểm tra pass 100%)

- [x] Sinh file audio MP3/WAV hoặc audio stream từ `ai_utterance`.
- [x] Độ trễ phát âm thanh thấp, giọng đọc tự nhiên chuẩn Anh/Mỹ.
- [x] Hỗ trợ cờ fallback `text_only_mode` rõ ràng chứ không âm thầm bỏ qua bước audio.
- [x] Viết unit test suite đầy đủ trong `tests/test_tts_streamer.py`.
- [x] Chạy `python3 H_docs/scripts/verify.py` pass 100%.

---

## Verification Commands

```bash
python3 H_docs/scripts/verify.py
pytest tests/test_tts_streamer.py
```

