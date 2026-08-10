# PROGRESS LOG
# Nhật ký tiến độ — Lịch sử thực thi tự động

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** Sau mỗi atomic step
>
> 🤖 AI APPEND vào file này sau mỗi lần hoàn thành 1 step/task. KHÔNG sửa/xóa entries cũ.
> File này là bằng chứng về quá trình làm việc của AI qua từng iteration.

---

## Lịch sử thực thi

<!-- AI append new entries to the bottom of this section -->

---

### [ITER-018] 2026-08-10 14:41 — TASK-004 Unit Tests for Prompt Factory & Sampling Diversity

**Phase:** COMMITTING
**Step:** Implementation & Tier 1/2 Verification of TASK-004
**Duration:** ~3 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `H_docs/context/Tasks_list.md`, và `H_docs/runtime/STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-004` (Unit Tests for Prompt Factory & Sampling Diversity).
3. Tạo file unit test suite `tests/test_prompt_factory.py` kiểm tra:
   - Singleton pattern & `get_prompt_factory` getter.
   - `sample_materials` dictionary keys, types, and safe fallback for unknown topic IDs.
   - `build_system_prompt` structure, character traits integration (Lily), target band level, and fallback handling.
   - Latency benchmark test: 100 runs of prompt assembly verifying average latency < 5ms (actual: ~0.15ms).
   - Sampling diversity test: 5 consecutive calls on rich topics proving non-repetitive sampling.
4. Chạy `pytest tests/test_prompt_factory.py` pass 100% (7/7 tests passed in 0.34s).
5. Executed Tier 1 verification via `python3 H_docs/scripts/verify.py` — Status PASS (100% clean check on Ruff, Mypy, Bandit, Pytest).
6. Performed Tier 2 Cognitive Review (`git diff` inspection, DEBATE-008 appended to `DEBATE_LOG.md`, APPROVED).
7. Created `iter_005.md` in `H_docs/runtime/ITERATIONS/`.
8. Updated `H_docs/context/Tasks_list.md` (`TASK-004` [x] DONE) and `H_docs/runtime/STATUS.md` (`Phase: IN_PROGRESS`, next task `TASK-005`).

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest tests/test_prompt_factory.py` (7 passed in 0.34s), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Used `time.perf_counter()` for high-precision latency measurement in prompt assembly benchmarking (< 5ms threshold).
- Implemented dynamic rich-topic selection for diversity assertions to prevent test flakiness while strictly verifying non-repetitive sampling.

#### Git
- **Commit:** `[iter-18] test(prompt-factory): add unit tests for Prompt Factory & sampling diversity`

#### Next
- **Action:** Start TASK-005: AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`).
- **State:** IN_PROGRESS

---

### [ITER-019] 2026-08-10 14:44 — TASK-005 AI Engine Prompt Integration & Parameter Tuning

**Phase:** COMMITTING
**Step:** Implementation & Tier 1/2 Verification of TASK-005
**Duration:** ~3 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `H_docs/context/Tasks_list.md`, và `H_docs/runtime/STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-005` (AI Engine Prompt Integration & Parameter Tuning).
3. Refactor `app/ai_engine.py`:
   - Import `get_prompt_factory` và nạp System Prompt động từ `PromptFactory` vào `start_roleplay_greeting` và `_build_token_efficient_prompt`.
   - Bổ sung fallback dynamic topic lookup cho `MaterialBank` topics nếu không tìm thấy trong static scenarios list.
   - Thiết lập parameter tuning: `temperature: 0.8` và `presence_penalty: 0.6` (hoặc `presencePenalty: 0.6` cho Gemini) trên tất cả provider call payloads (Groq, Gemini, OpenAI, Ollama).
4. Thêm các unit test cases trong `tests/test_ai_engine.py`:
   - `test_ai_engine_material_bank_topic_fallback`
   - `test_ai_engine_prompt_factory_integration`
5. Chạy `pytest tests/test_ai_engine.py` pass 100% (5/5 tests passed).
6. Thực thi Tier 1 verification via `python3 H_docs/scripts/verify.py` — Status PASS (100% clean check on Ruff, Mypy, Bandit, Pytest).
7. Thực hiện Tier 2 Cognitive Review (`git diff` inspection, DEBATE-009 appended to `DEBATE_LOG.md`, APPROVED).
8. Cập nhật `H_docs/context/Tasks_list.md` (`TASK-005` [x] DONE) và `H_docs/runtime/STATUS.md` (`Phase: IN_PROGRESS`, next task `TASK-006`).

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest tests/test_ai_engine.py` (5 passed), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Handled provider-specific key names (`presencePenalty` for Gemini, `presence_penalty` for Groq/OpenAI/Ollama).
- Maintained 100% backward compatibility for custom scenarios and local topics with graceful fallback.

#### Git
- **Commit:** `[iter-19] feat(ai-engine): integrate PromptFactory and tune temperature/presence_penalty`

#### Next
- **Action:** Start TASK-006: FastAPI Endpoints Bridge & Scenario Registry (`app/main.py`).
- **State:** IN_PROGRESS

---

### [ITER-020] 2026-08-10 14:47 — TASK-006 FastAPI Endpoints Bridge & Scenario Registry

**Phase:** COMMITTING
**Step:** Implementation & Tier 1/2 Verification of TASK-006
**Duration:** ~3 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `H_docs/context/Tasks_list.md`, và `H_docs/runtime/STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-006` (FastAPI Endpoints Bridge & Scenario Registry) và cập nhật status `TASK-006` thành `[/] IN_PROGRESS` trong `Tasks_list.md`.
3. Refactor `app/scenarios.py`:
   - Cập nhật `list_scenarios()` và `get_scenario(scenario_id)` để tự động nạp toàn bộ 100+ topics từ `MaterialBank` (`get_material_bank()`).
   - Đảm bảo tương thích ngược 100% với `DEFAULT_SCENARIOS` và `get_custom_scenarios()` từ Turso Cloud Database.
4. Tạo unit test suite `tests/test_scenarios_bridge.py`:
   - `test_list_scenarios_includes_material_bank`
   - `test_api_list_scenarios_endpoint`
   - `test_api_get_scenario_by_id`
   - `test_api_get_scenario_not_found`
   - `test_start_scenario_with_material_bank_topic`
   - `test_process_turn_with_material_bank_topic`
5. Chạy `pytest tests/test_scenarios_bridge.py` pass 100% (6/6 tests passed in 3.31s).
6. Thực thi Tier 1 verification via `python3 H_docs/scripts/verify.py` — Sửa lỗi unused import trong Ruff và re-run verify.py thành công 100% (Status: PASS).
7. Thực hiện Tier 2 Cognitive Review (`git diff` inspection, DEBATE-010 appended to `DEBATE_LOG.md`, APPROVED).
8. Cập nhật `H_docs/context/Tasks_list.md` (`TASK-006` [x] DONE) và `H_docs/runtime/STATUS.md` (`Phase: IN_PROGRESS`, next task `TASK-007`).

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest tests/test_scenarios_bridge.py` (6 passed in 3.31s), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Used lazy import pattern for `MaterialBank` in `app/scenarios.py` to prevent potential circular dependency cycles.
- Standardized topic representation so frontend receives consistent scenario JSON fields (`id`, `title`, `description`, `suggested_vocabulary`, `source: "material_bank"`).

#### Git
- **Commit:** `[iter-20] feat(api): bridge MaterialBank topics into scenarios registry endpoints`

#### Next
- **Action:** Start TASK-007: End-to-End Integration Testing & Latency Benchmarks.
- **State:** IN_PROGRESS


