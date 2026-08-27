# PROJECT BRIEF
# Tóm tắt dự án — Doulingo Speaking AI Engine Redesign

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-26
>
> ✏️ **HUMAN FILLS THIS FILE.** File này định nghĩa bức tranh tổng thể, mục tiêu và phạm vi dự án.

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:          Doulingo Speaking AI Engine Redesign
Mô tả ngắn:        Tái cấu trúc AI Engine cho ứng dụng học nói tiếng Anh, giải quyết triệt để lỗi câu từ gượng gạo/lặp từ ở Level 1-3 và trôi level ở 9 nhân vật.
Repo Name:         Doulingo
Track / Domain:    AI Agent / Voice Pipeline Backend (FastAPI, LLM RAG Engine)
Độ khó:             Hard
Thời gian ước tính: 40 hours
Tech Stack:        Python 3.10+, FastAPI, Pytest, Gemini API, RAG (Vector Embedding & Metadata Filtering)
```

---

## 2. Mục tiêu Kinh doanh (Business Goals) & Vấn đề Cốt lõi

### Vấn đề cần giải quyết
- **Nói tiếng Anh không tự nhiên (Word Padding):** AI bị bọc quá nhiều ràng buộc cứng (`min_words: 35-70`, `Present Simple only`), dẫn đến sinh các câu vô nghĩa như *"Hello. I am good. You are good. We are here now."* ở Level 1.
- **Trôi Level & Áp dụng cục bộ:** Ràng buộc Prompt không phù hợp làm ảnh hưởng đến cả 9 nhân vật (Alex, Lily, Oscar...).
- **Xung đột Prompt & Ép kịch bản lộn xộn:** Ép `SCENARIO_ANGLES` nhập vai vào các chủ đề chào hỏi thông thường.
- **Thiếu cơ chế Feedback liên tục từ Người dùng:** Chưa có tính năng cho user đánh giá câu AI nói (`hollow` - Sáo rỗng, `out_of_context` - Sai ngữ cảnh, `good` - Tốt) để liên tục loại bỏ mẫu câu dở và lưu mẫu câu hay vào DB.

### Giải pháp & Mục tiêu
- **Cào & Seed Dữ liệu Ban Đầu (TASK-001):** Tự động cào/tạo từ vựng CEFR A1-B1 và bộ mẫu hội thoại ban đầu để người dùng kiểm duyệt.
- **Tổ chức Prompt 3 tầng độc lập (Option 3):** Core Pedagogy & Warmth $\rightarrow$ Persona Overlay $\rightarrow$ Adaptive CEFR Horizon.
- **Cơ chế Kiểm soát Level Thông minh (CoT JSON Call 1 + Heuristic Validation Loop):**
  - **Lần Call đầu tiên:** Yêu cầu LLM trả về Structured Output JSON (`natural_draft`, `vocab_check`, `final_response`) cho phép LLM tự do brainstorm và tự simplify.
  - **Heuristic Check (<5ms):** Đếm từ, ngữ pháp, tra từ điển CEFR trên `final_response`.
  - **Nếu PASS:** Xuất ngay kết quả (tốn đúng 1 API Call, chiếm đa số trường hợp).
  - **Nếu FAIL:** Đưa lỗi vi phạm vào retry loop nhỏ phản hồi cho LLM tự hạ cấp lại cho đến khi PASS.
- **RAG Câu thoại Mẫu (Exemplar Bank):** Retrieve động các câu mẫu chuẩn sư phạm theo (level, persona, topic, dialogue_act).
- **Tính năng Đánh giá Phản hồi & Cập nhật DB Liên tục (TASK-007):** API cho user rate câu (`hollow`, `out_of_context`, `good`). Tự động hạ điểm/blacklist câu dở và thêm câu hay vào Dialogue Bank.
- **Adaptive Level Detection:** Đo trình độ thực tế của user từ ASR transcript.

---

## 3. Ground Rules & Constraints (Quy tắc & Giới hạn nền tảng)

| Quy tắc | Chi tiết bắt buộc |
|---------|-------------------|
| **1. Dedicated Repo** | Duy trì codebase FastAPI hiện tại trong `/home/avandall/project/Doulingo` |
| **2. Stack & Environment** | Python 3.10+, pytest, Pydantic |
| **3. Secrets & Security** | `.env` chứa API Keys |
| **4. Performance Limit** | Giữ latency phản hồi LLM < 1.2s bằng cách ưu tiên 1 API Call |
| **5. AI-Assisted Guidelines** | Tuân thủ tuyệt đối quy trình Ralph Loop & Harness Engineering |

---

## 4. Phạm vi Dự án (Project Scope) & Key Concerns

### Core Features / Modules
- **`scripts/seed_data.py`**: Script cào & sinh dữ liệu ban đầu.
- **`app/core/heuristic_checker.py`**: Module kiểm tra trần từ vựng & độ dài câu siêu nhanh (<5ms).
- **`app/core/exemplar_rag.py`**: Hệ thống Hybrid RAG tìm kiếm câu mẫu theo Metadata + Embedding.
- **`app/core/ai_engine.py`**: Pipeline sinh câu thoại Structured Output JSON CoT + Heuristic Validation Loop.
- **`app/api/feedback_router.py`**: Endpoint tiếp nhận đánh giá (`hollow`, `out_of_context`, `good`) và cập nhật DB.
- **`app/data/`**: Bộ 6 tập dữ liệu (Vocab, Dialogue Bank, Persona, Topic, Feedback Log, Grammar, Gold-Set).

---

## 5. Kiến trúc Hệ thống (Architecture Overview)

```
[ User ASR Input ]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 1. Adaptive Level Detector & Topic Classifier          │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│ 2. Hybrid Exemplar RAG (Metadata Filter + Embedding)   │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│ 3. LLM Call 1: Structured JSON Output (CoT)            │
│    - natural_draft (Brainstorm tự nhiên)              │
│    - vocab_check (Tự soi từ khó)                      │
│    - final_response (Bản tự simplify)                 │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│ 4. Heuristic Level Checker (<5ms) trên final_response  │
└───────┬────────────────────────────────────────┬───────┘
        │ (PASS - Không vi phạm)                 │ (FAIL - Vẫn vi phạm trần Level)
        ▼                                        ▼
┌──────────────────────────────┐  ┌──────────────────────────────────────────────┐
│ Return final_response ngay   │  │ Retry Loop (Phản hồi từ vi phạm cho LLM      │
│ (Tốn 1 API call duy nhất)    │  │ tự hạ cấp lại cho tới khi Heuristic PASS)    │
└──────────────┬───────────────┘  └──────────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│ 5. User Feedback Rating ("hollow" / "out_of_context" / "good") │
│    ──> Cập nhật quality_score & Continuous DB Update   │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────┐
│ 6. Real-Time Streaming & Ultra-Low-Latency Pipeline   │
│    - Optimistic Client STT (~0ms)                      │
│    - Fast Voice LLM Utterance (35 tokens, <150ms)      │
│    - Micro-LLM Heuristic Rewriter (<150ms)             │
│    - Sentence-Level Chunked Edge-TTS (TTFA < 200ms)    │
│    - Background Evaluation Task (Grammar/Score/VI)     │
└────────────────────────────────────────────────────────┘
```

---

## 6. Definition of Done Checklist (Tiêu chí Hoàn thành)

- [ ] Toàn bộ 9 nhân vật không bao giờ sinh ra chuỗi câu lặp từ ngô nghê (*Hello. I am good. You are good...*).
- [ ] Level 1 trả lời tự nhiên (8-25 từ), đúng cấu trúc giao tiếp thông thường.
- [ ] Mọi API Call hoàn thành với Latency tối ưu (đa số lượt hoàn thành ở Call 1).
- [ ] Chức năng User Rating câu thoại ghi log và liên tục cập nhật dữ liệu tốt/dở vào DB.
- [ ] Automated unit tests trong `tests/` pass 100%.

---

## 7. Các Giai đoạn Phát triển (Roadmap / Phases)

```
Phase 1: Data Seeding, Core Infrastructure & Structured CoT Engine (TASK-001 -> TASK-004)
 Phase Gate: Seed Data, Heuristic Checker, RAG Exemplar Engine & Single-Call CoT Validation Loop hoàn thành.

Phase 2: Architecture Harmonization, Topic Softening & User Feedback (TASK-005 -> TASK-007)
 Phase Gate: Prompt 3 tầng áp dụng đồng bộ 9 nhân vật, Topic Bank & Response Rating API hoàn tất.

Phase 3: Advanced Validation & Adaptive Level Detection (TASK-008 -> TASK-009)
 Phase Gate: Grammar Bank & ASR Adaptive Level Detector hoàn tất.

Phase 4: Ultra-Low-Latency & Real-Time Voice Streaming Optimization (TASK-010 -> TASK-013)
 Phase Gate: Optimistic STT, Decoupled Fast Voice LLM, Micro-LLM Rewriter & Sentence-Level Chunked TTS hoàn tất (TTFA < 1.0s).
```
