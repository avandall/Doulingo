# TASK EXECUTION PLAN
# Task TASK-002: Refactor AI Engine Parser, Token Budget 2048 & Truncation Failover

> **Trạng thái:** DONE | **Ngày:** 2026-09-09

---

## 🎯 Task Goal
Nâng ngân sách token lên 2048 cho tất cả providers, rút gọn prompt CoT (`natural_draft` và `vocab_check` tối đa 20 từ), xóa bỏ regex cắt chuỗi JSON trong `_parse_raw_json`, sử dụng `schema.model_validate_json(raw_text).model_dump()`, và xây dựng cơ chế failover tự động sang provider tiếp theo trong Pool khi output bị cắt cụt hoặc `ValidationError`.

---

## 📋 Atomic Steps

### [x] Step 1: Update Provider Token Budget (2048) & CoT Prompt Length Restrictions (`app/core/ai_engine.py`)
- Update `maxOutputTokens = 2048` in `_call_gemini`.
- Update `max_tokens = 2048` in `_call_groq` and `_call_openai`.
- Update `num_predict = 2048` in `_call_ollama`.
- Shorten CoT prompt instructions (`natural_draft` and `vocab_check` to max 20 words each).

### [x] Step 2: Refactor JSON Parser & Implement Truncation Failover Policy (`app/core/ai_engine.py`)
- Removed regex / string slicing logic (`start = text.find('{')`, `end = text.rfind('}')`) from `_parse_raw_json`.
- Added `schema: type[BaseModel] | None = None` parameter to `_parse_raw_json` and `_parse_json_response`.
- Used `schema.model_validate_json(text).model_dump()` when `schema` is provided, and `json.loads(text)` when `schema` is `None`.
- Handle `ValidationError`, `JSONDecodeError`, and `ValueError` in `_call_gemini`, `_call_groq`, `_call_openai`, `_call_ollama` by logging warnings and raising exceptions to trigger automatic failover to the next provider in `_call_llm_providers`.

### [x] Step 3: Add Unit Tests for Parser & Truncation Failover (`tests/test_ai_engine.py`)
- Added unit test verifying `_parse_raw_json` with Pydantic schema validation.
- Added unit test verifying `ValidationError` / `JSONDecodeError` on truncated JSON.
- Added unit test simulating truncated JSON or syntax error from Provider 1 and verifying automatic failover to Provider 2.
- Added unit test verifying 2048 token budget in provider request payloads.

### [x] Step 4: Verification (`python3 pipeline/scripts/verify.py --test-target tests/test_ai_engine.py`)
- Executed `python3 pipeline/scripts/verify.py --test-target tests/test_ai_engine.py`.
- Status: **PASS 100%** (Ruff PASS, Mypy PASS, Bandit PASS, Pytest PASS - 22/22 tests).
