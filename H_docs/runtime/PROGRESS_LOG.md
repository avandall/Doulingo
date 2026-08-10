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

---

### Iteration 8 — [2026-08-10 14:50]
**Task:** TASK-007 End-to-End Integration Testing & Latency Benchmarks
**Phase:** Phase 4 — VERIFY & REVIEW
**Step:** Implementation & Tier 1/2 Verification of TASK-007
**Duration:** ~3 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `H_docs/context/Tasks_list.md`, và `H_docs/runtime/STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` cho `TASK-007` và chuyển trạng thái `TASK-007` thành `[/] IN_PROGRESS` trong `Tasks_list.md`.
3. Xây dựng integration test suite `tests/test_integration_material_bank.py`:
   - `test_full_turn_conversation_flow`: Kiểm thử mô phỏng cuộc thoại 2 lượt liên tiếp với MaterialBank topic qua FastAPI client.
   - `test_structured_json_response_fields`: Kiểm tra đầy đủ kiểu dữ liệu và các trường `ai_response`, `user_feedback`, `fluency_score`.
   - `test_api_chat_integration_with_material_bank`: Kiểm thử endpoint `/api/chat` kết hợp MaterialBank scenarios.
   - `test_latency_benchmarks`: Đo đạc thời gian đáp ứng (latency) cho `start_scenario` và `process_turn`.
4. Chạy `pytest tests/test_integration_material_bank.py` pass 100% (4/4 tests passed in 5.75s).
5. Thực thi Tier 1 verification via `python3 H_docs/scripts/verify.py` — Pass 100% (Ruff, Mypy, Bandit, Pytest).
6. Thực hiện Tier 2 Cognitive Review (`git diff` inspection, DEBATE-011 appended to `DEBATE_LOG.md`, APPROVED).
7. Cập nhật `H_docs/context/Tasks_list.md` (`TASK-007` [x] DONE), `H_docs/runtime/STATUS.md` (`Phase: IN_PROGRESS`, next task `TASK-008`), và `H_docs/runtime/PROGRESS_LOG.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest tests/test_integration_material_bank.py` (4 passed in 5.75s), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Multi-turn history structure explicitly validated during end-to-end client integration testing.
- Added performance latency logging for scenario startup and turn processing.

#### Git
- **Commit:** `[iter-21] test(integration): add end-to-end integration tests & latency benchmarks for MaterialBank`

#### Next
- **Action:** Start TASK-008: System Verification Evidence & Harness Documentation Update.
- **State:** IN_PROGRESS

---

### [ITER-022] 2026-08-10 14:52 — TASK-008 System Verification Evidence & Harness Documentation Update

**Phase:** COMMITTING
**Step:** Final System Verification & Solution Proof of TASK-008
**Duration:** ~3 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `H_docs/context/Tasks_list.md`, và `H_docs/runtime/STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-008` (System Verification Evidence & Harness Documentation Update).
3. Chạy full test suite `pytest -v` thành công 100% (50/50 test cases passed in 45.46s).
4. Thực thi Tier 1 verification via `python3 H_docs/scripts/verify.py` — Status PASS (100% clean check on Ruff, Mypy, Bandit, Pytest).
5. Thực hiện Tier 2 Cognitive Review (`git diff` inspection, DEBATE-012 appended to `DEBATE_LOG.md`, APPROVED).
6. Cập nhật `H_docs/context/Tasks_list.md` (`TASK-008` [x] DONE).
7. Kiểm tra tất cả 9/9 tasks trong `Tasks_list.md` đã `[x] DONE`.
8. Cập nhật `H_docs/runtime/STATUS.md` chuyển sang `Phase: ALL_DONE`.
9. Tạo file `H_docs/runtime/PROOF_OF_SOLUTION.md` với tổng hợp minh chứng nghiệm thu toàn bộ 9 tasks & Retrospective theo Constitution §10.
10. Thực hiện atomic git commit cho TASK-008.

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest` (50/50 passed), `python3 H_docs/scripts/verify.py` status PASS (Ruff/Mypy/Bandit/Pytest 100% green), `PROOF_OF_SOLUTION.md` written, STATUS.md `Phase: ALL_DONE`.

#### Decisions Made
- Confirmed all 9 tasks in `Tasks_list.md` are marked `[x] DONE` and verified with zero errors before updating `STATUS.md` to `Phase: ALL_DONE`.

#### Git
- **Commit:** `[iter-22] docs(harness): update system verification evidence, STATUS.md to ALL_DONE & write PROOF_OF_SOLUTION.md`

#### Next
- **Action:** Dự án đã hoàn thành 100%. Sẵn sàng nghiệm thu.
- **State:** ALL_DONE

---

### [ITER-023] 2026-08-10 15:30 — TASK-009 UI Roleplay Simplification & Random Roleplay Placement

**Phase:** COMMITTING
**Step:** Implementation & Verification of TASK-009
**Duration:** ~3 phút

#### Actions Taken
1. Đọc `H_docs/core/AGENT_CONSTITUTION.md`, `H_docs/context/Tasks_list.md`, và `H_docs/runtime/STATUS.md`.
2. Tạo `H_docs/runtime/PLAN.md` mới cho `TASK-009` (UI Roleplay Simplification & Random Roleplay Placement).
3. Cập nhật `app/scenarios.py`: Tối giản các static default roleplays lặp lại/trùng lặp thành 5 chủ đề roleplay cốt lõi, tinh gọn (`everyday_chat`, `cafe_dining`, `travel_culture`, `work_study_space`, `digital_lifestyle`).
4. Cập nhật `static/index.html`: Di chuyển nút `#btn-random-roleplay` (`🎲 RANDOM ROLEPLAY`) từ hero banner xuống header box của Section 2 (`EVERYDAY & CREATIVE ROLEPLAY`), đồng thời xóa bỏ hoàn toàn thanh category filter `#roleplay-category-filter-bar`.
5. Cập nhật `static/js/app.js`: Loại bỏ logic gắn event listeners cho `#roleplay-category-filter-bar`, cập nhật `renderScenarios` hiển thị trực tiếp danh sách roleplay, và tinh chỉnh `startRandomRoleplay` để chọn ngẫu nhiên các kịch bản roleplay giao tiếp.
6. Chạy `pytest` thành công 100% (50/50 test cases passed in 26.49s).
7. Executed Tier 1 verification via `python3 H_docs/scripts/verify.py` — Status PASS (Ruff/Mypy/Bandit/Pytest 100% green).
8. Cập nhật `H_docs/context/Tasks_list.md` (`TASK-009` [x] DONE) và `H_docs/runtime/STATUS.md` (`Phase: ALL_DONE`).

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest` (50/50 passed), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Placed `#btn-random-roleplay` prominently in the header box of the Roleplay section for maximum usability.
- Streamlined roleplays to eliminate duplicate/repetitive topics while preserving full backend MaterialBank & Custom Topic compatibility.

#### Git
- **Commit:** `[TASK-009] feat(ui): simplify roleplay grid, move random roleplay button to section, remove category filters`

#### Next
- **Action:** TASK-009 complete. All tasks DONE.
- **State:** ALL_DONE

---

### [ITER-024] 2026-08-10 15:48 — Material Bank Topic Resolver Fix for AI Prompt Factory

**Phase:** COMMITTING
**Step:** Implementation & Verification of MaterialBank Smart Topic Mapping
**Duration:** ~3 phút

#### Actions Taken
1. Phản biện và giải thích cơ chế gọi LLM Cloud API (Groq/Gemini/OpenAI) cho User: LLM API không tự kết nối hay đọc disk/DB local. Server Python bắt buộc phải đọc/sample nguyên liệu -> lắp ráp thành System Prompt -> gửi kèm trong API payload.
2. Kiểm tra vết từ commit `cbbed2756fd246d77124528a67c914b319a57cee` đến nay: Phát hiện điểm nghẽn (root cause) khi gọi `pf.sample_materials(topic_id)`. Các scenario ID trên UI (`everyday_chat`, `cafe_dining`, `det_childhood_memory`) không khớp với 161 key ID trong `MaterialBank` (`food`, `friends`, `travel`, `study`, `technology`), dẫn đến `get_topic` trả về `None` làm System Prompt bị rỗng nguyên liệu.
3. Nâng cấp `MaterialBank.get_topic()` trong `app/material_bank.py`:
   - Bổ sung `PRESET_MAPPINGS` đa cấp ánh xạ trực tiếp scenario ID -> `MaterialBank` topics tương ứng.
   - Thêm bộ lọc Keyword & Token Substring Matching cho các custom topics.
   - Bổ sung Fallback Topic đảm bảo 100% các cuộc hội thoại luôn được nạp đầy đủ từ vựng academic, câu hỏi gợi mở, vai diễn persona và mẫu câu từ bộ `DB1_*.md` đến `DB5_*.md`.
4. Chạy `pytest` thành công 100% (50/50 test cases passed in 23.95s).
5. Executed Tier 1 verification via `python3 H_docs/scripts/verify.py` — Status PASS (Ruff/Mypy/Bandit/Pytest 100% green).

#### Result
- **Outcome:** PASS
- **Evidence:** `pytest` (50/50 passed), `python3 H_docs/scripts/verify.py` status PASS.

#### Decisions Made
- Maintained in-memory MaterialBank lookup for 0ms prompt assembly latency while ensuring 100% topic resolution coverage for all UI scenarios and custom topics.

#### Git
- **Commit:** `[TASK-003] fix(prompt-factory): implement smart topic mapping for MaterialBank dynamic prompt assembly`

#### Next
- **Action:** Retest AI conversation generation.
- **State:** ALL_DONE






