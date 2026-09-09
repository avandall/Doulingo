# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-09 22:52

---

## 🎯 Task Spec: TASK-001
### 📌 TASK-001: Khởi tạo Pydantic Schemas, Strict Mode `$defs` Converter & Provider Signature

#### Metadata
```
Task ID:         TASK-001
Task Name:       Khởi tạo Pydantic Schemas, Strict Mode $defs Converter & Provider Signature
Phase:           Phase 1 (Constrained Decoding)
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Tránh lỗi HTTP 400 từ OpenAI/Groq do thiếu `additionalProperties: false` trong `$defs` hoặc trường nullable bị bỏ quên khỏi `required`, đồng thời chuẩn hóa chữ ký tầng provider để nhận schema linh hoạt.
- **What:**
  1. Tạo `app/core/schemas.py` chứa: `UserFeedbackSchema`, `RoleplayTurnResponseSchema`, `GreetingResponseSchema`, `QuickTranslationSchema`.
  2. Viết hàm đệ quy `to_strict_json_schema(model_cls: type[BaseModel]) -> dict[str, Any]` duyệt qua root và `$defs`, ép `additionalProperties: False`, đưa toàn bộ keys vào `required`, và biến đổi nullable thành `anyOf: [type, "null"]`.
  3. Refactor chữ ký `_call_llm_providers(prompt, schema=None, temp=0.8, parse_raw=False)` trong `app/core/ai_engine.py` và truyền schema xuống các adapters (`_call_gemini`, `_call_groq`, `_call_openai`, `_call_ollama`).

#### Acceptance Criteria
- [ ] `to_strict_json_schema(RoleplayTurnResponseSchema)` tạo ra JSON Schema hợp lệ mà OpenAI/Groq Strict Mode chấp nhận (100% properties in required, no extra props in root & `$defs`).
- [ ] Các provider adapters tiếp nhận tham số `schema` và đóng gói đúng format của từng hãng.
- [ ] Chạy unit test kiểm tra schema không có lỗi runtime.

#### Scope
- **Files được sửa/tạo:** `app/core/schemas.py`, `app/core/ai_engine.py`, `tests/test_schemas.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 -c "from app.core.schemas import RoleplayTurnResponseSchema, to_strict_json_schema; print('Strict Schema Valid:', 'required' in to_strict_json_schema(RoleplayTurnResponseSchema))"
pytest tests/test_schemas.py
```

---

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime Backend:     Python 3.11+ (WSL Linux Ubuntu) Web Framework:       FastAPI >= 0.115.0 + Uvicorn (ASGI),Validation Standard: Pydantic v2 (Single Source of Truth cho toàn bộ LLM outputs) LLM Providers:       - Google Gemini (gemini-2.0-flash, gemini-1.5-flash) via responseSchema,                     - Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant) via json_schema strict                      - OpenAI (gpt-4o-mini) via json_schema strict,                     - Ollama (local fallback: llama3, qwen2.5) via format schema
- **Scope Boundaries:** ```,app/core/schemas.py                      # [TẠO MỚI] Khai báo các Pydantic Schemas & to_strict_json_schema app/core/ai_engine.py                    # [CHỈNH SỬA] Tích hợp responseSchema, strict mode, token budget 2048,app/rag/prompt_constructor.py            # [CHỈNH SỬA] Tách Static Prefix (~1,200 tokens) và Dynamic Suffix app/scoring/tier1_realtime.py            # [CHỈNH SỬA] Tiếp nhận và kẹp ngưỡng acoustic signals từ Client VAD,app/scoring/tier2_deep.py                # [CHỈNH SỬA] Chuẩn hóa output qua Pydantic schema scripts/build_vocab_wasm_db.py           # [TẠO MỚI] Offline script trích xuất SQLite vocab core,static/js/speech.js                      # [CHỈNH SỬA] Nhúng Audio State Machine & Silero VAD WASM
- **Last Synced:** 2026-09-09 22:52:54
