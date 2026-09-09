# PROJECT BRIEF
# Tóm tắt dự án — Haku Haku's Performance, Reliability & Voice Optimization Initiative

> **Trạng thái:** CONTEXT (Active) | **Cập nhật:** 2026-09-09
>
> ✏️ **HUMAN & ARCHITECT REWRITE (v2.0 Post-Review).** File này định nghĩa bức tranh tổng thể, mục tiêu kinh doanh và phạm vi kỹ thuật của giai đoạn nâng cấp toàn diện hệ sinh thái Haku Haku's.

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:          Haku Haku's — Zero-Defect AI Voice & Ultra-Low Latency Roleplay
Repo Name:         Doulingo
Mục tiêu cốt lõi:  Nâng cấp kiến trúc AI Engine và Frontend Voice bằng 3 công nghệ:
                   1) Constrained Decoding (Structured Outputs)
                   2) Prompt Caching (KV-Cache Optimization)
                   3) Client-Side WebAssembly (WASM VAD & 0ms Dictionary)
Track / Domain:    AI Voice Roleplay / IELTS Speaking / Low-Latency Realtime Systems
Tech Stack:        Python 3.11+, FastAPI, Pydantic v2, Google GenAI (Gemini), Groq (LLaMA 3.3/3.1),
                   OpenAI (GPT-4o-mini), SQLite/LibSQL, WebAssembly (Silero VAD Wasm, SQLite3 Wasm),
                   Web AudioWorklet.
```

---

## 2. Vấn đề Thực tế & Mục tiêu Đột phá

### 🛑 3 Vấn đề Cốt lõi Hiện tại:
1. **Lỗi Parse JSON & Thiếu Ổn định khi Luân chuyển Multi-Provider (Quota Fallback Fragility):**
   - Hệ thống dùng nhiều provider miễn phí (Gemini, Groq, OpenAI). Khi một key/model bị dính rate limit (`429`), hệ thống chuyển đổi qua provider khác.
   - Code hiện tại phụ thuộc vào việc parse chuỗi thủ công (`_parse_raw_json`), tìm kiếm dấu `{` `}` và cắt markdown fence ````json ````. Khi các model nhỏ hoặc model khác nhau sinh output lệch format, code văng exception và phải rơi vào nhánh heuristic fallback.
2. **Độ trễ phản hồi giọng nói quá cao (Voice Latency Bottleneck):**
   - Ở mỗi lượt nói (turn), hệ thống gửi lặp lại toàn bộ Persona identity, bộ luật 20 cấp độ CEFR, tiêu chí chấm điểm IELTS và dialogues mẫu (> 1,200 tokens).
   - Điều này khiến giai đoạn Prefill của LLM mất từ 1.2s - 2.5s, làm mất đi tính tự nhiên của một cuộc đàm thoại tiếng Anh thời gian thực.
3. **Micro bị ngắt quãng sai & Tra từ điển bị trễ (Client Audio & Network Lag):**
   - Trình duyệt dùng `SpeechRecognition` tự động ngắt khi người học ngập ngừng suy nghĩ từ vựng (hesitation).
   - Mỗi lần nhấp vào từ trên màn hình để tra nghĩa, client lại gửi HTTP request về FastAPI, gây độ trễ 100-300ms trên mạng di động và làm nghẽn server.

---

### 🚀 3 Trụ Cột Giải Pháp (The 3 Pillars):

| Trụ cột | Công nghệ áp dụng | Mục tiêu đo lường được (Metrics) |
| :--- | :--- | :--- |
| **Trụ cột 1: Zero-Error Output** | **Constrained Decoding (Structured Outputs)** | **100% output chuẩn Pydantic schema**, 0% lỗi parsing JSON, triệt tiêu hoàn toàn rủi ro lệch format khi đổi model lúc cạn quota; tự động failover nếu model bị cắt cụt token. |
| **Trụ cột 2: Realtime Voice Response** | **Prompt Caching (KV-Cache Optimization)** | **TTFT $< 400\text{ms}$ trên Groq/OpenAI** (nhờ prefix $\approx 1,200$ tokens vượt ngưỡng 1k cache). Gemini 2.0 Flash chạy standard un-cached mượt mà không bị nghẽn prefill. |
| **Trụ cột 3: Edge/Client Intelligence** | **WebAssembly (WASM: Silero VAD + SQLite)** | **0ms tra từ điển offline** ngay trên RAM trình duyệt; VAD đo thời lượng phát âm thực tế ($\ge 1.5\text{s}$), State Machine nâng cấp AudioWorklet an toàn khi micro IDLE. |

---

## 3. Kiến trúc Tổng thể (High-Level Architecture)

```
[ Client Browser / PWA ]
   │
   ├── [ Audio State Machine: Silero VAD WASM ] ──▶ Đo thời lượng âm học >= 1.5s, timeout 3.5s (Chống ngắt mic)
   ├── [ In-Memory SQLite3 WASM Dictionary ] ────▶ Tra cứu từ vựng 0ms trực tiếp từ RAM
   │
   ▼ (Audio & Spoken Transcript + Clamped Acoustic Signals)
[ FastAPI Backend: app/core/ai_engine.py ]
   │
   ├── [ Prompt Constructor: Static (~1,200 tokens) vs Dynamic Partition ]
   │        ├── Static Prefix ──▶ [ KV-Cache Hit trên Groq/OpenAI ] ──▶ TTFT < 400ms
   │        └── Dynamic Suffix (Rolling History + Utterance)
   │
   ▼ (Strict Token Masking / to_strict_json_schema)
[ Multi-Provider LLM Pool (Pydantic Schema Source of Truth) ]
   ├── Google Gemini API (responseSchema)
   ├── Groq API (response_format: json_schema strict with $defs)
   └── OpenAI API (response_format: json_schema strict with $defs)
```

---

## 4. Definition of Done (DoD) Toàn Dự Án

- [ ] 100% cuộc gọi LLM trong `app/core/ai_engine.py` và `app/scoring/` đi qua Pydantic model validation và `to_strict_json_schema`, loại bỏ hoàn toàn các hàm regex cắt chuỗi JSON.
- [ ] Khi chuyển đổi linh hoạt giữa Gemini, Groq và OpenAI (mô phỏng key exhausted hoặc token truncation), hệ thống failover an toàn không gặp lỗi schema mismatch.
- [ ] Prompt được phân tách rõ ràng thành Static Cacheable Prefix (~1,200 tokens) với scenario angle cố định, log trace chứng minh TTFT $< 400\text{ms}$ trên Groq.
- [ ] Trình duyệt tích hợp VAD WASM hoạt động theo Audio Engine State Machine (chỉ promote lúc IDLE), tự động chốt câu khi khoảng lặng $\ge 3.5\text{s}$ và thời lượng nói $\ge 1.5\text{s}$.
- [ ] Tra cứu từ vựng trên bubble chat hoạt động ngay tức thì trong 0ms từ RAM thông qua SQLite WASM, tự động fallback API khi cần.
- [ ] Toàn bộ test suite Hermetic trong `tests/` và `python3 pipeline/scripts/verify.py` pass 100%.
