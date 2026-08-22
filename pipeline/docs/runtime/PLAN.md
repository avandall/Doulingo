# PLAN
# Kế hoạch thực thi — TASK-004: Instant Conversational Fillers (<100ms) & Natural TTS Fallback Tuning

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Cập nhật:** 2026-08-22 19:20

---

## Task Reference

```
Task ID:    TASK-004
Task Name:  Instant Conversational Fillers (<100ms) & Natural TTS Fallback Tuning
Phase:      Phase 4 (Audio & Latency)
Spec:       Tạo bộ filler audio cho các nhân vật trong static/audio/fillers/, tích hợp vào frontend app.js phát tức thì <100ms khi user submit, và điều chỉnh rate (+0%) / pitch (+0Hz) cho Microsoft Edge-TTS trong app/tts_service.py.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [x] Tinh chỉnh parameter `rate` (+0%) và `pitch` (+0Hz) của `CHARACTER_VOICE_MAP` trong `app/tts_service.py` cho Microsoft Edge-TTS giọng tự nhiên.
- [x] Bổ sung/xây dựng bộ âm thanh fillers trong `static/audio/fillers/` cho tất cả các nhân vật ảo (`duo`, `lily`, `oscar`, `viktor`, `chanel`, `kaelen`, `colt`, `zarina`, `scarlet`, `luigi`).
- [x] Cập nhật frontend (`static/js/audio_fx.js` và `static/js/app.js`) để kích hoạt phát audio filler ngay lập tức (<100ms latency) khi dứt lời/submit, hiển thị hiệu ứng AI is thinking... và chuyển đổi mượt sang TTS response chính khi ready.
- [x] Viết bộ test `tests/test_tts_fillers.py` và chạy `python3 pipeline/scripts/verify.py` pass 100%.

### Verification Commands
```bash
pytest tests/test_tts_fillers.py -v
python3 pipeline/scripts/verify.py
```

---

## Execution Steps

### [x] Step 1: Natural Voice Fallback Tuning & Filler Subsystem trong `app/tts_service.py` & `app/main.py`
- **Mục tiêu:**
  - Chỉnh lại `rate` thành `"+0%"` và `pitch` thành `"+0Hz"` trong `CHARACTER_VOICE_MAP` cho tất cả các nhân vật trong `app/tts_service.py`.
  - Tạo helper `get_character_filler_path(char_id: str)` hoặc `/api/fillers/{char_id}` endpoint để serve audio fillers từ `static/audio/fillers/`.
- **Files tạo/sửa:** `app/tts_service.py`, `app/main.py`
- **Exit condition:** `CHARACTER_VOICE_MAP` có rate/pitch chuẩn `"+0%"`, `"+0Hz"`, filler audio route `/api/fillers/{char_id}` hoặc static resource truy cập thành công.

### [x] Step 2: Integrated Instant Filler Playback in Frontend (`static/js/audio_fx.js` & `static/js/app.js`)
- **Mục tiêu:**
  - Nâng cấp `DuoAudioFX` trong `static/js/audio_fx.js` hỗ trợ method `playFiller(charId)` kích hoạt phát filler tức thì <100ms (qua Web Audio synth hoặc preloaded HTML5 Audio).
  - Cập nhật `static/js/app.js` tại điểm user gửi tin nhắn/process turn để lập tức gọi `playFiller(charId)` và hiển thị "AI is thinking...". Khi TTS chính ready (`playTTS`), tự động stop filler và phát audio chính mượt mà.
- **Files tạo/sửa:** `static/js/audio_fx.js`, `static/js/app.js`
- **Exit condition:** User gửi message -> filler phát ngay lập tức (<100ms) -> AI response xong -> phát TTS mượt mà.

### [x] Step 3: Test Suite `tests/test_tts_fillers.py` & Verification
- **Mục tiêu:** Viết unit test suite cho natural voice params, filler file existence/route, tts fallback capabilities, và thực thi `python3 pipeline/scripts/verify.py`.
- **Files tạo/sửa:** `tests/test_tts_fillers.py`
- **Exit condition:** `pytest tests/test_tts_fillers.py -v` và `verify.py` pass 100%.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      3
Context refresh at:   Iteration 3
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-22 | Khởi tạo plan cho TASK-004 |
| v2 | 2026-08-22 | Hoàn thành tất cả các bước Step 1-3 của TASK-004 |
