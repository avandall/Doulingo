# PROGRESS LOG
# Nhật ký tiến độ — Lịch sử từng iteration

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** Append sau mỗi iteration
>
> 🤖 AI APPEND entry mới vào cuối file này sau mỗi iteration. KHÔNG xóa entries cũ.
> Entries cũ nhất ở trên, mới nhất ở dưới.

---

## Format mỗi entry

```markdown
### [ITER-NNN] YYYY-MM-DD HH:MM — <Tên ngắn của iteration>

**Phase:** EXECUTING | REVIEWING | COMMITTING
**Step:** Step N từ PLAN.md
**Duration:** ~X phút

#### Actions Taken
1. [Hành động 1]
2. [Hành động 2]

#### Result
- **Outcome:** PASS | FAIL | PARTIAL | BLOCKED
- **Evidence:** [Link/snippet bằng chứng, output của command]

#### Issues Found
- [Vấn đề gặp phải (nếu có)]

#### Decisions Made
- [Quyết định quan trọng trong iteration này]

#### Git
- **Commit:** `[iter-N] type: description` (hash: `abc1234`)

#### Next
- **Action:** [Bước tiếp theo]
- **State:** [Trạng thái STATE.md sau entry này]
```

---

## Log Entries

<!-- AI bắt đầu thêm entries từ đây -->

### [ITER-001] — Initialization

**Phase:** ORIENT
**Step:** N/A — Initial setup

#### Actions Taken
1. Đọc H_docs/core/AGENT_CONSTITUTION.md
2. Đọc H_docs/context/PROJECT_BRIEF.md
3. Đọc H_docs/context/CURRENT_TASK.md
4. Đọc H_docs/context/BOUNDARIES.md

#### Result
- **Outcome:** PASS
- **Evidence:** Context đã được load đầy đủ

#### Decisions Made
- Bắt đầu với PLANNING phase

#### Git
- **Commit:** N/A (chưa có gì để commit)

#### Next
- **Action:** Tạo PLAN.md
- **State:** PLANNING

### [ITER-002] 2026-08-07 14:46 — Capstone PDF Analysis & Context Population

**Phase:** EXECUTING
**Step:** Read Capstone PDF Brief & Fill Context Files
**Duration:** ~5 phút

#### Actions Taken
1. Đọc và phân tích 12 trang của file `Capstone - Usage Metering & Billing Engine.pdf`.
2. Trích xuất 5 Ground Rules, 4 Concerns (Usage Metering, Quota Enforcement, Cost Calculation, Stripe Integration), Definition of Done, 5 Phases Roadmap, 5 Acceptance Probes, Submission Pack, và 6-minute Demo Flow.
3. Cập nhật chi tiết [PROJECT_BRIEF.md](file:///home/avandall1999/Projects/Capstone_usage_metering/H_docs/context/PROJECT_BRIEF.md).
4. Cập nhật [TECH_CONTEXT.md](file:///home/avandall1999/Projects/Capstone_usage_metering/H_docs/context/TECH_CONTEXT.md) với chi tiết Prisma DB Schema, API contracts, AI token pricing math (cached input, reasoning tokens), Integer cents rules, Stripe CLI setup, và 5 Probes alignment.
5. Cập nhật [Tasks_list.md](file:///home/avandall1999/Projects/Capstone_usage_metering/H_docs/context/Tasks_list.md) thay thế các task mẫu bằng 8 tasks kĩ thuật thực tế theo 5 Phases từ PDF brief.

#### Result
- **Outcome:** PASS
- **Evidence:** Đã cập nhật 3/3 context files bám sát 100% tài liệu Capstone PDF.

#### Decisions Made
- Sử dụng Node.js Express TypeScript + PostgreSQL Prisma ORM làm tech stack chính ($0 stack).
- Lưu trữ tiền tệ dưới dạng Integer Cents / Micro-cents để tránh sai số thập phân IEEE 754.
- Lên lịch 8 tasks cụ thể từ Phase 1 đến Phase 5 trong `Tasks_list.md`.

#### Next
- **Action:** Bắt đầu thực thi TASK-001 trong `Tasks_list.md`
- **State:** EXECUTING

### [ITER-003] 2026-08-07 15:02 — Refactor to 100% Python Stack per User Rule

**Phase:** EXECUTING
**Step:** Refactor Tech Specs & Backlog to Python (FastAPI, SQLAlchemy, Pytest)
**Duration:** ~5 phút

#### Actions Taken
1. Tiếp nhận quy tắc mới trong `.agents/AGENTS.md`: *"Luôn dùng Python nếu có thể."*
2. Chuyển đổi toàn bộ [TECH_CONTEXT.md](file:///home/avandall1999/Projects/Capstone_usage_metering/H_docs/context/TECH_CONTEXT.md) sang 100% Python Stack:
   - Framework: FastAPI + Uvicorn + Pydantic v2
   - ORM: SQLAlchemy 2.0 (AsyncSession) + Alembic
   - SDK: Stripe Python SDK (`stripe`)
   - Test Runner: Pytest (`pytest`, `pytest-asyncio`, `httpx`)
   - Replaced Node.js/Prisma folder structure with Python `app/` folder structure & `app/db/models.py`.
3. Cập nhật [PROJECT_BRIEF.md](file:///home/avandall1999/Projects/Capstone_usage_metering/H_docs/context/PROJECT_BRIEF.md) phản ánh Python stack & `chat_pricing_config.py`.
4. Cập nhật [Tasks_list.md](file:///home/avandall1999/Projects/Capstone_usage_metering/H_docs/context/Tasks_list.md) chuyển đổi tất cả file scopes, models, và verification commands (`pytest`, `alembic`, `uvicorn`) sang Python.

#### Result
- **Outcome:** PASS
- **Evidence:** Toàn bộ 3/3 context files đã đồng bộ 100% sang Python Stack.

#### Decisions Made
- Sử dụng **FastAPI** làm REST web framework chính.
- Sử dụng **SQLAlchemy 2.0** cho data persistence và **Alembic** cho database migrations.
- Sử dụng **Pytest** và `pytest-asyncio` cho việc thực thi 5 Acceptance Probes.

#### Next
- **Action:** Tiến hành thực thi TASK-001 (Setup FastAPI, SQLAlchemy Models, Alembic, Docker Compose)
- **State:** EXECUTING

### [ITER-004] 2026-08-07 16:00 — TASK-001 Infrastructure & DB Schema Setup

**Phase:** EXECUTING
**Step:** Step 1 to Step 4 of TASK-001
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`, `PLAN.md`.
2. Tạo `H_docs/runtime/PLAN.md` chi tiết cho TASK-001 với 4 atomic steps.
3. Cập nhật `Tasks_list.md` chuyển `TASK-001` sang `[/] IN_PROGRESS`.
4. Tạo môi trường virtualenv `venv` và file `requirements.txt` (FastAPI, SQLAlchemy 2.0, Alembic, asyncpg, psycopg2-binary, Pydantic v2, Stripe, Pytest).
5. Tạo `.env.example`, `.env`, `docker-compose.yml` (PostgreSQL 15-alpine container).
6. Tạo `app/main.py`, `app/db/base.py`, `app/db/models.py` chứa đầy đủ 6 models: `Tenant`, `Plan`, `Subscription`, `UsageEvent`, `IdempotencyRecord`, `ProcessedWebhook` và unique constraints.
7. Tạo `alembic.ini`, `app/db/migrations/env.py`, và initial migration `001_initial_schema.py`.
8. Tạo script `app/db/seed.py` khởi tạo Free (1k API calls, 100k tokens) và Pro (50k API calls, 10M tokens) plans cùng sample tenants.

#### Result
- **Outcome:** PASS
- **Evidence:** Toàn bộ code hạ tầng và database schema đã được tạo chính xác theo đặc tả Python Stack.

#### Decisions Made
- Cấu hình dual database URL: `DATABASE_URL` (asyncpg cho FastAPI async app) và `SYNC_DATABASE_URL` (psycopg2 cho Alembic migrations và sync seed script).
- Unique constraint `(tenant_id, idempotency_key)` được áp dụng trên cả `UsageEvent` và `IdempotencyRecord`.

#### Next
- **Action:** Chạy verification command `docker compose up -d`, `alembic upgrade head`, `python -m app.db.seed`, đánh dấu TASK-001 là [x] DONE và thực hiện atomic git commit.
- **State:** EXECUTING

### [ITER-005] 2026-08-07 22:25 — Verification & Completion of TASK-001

**Phase:** COMMITTING
**Step:** Verification & Seed Execution for TASK-001
**Duration:** ~5 phút

#### Actions Taken
1. Phát hiện port 5432 bị chiếm bởi local PostgreSQL engine; cập nhật port mapping trong `docker-compose.yml` thành `5433:5432` và cập nhật `DATABASE_URL`/`SYNC_DATABASE_URL` trong `.env` & `.env.example`.
2. Cấu hình `[tool.hatch.build.targets.wheel] packages = ["app"]` trong `pyproject.toml` để fix lỗi build wheel của hatchling.
3. Khởi động PostgreSQL 15 container thành công với `docker compose up -d`.
4. Thực thi thành công `uv run alembic upgrade head` (tạo 6 bảng trong DB).
5. Thực thi thành công `uv run python -m app.db.seed` (tạo 2 Plans: Free & Pro và 2 sample Tenants: `tenant_free_01` & `tenant_pro_01`).
6. Đánh dấu `TASK-001` thành `[x] DONE` trong `Tasks_list.md`, `PLAN.md` và `STATUS.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** Container running trên port 5433, Alembic migration `001_initial_schema` applied, Seed script logs confirm plans & tenants created.

#### Decisions Made
- Chuyển port host PostgreSQL Docker container sang 5433 để không ảnh hưởng đến local PostgreSQL.

#### Git
- **Commit:** `[iter-5] feat(db): verify postgres setup, alembic migration, seed data for TASK-001`

#### Next
- **Action:** Chuyển sang TASK-003: Quota Enforcement Engine (`429` & `402` Handling)
- **State:** READY

### [ITER-007] 2026-08-07 22:40 — TASK-003 Quota Enforcement Implementation & PROBE 2 Verification

**Phase:** COMMITTING
**Step:** Implementation & Integration Testing for TASK-003
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-003` Quota Enforcement Engine.
3. Tạo `app/services/quota_service.py` kiểm tra subscription status (402 past_due) và cộng dồn API calls / tokens trong period hiện tại để so sánh với plan limits (429 quota exceeded).
4. Tích hợp `QuotaService.check_and_enforce_quota()` vào endpoint `POST /generate` trong `app/api/generate.py` (thực hiện sau khi kiểm tra cached idempotency record).
5. Viết test suite `tests/test_boundary_quota.py` xác minh PROBE 2 (chặn HTTP 402 cho subscription past_due, cho phép request mốc trần 5/5 boundary, từ chối HTTP 429 cho request vượt trần 6/5, và replay cached response thành công).
6. Chạy `.venv/bin/pytest` pass 100% (5/5 tests passed).
7. Đánh dấu `TASK-002` và `TASK-003` thành `[x] DONE` trong `Tasks_list.md`, `PLAN.md` và `STATUS.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** `.venv/bin/pytest` 5 passed in 0.66s (PROBE 2 verified).

#### Decisions Made
- Idempotency key replay được ưu tiên chạy trước Quota Enforcement để đảm bảo request đã được xử lý trước đó không bị 429 khi retry.
- Subscription status không phải `active` hoặc `trialing` sẽ bị từ chối với `402 Payment Required`.

#### Git
- **Commit:** `[iter-7] feat(quota): implement QuotaService and boundary quota enforcement with PROBE 2 verification`

#### Next
- **Action:** Chuyển sang TASK-004: Stripe Webhook Signature Verification
- **State:** READY

### [ITER-008] 2026-08-07 23:05 — TASK-004 Stripe Webhook Signature Verification Implementation & PROBE 4 Verification

**Phase:** COMMITTING
**Step:** Implementation & Integration Testing for TASK-004
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`, `BOUNDARIES.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-004` Stripe Webhook Signature Verification.
3. Cập nhật `H_docs/context/Tasks_list.md` chuyển `TASK-004` sang `[/] IN_PROGRESS`.
4. Tạo `app/services/stripe_service.py` thực hiện `stripe.Webhook.construct_event()` với raw request payload bytes và secret `STRIPE_WEBHOOK_SECRET`.
5. Tạo router `POST /webhooks/stripe` trong `app/api/webhooks.py` nhận raw bytes và header `stripe-signature`, tích hợp vào `app/main.py`.
6. Bổ sung `StripeService` vào `app/services/__init__.py`.
7. Viết test suite `tests/test_webhook.py` kiểm tra signature verification (valid signature returns 200 OK, missing/forged signature returns 400 Bad Request cho PROBE 4).
8. Chạy `.venv/bin/pytest` pass 100% (8/8 tests passed).
9. Đánh dấu `TASK-004` thành `[x] DONE` trong `Tasks_list.md`, `PLAN.md` và `STATUS.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** `.venv/bin/pytest` 8 passed in 1.27s (PROBE 4 verified).

#### Decisions Made
- Raw payload bytes được đọc trực tiếp từ `await request.body()` trước khi thực hiện verify signature nhằm giữ nguyên tính toàn vẹn của dữ liệu webhook.
- Signature hợp lệ hoặc signature giả mạo/thiếu được phân loại rõ ràng: valid -> 200 OK, invalid/missing -> 400 Bad Request.

#### Git
- **Commit:** `[iter-8] feat(webhook): implement Stripe Webhook Signature Verification with PROBE 4 test suite`

#### Next
- **Action:** Chuyển sang TASK-005: Stripe Event Deduplication & Plan Sync (Free -> Pro)
- **State:** READY

### [ITER-009] 2026-08-07 23:10 — TASK-005 Stripe Event Deduplication & Plan Sync Implementation & PROBE 3 Verification

**Phase:** COMMITTING
**Step:** Implementation & Integration Testing for TASK-005
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`, `BOUNDARIES.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-005` Stripe Event Deduplication & Plan Sync (Free -> Pro).
3. Cập nhật `H_docs/context/Tasks_list.md` chuyển `TASK-005` sang `[/] IN_PROGRESS`.
4. Mở rộng `app/services/stripe_service.py` với method `process_webhook_event`:
   - Lớp 1: Deduplication check bằng `ProcessedWebhook(id=event_id)` DB query. Đã xử lý -> Trả về HTTP 200 with status `already_processed`.
   - Lớp 2: Event handler cho `checkout.session.completed` (nâng cấp Subscription tenant sang gói `pro`, status `active`).
   - Lớp 3: Event handler cho `customer.subscription.updated` & `deleted` (đồng bộ trạng thái `active`, `past_due`, `canceled`).
   - Lớp 4: Lưu `ProcessedWebhook` record và commit transaction.
5. Cập nhật router `POST /webhooks/stripe` trong `app/api/webhooks.py` inject `db: AsyncSession` và gọi `StripeService.process_webhook_event`.
6. Cập nhật `tests/test_webhook.py` với 4 test cases async:
   - `test_stripe_webhook_valid_signature_and_deduplication` (replaying event 2 lần).
   - `test_stripe_webhook_invalid_signature_probe4` (forged signature 400).
   - `test_stripe_webhook_missing_signature` (missing header 400).
   - `test_stripe_webhook_checkout_completed_upgrades_free_to_pro_probe3` (PROBE 3: 1,000/1,000 free quota blocked with 429 -> webhook upgrade to pro -> quota expanded to 50,000 -> request 200 OK).
7. Chạy `.venv/bin/pytest` pass 100% (9/9 tests passed).
8. Cập nhật `DEBATE_LOG.md` (DEBATE-002), `iter_009.md`, `Tasks_list.md` (`TASK-005` [x] DONE), và `STATUS.md` (`Phase: IN_PROGRESS`).

#### Result
- **Outcome:** PASS
- **Evidence:** `.venv/bin/pytest` 9 passed in 2.98s (PROBE 3 & PROBE 4 verified).

#### Decisions Made
- Primary Key unique constraint trên `ProcessedWebhook(id)` ngăn ngừa race conditions khi Stripe gửi webhooks lặp lại đồng thời.
- `checkout.session.completed` liên kết tenant qua `client_reference_id` hoặc `metadata.tenant_id`.

#### Git
- **Commit:** `[iter-9] feat(webhook): implement Stripe Event Deduplication & Plan Sync (Free -> Pro) with PROBE 3 & PROBE 4 verification`

#### Next
- **Action:** Chuyển sang TASK-006: AI Token Pricing Math & Rollup (`GET /usage`)
- **State:** READY

### [ITER-010] 2026-08-07 23:14 — TASK-006 AI Token Pricing Math & Rollup Implementation & PROBE 5 Verification

**Phase:** COMMITTING
**Step:** Implementation & Unit/Integration Testing for TASK-006
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`, `BOUNDARIES.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-006` AI Token Pricing Math & Rollup (`GET /usage`).
3. Cập nhật `H_docs/context/Tasks_list.md` chuyển `TASK-006` sang `[/] IN_PROGRESS`.
4. Tạo `app/config/chat_pricing_config.py` chứa định nghĩa hằng số giá token AI bằng integer micro-cents (input $2.50/1M = 250 micro-cents/token, cached_input $1.25/1M = 125 micro-cents/token, output $10.00/1M = 1,000 micro-cents/token, reasoning $10.00/1M = 1,000 micro-cents/token) và các hàm `calculate_token_cost_micro_cents` & `calculate_token_cost_cents`.
5. Tạo `app/services/cost_service.py` xây dựng `CostService` thực hiện SQL rollup tổng hợp usage theo tháng (`api_calls`, `ai_tokens` breakdown, `cost` in cents & formatted currency).
6. Tạo `app/api/usage.py` endpoint `GET /usage` nhận `X-Tenant-ID` header và `month` query parameter, đăng ký router trong `app/main.py`.
7. Cập nhật `app/api/generate.py` sử dụng `calculate_token_cost_cents` từ `app.config.chat_pricing_config`.
8. Tạo `tests/test_pricing.py` với 5 test cases unit & integration (xác minh PROBE 5: pricing math, ceiling rounding, GET /usage JSON rollup, POST /generate rollup sync, 400 & 404 error cases).
9. Chạy `.venv/bin/pytest` pass 100% (14/14 tests passed).
10. Cập nhật `Tasks_list.md` (`TASK-006` [x] DONE) và `STATUS.md` (`Phase: IN_PROGRESS`).

#### Result
- **Outcome:** PASS
- **Evidence:** `.venv/bin/pytest` 14 passed in 4.45s (PROBE 5 verified).

#### Decisions Made
- Tất cả tính toán tiền tệ sử dụng Integer Micro-Cents ($1 = 100,000,000 micro-cents) để tránh sai số floating point IEEE 754.
- Reasoning tokens được tính giá như output tokens ($10.00 / 1M).
- Cached input tokens được giảm giá 50% ($1.25 / 1M).
- Format tiền tệ `cost.formatted` hiển thị dạng chuỗi chuẩn `$X.XX`.

#### Git
- **Commit:** `[iter-10] feat(pricing): implement AI Token Pricing Math & Rollup (GET /usage) with PROBE 5 verification`

#### Next
- **Action:** Chuyển sang TASK-007: Submission Pack & 5 Acceptance Probes Verification
- **State:** READY

### [ITER-011] 2026-08-07 23:15 — TASK-007 Submission Pack & 5 Acceptance Probes Verification

**Phase:** COMMITTING
**Step:** Submission Pack Creation & Acceptance Probes Verification for TASK-007
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`, `BOUNDARIES.md`.
2. Tạo `H_docs/runtime/PLAN.md` cho `TASK-007` Submission Pack & 5 Acceptance Probes Verification.
3. Cập nhật `H_docs/context/Tasks_list.md` chuyển `TASK-007` sang `[/] IN_PROGRESS`.
4. Tạo `capstone.yaml` chứa thông tin evaluator manifest, stack metadata, và các lệnh runner (`run`, `seed`, `test`, `base_url`).
5. Tạo `BUILDLOG.md` tổng hợp toàn bộ lịch sử xây dựng, quyết định kỹ thuật ($0 Stack, micro-cents, unique DB constraints), và quy trình AI-assisted harness.
6. Chạy `.venv/bin/pytest -v` và tạo `EVIDENCE.md` trình bày ma trận 5 Acceptance Probes (PROBE 1 - PROBE 5), code assertions, và log thực thi 14/14 passed.
7. Tạo `README.md` với sơ đồ kiến trúc ASCII, bảng API endpoints spec, hướng dẫn cài đặt local, và summary 5 probes.
8. Tạo `iter_011.md` và append `DEBATE-003` vào `DEBATE_LOG.md`.
9. Cập nhật `Tasks_list.md` (`TASK-007` [x] DONE) và `STATUS.md` (`Phase: IN_PROGRESS`).

#### Result
- **Outcome:** PASS
- **Evidence:** `.venv/bin/pytest` 14 passed in 2.20s; 5/5 submission pack files exist (`README.md`, `capstone.yaml`, `EVIDENCE.md`, `BUILDLOG.md`, `.env.example`).

#### Decisions Made
- `capstone.yaml` cấu hình cổng `3000` và base_url `http://localhost:3000`.
- Tất cả 5 Probes được liên kết trực tiếp với các file test unit/integration trong Pytest test suite.

#### Git
- **Commit:** `[iter-11] feat(submission): create capstone.yaml, EVIDENCE.md, BUILDLOG.md, README.md submission pack`

#### Next
- **Action:** Chuyển sang TASK-008: Demo Script Rehearsal & Failure Scenario Verification
- **State:** READY

### [ITER-012] 2026-08-07 23:16 — TASK-008 Demo Script Rehearsal & Failure Scenario Verification

**Phase:** COMMITTING
**Step:** 6-Step Demo Rehearsal Implementation & Full Suite Verification for TASK-008
**Duration:** ~5 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `Tasks_list.md`, `STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` cho `TASK-008` Demo Script Rehearsal & Failure Scenario Verification.
3. Cập nhật `H_docs/context/Tasks_list.md` chuyển `TASK-008` sang `[/] IN_PROGRESS`.
4. Tạo `app/db/demo_seed.py` seed dữ liệu tenant `tenant_demo_01` (Free plan) đã prefilled 999 usage events sẵn sàng cho demo mốc 1,000 boundary và 1,001 HTTP 429 limit.
5. Tạo `tests/test_demo_rehearsal.py` tự động hóa và kiểm tra 6 bước demo (§13 Capstone PDF):
   - Step 1: Quota boundary & HTTP 429 Too Many Requests.
   - Step 2: Idempotency retry with same key (No double counting).
   - Step 3: Stripe Test Checkout Webhook (Free -> Pro upgrade).
   - Step 4: Forged webhook 400 Bad Request & Duplicate webhook replay `already_processed`.
   - Step 5: `GET /usage` rollup numbers & AI pricing math verification.
   - Step 6: Final stability assertion.
6. Tạo executable bash script `demo-rehearsal.sh` khởi chạy demo rehearsal flow.
7. Chạy `./demo-rehearsal.sh` và `.venv/bin/pytest` pass 100% (15/15 tests passed).
8. Cập nhật `Tasks_list.md` (`TASK-008` [x] DONE) và `STATUS.md` (`Phase: ALL_DONE`).
9. Tạo `H_docs/runtime/PROOF_OF_SOLUTION.md` tổng kết minh chứng hoàn tất toàn bộ 8/8 tasks dự án.

#### Result
- **Outcome:** PASS
- **Evidence:** `./demo-rehearsal.sh` 6/6 demo steps verified; `.venv/bin/pytest` 15 passed in 4.95s.

#### Decisions Made
- `demo_seed.py` prefill 999 events giúp kịch bản demo diễn ra ngay lập tức tại boundary chỉ sau 1 API call duy nhất.
- `demo-rehearsal.sh` tích hợp pytest rehearsal flow mang tính tự động hóa và tái hiện 100% kịch bản demo 6 phút của Capstone Brief.

#### Git
- **Commit:** `[iter-12] feat(demo): implement demo_seed.py, test_demo_rehearsal.py and demo-rehearsal.sh for 6-minute presentation`

---

### Iteration 014 — 2026-08-10 14:33

#### Task Reference
- **Task ID:** TASK-000
- **Task Name:** Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite)
- **Phase:** Phase 0 (Cloud Infrastructure & Database)

#### Goal
Replace local file SQLite DB in `app/db.py` with Turso Cloud SQLite (`libsql_experimental`) support using environment variables `TURSO_DATABASE_URL` & `TURSO_AUTH_TOKEN`, with seamless local SQLite fallback when credentials are absent or unreachable.

#### Actions Taken
1. Updated `requirements.txt` to include `libsql-experimental>=0.0.55`.
2. Refactored `app/db.py` with `get_db_connection()`, fallback handling, connection probe (`SELECT 1`), and unified dictionary fetching helpers `_fetch_all_dicts` and `_fetch_one_dict`.
3. Created table schemas `custom_scenarios`, `word_dictionary`, `saved_vocabulary`, and `user_stats`.
4. Authored unit test suite `tests/test_db_turso.py` covering table creation, custom scenario CRUD, vocabulary dictionary caching, user XP stats, and invalid URL fallback.
5. Executed Tier 1 quality checks via `python3 H_docs/scripts/verify.py` (23/23 tests pass 100%).
6. Conducted Tier 2 Cognitive Review (`git diff` inspection, DEBATE-004 entry appended to `DEBATE_LOG.md`).
7. Updated `Tasks_list.md` (`TASK-000` [x] DONE) and `STATUS.md` (`Phase: IN_PROGRESS`).

#### Result
- **Outcome:** PASS
- **Evidence:** `python3 H_docs/scripts/verify.py` report status PASS (23 passed in 7.13s).

#### Decisions Made
- Added `SELECT 1` connection probe in `get_db_connection()` to catch lazy connection errors instantly when Turso URLs are invalid, forcing clean fallback to local SQLite.
- Used `cursor.description` column zip mapping to standard dicts to unify data structures across `sqlite3.Row` and `libsql_experimental` tuple results.

#### Git
- **Commit:** `[iter-14] feat(db): migrate app/db.py to Turso Cloud SQLite with local fallback & add unit tests`

#### Next
- **Action:** Start TASK-001: Material Bank Data Models & Markdown Parser (`app/material_bank.py`).
- **State:** IN_PROGRESS

---

### Iteration 015 — 2026-08-10 14:36

#### Task Reference
- **Task ID:** TASK-001
- **Task Name:** Material Bank Data Models & Markdown Parser (`app/material_bank.py`)
- **Phase:** Phase 1 (Ingestion & Models)

#### Goal
Create `app/material_bank.py` module containing Pydantic models (`Persona`, `Question`, `VocabularyItem`, `GrammarPattern`, `TopicBank`) and class `MaterialBank` to automatically parse all 5 academic IELTS database markdown files (`DB1_*.md` to `DB5_*.md`) into memory for sub-5ms retrieval.

#### Actions Taken
1. Created `app/material_bank.py` with Pydantic v2 schemas (`Persona`, `Question`, `VocabularyItem`, `GrammarPattern`, `TopicBank`).
2. Implemented `MaterialBank` class with robust AST/regex parsing for Persona Pool, Question Pool (by Band), Vocabulary Pool (by Band), and Grammar Patterns.
3. Implemented `normalize_id` for case-insensitive and slug-insensitive topic lookups (`get_topic`) and `_merge_topic` for set-based deduplication across multi-file topic blocks.
4. Executed Tier 1 quality checks via `python3 H_docs/scripts/verify.py` (Ruff, Mypy, Bandit, Pytest passed 100%).
5. Conducted Tier 2 Cognitive Review (`git diff` inspection, DEBATE-005 entry appended to `DEBATE_LOG.md`).
6. Updated `Tasks_list.md` (`TASK-001` [x] DONE) and `STATUS.md` (`Phase: IN_PROGRESS`).

#### Result
- **Outcome:** PASS
- **Evidence:** `python3 H_docs/scripts/verify.py` report status PASS. 161 unique academic IELTS topic banks parsed and indexed into memory.

#### Decisions Made
- Added `normalize_id` static method to convert underscores/spaces to hyphens and lowercase topic IDs, handling varied slug formats seamlessly.
- Built set-based deduplication in `_merge_topic` to gracefully merge topic stubs and full content blocks across multiple markdown files without repeating personas, questions, or vocabulary.

#### Git
- **Commit:** `[iter-15] feat(material-bank): add material bank Pydantic models & markdown parser in app/material_bank.py`

#### Next
- **Action:** Start TASK-002: Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`).
- **State:** IN_PROGRESS

---

### Iteration 016 — 2026-08-10 14:37

#### Task Reference
- **Task ID:** TASK-002
- **Task Name:** Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`)
- **Phase:** Phase 1 (Ingestion & Models)

#### Goal
Write comprehensive unit test suite in `tests/test_material_bank.py` to verify loading, parsing, schema integrity, case-insensitive indexing, listing, and singleton behavior of `MaterialBank`.

#### Actions Taken
1. Created `tests/test_material_bank.py` with 8 unit test cases covering real markdown file loading, schema validation, case/slug-insensitive lookup, non-existent topic handling, summary listing, singleton pattern, and custom markdown block parsing.
2. Resolved Ruff unused import warnings by adding explicit `assertIsInstance` checks for Pydantic models (`Persona`, `Question`, `VocabularyItem`, `GrammarPattern`).
3. Ran Tier 1 verification via `python3 H_docs/scripts/verify.py` — 100% PASS across Ruff, Mypy, Bandit, and Pytest.
4. Conducted Tier 2 Cognitive Review (DEBATE-006 entry appended to `DEBATE_LOG.md`, APPROVED).
5. Updated `Tasks_list.md` (`TASK-002` [x] DONE) and `STATUS.md` (`Phase: IN_PROGRESS`).

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest tests/test_material_bank.py` (8/8 passed in 1.09s), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Used `tempfile.TemporaryDirectory()` for custom markdown test cases to ensure complete test isolation without mutating production files.
- Used explicit `assertIsInstance` checks for all schema types to ensure zero dead code or unused imports under Ruff linting rules.

#### Git
- **Commit:** `[iter-16] test(material-bank): add unit tests for Material Bank parser & indexer`

#### Next
- **Action:** Start TASK-003: Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`).
- **State:** IN_PROGRESS

---

### Iteration 017 — 2026-08-10 14:39

#### Task Reference
- **Task ID:** TASK-003
- **Task Name:** Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)
- **Phase:** Phase 2 (Sampling & Prompt Factory)

#### Goal
Implement `app/prompt_factory.py` with `PromptFactory` class to perform dynamic sampling of Personas, Vocabulary, Questions, and Grammar patterns from `MaterialBank` and build structured System Prompts.

#### Actions Taken
1. Created `app/prompt_factory.py` implementing `PromptFactory` class and `get_prompt_factory()` singleton factory.
2. Implemented `sample_materials(topic_id, level)` sampling 1 Persona, 3-4 Vocab items, 1-2 Questions, and 1-2 Grammar patterns according to target level with safe fallbacks for missing/unknown topics.
3. Implemented `build_system_prompt(topic_id, level, character_id, user_history)` assembling full structured prompts combining AI Character system prompt and sampled MaterialBank components.
4. Executed Tier 1 verification via `python3 H_docs/scripts/verify.py` — 100% PASS (Ruff, Mypy, Bandit, Pytest).
5. Performed Tier 2 Cognitive Review (DEBATE-007 appended to `DEBATE_LOG.md`, APPROVED).
6. Updated `CURRENT_TASK.md`, `PLAN.md`, `Tasks_list.md` (TASK-003 [x] DONE), `STATUS.md` (`Phase: IN_PROGRESS`), and created `iter_004.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** `python3 H_docs/scripts/verify.py` status PASS (100% clean check).

#### Decisions Made
- Implemented boundary guard `min(len(candidates), count)` before calling `random.sample` to prevent `ValueError` on small pool sizes.
- Added graceful fallback handling for unknown topic IDs (e.g. custom user scenarios) so `build_system_prompt` never raises runtime exceptions.

#### Git
- **Commit:** `[iter-17] feat(prompt-factory): implement Backend Prompt Factory & Dynamic Sampling Engine`

#### Next
- **Action:** Start TASK-004: Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`).
- **State:** IN_PROGRESS












