# PROJECT BRIEF
# Tóm tắt dự án — Duolingo Speak: Architecture Refactor (Blueprint 2026 v2)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-11 (Dựa trên `docs/plan.md`, `Tasks_list.md` v2 & `6_important_tasks_solution.md`)

---

## 1. Tên & Mô tả Dự án

```
Tên dự án:        Duolingo Speak - Next-Gen AI Speaking Architecture Refactor
Mô tả ngắn:      Refactor toàn bộ hệ thống AI English Speaking App từ mô hình sample kịch bản tĩnh sang Kiến trúc AI Kép (Conversational Agent + Silent Scoring Agent), hệ thống Retrieval Layer (RAG) với Database Schema hợp nhất (Content Units), Scoring Agent 2 tầng (Real-time & Deep Scorer), Adaptive Difficulty Engine, AI Persona kèm bộ nhớ dài hạn, Sổ lỗi cá nhân dệt vào hội thoại mới và Data Flywheel tự làm giàu dữ liệu.
Repo Name:        Doulingo_speak
Tech Stack:       Python 3.10+ / FastAPI, Pydantic v2, PostgreSQL + pgvector, spaCy / LanguageTool, Edge TTS / Streaming ASR, LLMs (Groq / Gemini / Claude APIs).
Tài liệu Spec:    H_docs/context/6_important_tasks_solution.md (Spec kỹ thuật chi tiết cho 6 task rủi ro cao nhất: TASK-010, TASK-011, TASK-005/015, TASK-004, TASK-013, TASK-022/023)
```

---

## 2. Mục tiêu Kinh doanh & Vấn đề Cốt lõi

### 2.1 Vấn đề hiện tại (Core Pain Point)
1. **Thiên vị & Không ổn định khi chấm điểm (Single Agent Bias):** AI vừa đóng vai trò người đối thoại vừa tự đánh giá band điểm của chính cuộc hội thoại do nó tạo ra, dẫn đến kết quả không khách quan và nhảy band lung tung.
2. **Loãng ngữ cảnh & Tốn chi phí (Prompt Bloat):** Việc nhét toàn bộ kịch bản hoặc tài liệu vào System Prompt gây tốn token, độ trễ cao và làm loãng ngữ cảnh.
3. **Cảm giác thi cử thay vì trò chuyện thật (Evaluation Anxiety):** Hiển thị điểm số real-time sau mỗi câu khiến người dùng căng thẳng, mất tự nhiên khi luyện nói.
4. **Hội thoại bị lặp lại & Thiếu trí nhớ (Repetitive & Forgetful):** AI không nhớ các chi tiết cá nhân người dùng từng chia sẻ và lặp lại các câu hỏi motif cũ.
5. **Dữ liệu đóng băng (Static Content):** Nội dung ứng dụng bị phụ thuộc hoàn toàn vào các file tài liệu ban đầu từ sách, không tự mở rộng hay làm mới theo câu trả lời xuất sắc của người dùng thật.

### 2.2 Giải pháp Kiến trúc Master (`docs/plan.md` & `6_important_tasks_solution.md`)
1. **Tách 2 vai trò AI độc lập:**
   - **Conversational Agent (Diễn viên):** LLM tạo câu nói tự nhiên, hấp dẫn. Trả về JSON chứa `ai_utterance`, `internal_band_signal`, `topic_tag`, `difficulty_adjustment`.
   - **Scoring Agent (Giám khảo âm thầm):** Model/pipeline riêng bám rubric 4 trục (Fluency, Lexical, Grammar, Pronunciation), chạy song song, không lộ diện.
2. **Pipeline 5 bước thời gian thực:** `[1] Voice Input` -> `[2] Streaming ASR + Scoring Agent (Tầng 1 <300ms)` -> `[3] Retrieval Layer (SQL + pgvector sample_dialogues)` -> `[4] Prompt Constructor` -> `[5] Conversational Agent (LLM structured output)`.
3. **Scoring Agent 2 tầng & Calibration Bootstrap:**
   - **Phase 1.5 Calibration (`TASK-010`):** Hiệu chỉnh anchor points từ corpus học thuật thực tế (`scripts/calibrate_thresholds.py`), lưu config versioned `config/scoring_anchors.v{N}.json`, KHÔNG dùng magic numbers hardcode.
   - **Tầng 1 (Real-time Scorer, <300ms - `TASK-011`):** WPM, tỷ lệ khoảng lặng, filler words, self-correction, MTLD từ vựng $\rightarrow$ đưa ra `difficulty_adjustment` tức thì (không persist DB).
   - **Tầng 2 (Deep Scorer / LLM-as-Judge, chạy nền - `TASK-012`):** Phân tích cú pháp (spaCy), độ phức tạp ngữ pháp, MTLD, phát âm GOP $\rightarrow$ cập nhật EMA band chính thức qua `TASK-013`.
4. **Trải nghiệm cá nhân hóa & Mô phỏng đời thực:**
   - Persona AI có trí nhớ dài hạn (entity summary).
   - Ẩn điểm real-time, chuyển sang Báo cáo tuần (Weekly Performance Report).
   - Sổ lỗi cá nhân (Error Journal) dệt lỗi cũ vào tình huống mới (Interleaved practice).
5. **Data Flywheel & PII Protection:** Thu hoạch câu trả lời band cao của user thật qua module PII Scrubber (`TASK-022`) và Review Queue (`TASK-023`) đưa ngược vào Database để làm giàu dữ liệu tự động.

---

## 3. Quy tắc Kiến trúc & Chỉ số Đầu ra (Core Architectural Rules & KPIs)

| Chỉ số / Quy tắc | Yêu cầu bắt buộc |
|------------------|------------------|
| **1. Dual-Agent Separation** | 100% không cho Conversational Agent tự chấm điểm chính mình. Scoring Agent phải chạy độc lập. |
| **2. Retrieval Latency & Fallback** | Tầng RAG Retrieval query `sample_dialogues` (lọc band + topic + vector search + loại trừ lặp) phải chạy dưới **30ms**. Có cơ chế Fallback Cascade khi kết quả strict < 2 items. |
| **3. Real-Time Scorer Latency** | Tầng 1 Scoring Agent phải hoàn tất dưới **300ms** để cung cấp `difficulty_adjustment` cho lượt hội thoại kế tiếp. Đọc anchor points từ versioned config `TASK-010`. |
| **4. Structured Output Format** | Conversational Agent phải trả về đúng Schema JSON (`ai_utterance`, `internal_band_signal`, `topic_tag`, `difficulty_adjustment`). |
| **5. Cumulative Timestamps ASR** | Streaming ASR phải duy trì `cumulative_offset_sec` từ số sample audio, không dùng wall-clock server nhận chunk. |
| **6. EMA Band Smoothing with Confidence** | Điểm band chính thức cập nhật theo công thức `EMA(band_cu, raw_score, alpha=effective_alpha)` với `effective_alpha` tính động dựa trên word count & confidence factor. |
| **7. PII Safety in Data Flywheel** | 100% dữ liệu harvest phải đi qua `check_pii()` từ `TASK-022` với chính sách REJECT-FIRST trước khi vào `harvest_review_queue`. |

---

## 4. Kế hoạch Triển khai 25 Tasks (Master Roadmap v2)

- **Giai đoạn 0 — Nền dữ liệu (Tasks 000–003):** Schema DB PostgreSQL+pgvector (`content_units`, `sample_dialogues`, `hook_bank`, `vocabulary_lookup`), ingest script, unit tests, admin CLI tool.
- **Giai đoạn 1 — MVP Pipeline (Tasks 004–009):** Streaming ASR chunk processor (cumulative offset), RAG Retrieval v1 (fallback cascade), Prompt Constructor, Conversational Agent JSON output, TTS Streamer (P0), MVP End-to-End API.
- **Giai đoạn 1.5 — Calibration Bootstrap (Task 010):** Scoring threshold calibration script & versioned JSON config export.
- **Giai đoạn 2 — Scoring Agent & Adaptive Difficulty (Tasks 011–015):** Tier 1 Scorer (<300ms, ephemeral signal), Tier 2 Deep Scorer, Dynamic User Profile & EMA Band Smoothing (alpha động), Cold-Start Diagnostic Probe, Adaptive Retrieval Integration.
- **Giai đoạn 3 — Anti-Repetition, Persona & Memory (Tasks 016–018):** Embedding anti-repetition check, Persona AI cố định với entity memory, ẩn điểm real-time, Báo cáo tuần.
- **Giai đoạn 4 — Simulation & Interleaved Practice (Tasks 019–021):** Scenario nhập vai đời thực, Error journal & dệt lỗi cũ, Adaptive Multi-Armed Bandit difficulty engine.
- **Giai đoạn 5 — Data Flywheel & Quality Control (Tasks 022–024):** PII Scrubber module độc lập, High-band user answer harvest pipeline (review queue), Scoring model drift benchmark định kỳ.
