# BOUNDARIES
# Giới hạn quyền hạn — Phạm vi sửa đổi cho hệ thống Tracing, Fallback, IELTS STT & Roleplay Hub

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.** AI phải tuân thủ nghiêm ngặt ranh giới dưới đây khi thực thi các tasks trong `Tasks_list.md`.

---

## 1. Phạm vi File (File Scope)

### AI được phép đọc và sửa:
```
✅ app/ai_engine.py           (Logging trace, dynamic fallback, empathy prompt, topic-shift)
✅ app/tts_service.py         (Logging trace, natural voice tuning cho Edge-TTS)
✅ app/main.py                (API logging trace, endpoints)
✅ app/scenarios/**           (Định nghĩa và phân loại topics)
✅ static/index.html          (Cấu trúc HTML Roleplay Hub, All Topics Explorer, DET exam modal)
✅ static/css/**              (Styling cho Topic Explorer, filters, badges, cards)
✅ static/js/app.js           (Logic hiển thị <11 topics, Topic Explorer modal, fix IELTS submit)
✅ static/js/speech.js        (ASR submission, buffer tracking & logging)
✅ static/audio/fillers/**    (Thư mục chứa/tạo các file audio filler ngắn)
✅ tests/**                   (Các file test kiểm thử pytest & e2e)
✅ pipeline/docs/runtime/**   (Các tài liệu runtime: STATUS.md, PLAN.md, PROGRESS_LOG.md)
✅ pyproject.toml / requirements.txt (Nếu cần thêm dependency)
```

### AI KHÔNG được chạm vào:
```
❌ .env                       (User sẽ tự thêm API keys)
❌ pipeline/docs/core/**      (Bộ hiến pháp và quy chuẩn cốt lõi)
❌ data/custom_topics.db      (Database nội dung mẫu không được xóa/drop)
```

---

## 2. API & Testing Permissions

```
- Giới hạn gọi API kiểm thử: < 10 lần gọi API thực thi thử nghiệm, không spam.
- Không hardcode API key, password hoặc raw credentials vào code.
- Mọi API key khi in ra log hoặc terminal BẮT BUỘC phải dùng helper mask_api_key() (ví dụ: gsk_...9aB).
- Giữ nguyên các API Contracts hiện tại để không làm vỡ các tính năng khác của Web/PWA:
  - POST /api/process_turn
  - POST /api/start_scenario
  - POST /api/transcribe_audio
  - POST /api/det/evaluate_speech
  - GET  /api/tts
```

---

## 3. Git Commit Rules

```
- CHỈ git commit khi 1 TASK đã hoàn thành ([x] DONE) và đã verify pass 100%.
- Commit format: [TASK-ID] <type>(<scope>): <mô tả ngắn>
- KHÔNG commit runtime docs (STATUS.md, PROGRESS_LOG.md) hay dùng format [iter-N].
```
