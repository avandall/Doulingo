# PROJECT BRIEF
# Tóm tắt dự án — Duolingo Speak: Dynamic Material Bank Refactor

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-10 (Dựa trên `docs/solution2.md` và các file nguyên liệu `docs/DB*.md`)

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:        Duolingo Speak - Dynamic Material Bank Refactor
Mô tả ngắn:      Refactor hệ thống AI English Speaking App bằng kiến trúc Ngân hàng Nguyên liệu Động (Dynamic Material Bank) bóc tách từ tài liệu IELTS chuẩn (DB*.md) kết hợp Backend Prompt Factory và Turso Cloud DB (9GB Free Tier) nhằm tối ưu hóa chất lượng từ vựng academic, duy trì dữ liệu tồn tại vĩnh viễn trên Render, đảm bảo latency cực thấp (< 5ms prompt assembly) và tạo sự đa dạng 100% không lặp lại cho các phiên luyện nói.
Repo Name:        Doulingo_speak
Tech Stack:       Python 3.10+ / FastAPI, Pydantic, Markdown AST/Regex Parser, Turso DB (Cloud SQLite 9GB), LLMs (Groq / Gemini / Claude APIs), Edge TTS.
```

---

## 2. Mục tiêu Kinh doanh (Business Goals) & Vấn đề Cốt lõi

### 2.1 Vấn đề hiện tại (Core Pain Point)
1. **Nội dung chung chung, thiếu chuẩn IELTS:** Nội dung do Generative AI tự sinh tự do (pure generation) hoặc từ các scenario tĩnh (`app/scenarios.py`) thiếu từ vựng ăn điểm (collocations, idioms, phrasal verbs, academic structures) phân cấp theo band điểm IELTS.
2. **Trải nghiệm lặp lại (Repetitiveness):** Khi người dùng chọn cùng một Topic + Level nhiều lần, các câu hỏi và phản hồi từ AI dễ bị rập khuôn 100%.
3. **Render Ephemeral Disk Data Loss:** Deploy trên Render free tier làm mất sạch dữ liệu file SQLite local (`custom_topics.db`) sau 15 phút idle sleep hoặc redeploy.
4. **Độ trễ cao nếu dùng Vector RAG:** Việc triển khai RAG (Retrieval-Augmented Generation) hoặc Vector Database truyền thống gây tăng overhead latency đáng kể, không phù hợp cho ứng dụng giao tiếp thoại thời gian thực (Real-time Voice Conversation).

### 2.2 Giải pháp Kiến trúc: Dynamic Material Bank & Turso Cloud DB Architecture
Tránh sử dụng RAG/Vector Search cồng kềnh hoặc load kịch bản tĩnh. Thay vào đó:
- Coi các file `.md` tài liệu chuẩn IELTS (`docs/DB1_*.md` đến `docs/DB5_*.md`) như **Material Banks** (ngân hàng chứa các nguyên liệu hạt nhân) và thực hiện **Backend Dynamic Sampling & Prompt Assembly** tại server trước khi gọi LLM API.
- Tích hợp **Turso DB (Cloud SQLite - 9GB Free Tier)** cho phần dữ liệu người dùng (Custom Scenarios, Word Dictionary, User Stats) để duy trì dữ liệu vĩnh viễn trên Render mà không cần thay đổi dialect SQL.

---

## 3. Quy tắc Kiến trúc & Chỉ số Đầu ra (Core Architectural Rules & KPIs)

| Chỉ số / Quy tắc | Yêu cầu bắt buộc |
|------------------|------------------|
| **1. Ground Truth Material** | 100% nguyên liệu học thuật (Personas, Questions, Vocabulary, Grammar) phải được trích xuất từ bộ file `docs/DB*.md`. |
| **2. Cloud DB Persistence** | Dữ liệu custom scenarios và từ điển được lưu vĩnh viễn trên Turso DB (9GB Free Tier) thông qua `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN`. |
| **3. Prompt Assembly Latency** | Thuật toán bóc tách & sample nguyên liệu tại Backend Prompt Factory phải chạy dưới **5ms** (in-memory lookup). |
| **4. Non-Repetitive Sessions** | Cùng 1 Topic & Level, 2 lần bắt đầu phiên hội thoại kế tiếp phải chọn ngẫu nhiên Persona / Vocab / Question khác nhau. |
| **5. Structured Output Format** | AI Engine phải trả về đủ: `ai_response`, `ai_response_vi`, `user_feedback` (fluency, grammar correction, vocabulary suggestions). |
| **6. Multi-Provider Fallback** | Duy trì luồng fallback tự động qua danh sách API keys (Groq -> Gemini) và trace log chi tiết tại `logs/api_trace.log`. |

---

## 4. Phạm vi Dự án (Project Scope) & 5 Material Banks

### 4.1 Danh sách Material Banks (`docs/DB*.md`)
1. **`DB1_Personal_and_Daily_Life.md`**: Personal life, hometown, study, daily routines, habits, family, relationships.
2. **`DB2_Education_and_Career.md`**: Work, economy, employment, social equality, career development, financial literacy.
3. **`DB3_Society_and_Culture.md`**: Culture, traditions, environment, technology impact, social issues, community.
4. **`DB4_Science_Nature_and_Health.md`**: Science, health, fitness, nature, environment, technology, space.
5. **`DB5_Leisure_Entertainment_and_Media.md`**: Leisure, hobbies, music, movies, sports, media, arts, travel.

### 4.2 Cấu trúc Nguyên liệu hạt nhân (Material Bank Schema)
Mỗi Topic trong `DB*.md` tuân thủ Schema nguyên liệu chuẩn:
- **Metadata**: `topic_id`, `topic_name`, `target_levels`.
- **Persona Pool**: Các vai diễn AI (ví dụ: `[P1] Friendly Local Resident`, `[P2] Adventurous Backpacker`, `[P3] Strict IELTS Examiner`).
- **Question Pool**: Phân cấp theo Band:
  - Band 5.0 - 6.0 (Part 1 Focus)
  - Band 6.5+ (Part 2 & Part 3 Focus)
- **Vocabulary & Collocation Pool**: Phân cấp theo Band:
  - Intermediate (Band 5.5 - 6.5)
  - Advanced (Band 7.0+)
- **Grammar & Response Patterns**: Mẫu cấu trúc trả lời ăn điểm.

---

## 5. Flow Vận Hành Hệ Thống (Architectural Flow)

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                       LOCAL MATERIAL BANK (In-Memory Index)                       │
│  ├── docs/DB1_Personal_and_Daily_Life.md                                          │
│  ├── docs/DB2_Education_and_Career.md                                             │
│  ├── docs/DB3_Society_and_Culture.md                                              │
│  ├── docs/DB4_Science_Nature_and_Health.md                                        │
│  └── docs/DB5_Leisure_Entertainment_and_Media.md                                  │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼ (Parsed at startup < 50ms)
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND PROMPT FACTORY ENGINE                           │
│  1. Incoming Request: Topic ID + Level (e.g. Band 5.0-6.0)                        │
│  2. Dynamic Sampling Algorithm:                                                   │
│     - Pick 1 Persona from Persona Pool                                            │
│     - Sample 3-4 Focus Collocations matching Band                                 │
│     - Pick 1-2 Anchor Questions matching Band                                     │
│     - Pick 1 Response Pattern                                                     │
│  3. Assemble Custom System Prompt dynamically                                     │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼ (Latency < 5ms)
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              LLM GENERATIVE ENGINE                                │
│  - API Call with System Prompt + Temperature (0.75-0.85)                          │
│  - Multi-Key Provider Fallback & Latency Trace Logging                            │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                 DYNAMIC, HIGH-QUALITY IELTS VOICE CONVERSATION                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```
