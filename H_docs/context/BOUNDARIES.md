# BOUNDARIES
# Giới hạn quyền hạn — Duolingo Speak Refactor (`docs/plan.md` & `Tasks_list.md` v2)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-11
>
> ✏️ **HUMAN FILLS THIS FILE.** AI phải đọc và tuân thủ nghiêm ngặt trong suốt quá trình chạy Ralph Loop.

---

## 1. Phạm vi File (File Scope)

### AI được phép đọc và sửa (Allowed Read & Modify Scope):
```
✅ app/conversational_agent.py [Conversational Agent LLM engine & structured output parser - TASK-007]
✅ app/scoring/features.py     [Single source of truth cho các hàm trích xuất đặc trưng - TASK-010]
✅ app/scoring/tier1_realtime.py [Scoring Agent Tier 1 real-time ephemeral scorer - TASK-011]
✅ app/scoring/tier2_deep.py    [Scoring Agent Tier 2 deep scorer & LLM judge - TASK-012]
✅ app/scoring/cold_start.py   [Cold-start 3-turn diagnostic probe - TASK-014]
✅ app/user_profile_engine.py  [Dynamic user profile & EMA band smoothing engine - TASK-013]
✅ app/retrieval.py             [RAG Retrieval Layer: SQL + pgvector hybrid query & fallback cascade - TASK-005 & TASK-015]
✅ app/prompt_constructor.py   [Prompt Constructor: User profile + RAG references + rules - TASK-006]
✅ app/asr_processor.py        [Streaming ASR chunk ingestion & cumulative sample timestamps - TASK-004]
✅ app/tts_streamer.py         [TTS Audio Output Streamer - TASK-008 P0]
✅ app/persona_memory.py       [Persona identity & long-term entity memory - TASK-017]
✅ app/anti_repetition.py      [Embedding similarity anti-repetition engine - TASK-016]
✅ app/error_journal.py         [Personal error journal & interleaved practice weaver - TASK-020]
✅ app/adaptive_engine.py      [Multi-armed bandit / adaptive difficulty engine - TASK-021]
✅ app/data_quality/pii_scrubber.py [Standalone PII Scrubber module - TASK-022 P0]
✅ app/data_flywheel.py        [High-band user answer harvesting & review queue - TASK-023]
✅ app/reporting.py            [Weekly performance reporting engine - TASK-018]
✅ app/db.py                   [PostgreSQL + pgvector connection pool & schema migrations - TASK-000]
✅ scripts/**                  [Ingestion scripts, threshold calibration, CLI, calibration benchmarks]
✅ config/**                   [Scoring anchor versioned config JSONs (scoring_anchors.v{N}.json)]
✅ tests/**                    [Unit, Integration, Benchmark & Verification tests]
✅ static/**                   [Frontend UI: Hidden scoring display, Weekly reports]
```

### Tài liệu Đặc tả Kỹ thuật (Read-Only Reference Context):
```
📖 H_docs/context/6_important_tasks_solution.md [Spec chi tiết bắt buộc tuân thủ cho SPEC 0 -> SPEC 5]
📖 H_docs/context/Tasks_list.md                [Danh sách 25 tasks v2]
📖 docs/plan.md                                 [Master Architectural Blueprint]
📖 docs/tempA.md / tempB.md / tempC.md          [Template Specification References]
```

### AI KHÔNG được chạm vào (Strictly Disallowed / Read-Only):
```
❌ .env / .env.example         [Secrets & API Credentials - READ ONLY]
❌ H_docs/core/**              [Fixed Core Governance Rules - READ ONLY]
```

---

## 2. Database Permissions

```
READ:    ✅ PostgreSQL + pgvector (`content_units`, `sample_dialogues`, `user_profile`, `harvest_review_queue`, etc.)
WRITE:   ✅ Full CRUD on `content_units`, `sample_dialogues`, `user_profile`, `user_content_exposure`, `harvest_review_queue`, etc.
MIGRATE: ✅ Database DDL migrations via Alembic / Python SQL scripts
DROP:    ❌ KHÔNG BAO GIỜ DROP DATABASE HOẶC TABLES TRONG MOI TRƯỜNG PRODUCTION
```

---

## 3. External Services & APIs

```
Được gọi:
✅ PostgreSQL + pgvector
✅ Groq / Gemini / OpenAI / Claude APIs
✅ Edge TTS API
✅ LanguageTool API / spaCy models

KHÔNG được gọi:
❌ Push code lên GitHub (NGHIÊM CẤM theo chỉ thị người dùng)
❌ Commercial payment or production billing gateways
```
