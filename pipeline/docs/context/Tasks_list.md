# TASKS LIST
# Danh sách tác vụ & Queue thực thi — Haku Haku's Performance & Reliability Initiative

> **Trạng thái:** CONTEXT (Active) | **Cập nhật:** 2026-09-09
>
> ✏️ **HUMAN & ARCHITECT REWRITE (v2.0 Post-Review).** Danh sách tác vụ chuẩn hóa sau rà soát phản biện kỹ thuật, sẵn sàng cho chu trình Ralph Loop thực thi.
> 🤖 **AI EXECUTION RULE:** AI đọc danh sách từ trên xuống dưới, thực hiện task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS`. Khi hoàn thành và verify pass 100%, đánh dấu `[x] DONE` trước khi chuyển sang task kế tiếp.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Mục tiêu chính |
|---|---|---|---|---|---|
| `TASK-001` | Khởi tạo Pydantic Schemas, Strict Mode `$defs` Converter & Provider Signature | Phase 1 | P0-Critical | `[x] DONE` | `to_strict_json_schema` + Multi-provider signature |
| `TASK-002` | Refactor AI Engine Parser, Token Budget 2048 & Truncation Failover | Phase 1 | P0-Critical | `[x] DONE` | Xóa `_parse_raw_json`, failover khi vỡ JSON |
| `TASK-003` | Phân Vùng Prompt & Tối Ưu Hóa Prompt Caching (~1,200 Tokens) | Phase 2 | P0-Critical | `[x] DONE` | Cố định angle, TTFT < 400ms trên Groq/OpenAI |
| `TASK-004` | Tích Hợp Silero VAD WASM Âm Học & Audio Engine State Machine | Phase 3 | P1-Normal | `[x] DONE` | VAD thuần acoustic, nâng cấp an toàn lúc mic IDLE |
| `TASK-005` | Build Script & Tích Hợp SQLite3 WASM Tra Cứu Từ Điển 0ms | Phase 3 | P1-Normal | `[x] DONE` | `build_vocab_wasm_db.py` + 0ms RAM dictionary |
| `TASK-006` | Test Suite Tích Hợp Hermetic & Deterministic Verification (`verify.py`) | Phase 4 | P0-Critical | `[ ] TODO` | 100% Hermetic mock test failover + harness pass |

> **Quy định trạng thái:**
> - `[ ] TODO`: Chưa thực hiện, sẵn sàng trong queue
> - `[/] IN_PROGRESS`: Đang được AI thực thi
> - `[x] DONE`: Hoàn thành, đã pass kiểm thử và có proof
> - `[!] BLOCKED`: Bị nghẽn, cần can thiệp từ con người

---

## 2. Chi Tiết Từng Task (Task Specifications)

---

### 📌 TASK-001: Khởi tạo Pydantic Schemas, Strict Mode `$defs` Converter & Provider Signature

#### Metadata
```
Task ID:         TASK-001
Task Name:       Khởi tạo Pydantic Schemas, Strict Mode $defs Converter & Provider Signature
Phase:           Phase 1 (Constrained Decoding)
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [x] DONE
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

### 📌 TASK-002: Refactor AI Engine Parser, Token Budget 2048 & Truncation Failover

#### Metadata
```
Task ID:         TASK-002
Task Name:       Refactor AI Engine Parser, Token Budget 2048 & Truncation Failover
Phase:           Phase 1 (Constrained Decoding)
Task Type:       refactor
Priority:        P0-Critical
Trạng thái:      [x] DONE
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
- [x] Xóa bỏ hoàn toàn mã nguồn regex cắt chuỗi JSON trong `_parse_raw_json`.
- [x] Khi model trả về chuỗi JSON chuẩn, Pydantic parse thành công 100%.
- [x] Giả lập chuỗi JSON bị cắt cụt hoặc lỗi cú pháp: hệ thống không crash mà tự động chuyển sang provider tiếp theo trong Pool.

#### Scope
- **Files được sửa/tạo:** `app/core/ai_engine.py`, `tests/test_ai_engine.py`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py --test-target tests/test_ai_engine.py
```

---

### 📌 TASK-003: Phân Vùng Prompt & Tối Ưu Hóa Prompt Caching (~1,200 Tokens)

#### Metadata
```
Task ID:         TASK-003
Task Name:       Phân Vùng Prompt & Tối Ưu Hóa Prompt Caching (~1,200 Tokens)
Phase:           Phase 2 (Prompt Caching)
Task Type:       perf
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Tối ưu hóa thời gian prefill của Groq/OpenAI xuống $< 400\text{ms}$ bằng Prefix Caching, đồng thời giữ Gemini chạy mượt mà ở chế độ throughput tiêu chuẩn.
- **What:**
  1. Tách cấu trúc trong `app/rag/prompt_constructor.py` thành:
     - `build_static_cacheable_prefix(character_id, level, scenario, scenario_angle)`: Kích thước $\approx 1,200$ tokens, giữ nguyên bất biến trong suốt session.
     - `build_dynamic_turn_suffix(history, user_transcript)`: Chỉ chứa lịch sử đối thoại và câu nói mới nhất.
  2. Cố định `scenario_angle` ngay từ `start_roleplay_greeting` và lưu vào session, không sinh ngẫu nhiên ở giữa các turns.
  3. Đảm bảo rolling prune lịch sử chỉ thay đổi phần suffix, không chạm vào prefix.

#### Acceptance Criteria
- [x] Static Prefix duy trì độ dài $\ge 1,024$ tokens và nội dung bất biến giữa các turn của cùng một session.
- [x] Đo lường TTFT trên Groq/OpenAI giảm xuống $< 400\text{ms}$ từ turn 2 trở đi.
- [x] Gemini 2.0 Flash xử lý prompt trơn tru mà không bị nghẽn prefill.

#### Scope
- **Files được sửa/tạo:** `app/rag/prompt_constructor.py`, `app/core/ai_engine.py`, `tests/test_prompt_caching.py`

#### Verification Commands
```bash
pytest tests/test_prompt_caching.py
```

---

### 📌 TASK-004: Tích Hợp Silero VAD WASM Âm Học & Audio Engine State Machine

#### Metadata
```
Task ID:         TASK-004
Task Name:       Tích Hợp Silero VAD WASM Âm Học & Audio Engine State Machine
Phase:           Phase 3 (WebAssembly Client)
Task Type:       feat
Priority:        P1-Normal
Trạng thái:      [x] DONE
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Khắc phục tình trạng micro tự ngắt khi học viên ngập ngừng bằng mô hình âm học VAD thuần túy, loại bỏ sự phụ thuộc vào đếm từ của Web Speech API, và chống xung đột mic trên iOS.
- **What:**
  1. Xây dựng State Machine trong `static/js/speech.js`: `LEGACY_FALLBACK` $\rightarrow$ `WASM_LOADING` $\rightarrow$ `WASM_STAGED` $\rightarrow$ `WASM_ACTIVE` (chỉ chuyển trạng thái khi `MIC_STATE == "IDLE"`).
  2. Tích lũy biến `accumulated_voiced_duration_ms` trong AudioWorklet. Tại $t_{\text{silence}} \ge 3.5\text{s}$:
     - Nếu $\ge 1500\text{ms}$: Tự động đóng mic và gửi request.
     - Nếu $< 1500\text{ms}$: Reset trạng thái, không đóng mic.
  3. Tại backend `app/scoring/tier1_realtime.py`: Thêm Pydantic clamping cho `AcousticMetricsInput` (kẹp `pause_duration_ms <= 60000`, `wpm <= 350`) và fallback về STT timestamps nếu dữ liệu client out-of-bounds.

#### Acceptance Criteria
- [x] Audio Engine State Machine không bao giờ hot-swap AudioWorklet khi mic đang ở trạng thái RECORDING.
- [x] Tự động gửi câu trả lời khi khoảng lặng $\ge 3.5\text{s}$ VÀ tổng thời lượng giọng nói $\ge 1.5\text{s}$.
- [x] Backend kẹp ngưỡng an toàn, không bị crash bởi dữ liệu âm học bất thường.

#### Scope
- **Files được sửa/tạo:** `static/js/speech.js`, `static/wasm/**`, `app/scoring/tier1_realtime.py`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py --quick
```

---

### 📌 TASK-005: Build Script & Tích Hợp SQLite3 WASM Tra Cứu Từ Điển 0ms

#### Metadata
```
Task ID:         TASK-005
Task Name:       Build Script & Tích Hợp SQLite3 WASM Tra Cứu Từ Điển 0ms
Phase:           Phase 3 (WebAssembly Client)
Task Type:       feat
Priority:        P1-Normal
Trạng thái:      [x] DONE
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Loại bỏ độ trễ mạng 100-300ms khi tra nghĩa từ vựng trên bong bóng chat bằng cơ sở dữ liệu SQLite nhúng trực tiếp trong RAM trình duyệt.
- **What:**
  1. Tạo offline build script `scripts/build_vocab_wasm_db.py` trích xuất 3,000 từ vựng cốt lõi từ `data/dictionary.db` tạo thành `static/data/vocab_core.sqlite` (~1.1MB, có index `idx_word`).
  2. Tạo `static/js/dict_wasm.js` nạp `sqlite3.wasm` và mở file DB trong RAM.
  3. Kết nối sự kiện click từ vựng trên speech bubble với hàm `dict_wasm.lookup(word)`.
  4. Cơ chế Progressive Enhancement: nếu WASM chưa sẵn sàng hoặc từ không có trong 3,000 từ cốt lõi $\rightarrow$ tự động gọi API `/api/dictionary/lookup`.

#### Acceptance Criteria
- [x] Script `scripts/build_vocab_wasm_db.py` chạy độc lập và sinh ra file SQLite hợp lệ.
- [x] Tra cứu 3,000 từ cốt lõi trên client phản hồi $< 1\text{ms}$ (0ms network round-trip).
- [x] Tự động fallback về API backend đối với các từ hiếm không nằm trong database RAM.

#### Scope
- **Files được sửa/tạo:** `scripts/build_vocab_wasm_db.py`, `static/js/dict_wasm.js`, `static/data/vocab_core.sqlite`, `static/js/app.js`

#### Verification Commands
```bash
python3 scripts/build_vocab_wasm_db.py
python3 pipeline/scripts/verify.py --quick
```

---

### 📌 TASK-006: Test Suite Tích Hợp Hermetic & Deterministic Verification (`verify.py`)

#### Metadata
```
Task ID:         TASK-006
Task Name:       Test Suite Tích Hợp Hermetic & Deterministic Verification (`verify.py`)
Phase:           Phase 4 (Quality & Verification)
Task Type:       test
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Đảm bảo toàn bộ hệ thống đạt tiêu chuẩn kỹ thuật Harness Engineering, chạy cô lập không tốn token mạng (Hermetic) và kiểm chứng đầy đủ các kịch bản failover.
- **What:**
  1. Viết bộ unit tests `tests/test_schemas.py` và `tests/test_ai_engine.py` với Mock LLM responses (Gemini, Groq, OpenAI).
  2. Giả lập kịch bản Gemini trả về lỗi 429 Quota $\rightarrow$ kiểm tra hệ thống chuyển sang Groq với cùng schema.
  3. Giả lập kịch bản model trả về JSON bị cắt cụt (Truncation) $\rightarrow$ kiểm tra cơ chế chuyển provider kế tiếp.
  4. Viết script benchmark riêng ngoài CI: `scripts/benchmark_prompt_caching.py` để kiểm chứng độ trễ thực tế khi có API key.

#### Acceptance Criteria
- [ ] Toàn bộ test suite trong `tests/` chạy độc lập không phụ thuộc Internet và pass 100%.
- [ ] Giả lập lỗi quota và lỗi cắt cụt token được xử lý mượt mà qua failover logic.
- [ ] `python3 pipeline/scripts/verify.py` pass 100% (Tier 1 check).
- [ ] Git status sạch sẽ, tuân thủ đúng quy ước commit.

#### Scope
- **Files được sửa/tạo:** `tests/**`, `scripts/benchmark_prompt_caching.py`, `.gitignore`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py
```
