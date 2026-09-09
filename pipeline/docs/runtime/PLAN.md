# TASK EXECUTION PLAN
# Task TASK-001: Khởi tạo Pydantic Schemas, Strict Mode $defs Converter & Provider Signature

> **Trạng thái:** COMPLETED | **Ngày:** 2026-09-09

---

## 🎯 Task Goal
Tránh lỗi HTTP 400 từ OpenAI/Groq do thiếu `additionalProperties: false` hoặc thiếu `required` trong root và `$defs`, đồng thời chuẩn hóa chữ ký tầng provider trong `app/core/ai_engine.py` để nhận Pydantic schema linh hoạt.

---

## 📋 Atomic Steps

### [x] Step 1: Create Pydantic Schemas & `to_strict_json_schema` Converter (`app/core/schemas.py`)
- Define `UserFeedbackSchema`, `RoleplayTurnResponseSchema`, `GreetingResponseSchema`, `QuickTranslationSchema` in `app/core/schemas.py`.
- Write `to_strict_json_schema(model_cls: type[BaseModel]) -> dict[str, Any]` function:
  - Traverses root schema and any `$defs` / `definitions` recursively.
  - Sets `additionalProperties: False` on all object schemas.
  - Ensures all property keys are present in `required`.
  - Converts nullable fields with `default: None` / `NoneType` to `anyOf: [..., {"type": "null"}]`.

### [x] Step 2: Refactor Provider Signatures in AI Engine (`app/core/ai_engine.py`)
- Update `_call_llm_providers(self, prompt: str, schema: type[BaseModel] | None = None, temp: float = 0.8, parse_raw: bool = False)` signature.
- Update `_call_gemini`, `_call_groq`, `_call_openai`, and `_call_ollama` methods to receive `schema` parameter and format response schemas:
  - Gemini: `responseSchema` in `generationConfig`
  - Groq & OpenAI: `response_format = {"type": "json_schema", "json_schema": {"name": ..., "strict": True, "schema": to_strict_json_schema(schema)}}`
  - Ollama: `format` schema dictionary if supported/provided.

### [x] Step 3: Write Unit Test Suite (`tests/test_schemas.py`)
- Create unit tests for `to_strict_json_schema`:
  - Test root & `$defs` `additionalProperties == False`.
  - Test 100% properties in `required`.
  - Test nullable transformations.
  - Test model validation for each of the 4 schemas.

### [x] Step 4: Verification (`python3 pipeline/scripts/verify.py`)
- Run `python3 -c "from app.core.schemas import RoleplayTurnResponseSchema, to_strict_json_schema; print('Strict Schema Valid:', 'required' in to_strict_json_schema(RoleplayTurnResponseSchema))"`
- Run `pytest tests/test_schemas.py`
- Run `python3 pipeline/scripts/verify.py` and ensure 100% pass.
