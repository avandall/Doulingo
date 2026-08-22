# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.** Task đang sẵn sàng được giao cho vòng lặp `harness.sh`.

---

## Task đang thực hiện

```
Task ID:      TASK-004
Task Name:    Instant Conversational Fillers (<100ms) & Natural TTS Fallback Tuning
Phase:        Phase 4 (Audio & Latency)
Priority:     P1-High
Started:      2026-08-22
```

---

## Mục tiêu (Why & What)

**Tại sao cần làm task này?**
- Trong giao tiếp thực tế, người bản xứ luôn có các từ đệm câu giờ (*"Hmm...", "Let me see...", "Well..."*) khi suy nghĩ. Cần có âm thanh phát ra ngay lập tức (<100ms) để che lấp độ trễ mạng gọi API LLM/TTS, đồng thời chỉnh giọng Edge-TTS không bị méo tiếng khi fallback.

**Cụ thể cần làm gì?**
1. **Instant Filler Subsystem:**
   - Tạo/tích hợp sẵn bộ âm thanh filler ngắn (< 1s) cho từng nhân vật ảo (`lily`, `oscar`, `viktor`, `duo`, `chanel`, `kaelen`, `colt`, `zarina`, `scarlet`, `luigi`) lưu trong `static/audio/fillers/` và qua API/Web Audio cache.
   - Cập nhật `static/js/app.js`: Ngay khi user bấm gửi hoặc dứt lời, client lập tức phát 1 audio filler ngẫu nhiên phù hợp với nhân vật (<100ms response time), đồng thời hiển thị hiệu ứng "AI is thinking...".
   - Khi âm thanh chính từ `/api/tts` tải về xong, chuyển tiếp mượt mà để phát câu trả lời chính của AI.
2. **Natural Voice Fallback Tuning:**
   - Trong `app/tts_service.py`, chỉnh lại `pitch` và `rate` của `CHARACTER_VOICE_MAP` cho Edge-TTS về mức tự nhiên (`rate: "+0%"`, `pitch: "+0Hz"`).
   - Đảm bảo khi ElevenLabs hết quota, giọng Microsoft Edge-TTS phát ra trong trẻo, ấm áp và tự nhiên.

---

## Acceptance Criteria (Tiêu chí hoàn thành)

Task được coi là DONE khi:
- [ ] Khi user nói xong, audio filler phát trong vòng < 100ms, tạo cảm giác phản xạ tự nhiên.
- [ ] Luồng audio chính phát mượt mà sau khi filler kết thúc mà không bị chèn âm thanh.
- [ ] Giọng Edge-TTS fallback nghe tự nhiên, không bị trầm đục hay méo tiếng.
- [ ] Tests cho TTS Service và Filler mapping pass 100%.

---

## Verification Commands

```bash
pytest tests/test_tts_fillers.py -v
python3 pipeline/scripts/verify.py
```
