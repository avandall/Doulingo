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
