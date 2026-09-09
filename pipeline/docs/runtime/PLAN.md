# TASK EXECUTION PLAN
# Task TASK-003: Phân Vùng Prompt & Tối Ưu Hóa Prompt Caching (~1,200 Tokens)

> **Trạng thái:** IN_PROGRESS | **Ngày:** 2026-09-09

---

## 🎯 Task Goal
Tách cấu trúc prompt thành Static Cacheable Prefix (~1,200 tokens) và Dynamic Suffix, cố định `scenario_angle` ngay từ session init, đảm bảo prefix bất biến 100% qua các turns, đạt tiêu chuẩn Prompt Caching trên Groq/OpenAI.

---

## 📋 Atomic Steps

### [ ] Step 1: Implement Prompt Partitioning Functions in `app/rag/prompt_constructor.py`
- Implement `build_static_cacheable_prefix(scenario, character, level, scenario_angle=None)`.
- Implement `build_dynamic_turn_suffix(history, user_transcript, turn_count, scenario_title)`.
- Ensure `build_static_cacheable_prefix` yields >= 1,024 tokens.

### [ ] Step 2: Refactor `ai_engine.py` to use Partitioned Prompt Construction & Fixed Scenario Angle
- Fix `scenario_angle` per session at `start_roleplay_greeting`, store in session / character context.
- Use `build_static_cacheable_prefix` + `build_dynamic_turn_suffix` in `_build_token_efficient_prompt`.
- Verify history pruning only affects suffix, never modifying prefix.

### [ ] Step 3: Implement Unit Tests in `tests/test_prompt_caching.py`
- Test `build_static_cacheable_prefix` token count >= 1,024.
- Test prefix immutability across multiple simulated turns.
- Test rolling history pruning preserves static prefix 100%.

### [ ] Step 4: Verification & Milestone Completion
- Run `python3 pipeline/scripts/verify.py --test-target tests/test_prompt_caching.py` (ensure PASS 100%).
- Mark `TASK-003` as `[x] DONE` in `Tasks_list.md`.
- Commit Git cleanly.
