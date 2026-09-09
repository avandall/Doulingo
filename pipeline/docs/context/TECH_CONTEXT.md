# TECH CONTEXT
# Bối cảnh kỹ thuật — Stack, Môi trường và Kiến trúc Kỹ thuật

> **Trạng thái:** CONTEXT (Active) | **Cập nhật:** 2026-09-09
>
> ✏️ **HUMAN & ARCHITECT REWRITE (v2.0 Post-Review).** File này quy định chi tiết stack công nghệ, chuẩn Pydantic schema, kiến trúc Prompt Caching (Groq/Gemini), Audio State Machine và WebAssembly (WASM).

---

## 1. Tech Stack & Execution Environment

```
Runtime Backend:     Python 3.11+ (WSL Linux Ubuntu)
Web Framework:       FastAPI >= 0.115.0 + Uvicorn (ASGI)
Validation Standard: Pydantic v2 (Single Source of Truth cho toàn bộ LLM outputs)
LLM Providers:       - Google Gemini (gemini-2.0-flash, gemini-1.5-flash) via responseSchema
                     - Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant) via json_schema strict
                     - OpenAI (gpt-4o-mini) via json_schema strict
                     - Ollama (local fallback: llama3, qwen2.5) via format schema
Output Token Budget: max_tokens = 2048 (ngăn chặn cắt cụt JSON ở CEFR C1/C2)
TTS Engine:          Edge-TTS & gTTS (Async audio streaming)
Client Runtime:      Modern Browser (Chrome/Edge/Safari/PWA)
Client WASM:         - Silero VAD WASM (Web AudioWorklet PCM 16kHz)
                     - SQLite3 WASM (Official in-memory database ~1.1MB for 0ms dictionary)
Primary Database:    SQLite / LibSQL (data/custom_topics.db, data/reports.db)
Verification Engine: python3 pipeline/scripts/verify.py (Synchronous foreground execution only; Pytest, Ruff, Mypy; use --quick or --test-target for <60s turns)
```

---

## 2. Pydantic Schemas & Constrained Decoding Contracts

Toàn bộ phản hồi có cấu trúc từ các LLM providers bắt buộc phải validate qua Pydantic models tại `app/core/schemas.py`.

### 2.1. Cấu trúc Schema Chuẩn

```python
from pydantic import BaseModel, Field
from typing import Literal

class UserFeedbackSchema(BaseModel):
    grammar_status: str = Field(
        description="Trạng thái ngữ pháp ngắn gọn (vd: 'Clean & Clear' hoặc ghi chú lỗi nhỏ)"
    )
    corrected_text: str = Field(
        description="Câu của học viên đã được sửa lỗi ngữ pháp, bảo toàn 100% ý định ban đầu"
    )
    native_phrasing: str = Field(
        description="Cách diễn đạt tự nhiên chuẩn bản xứ của câu nói đó"
    )
    duo_reaction: Literal["celebrate", "happy", "encouraging"] = Field(
        default="happy",
        description="Cảm xúc của nhân vật đại diện Duo"
    )
    grammar_explanation: str | None = Field(
        default=None,
        description="Giải thích ngắn gọn bằng tiếng Việt về lỗi ngữ pháp hoặc phát âm"
    )

class RoleplayTurnResponseSchema(BaseModel):
    natural_draft: str = Field(
        description="Suy nghĩ nháp súc tích tối đa 20 từ trước khi phản hồi"
    )
    vocab_check: str = Field(
        description="Tự kiểm tra trần từ vựng CEFR Level tối đa 20 từ"
    )
    final_response: str = Field(
        description="Câu thoại tiếng Anh chuẩn 100% của nhân vật, kết thúc bằng 1 câu hỏi mở gợi chuyện"
    )
    user_feedback: UserFeedbackSchema

class GreetingResponseSchema(BaseModel):
    natural_draft: str = Field(description="Ý tưởng mở đầu tình huống (max 20 words)")
    vocab_check: str = Field(description="Kiểm tra cấp độ CEFR (max 20 words)")
    final_response: str = Field(description="Lời mở đầu chào hỏi và câu hỏi gợi mở đầu tiên")

class QuickTranslationSchema(BaseModel):
    vietnamese_translation: str = Field(
        description="Bản dịch tiếng Việt tự nhiên, trực tiếp, không chứa văn bản râu ria"
    )
```

### 2.2. Xử lý Strict JSON Schema (`$defs` & Required Nullable Transformation)
OpenAI và Groq Strict Mode (`strict: True`) yêu cầu:
1. `additionalProperties: False` tại mọi node `type: "object"`.
2. Mọi properties (kể cả optional có `default=None`) đều phải nằm trong mảng `required`.
3. Các schema con nằm trong `$defs` cũng phải được áp dụng đầy đủ 2 quy tắc trên.

Hàm chuyển đổi tập trung `to_strict_json_schema(model_cls: type[BaseModel]) -> dict[str, Any]` trong `app/core/schemas.py`:
- Duyệt đệ quy toàn bộ cây schema bao gồm root và mọi nodes trong `$defs` / `definitions`.
- Ép `node["additionalProperties"] = False`.
- Gán `node["required"] = list(node["properties"].keys())`.
- Biến đổi các trường nullable có `default: null` thành `anyOf: [{"type": ...}, {"type": "null"}]`.

### 2.3. Chữ ký Hàm Tầng Provider (Unified Provider Signatures)
Trong `app/core/ai_engine.py`:
```python
def _call_llm_providers(
    self,
    prompt: str,
    schema: type[BaseModel] | None = None,
    temp: float = 0.8,
    parse_raw: bool = False
) -> dict[str, Any] | str | None:
```
- Nếu `schema is not None`:
  - Gemini: `generationConfig["responseSchema"] = schema.model_json_schema()`
  - Groq/OpenAI: `response_format = {"type": "json_schema", "json_schema": {"name": "...", "strict": True, "schema": to_strict_json_schema(schema)}}`
  - Parse kết quả: `schema.model_validate_json(raw_text).model_dump()`
  - Nếu `pydantic.ValidationError` hoặc JSON bị cắt cụt do chạm trần token: Coi là Provider Failure $\rightarrow$ Tự động failover sang provider tiếp theo trong Pool.
- Nếu `schema is None`: Chạy unconstrained mode trả về raw text.

---

## 3. Prompt Caching (KV-Cache Optimization) Strategy & Caching Thresholds

### 3.1. Phân định Thực tế Caching giữa các Providers
- **Groq (LLaMA 3.3/3.1) & OpenAI**: Hỗ trợ Automatic Prefix Caching từ **1,024 tokens**.
  - Cam kết: **TTFT $< 400\text{ms}$** từ lượt thoại thứ 2 trở đi.
  - Tiết kiệm: $\ge 70\%$ chi phí token đầu vào.
- **Google Gemini API**: Ngưỡng kích hoạt Prompt Caching tối thiểu là **32,768 tokens** (trên dòng Flash/Pro).
  - Quyết định kiến trúc: **KHÔNG nhồi nhét 32k tokens** để tránh làm nổ thời gian prefill Turn 1 cold-start (5-8s).
  - Gemini sẽ chạy ở chế độ **Standard Un-cached Throughput** với `gemini-2.0-flash` (tốc độ sinh 100+ tps, TTFT tự nhiên $\approx 700\text{ms} - 1,000\text{ms}$).

### 3.2. Cấu trúc Prompt Chuẩn (Prompt Partitioning)
Kích thước Static Prefix được duy trì ở mức $\approx 1,200$ tokens — vừa vặn kích hoạt cache của Groq/OpenAI, vừa nhẹ nhàng để Gemini prefill tức thì:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. STATIC CACHEABLE PREFIX (~1,200 Tokens - Bất biến trong 1 session)   │
│    - System Role & Character Persona Identity (Lily, Rajesh...)        │
│    - Session Scenario Angle (Cố định duy nhất 1 lần lúc init session)  │
│    - CEFR 20-Level Difficulty Rules & Example Reference Responses       │
│    - IELTS Book Reference Dialogues & Scoring Rubric                   │
│    - Output Format Directives (CoT súc tích max 20 words)              │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼ [Cached in KV Memory on Groq/OpenAI]
┌────────────────────────────────────────────────────────────────────────┐
│ 2. DYNAMIC TURN SUFFIX (Biến đổi theo từng câu thoại của người học)    │
│    - Conversation History (Rolling window N turns gần nhất)            │
│    - Current Spoken Transcript từ người học                            │
│    - Current Turn Number & Immediate Goal                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Client-Side WebAssembly (WASM) & Audio Architecture

### 4.1. Silero VAD WASM: Thuần Âm Học (Acoustic-Only Decoupling)
- **Vị trí tích hợp:** `static/js/speech.js` qua Web AudioWorklet (luồng PCM 16kHz thô).
- **Nguyên lý đo lường:** Độc lập 100% với Web Speech API, tích lũy biến `accumulated_voiced_duration_ms` (thời gian có xác suất giọng nói $p > 0.5$).
- **Ngưỡng ngắt lời (Silence Timeout):** Khi phát hiện khoảng lặng $t_{\text{silence}} \ge 3.5\text{s}$:
  - Nếu `accumulated_voiced_duration_ms >= 1500` ($1.5\text{s}$ âm thanh thực $\approx$ 1 câu nói): Coi là học viên đã kết thúc phát biểu $\rightarrow$ **Tự động đóng mic và gửi request `/api/voice/chat`**.
  - Nếu `accumulated_voiced_duration_ms < 1500`: Coi là tiếng thở, tiếng ho, tiếng lách cách $\rightarrow$ Reset trạng thái, không đóng mic và không gửi audio rác.
- **Sanity Bounds & Clamping tại Backend (`app/scoring/tier1_realtime.py`):**
  - Nhận DTO `AcousticMetricsInput` (kẹp ngưỡng `pause_duration_ms <= 60000`, `wpm <= 350`).
  - Nếu dữ liệu client bị out-of-bounds: Tự động fallback tính WPM và Pause ratio từ timestamps của STT engine.

### 4.2. Audio Engine State Machine (Chống Race Condition)
Để tránh tiếng nổ audio buffer hoặc xung đột mic trên Safari iOS khi file WASM tải xong lúc đang thu âm, hệ thống tuân theo State Machine tường minh:

```
[AUDIO_ENGINE_STATE]
  ├── LEGACY_FALLBACK (Trình duyệt dùng Web Speech API / MediaRecorder cũ)
  ├── WASM_LOADING    (Đang tải bytecode silero_vad.wasm về máy)
  ├── WASM_STAGED     (WASM đã biên dịch xong, ĐANG ĐỢI MIC IDLE)
  └── WASM_ACTIVE     (Đã chính thức nâng cấp thành AudioWorklet VAD)
```
- **Luật bất biến:** Quá trình chuyển từ `WASM_STAGED` sang `WASM_ACTIVE` **CHỈ ĐƯỢC PHÉP THỰC HIỆN KHI `MIC_STATE == "IDLE"`** (giữa 2 turns khi micro đã tắt hoàn toàn). Tuyệt đối không can thiệp vào audio stream đang mở.

### 4.3. 0ms Local Dictionary (SQLite3 WASM)
- **Vị trí tích hợp:** `static/js/dict_wasm.js`.
- **Database Asset:** `static/data/vocab_core.sqlite` (~1.1MB, nén gzip ~400KB) sinh ra bởi offline script `scripts/build_vocab_wasm_db.py`.
- **Progressive Enhancement:** 
  - Khi WASM chưa sẵn sàng: Tra từ fallback gọi API `/api/dictionary/lookup`.
  - Khi WASM đã sẵn sàng: Tra từ trực tiếp trong RAM trình duyệt phản hồi trong **$< 1\text{ms}$** (0ms network delay).
