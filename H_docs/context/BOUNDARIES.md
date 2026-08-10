# BOUNDARIES
# Giới hạn quyền hạn — Duolingo Speak Dynamic Material Bank Refactor

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-10
>
> ✏️ **HUMAN FILLS THIS FILE.** AI phải đọc và tuân thủ nghiêm ngặt trong suốt quá trình chạy Ralph Loop.

---

## 1. Phạm vi File (File Scope)

### AI được phép đọc và sửa (Allowed Read & Modify Scope):
```
✅ app/material_bank.py       [Core Material Bank Parser & Indexer]
✅ app/prompt_factory.py      [Backend Prompt Factory & Dynamic Sampling Algorithm]
✅ app/ai_engine.py           [LLM Engine Prompt Integration & Parameter Tuning]
✅ app/main.py                [FastAPI Endpoints Bridge]
✅ app/scenarios.py           [Scenario Registry Integration]
✅ app/characters.py          [Persona Matching Layer]
✅ app/db.py                  [Turso Cloud SQLite & Local SQLite Persistence]
✅ tests/**                   [Unit & Integration Tests]
✅ static/index.html           [Frontend HTML Structure]
✅ static/js/app.js            [Frontend JS Application Logic]
✅ static/css/duolingo.css     [Frontend Styling]

### AI KHÔNG được chạm vào (Strictly Disallowed / Read-Only):
```
❌ docs/DB1_Personal_and_Daily_Life.md    [Ground Truth Raw Materials - READ ONLY]
❌ docs/DB2_Education_and_Career.md       [Ground Truth Raw Materials - READ ONLY]
❌ docs/DB3_Society_and_Culture.md        [Ground Truth Raw Materials - READ ONLY]
❌ docs/DB4_Science_Nature_and_Health.md   [Ground Truth Raw Materials - READ ONLY]
❌ docs/DB5_Leisure_Entertainment_and_Media.md [Ground Truth Raw Materials - READ ONLY]
❌ .env / .env.example                     [API Keys & Secrets - READ ONLY]
```

---

## 2. Database Permissions

```
READ:    ✅ Turso Cloud SQLite / Local SQLite (`data/custom_topics.db`)
WRITE:   ✅ Turso Cloud SQLite / Local SQLite (Chỉ cập nhật custom scenarios, word_dictionary, saved_vocabulary, user_stats)
MIGRATE: ✅ Python SQLite/Turso schema initialization & migration
DROP:    ❌ KHÔNG BAO GIỜ DROP CƠ SỞ DỮ LIỆU LOCAL HAY CLOUD
```

---

## 3. External Services & APIs

```
Được gọi:
✅ Turso Cloud SQLite (TURSO_DATABASE_URL / TURSO_AUTH_TOKEN)
✅ Groq LLM API (GROQ_API_KEY / GROQ_API_KEYS)
✅ Gemini LLM API (GEMINI_API_KEY / GEMINI_API_KEYS)
✅ Edge TTS API (generate_tts_mp3)

KHÔNG được gọi:
❌ Bất kỳ Production Payment Gateway hay Live Billing API nào
❌ Google Translate Web Scraping (dùng LLM Fallback translation)
```
