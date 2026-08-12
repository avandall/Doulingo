# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** Mỗi khi chuyển sang task mới

---

## Task đang thực hiện

```
Task ID:      TASK-004
Task Name:    Streaming ASR Ingestion & Chunk Processor (`app/asr_processor.py`)
Phase:        Phase 1 (MVP Pipeline)
Priority:     P0-Critical
Started:      2026-08-12
Status:       [ ] TODO
```

---

## Mục tiêu (Why & What)

**Tại sao cần làm task này?**
- Nhận giọng nói từ user theo từng chunk câu, giữ lại audio + word-level timestamps để làm đầu vào cho ASR transcript và Scoring Agent.

**Cụ thể cần làm gì?**
- Xây dựng `app/asr_processor.py` xử lý streaming audio input, trích xuất text transcript và mảng `word_timestamps`.

---

## Acceptance Criteria (Tiêu chí hoàn thành)

Task được coi là DONE khi:
- [ ] Xử lý audio stream theo chunk câu ngắn (khuyến nghị cắt theo VAD/silence, không cắt cứng theo thời gian cố định).
- [ ] Trả về transcript văn bản và word-level timestamps (`word`, `start_time`, `end_time`, `confidence`), timestamps đơn điệu tăng qua toàn bộ session.
- [ ] Giữ đệm audio gốc phục vụ tính điểm phát âm (Pronunciation GOP).
- [ ] Chạy `python3 H_docs/scripts/verify.py` pass 100%.

---

## Verification Commands

```bash
python3 H_docs/scripts/verify.py
pytest tests/
```
