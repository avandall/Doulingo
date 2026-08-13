# TECH CONTEXT
# Bối cảnh Kỹ thuật & Chi tiết Kiến trúc — Master Blueprint (`docs/plan.md` & `6_important_tasks_solution.md`)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-11 (Dựa trên `Tasks_list.md` v2 & `6_important_tasks_solution.md`)

---

## 1. Tóm tắt Kiến trúc Hệ thống (Dual-Agent System)

```
[1] User Audio Voice
        │
        ▼
[2] ASR Processor (`TASK-004` SPEC 3: Chunk Streaming + Cumulative Sample Timestamps)
        │
        ├──────────────────────────────────────────────────┐
        ▼                                                  ▼
[Tầng 1 Scorer <300ms (`TASK-011` SPEC 1)]         [Tầng 2 Deep Scorer (`TASK-012` SPEC 4)]
 (WPM, Pause Ratio, Fillers, MTLD từ SPEC 0 Config) (spaCy Grammar, GOP Pronunciation, LLM Judge)
        │                                                  │
        ▼                                                  ▼
   `difficulty_adjustment` (ephemeral)              `raw_score` 4 trục
        │                                                  │
        │                                                  ▼
        │                                          `EMA Band Smoothing Engine` (`TASK-013` SPEC 4)
        │                                          (`effective_alpha` động = word_factor * confidence_factor)
        │                                                  │
        └─────────────────────────┬────────────────────────┘
                                  ▼
[3] Retrieval Layer (`TASK-005` & `TASK-015` SPEC 2: SQL + pgvector / Hybrid RAG with Fallback Cascade)
    - Query `sample_dialogues` matching `topic_tags`, band window [band-0.5, band+1.0]
    - Exclude dialogue IDs in `user_content_exposure` (last 30 days)
    - Vector similarity search (`embedding <-> query_embedding`)
    - Fallback Cascade if strict query returns < 2 items
        │
        ▼
[4] Prompt Constructor (`TASK-006`)
    - Combine: User Profile (EMA band, recurring errors) + Retrieved Dialogues + Persona Directives
        │
        ▼
[5] Conversational Agent (`TASK-007`)
    - Structured JSON Output:
      {
        "ai_utterance": "...",
        "internal_band_signal": "rising | stable | struggling",
        "topic_tag": "accommodation",
        "difficulty_adjustment": "increase | hold | decrease"
      }
        │
        ▼
[6] TTS Audio Output Streamer (`TASK-008` P0) -> User
```

---

## 2. Quy chuẩn Kỹ thuật Cho 6 Task Rủi Ro Cao (`H_docs/context/6_important_tasks_solution.md`)

Hệ thống bắt buộc tuân thủ 6 bản spec kỹ thuật chi tiết đã được biên soạn trong [6_important_tasks_solution.md](file:///home/avandall1999/Projects/Doulingo_speak/H_docs/context/6_important_tasks_solution.md):

### SPEC 0 — `TASK-010`: Scoring Threshold Bootstrap & Calibration Config
- **Single Source of Truth:** Tất cả các hàm trích xuất đặc trưng `compute_wpm()`, `compute_pause_ratio()`, `compute_filler_density()`, `compute_mtld()` phải nằm duy nhất tại `app/scoring/features.py`. Cả script calibration `scripts/calibrate_thresholds.py` lẫn runtime Tier 1 Scorer `app/scoring/tier1_realtime.py` đều import từ module này.
- **Versioned Config:** Output xuất ra `config/scoring_anchors.v{N}.json`. Cấm hardcode anchor numbers trong code. Hệ thống đọc file config có `"status": "active"`.

### SPEC 1 — `TASK-011`: Tier 1 Real-Time Scorer (<300ms)
- **Ephemeral State:** Tier 1 chỉ đo 2 trục proxy (Fluency, Lexical) để đưa ra tín hiệu tạm thời `difficulty_adjustment` ("increase" | "hold" | "decrease"). Tier 1 **KHÔNG được gọi EMA update** vào DB `user_profile`.
- **Lexicon & Algorithm:** Filler lexicon cố định `{"um", "uh", "umm", "erm", "hmm"}`. MTLD tính 2 chiều (forward & backward) với `ttr_threshold = 0.72`.

### SPEC 2 — `TASK-005` & `TASK-015`: RAG Retrieval Layer & Fallback Cascade
- **Single-Query Hybrid RAG:** SQL lọc metadata band + topic + NOT IN exposure history 30 ngày + Vector similarity search `<->` được thực thi **trong CÙNG MỘT câu SQL**. Không lọc 2 pha bằng Python.
- **Fallback Cascade:** Nếu câu query strict trả về < 2 items, tự động chạy qua 3 cấp fallback: (1) nới exposure history 30 ngày -> 7 ngày; (2) nới dải band window; (3) bỏ topic filter. Log cảnh báo mỗi lần fallback kích hoạt.

### SPEC 3 — `TASK-004`: Streaming ASR Ingestion & Cumulative Timestamps
- **Sample-Based Offset:** `cumulative_offset_sec` được tính dựa trên số mẫu audio nhận được (`len(chunk) / sample_rate`), KHÔNG dùng wall-clock server.
- **Monotonic Timestamps:** Timestamp từng từ (`start_time`, `end_time`) luôn đơn điệu tăng qua toàn bộ session, phục vụ chính xác cho việc tính Pause Ratio.

### SPEC 4 — `TASK-013`: Dynamic User Profile & EMA Band Smoothing Engine
- **Dynamic Effective Alpha:** $\text{alpha}_{\text{effective}} = 0.2 \times \text{word\_count\_factor} \times \text{confidence\_factor}$.
- **Filtering Noise:** Nếu `word_count < 5` hoặc `avg_asr_confidence < 0.6`, `alpha_effective = 0.0` (skip update). Có floor alpha chống kẹt band khi bị skip liên tục.

### SPEC 5 — `TASK-022` & `TASK-023`: PII Scrubber & Harvest Review Queue
- **Standalone PII Scrubber (`TASK-022`):** Phát hiện PII (PERSON, GPE, ORG, phone/email) dùng spaCy NER + regex. Áp dụng chính sách REJECT-FIRST.
- **Review Queue Safety (`TASK-023`):** Mọi candidate band cao (≥7.5) dừng ở `harvest_review_queue` với `review_status='pending'`. TUYỆT ĐỐI không insert trực tiếp vào `sample_dialogues`.

---

## 3. Dynamic Database Schema (Relational + Vector DDL)

Database hợp nhất 3 loại Template (A: Progressive Band Ladder, B: Functional Bank, C: Scenario) qua bảng cha `content_units` và bảng trung tâm `sample_dialogues`.

```sql
-- Bảng cha dùng chung cho mọi Template
CREATE TABLE content_units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_type TEXT NOT NULL CHECK (template_type IN ('band_ladder','functional_bank','scenario')),
  title TEXT NOT NULL,
  topic_tags TEXT[] NOT NULL DEFAULT '{}',
  target_band_min NUMERIC(3,1),
  target_band_max NUMERIC(3,1),
  register TEXT,                       -- casual / neutral / formal
  source_citation TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  version INT DEFAULT 1
);
CREATE INDEX idx_content_units_topic ON content_units USING GIN (topic_tags);
CREATE INDEX idx_content_units_band ON content_units (target_band_min, target_band_max);

-- Template A & C: Band Tiers
CREATE TABLE band_tiers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_unit_id UUID REFERENCES content_units(id) ON DELETE CASCADE,
  band_min NUMERIC(3,1) NOT NULL,
  band_max NUMERIC(3,1) NOT NULL,
  can_do_description TEXT,
  grammar_required TEXT[],
  vocabulary_core TEXT[],
  vocabulary_stretch TEXT[],
  vocabulary_avoid TEXT[],
  sentence_length_target TEXT,
  common_errors_to_simulate TEXT
);

-- Template B: Function Details & Variants
CREATE TABLE function_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_unit_id UUID UNIQUE REFERENCES content_units(id) ON DELETE CASCADE,
  function_name TEXT NOT NULL,
  applicable_topics TEXT[]
);

CREATE TABLE function_band_variants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  function_id UUID REFERENCES function_details(id) ON DELETE CASCADE,
  band_min NUMERIC(3,1) NOT NULL,
  band_max NUMERIC(3,1) NOT NULL,
  phrases TEXT[],
  grammar_pattern TEXT
);

-- Template C: Scenarios, Branches & Hooks
CREATE TABLE scenarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_unit_id UUID UNIQUE REFERENCES content_units(id) ON DELETE CASCADE,
  setting TEXT,
  ai_role TEXT,
  user_role TEXT,
  grammar_required TEXT[],
  vocabulary_core TEXT[],
  vocabulary_stretch TEXT[]
);

CREATE TABLE scenario_branches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID REFERENCES scenarios(id) ON DELETE CASCADE,
  branch_type TEXT CHECK (branch_type IN ('low_band','high_band')),
  condition_rule TEXT,
  ai_response_style TEXT,
  example_text TEXT
);

CREATE TABLE evaluation_hooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID REFERENCES scenarios(id) ON DELETE CASCADE,
  trigger_condition TEXT,
  ai_reaction TEXT
);

-- Bảng trung tâm cho RAG Retrieval (Vector Search)
CREATE TABLE sample_dialogues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_unit_id UUID REFERENCES content_units(id) ON DELETE CASCADE,
  band_level NUMERIC(3,1) NOT NULL,
  turn_type TEXT,                      -- opening / elaborate / negotiation / closing / standalone
  function_tag TEXT,
  ai_line TEXT NOT NULL,
  user_model_answer TEXT NOT NULL,
  embedding VECTOR(1536),              -- embed(ai_line + user_model_answer + topic_tags)
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_sample_dialogues_band ON sample_dialogues (band_level);
CREATE INDEX idx_sample_dialogues_embedding ON sample_dialogues USING hnsw (embedding vector_cosine_ops);

-- Ngân hàng phụ trợ
CREATE TABLE hook_bank (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_tags TEXT[],
  text TEXT NOT NULL,
  type TEXT CHECK (type IN ('hook','anti_cliche'))
);

CREATE TABLE vocabulary_lookup (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category TEXT NOT NULL,
  tier TEXT,
  terms TEXT[]
);

-- Hồ sơ User & Tracking lặp
CREATE TABLE user_profile (
  user_id UUID PRIMARY KEY,
  band_estimate_overall NUMERIC(3,1) DEFAULT 5.0,
  band_fluency NUMERIC(3,1) DEFAULT 5.0,
  band_lexical NUMERIC(3,1) DEFAULT 5.0,
  band_grammar NUMERIC(3,1) DEFAULT 5.0,
  band_pronunciation NUMERIC(3,1) DEFAULT 5.0,
  recurring_errors JSONB DEFAULT '[]',
  entity_memory JSONB DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_content_exposure (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profile(user_id),
  sample_dialogue_id UUID REFERENCES sample_dialogues(id),
  exposed_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_exposure_user_time ON user_content_exposure (user_id, exposed_at);

-- Queue duyệt Data Flywheel (TASK-023)
CREATE TABLE harvest_review_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profile(user_id),
  ai_line TEXT NOT NULL,
  user_response TEXT NOT NULL,
  scores_json JSONB NOT NULL,
  review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected')),
  reviewed_by TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. Real-Time Single Query Hybrid RAG (`app/retrieval.py`)

```sql
SELECT sd.id, sd.ai_line, sd.user_model_answer, sd.band_level
FROM sample_dialogues sd
JOIN content_units cu ON sd.content_unit_id = cu.id
WHERE cu.topic_tags && ARRAY[:topic_tag]
  AND sd.band_level BETWEEN :band_min AND :band_max
  AND sd.id NOT IN (
    SELECT sample_dialogue_id FROM user_content_exposure
    WHERE user_id = :user_id AND exposed_at > now() - interval '30 days'
  )
ORDER BY sd.embedding <-> :query_embedding
LIMIT 4;
```

---

## 5. Môi trường & Dependencies

- Python 3.10+
- FastAPI, Pydantic v2
- PostgreSQL + pgvector (`psycopg3` / `asyncpg`)
- `spaCy` (`en_core_web_sm` / `en_core_web_trf`)
- `scikit-learn` (`IsotonicRegression` cho `scripts/calibrate_thresholds.py`)
- `sentence-transformers` / `openai` embeddings
- `pytest`, `pytest-asyncio`

---

## 6. Chiến lược Nạp Database & Triển khai (Database Ingestion Strategy)

1. **Phát triển & Integration Test (Môi trường Local / Dev):**
   - **Tách biệt hoàn toàn:** Tiến độ lập trình các task (`TASK-012` trở đi) **KHÔNG CẦN CHỜ DB Turso thật**.
   - **SQLite Decoupling:** Toàn bộ test suite (`pytest`) và chạy local sử dụng SQLite in-memory hoặc file local `content.db` (thông qua `scripts/insert_turso.py --sqlite content.db`).

2. **Quy trình Nạp Dữ liệu vào Turso DB thật (Production / Staging):**
   - Khi DB Turso thật đã được chuẩn bị xong (có `TURSO_URL` và `TURSO_TOKEN`), chạy 2 bước nạp dữ liệu:
     - **Bước 1 — Ingest YAML metadata & dialogues:**
       `python scripts/insert_turso.py output/extracted/ --turso-url $TURSO_URL --turso-token $TURSO_TOKEN`
     - **Bước 2 — Generate Vector Embeddings & Vector Index:**
       `python scripts/generate_embeddings.py --turso-url $TURSO_URL --turso-token $TURSO_TOKEN --backend local`
   - **Thời điểm kích hoạt hợp lý:** Nạp ngay khi DB thật sẵn sàng, hoặc bắt buộc hoàn tất trước khi tiến hành **E2E Integration Testing & Deployment (Phase 5)**.

