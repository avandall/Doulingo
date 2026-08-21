# TECH CONTEXT
# Bối cảnh kỹ thuật — Stack, Môi trường và Kiến trúc Kỹ thuật

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-21
>
> ✏️ **HUMAN FILLS THIS FILE.** File này quy định chi tiết kỹ thuật, công nghệ, cấu trúc code và API contracts.

---

## 1. Tech Stack & Environment

### Language & Framework
```
Runtime:          Python 3.10+
Framework:        FastAPI 0.100+
Web Server:       Uvicorn
Validation:       Pydantic v2
API Protocol:     REST API (JSON) & Multipart Form Upload
LLM Providers:    Groq (llama-3.3-70b-versatile, mixtral-8x7b-32768), Gemini (gemini-2.5-flash, gemini-3.6-flash), OpenAI (gpt-4o-mini), Ollama (llama3)
```

### Database & Storage
```
Primary DB:       SQLite 3 (Local data/custom_topics.db) & Turso Cloud (libsql)
ORM / Query:      Raw SQL / sqlite3 / libsql_experimental
Tables Core:      content_units, band_tiers, sample_dialogues, hook_bank, vocabulary_lookup
```

### Testing Framework
```
Test Runner:      Pytest
Types of Tests:   Unit Tests, Integration Tests, End-to-End API Tests
Verification:     pipeline/scripts/verify.py
```

---

## 2. Cấu trúc Thư mục Dự án (Directory Structure)

```
Doulingo/
├── app/
│   ├── main.py                       # FastAPI application entry point & endpoints
│   ├── ai_engine.py                  # Core AI Engine (process_turn, start_roleplay_greeting, LEVEL_CONFIGS)
│   ├── retrieval.py                  # RAG Retrieval Layer (retrieve_dialogues, compute_band_window)
│   ├── prompt_constructor.py         # Prompt Construction Engine & System Prompt builder
│   ├── conversational_agent.py       # Structured JSON LLM response parser
│   ├── db.py                         # SQLite / Turso database connection & helpers
│   ├── material_bank.py              # In-memory material bank loader
│   └── characters.py / scenarios/    # Persona identities & scenario definitions
├── books/                            # Raw markdown books (Kiran Makkar, Simon, Fighter...)
├── output/
│   ├── extracted/                    # Extracted YAML chunks (Group B & Group C books)
│   └── chunks/                       # JSON chunk files
├── scripts/
│   ├── insert_turso.py               # YAML chunk ingestion script into SQLite/Turso DB
│   ├── generate_embeddings.py        # Vector embeddings generator script
│   └── admin_content_cli.py          # Admin CLI tool
├── data/
│   └── custom_topics.db              # Active SQLite database file
├── pipeline/                         # Ralph Loop Harness Pipeline Engine & Docs
│   ├── docs/                         # core/, context/, runtime/ docs
│   └── scripts/                      # verify.py & harness.sh
├── tests/                            # Pytest test suite
├── pyproject.toml / requirements.txt # Dependency manifest
└── main.py                           # Root entry point
```

---

## 3. Database Schema & Data Models

```sql
CREATE TABLE IF NOT EXISTS content_units (
    id              TEXT PRIMARY KEY,
    template_type   TEXT NOT NULL CHECK(template_type IN ('band_ladder','functional_bank','scenario')),
    title           TEXT NOT NULL,
    topic_tags      TEXT NOT NULL DEFAULT '[]',
    target_band_min REAL,
    target_band_max REAL,
    register        TEXT,
    source_citation TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sample_dialogues (
    id              TEXT PRIMARY KEY,
    content_unit_id TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
    band_level      REAL NOT NULL,
    turn_type       TEXT,
    function_tag    TEXT,
    ai_line         TEXT NOT NULL,
    user_model_answer TEXT NOT NULL,
    embedding       BLOB,
    created_at      TEXT DEFAULT (datetime('now'))
);
```

---

## 4. API Contracts & Specifications

### Endpoint Overview
- **`POST /api/process_turn`**: Lượt hội thoại chính trên Web UI
  - **Request Body**:
    ```json
    {
      "scenario_id": "det_childhood_memory",
      "character_id": "lily",
      "user_transcript": "I lost my memory",
      "conversation_history": [{"role": "assistant", "content": "..."}],
      "level": 9
    }
    ```
  - **Response 200 OK**:
    ```json
    {
      "ai_response": "To be honest, memory loss can be really challenging...",
      "ai_response_vi": "Thành thật mà nói...",
      "user_feedback": {
        "fluency_score": 90,
        "grammar_score": 92,
        "corrected_text": "I lost my memory.",
        "native_phrasing": "I've lost my memory."
      }
    }
    ```

---

## 5. Build, Run & Verification Commands

```bash
# Ingest dữ liệu sách từ output/extracted/ vào SQLite DB
python3 scripts/insert_turso.py output/extracted/ --sqlite data/custom_topics.db

# Khởi chạy FastAPI dev server
uvicorn app.main:app --reload --port 8000

# Chạy test suite
pytest tests/

# Chạy Harness Verification Script
python3 pipeline/scripts/verify.py
```
