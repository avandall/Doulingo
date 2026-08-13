# DEBATE LOG
# Nhật ký phản biện — Lịch sử tự phản biện và inter-agent critique

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** Sau mỗi review session
>
> 🤖 AI APPEND vào file này sau mỗi lần review. KHÔNG xóa entries cũ — lịch sử này có giá trị.
> Đây là "second opinion trail" chứng minh AI đã suy nghĩ nghiêm túc trước khi commit.

---

## Cách đọc file này

Mỗi entry là một round phản biện. Entries được sắp xếp theo thứ tự thời gian (cũ → mới).
Đọc từ cuối file để xem review gần nhất.

---

## Debate Entries

<!-- AI bắt đầu append entries từ đây -->

---

### DEBATE-001 — [YYYY-MM-DD HH:MM]

**Iteration:** ITER-NNN
**Type:** SELF_REVIEW | ADVERSARIAL | INTER_AGENT
**Reviewer:** AI Self | Agent-B (Critic)
**Subject:** [Mô tả ngắn thứ đang review]

#### Critique Raised

**Q1: [Câu hỏi/phê bình 1]**
- **Raised by:** Self / Agent-B
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW | INFO
- **Detail:** [Mô tả chi tiết vấn đề]
- **Response:** [Câu trả lời / phản hồi]
- **Action:** 
  - [ ] FIXED — [Mô tả gì đã fix]
  - [ ] ACCEPTED_RISK — [Lý do chấp nhận rủi ro]
  - [ ] WON'T_FIX — [Lý do không fix]
  - [ ] DEFERRED — [Khi nào sẽ fix: Task-XXX]

---

**Q2: [Câu hỏi/phê bình 2]**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** [...]
- **Response:** [...]
- **Action:** [ ] FIXED

---

#### Session Summary

```
Total issues raised:   N
  CRITICAL:  0
  HIGH:      0
  MEDIUM:    N
  LOW:       N
  INFO:      N

Resolution:
  Fixed:          N
  Accepted risk:  N
  Won't fix:      N
  Deferred:       N

Review Result: APPROVED | NEEDS_REVISION | ESCALATE_TO_HUMAN
```

#### Confidence Score

```
Before review:  [Ví dụ: 7/10 — khá tự tin nhưng chưa chắc về edge cases]
After review:   [Ví dụ: 9/10 — đã address tất cả concerns quan trọng]
```

---

### DEBATE-002 — [2026-08-07 23:10]

**Iteration:** ITER-009
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-005 Stripe Event Deduplication & Plan Sync (Free -> Pro) Implementation

#### Critique Raised

**Q1: Multi-type event handling: Event object format compatibility (dict vs stripe.Event)**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** In tests, event payloads are JSON dicts, while Stripe CLI or Stripe SDK might pass `stripe.Event` objects.
- **Response:** Handled both `dict` and `stripe.Event` by safely extracting `id`, `type`, and converting `data.object` using `to_dict()`.
- **Action:** FIXED — Flexible attribute & dict accessor logic implemented in `process_webhook_event`.

**Q2: Double-processing race condition on duplicate webhooks**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** If Stripe retries webhooks in parallel, two requests might bypass `select` before insertion.
- **Response:** Primary Key on `ProcessedWebhook(id)` ensures PostgreSQL unique constraint rejects duplicate insertion cleanly.
- **Action:** FIXED — DB-level PK constraint backs up application-level check.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  8/10
After review:   10/10 — PROBE 3 and PROBE 4 integration tests pass 100%.
```

---

## Patterns & Learnings

### Lỗi thường gặp trong task này
- `stripe.Webhook.construct_event` returns `stripe.Event` structure which has nested objects (`event.data.object`). Dict fallback is necessary when unit testing mock payloads.

### Câu hỏi hiệu quả để phát hiện lỗi
- Replay 1 valid webhook 2 times: Does second invocation return HTTP 200 with status `already_processed`?

---

### DEBATE-003 — [2026-08-07 23:15]

**Iteration:** ITER-011
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-007 Submission Pack & 5 Acceptance Probes Verification

#### Critique Raised

**Q1: Evaluator manifest format (`capstone.yaml`) compatibility**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** Does `capstone.yaml` contain exact expected keys (`run`, `seed`, `test`, `base_url`, `submission_pack`) for machine evaluation?
- **Response:** Checked against Capstone PDF §11 requirements. Configured `run: uvicorn app.main:app --host 0.0.0.0 --port 3000`, `seed: python -m app.db.seed`, `test: pytest`, `base_url: http://localhost:3000`.
- **Action:** FIXED — Created valid YAML manifest.

**Q2: Completeness of 5 Acceptance Probes proof in `EVIDENCE.md`**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** Are all 5 Probes mapped to exact test cases with code snippets and execution logs?
- **Response:** Mapped PROBE 1 to `test_idempotency.py`, PROBE 2 to `test_boundary_quota.py`, PROBE 3 & 4 to `test_webhook.py`, and PROBE 5 to `test_pricing.py`. Included complete `pytest` test output.
- **Action:** FIXED — `EVIDENCE.md` formatted with matrix, code assertions, and 14/14 test pass logs.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      2
  MEDIUM:    0
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  8/10
After review:   10/10 — All 5 submission pack files validated & 14/14 tests pass GREEN.
```

---

### DEBATE-004 — [2026-08-10 14:33]

**Iteration:** ITER-001
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-000 Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite)

#### Critique Raised

**Q1: Lazy connection error with invalid/unreachable Turso Cloud URL**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** `libsql.connect()` does not throw an immediate exception on invalid DB URL; it fails lazily on the first `cursor.execute()`.
- **Response:** Added an explicit `SELECT 1` verification probe inside `get_db_connection()`. If the query fails, it catches the exception and falls back to local SQLite immediately.
- **Action:** FIXED — Connection verification probe `cursor.execute("SELECT 1")` added to `get_db_connection()`. Tested via `test_turso_fallback_on_invalid_url`.

**Q2: Cursor fetch differences between sqlite3 (Row object) and libsql (tuple object)**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** `sqlite3` uses `conn.row_factory = sqlite3.Row`, allowing key-based dict lookup `row["title"]`. `libsql_experimental` cursor returns standard row tuples.
- **Response:** Created `_fetch_all_dicts` and `_fetch_one_dict` helpers in `app/db.py` using `cursor.description` column mapping. Works uniformly on both drivers.
- **Action:** FIXED — Unified dict fetching helpers implemented and verified across all DB operations.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  8/10
After review:   10/10 — All 23 unit tests pass 100% and Tier 1 verification status is PASS.
```

---

### DEBATE-005 — [2026-08-10 14:36]

**Iteration:** ITER-002
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-001 Material Bank Data Models & Markdown Parser (`app/material_bank.py`)

#### Critique Raised

**Q1: Inconsistent Topic ID slugification across multiple DB markdown files**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** `topic_id` in `DB1`..`DB5` uses varied casing (`study` vs `STUDY`, `mobile_phones` vs `mobile-phones`, or topic titles like `Work, Economy & Social Equality Topics`).
- **Response:** Implemented `normalize_id` static method which converts underscores/spaces to hyphens, lowercases strings, and strips non-alphanumeric chars. `get_topic` uses this normalized form for lookup, so `"mobile_phones"`, `"mobile-phones"`, `"Mobile Phones"` all resolve to the same `TopicBank`.
- **Action:** FIXED — `normalize_id` and fallback lookup by `topic_name` added to `MaterialBank`.

**Q2: Multi-file topic merging without duplicate items**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** When topics appear across multiple DB files or as stubs and full sections, naive appending would create duplicate personas, questions, or vocabulary.
- **Response:** Added `_merge_topic` helper using case-insensitive set matching (`title.lower()`, `text.lower()`, `phrase.lower()`, `pattern.lower()`) to merge new unique pool items into existing topic banks.
- **Action:** FIXED — Set-based deduplication implemented in `_merge_topic`. Tested successfully with 161 unique topics parsed.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — Tier 1 verification passed 100% (ruff/mypy/bandit/pytest) and 161 topics loaded cleanly into memory.
```

---

### DEBATE-006 — [2026-08-10 14:37]

**Iteration:** ITER-003
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-002 Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`)

#### Critique Raised

**Q1: Unused import warnings flagged by Ruff in test suite**
- **Raised by:** Self / Ruff Linter
- **Severity:** LOW
- **Detail:** Pydantic models (`Persona`, `Question`, `VocabularyItem`, `GrammarPattern`) were imported into `tests/test_material_bank.py` but initially only used in type annotations.
- **Response:** Added explicit `self.assertIsInstance(obj, ModelClass)` assertions in `test_topic_structure_and_completeness` and `test_parse_custom_markdown_block`.
- **Action:** FIXED — Unused imports resolved and verified with 100% PASS on Ruff.

**Q2: Isolation of custom markdown parser tests without side effects**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** Testing custom markdown block parsing could contaminate global state or write files into `docs/`.
- **Response:** Used Python's `tempfile.TemporaryDirectory()` to create isolated ephemeral files and instantiated a separate `MaterialBank(docs_dir=tmpdir)` instance.
- **Action:** FIXED — Full isolation achieved in `test_parse_custom_markdown_block`.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      0
  MEDIUM:    1
  LOW:       1
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — 8/8 unit tests pass 100% and Tier 1 verification report status is PASS.
```

---

### DEBATE-007 — [2026-08-10 14:39]

**Iteration:** ITER-004
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-003 Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)

#### Critique Raised

**Q1: Safe fallback handling for custom scenario IDs or unknown topics**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** When users start custom scenarios or unknown topic IDs, `MaterialBank.get_topic(topic_id)` returns `None`. If `PromptFactory` does not handle `None` gracefully, `build_system_prompt` will crash with `AttributeError` or `TypeError`.
- **Response:** In `PromptFactory.sample_materials`, checked if `topic` is `None`. If so, returns a formatted default dictionary with title derived from `topic_id`, `persona=None`, and empty lists for pools. In `build_system_prompt`, optional sections are added conditionally.
- **Action:** FIXED — Safe fallback implemented and verified without any runtime exceptions.

**Q2: Boundary safety of `random.sample()` when candidate pools have fewer items than requested sample size**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** Python's `random.sample(population, k)` raises a `ValueError: Sample larger than population` if `k > len(population)`.
- **Response:** Calculated `vocab_count = min(len(vocab_candidates), random.randint(3, 4))` and similarly for questions and grammar before calling `random.sample`. If count is 0, empty list `[]` is returned.
- **Action:** FIXED — Guarded count calculations prevent `ValueError` under all pool size conditions.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — Tier 1 verification passed 100% (ruff/mypy/bandit/pytest) and PromptFactory handles all fallback paths smoothly.
```

---

### DEBATE-008 — [2026-08-10 14:40]

**Iteration:** ITER-005
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-004 Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`)

#### Critique Raised

**Q1: Flakiness in sampling diversity assertions when candidate pools are small**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** If a topic has very few vocabulary items or questions, calling `sample_materials` 5 times might randomly select the exact same items, causing `len(unique_prompts) == 1` and triggering a test flake.
- **Response:** Added an explicit pool size check before asserting diversity (`len(topic_obj.vocabulary) > 4 or len(topic_obj.questions) > 2`), dynamically picking a rich topic with ample candidate items to guarantee statistical diversity without test flakes.
- **Action:** FIXED — Dynamic rich-topic selection prevents flakiness while strictly validating sampling non-repeatability.

**Q2: System timing accuracy for sub-millisecond benchmark test**
- **Raised by:** Self
- **Severity:** LOW
- **Detail:** Low-precision timers like `time.time()` may measure 0.0ms for sub-millisecond operations or suffer from system clock adjustments.
- **Response:** Used `time.perf_counter()` for high-precision monotonic timing across 100 iterations.
- **Action:** FIXED — High-precision benchmarking confirmed average prompt assembly time is ~0.15ms (well below 5.0ms threshold).

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      0
  MEDIUM:    1
  LOW:       1
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — Tier 1 verification passed 100% (Ruff, Mypy, Bandit, Pytest) with 7/7 tests passing in 0.34s.
```

---

### DEBATE-009 — [2026-08-10 14:43]

**Iteration:** ITER-006
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-005 AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`)

#### Critique Raised

**Q1: Backward compatibility when scenario_id is not in static scenarios dict**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** If `scenario_id` is an IELTS topic from `MaterialBank` (e.g. `topic_001_education`) or a custom scenario, calling `get_scenario(scenario_id)` returns `None`. `ai_engine` would raise `ValueError("Unknown scenario")`.
- **Response:** Added fallback logic in `start_roleplay_greeting` and `process_turn`: if `get_scenario(scenario_id)` returns `None`, `ai_engine` queries `get_prompt_factory()._get_bank().get_topic(scenario_id)` to dynamically build scenario metadata.
- **Action:** FIXED — Seamless fallback between static scenarios, custom Turso DB scenarios, and MaterialBank topics implemented and tested in `test_ai_engine_material_bank_topic_fallback`.

**Q2: Parameter tuning across multiple LLM Provider Adapters (Gemini, Groq, OpenAI, Ollama)**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** Gemini API uses `presencePenalty` (camelCase) inside `generationConfig`, while Groq/OpenAI/Ollama use `presence_penalty` (snake_case).
- **Response:** Customized payload schemas per provider: `presencePenalty: 0.6` for Gemini, `presence_penalty: 0.6` for Groq, OpenAI, and Ollama options. Standardized default temperature to `0.8`.
- **Action:** FIXED — Correct provider-specific parameter keys configured and verified across all LLM adapters.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — Tier 1 verification passed 100% (Ruff, Mypy, Bandit, Pytest) with 5/5 ai_engine unit tests passing.
```

---

### DEBATE-010 — [2026-08-10 14:46]

**Iteration:** ITER-007
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-006 FastAPI Endpoints Bridge & Scenario Registry (`app/main.py` & `app/scenarios.py`)

#### Critique Raised

**Q1: Lazy import of `MaterialBank` in `app/scenarios.py` to prevent circular dependencies**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** Importing `get_material_bank` at top-level in `app/scenarios.py` could trigger circular imports if `material_bank.py` or `prompt_factory.py` imports `scenarios.py`.
- **Response:** Used inline lazy imports inside `list_scenarios()` and `get_scenario()` with exception handling guards.
- **Action:** FIXED — Lazy import pattern prevents circular imports while bridging 100+ MaterialBank topics.

**Q2: Uniform topic schema for `/api/scenarios` response across default, MaterialBank, and custom scenarios**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** MaterialBank topics are `TopicBank` model instances with different field names (`topic_id`, `topic_name`, `vocabulary`) compared to default scenario dicts (`id`, `title`, `suggested_vocabulary`).
- **Response:** Normalized `TopicBank` instances into standard scenario dictionary objects containing `id`, `title`, `category`, `icon`, `color`, `description`, `open_story_guide`, `is_custom: False`, `source: "material_bank"`, `target_levels`, and `suggested_vocabulary`.
- **Action:** FIXED — Standardized dictionary mapping ensures frontend receives identical JSON schema for all scenario sources.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — Tier 1 verification passed 100% (Ruff, Mypy, Bandit, Pytest) with 6/6 scenarios bridge unit tests passing.
```

---

### DEBATE-011 — [2026-08-10 14:49]

**Iteration:** ITER-008
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-007 End-to-End Integration Testing & Latency Benchmarks (`tests/test_integration_material_bank.py`)

#### Critique Raised

**Q1: Integration test coverage for multi-turn roleplay conversation and structured feedback schema**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** Need to ensure end-to-end flow from FastAPI client (`/api/start_scenario`, `/api/process_turn`, `/api/chat`) correctly exercises LLM engine, prompt factory sampling, and returns valid structured output fields (`ai_response`, `user_feedback`, `fluency_score`).
- **Response:** Created `tests/test_integration_material_bank.py` with full 2-turn conversation simulation accumulating history context, schema assertions on response dicts, and chat endpoint integration.
- **Action:** FIXED — All integration test cases pass 100% under `pytest`.

**Q2: Latency benchmarking overhead and stability**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** Need to measure initialization and turn processing latency without risking flaky test failures in CI environment.
- **Response:** Added latency benchmarking in `test_latency_benchmarks` printing precise timing in milliseconds and asserting sanity boundary (< 15s execution threshold).
- **Action:** FIXED — Latency benchmark test executes smoothly and reports sub-second assembly and turn response times.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9/10
After review:   10/10 — Tier 1 verification passed 100% (Ruff, Mypy, Bandit, Pytest) with 4/4 integration tests passing.
```

---

### DEBATE-012 — [2026-08-10 14:52]

**Iteration:** ITER-009
**Type:** SELF_REVIEW
**Reviewer:** AI Self
**Subject:** TASK-008 System Verification Evidence & Harness Documentation Update

#### Critique Raised

**Q1: Verification status of all 9 tasks in Tasks_list.md and full test suite execution**
- **Raised by:** Self
- **Severity:** HIGH
- **Detail:** Must verify that all tasks from TASK-000 through TASK-008 are completed, tested, verified 100% PASS via Tier 1 `verify.py`, and properly documented before declaring Phase: ALL_DONE.
- **Response:** Executed full test suite (`pytest`) and `python3 H_docs/scripts/verify.py`. All 50/50 test cases passed 100%. Ruff, Mypy, Bandit, and Pytest all returned PASS status.
- **Action:** FIXED — `VERIFICATION_REPORT.md` confirmed 100% PASS across all Tier 1 checks.

**Q2: Proof of solution completeness and Retrospective guidelines compliance**
- **Raised by:** Self
- **Severity:** MEDIUM
- **Detail:** Need to ensure `H_docs/runtime/PROOF_OF_SOLUTION.md` is generated with full task completion matrix, verification report reference, system architecture diagram, and Retrospective section according to Article 10 of `AGENT_CONSTITUTION.md`.
- **Response:** Created `H_docs/runtime/PROOF_OF_SOLUTION.md` with complete evidence summary, verification matrix, performance benchmarks, and Retrospective.
- **Action:** FIXED — `PROOF_OF_SOLUTION.md` written and validated.

#### Session Summary

```
Total issues raised:   2
  CRITICAL:  0
  HIGH:      1
  MEDIUM:    1
  LOW:       0
  INFO:      0

Resolution:
  Fixed:          2
  Accepted risk:  0
  Won't fix:      0
  Deferred:       0

Review Result: APPROVED
```

#### Confidence Score

```
Before review:  9.5/10
After review:   10/10 — All 9 tasks (TASK-000 through TASK-008) verified 100% PASS, Phase set to ALL_DONE, and PROOF_OF_SOLUTION produced.
```

---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-12 22:35
### Iteration: 28
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-000 implemented 12 schema tables, foreign key support with PRAGMA foreign_keys = ON, and comprehensive unit tests.
- [LOW] Minor stdout usage `print()` in exception handler fallback warning — Evidence: `app/db.py:35`

#### Adversarial Questions
1. [Điều gì xảy ra khi mở connection local SQLite mà quên PRAGMA foreign_keys = ON?] → [PRAGMA được bổ sung trực tiếp vào cả Turso cloud conn và local sqlite3 conn trong `get_db_connection()` ở `app/db.py:33,41`, đảm bảo FK & CASCADE luôn có hiệu lực.]
2. [Tại sao không dùng Alembic hay migration tool mà dùng CREATE TABLE IF NOT EXISTS trong init_db()?] → [Dự án ở Phase 0 Data Foundation, DDL idempotent trong `init_db()` đơn giản, không phát sinh overhead cho MVP libSQL/Turso.]
3. [Điều gì xảy ra khi xóa `content_units` chứa dữ liệu liên quan ở `band_tiers` và `sample_dialogues`?] → [Đã có `ON DELETE CASCADE` ở DDL và test case `test_task_000_schema_tables_and_fk_cascade()` kiểm tra thực tế row con bị xóa sạch.]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 07:16
### Iteration: 1
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-003 content validation and DB import tool (`scripts/admin_content_cli.py`) and tests (`tests/test_admin_content_cli.py`) implemented cleanly with full test coverage.
- [LOW] Command line interface prints info logs via print statements instead of structured logger — Evidence: `scripts/admin_content_cli.py:45`

#### Adversarial Questions
1. [Điều gì xảy ra nếu file YAML truyền vào `validate` hoặc `import` bị malformed / sai cú pháp YAML?] → [Thư viện `yaml.safe_load` sẽ ném ngoại lệ `yaml.YAMLError`, CLI catch lỗi hoặc exit với mã lỗi không bằng 0, ngăn ngừa import bẩn vào DB.]
2. [Tại sao không hỗ trợ tự động rollback khi import nhiều file batch mà một file thất bại?] → [CLI chạy ở mức đơn file/script administrative tool, mỗi transaction được bọc riêng biệt với `conn.commit()`, đảm bảo tính nguyên tử per-file.]
3. [Điều gì xảy ra khi nhập câu trả lời ngoài khoảng 5-300 từ hoặc thiếu `function_tag`?] → [CLI xuất cảnh báo (warning) rõ ràng trên stdout/stderr để reviewer điều chỉnh content trước khi commit chính thức.]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 07:25
### Iteration: 2
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-004 streaming ASR ingestion processor (`app/asr_processor.py`) and test suite (`tests/test_asr_processor.py`) implemented cleanly with sample-count based offset tracking and buffer retention.
- [LOW] Exception in `is_silence_chunk` catches broad `Exception` silently — Evidence: `app/asr_processor.py:175`

#### Adversarial Questions
1. [Điều gì xảy ra khi audio chunk được gửi lên qua WebSocket bị trễ do mạng hoặc jitter?] → [Thời gian offset được tính theo tổng số samples audio (`num_samples / sample_rate`), hoàn toàn độc lập với wall-clock time hay network latency, loại bỏ triệt để time drift.]
2. [Tại sao không cộng `cumulative_offset_sec` trực tiếp vào `asr_result.words` mà phải tạo object `WordTimestamp` mới?] → [Tránh side effect làm thay đổi object `WordTimestamp` ban đầu của ASR engine, đảm bảo immutability của result truyền vào.]
3. [Điều gì xảy ra khi `sample_width` hoặc `channels` truyền vào `StreamingSessionState` bị 0 hoặc âm?] → [Đã bổ sung guard check `bytes_per_frame <= 0` fallback về 2 bytes, ngăn chia cho 0 (ZeroDivisionError).]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 07:35
### Iteration: 33
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-005 RAG Retrieval Layer v1 (`app/retrieval.py`) and test suite (`tests/test_retrieval.py`) implemented with 4-stage fallback cascade, 30-day exposure exclusion, vector similarity calculation, and exposure logging.
- [LOW] SQLite LIKE clause for JSON array matching requires clean string escaping when matching topic tags — Evidence: `app/retrieval.py:168`

#### Adversarial Questions
1. [Điều gì xảy ra khi user query một topic không tồn tại trong DB?] → [Cascade rơi qua 4 stages và trả về kết quả fallback nới lỏng (hoặc danh sách rỗng nếu DB rỗng), log cảnh báo/lỗi rõ ràng và không crash.]
2. [Tại sao không tính cosine similarity trong SQLite bằng SQL extension mà lại tính bằng Python?] → [Chạy trên SQLite/libSQL standard fallback mode đảm bảo tính tương thích 100% trên cả in-memory SQLite test fixture và Turso production.]
3. [Điều gì xảy ra khi `user_content_exposure` bị trùng `sample_dialogue_id`?] → [Log exposure cho phép ghi nhận nhiều lần exposed ở các mốc thời gian khác nhau, chỉ lọc các ID bị exposed trong N ngày gần nhất (`datetime('now', '-30 days')`).]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 07:44
### Iteration: 34
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-006 Prompt Constructor Engine v1 (`app/prompt_constructor.py`) and test suite (`tests/test_prompt_constructor.py`) implemented with context assembly, RAG dialogue injection, anti-verbatim rules, follow-up constraints, JSON schema instructions, and sub-millisecond execution.
- [LOW] Default prompt template hardcodes character name 'Lily' when `character_name` is empty string or None — Evidence: `app/prompt_constructor.py:48`

#### Adversarial Questions
1. [Điều gì xảy ra khi RAG Retrieval Layer (TASK-005) trả về danh sách rỗng (dữ liệu rỗng)?] → [Prompt constructor tự động fallback chèn phần hướng dẫn mặc định `No specific sample dialogues retrieved...`, đảm bảo prompt không bị crash hay rỗng.]
2. [Làm thế nào để đảm bảo tốc độ tạo prompt đạt tiêu chuẩn < 5ms?] → [Toàn bộ logic là chuỗi ghép chuỗi thuần túy (string interpolation & array join), test benchmark cho thấy thời gian trung bình < 0.1ms cho 1000 lượt.]
3. [Điều gì ngăn cản AI lặp lại nguyên văn mẫu câu từ reference dialogues?] → [Cài đặt quy tắc bắt buộc ANTI-VERBATIM REPETITION ngay trong section 4 của System Prompt và yêu cầu tuân thủ JSON Schema `ai_utterance`.]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 08:08
### Iteration: 36
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-008 TTS Audio Output Streamer (`app/tts_streamer.py`) and unit tests (`tests/test_tts_streamer.py`) implemented with multi-provider support (ElevenLabs/Edge-TTS/gTTS), async streaming chunks, explicit `text_only_mode` fallback, and full exception resilience.
- [LOW] Default character identifier 'lily' is hardcoded as default argument in streamer helper functions — Evidence: `app/tts_streamer.py:113`

#### Adversarial Questions
1. [Điều gì xảy ra khi dịch vụ TTS bị lỗi kết nối hoặc hạ tầng chưa sẵn sàng?] → [Hàm catch exception và trả về `TTSStreamResult(text_only_mode=True, error_message=...)` thay vì quăng ngoại lệ ra ngoài, giúp pipeline không bị crash.]
2. [Làm thế nào để hỗ trợ phát âm thanh với độ trễ thấp < 300ms?] → [Phương thức `stream_audio_chunks` sử dụng async generator phát từng chunk MP3 bóc tách từ `stream_tts_mp3_chunks` ngay khi nhận được byte đầu tiên.]
3. [Điều gì xảy ra khi `text` truyền vào là chuỗi rỗng hoặc chỉ có khoảng trắng?] → [Streamer tự động ghi log `TTS skipped` và chuyển sang `text_only_mode=True` lập tức mà không gọi API tổng hợp giọng nói vô ích.]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 08:15
### Iteration: 37
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-009 MVP End-to-End Pipeline & API Endpoints Bridge (`app/main.py`) and test suite (`tests/test_mvp_pipeline.py`) implemented cleanly connecting ASR, RAG, Prompt Construction, Conversational LLM, and TTS Streamer into FastAPI endpoints (`/api/voice/process_turn`, `/api/voice/process_turn_multipart`, and `/api/topics`).
- [LOW] Fallback user transcript message "Hello! Let's practice English." is hardcoded when both audio and text inputs are empty.

#### Adversarial Questions
1. [Điều gì xảy ra khi client không gửi file audio mà chỉ truyền JSON payload?] → [API tự động nhận dạng `user_transcript` và bỏ qua bước ASR, sau đó tiếp tục xử lý 4 bước pipeline RAG, Prompt, LLM, TTS bình thường.]
2. [Làm thế nào để đảm bảo endpoint `/api/topics` hoạt động chính xác bất kể DB trả về dict hay SQLite Row?] → [Bổ sung logic check `isinstance(r, dict)` / `hasattr(r, "keys")` linh hoạt khi parse `content_units` và `topic_tags`.]
3. [Điều gì xảy ra nếu chuỗi JSON `conversation_history` truyền vào `process_turn_multipart` bị lỗi cú pháp?] → [Endpoint bọc `json.loads` trong khối `try...except`, nếu lỗi tự động fallback về danh sách rỗng `[]` mà không làm ngắt kết nối API.]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-13 08:24
### Iteration: 38
### Type: dual-model-review

#### Issues Found
- [INFO] TASK-010 Scoring Threshold Bootstrap & Calibration Config (`scripts/calibrate_thresholds.py`, `app/scoring/features.py`, `app/scoring/config_loader.py`) and unit tests (`tests/test_calibration.py`) implemented with feature extraction functions (WPM, pause ratio, filler density, MTLD, interpolation), active config loader, Isotonic Regression calibration script, versioned JSON anchors (`config/scoring_anchors.v0.json`, `config/scoring_anchors.v1.json`), and calibration report (`calibration_report.md`).
- [LOW] MTLD factor calculation relies on standard 0.72 TTR factor boundary — Evidence: `app/scoring/features.py:85`

#### Adversarial Questions
1. [Điều gì xảy ra nếu tập dữ liệu calibration thiếu một trong các thuộc tính đặc trưng?] → [Isotonic Regression tự động fallback về expert anchors (v0) cho đặc trưng đó, bảo vệ pipeline không bị văng ZeroDivisionError hoặc NaN.]
2. [Làm thế nào để đảm bảo `load_active_anchors()` luôn chọn đúng phiên bản config active mà không cần sửa code khi release v2, v3?] → [Config loader quét tất cả file `config/scoring_anchors.v*.json`, đọc `status` trong JSON và chọn file có `"status": "active"` hoặc có phiên bản cao nhất.]
3. [Điều gì xảy ra khi `interpolate_band()` nhận giá trị đặc trưng nằm ngoài dải anchor points?] → [Hàm tự động clamp kết quả về dải band hợp lệ [4.0, 9.0], đảm bảo không bao giờ trả về band âm hoặc > 9.0.]

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 1

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---











