# BOUNDARIES
# Giới hạn quyền hạn — Những gì AI được và không được làm

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-21
>
> ✏️ **HUMAN FILLS THIS FILE.** AI phải đọc và tuân thủ nghiêm ngặt.
>
> ⚠️ **CRITICAL:** Đây là "hợp đồng" ranh giới giữa bạn và AI. AI sẽ dừng lại và hỏi nếu thao tác vượt quá scope.

---

## 1. Phạm vi File (File Scope)

### AI được phép đọc và sửa:
```
✅ app/** (Các file backend FastAPI, AI engine, RAG retrieval, prompt constructors)
✅ scripts/** (Các script ingest dữ liệu, CLI tools, benchmarks)
✅ data/custom_topics.db (Database SQLite local)
✅ tests/** (Test suite cho pipeline)
✅ pipeline/docs/context/** (Tài liệu ngữ cảnh)
✅ pipeline/docs/runtime/** (Tài liệu lưu trạng thái runtime)
```

### AI KHÔNG được chạm vào:
```
❌ .env (Không bao giờ xóa hay lộ API keys)
❌ pipeline/docs/core/** (Bộ quy chuẩn cố định không được sửa)
❌ .git/**
```

---

## 2. Database Permissions

```
READ:    ✅ Cho phép đọc database SQLite local (data/custom_topics.db)
WRITE:   ✅ Cho phép INSERT / UPDATE dữ liệu sample_dialogues & content_units
MIGRATE: ✅ Cho phép tạo tables bằng DDL tương thích SQLite
DROP:    ❌ KHÔNG BAO GIỜ được phép DROP DB

Môi trường:
  - Local DB:    ✅ Quyền đọc/ghi/insert trên DB local (data/custom_topics.db)
  - Staging DB:  NONE
  - Production:  ❌ Không có access
```

---

## 3. External Services & APIs

```
Được phép gọi:
✅ Groq API (https://api.groq.com)
✅ Gemini API (https://generativelanguage.googleapis.com)
✅ OpenAI API (https://api.openai.com)
✅ Ollama Local (http://localhost:11434)

KHÔNG được phép gọi:
❌ Dịch vụ trả phí không chỉ định
```

---

## 4. Quyền Kiến trúc (Architecture Decisions)

### AI có thể tự quyết định:
```
✅ Cấu trúc logic xử lý RAG & Fallback trong app/ai_engine.py
✅ Naming conventions theo CODE_STANDARDS.md
✅ Viết thêm unit tests & integration tests trong tests/
```

### Phải hỏi human trước:
```
❓ Thêm dependencies mới ngoài requirements.txt / pyproject.toml
❓ Xóa các file source code hiện có
```

### KHÔNG được làm dù có lý do:
```
❌ Hardcode credentials, API keys vào source code
❌ Sửa đổi files trong pipeline/docs/core/
❌ Xóa bớt unit tests sẵn có
```

---

## 5. Rollback & Git Permissions

```
AI được phép:
✅ git reset --hard HEAD (khi test thất bại cần rollback)
✅ Commit theo đúng quy chuẩn: [TASK-ID] <type>(<scope>): <mô tả ngắn task đã hoàn thành> — CHỈ khi task [x] DONE
```

---

## 6. Escalation Path

Khi AI gặp tình huống chưa rõ ràng hoặc nằm ngoài ranh giới:
```
1. DỪNG LẠI ngay lập tức.
2. Tạo pipeline/docs/runtime/BLOCKED.md mô tả chi tiết lý do.
3. Đặt câu hỏi cụ thể cho Human.
```
