# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced by harness.sh) | **Cập nhật:** 2026-09-09 23:08

---

## 🎯 Task Spec: TASK-002
### 📌 TASK-002: Refactor AI Engine Parser, Token Budget 2048 & Truncation Failover

#### Metadata
```
Task ID:         TASK-002
Task Name:       Refactor AI Engine Parser, Token Budget 2048 & Truncation Failover
Phase:           Phase 1 (Constrained Decoding)
Task Type:       refactor
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Ngân sách token cũ (1200) dễ bị tràn ở CEFR C1/C2 làm cắt cụt JSON. Cần nâng ngân sách lên 2048, bóp gọn CoT, xóa bỏ `_parse_raw_json` regex và xây dựng cơ chế failover khi vỡ schema.
- **What:**
  1. Nâng `max_tokens = 2048` trong tất cả các payload provider.
  2. Rút gọn prompt CoT (`natural_draft` và `vocab_check` tối đa 20 từ mỗi trường).
  3. Xóa bỏ logic regex cắt chuỗi trong `_parse_raw_json`, thay bằng `schema.model_validate_json(raw_text).model_dump()`.
  4. Bổ sung cơ chế: nếu output bị cắt cụt hoặc `ValidationError`, ghi log cảnh báo và tự động chuyển sang provider kế tiếp trong Pool (Failover Policy).

#### Acceptance Criteria
- [ ] Xóa bỏ hoàn toàn mã nguồn regex cắt chuỗi JSON trong `_parse_raw_json`.
- [ ] Khi model trả về chuỗi JSON chuẩn, Pydantic parse thành công 100%.
- [ ] Giả lập chuỗi JSON bị cắt cụt hoặc lỗi cú pháp: hệ thống không crash mà tự động chuyển sang provider tiếp theo trong Pool.

#### Scope
- **Files được sửa/tạo:** `app/core/ai_engine.py`, `tests/test_ai_engine.py`

#### Verification Commands
```bash
pytest tests/test_ai_engine.py
```

---

---

## 🛡️ JIT Environment Context
- **Tech Stack:** ```,Runtime Backend:     Python 3.11+ (WSL Linux Ubuntu) Web Framework:       FastAPI >= 0.115.0 + Uvicorn (ASGI),Validation Standard: Pydantic v2 (Single Source of Truth cho toàn bộ LLM outputs) LLM Providers:       - Google Gemini (gemini-2.0-flash, gemini-1.5-flash) via responseSchema,                     - Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant) via json_schema strict                      - OpenAI (gpt-4o-mini) via json_schema strict,                     - Ollama (local fallback: llama3, qwen2.5) via format schema
- **Scope Boundaries:** ```,app/core/schemas.py                      # [TẠO MỚI] Khai báo các Pydantic Schemas & to_strict_json_schema app/core/ai_engine.py                    # [CHỈNH SỬA] Tích hợp responseSchema, strict mode, token budget 2048,app/rag/prompt_constructor.py            # [CHỈNH SỬA] Tách Static Prefix (~1,200 tokens) và Dynamic Suffix app/scoring/tier1_realtime.py            # [CHỈNH SỬA] Tiếp nhận và kẹp ngưỡng acoustic signals từ Client VAD,app/scoring/tier2_deep.py                # [CHỈNH SỬA] Chuẩn hóa output qua Pydantic schema scripts/build_vocab_wasm_db.py           # [TẠO MỚI] Offline script trích xuất SQLite vocab core,static/js/speech.js                      # [CHỈNH SỬA] Nhúng Audio State Machine & Silero VAD WASM
- **Last Synced:** 2026-09-09 23:08:57
