"""
scripts/update_context_docs.py
==============================
Safely updates all files in pipeline/docs/context/:
- Tasks_list.md
- PROJECT_BRIEF.md
- TECH_CONTEXT.md
- BOUNDARIES.md
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "pipeline" / "docs" / "context"

# ==========================================
# 1. UPDATE Tasks_list.md
# ==========================================
tasks_list_path = BASE_DIR / "Tasks_list.md"
tasks_content = tasks_list_path.read_text(encoding="utf-8")

old_table_marker = "| `TASK-009` | Implement ASR Adaptive Level Detector (IRT Model) | Phase 3 | P2 | `[x] DONE` | Đo trình độ động từ transcript user |"
new_table_rows = """| `TASK-009` | Implement ASR Adaptive Level Detector (IRT Model) | Phase 3 | P2 | `[x] DONE` | Đo trình độ động từ transcript user |
| `TASK-010` | Optimistic Client-Side STT & Asynchronous Acoustic Extraction | Phase 4 | P0 | `[ ] TODO` | Triệt tiêu 2s chờ ASR lặp, gửi transcript ngay |
| `TASK-011` | Decoupled Fast Voice LLM & Background Evaluation Pipeline | Phase 4 | P0 | `[ ] TODO` | Tách luồng thoại siêu tốc (<40 tokens) vs chấm điểm ngầm |
| `TASK-012` | Micro-LLM Heuristic Retry Rewriter (Natural Contextual Downgrade) | Phase 4 | P1 | `[ ] TODO` | Retry tự nhiên bằng Micro-LLM thay vì thay từ cứng |
| `TASK-013` | Sentence-Level Streaming & Direct Chunked Audio Synthesis | Phase 4 | P0 | `[ ] TODO` | Stream audio câu đầu ngay lập tức (<1.0s TTFA) |"""

if old_table_marker in tasks_content and "TASK-010" not in tasks_content:
    tasks_content = tasks_content.replace(old_table_marker, new_table_rows)

phase_4_tasks_detail = """

---

### 📌 TASK-010: Optimistic Client-Side STT & Asynchronous Acoustic Extraction

#### Metadata
```
Task ID:         TASK-010
Task Name:       Optimistic Client-Side STT & Asynchronous Acoustic Extraction
Phase:           Phase 4 (Ultra-Low-Latency & Real-Time Voice Streaming Optimization)
Task Type:       perf
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-27
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Hiện tại `speech.js` đã nhận diện xong chữ qua Web Speech API ở trình duyệt nhưng lại chặn đứng luồng chờ đóng gói file `webm` upload lên server rồi gọi Groq/Gemini Whisper transcribe lại lần 2 (lãng phí 1.5s - 2.5s).
- **What:**
  1. Cập nhật `static/js/speech.js` để gửi ngay lập tức transcript sẵn có từ trình duyệt vào `/api/process_turn` (độ trễ ~0ms).
  2. Đẩy việc upload file ghi âm `webm` sang chế độ bất đồng bộ (Asynchronous Background) gửi lên `/api/audio/extract_acoustic_metrics` để tính WPM/Pauses/Pitch mà không chặn hội thoại.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Gửi transcript người dùng vào AI Engine ngay khi dứt lời mà không phải chờ đợi ASR server-side.
- [ ] Tính năng trích xuất chỉ số âm học (WPM, Pauses) vẫn hoạt động chính xác qua kênh nền.
- [ ] Pytest cho luồng STT & Audio router pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `static/js/speech.js`, `app/api/routers/audio.py`, `tests/test_optimistic_stt.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_optimistic_stt.py
```

---

### 📌 TASK-011: Decoupled Fast Voice LLM & Background Evaluation Pipeline

#### Metadata
```
Task ID:         TASK-011
Task Name:       Decoupled Fast Voice LLM & Background Evaluation Pipeline
Phase:           Phase 4 (Ultra-Low-Latency & Real-Time Voice Streaming Optimization)
Task Type:       perf
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-27
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Prompt hiện tại ép LLM sinh toàn bộ JSON CoT, bảng chấm điểm ngữ pháp, phát âm, dịch tiếng Việt (~450 tokens) làm LLM 70B mất 3.5s - 5.0s mới sinh xong.
- **What:**
  1. Bóc tách thành 2 luồng:
     - **Fast Voice LLM:** Sử dụng model siêu tốc (`llama-3.1-8b-instant` trên Groq hoặc `gemini-2.5-flash`) chỉ sinh **duy nhất câu thoại của AI** (~30-40 tokens plain text trong 50-150ms).
     - **Async Evaluation Task:** Đẩy toàn bộ việc phân tích ngữ pháp, chấm điểm IELTS, gợi ý câu bản xứ và ghi nhật ký Error Journal vào `FastAPI BackgroundTasks`.
  2. Cung cấp endpoint nhận kết quả đánh giá feedback nền để UI cập nhật mượt mà sau khi AI đã cất lời.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Thời gian LLM sinh câu thoại giảm xuống < 400ms.
- [ ] Bảng đánh giá chi tiết (Grammar, Fluency, Translation) vẫn được tính toán chuẩn xác và gửi về client qua kênh ngầm.
- [ ] Pytest cho Decoupled Engine pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/core/ai_engine.py`, `app/api/routers/chat.py`, `tests/test_decoupled_voice_llm.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_decoupled_voice_llm.py
```

---

### 📌 TASK-012: Micro-LLM Heuristic Retry Rewriter (Natural Contextual Downgrade)

#### Metadata
```
Task ID:         TASK-012
Task Name:       Micro-LLM Heuristic Retry Rewriter (Natural Contextual Downgrade)
Phase:           Phase 4 (Ultra-Low-Latency & Real-Time Voice Streaming Optimization)
Task Type:       feat
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-27
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Việc giữ LLM retry loop là cần thiết để câu nói tự nhiên (tránh thay từ đồng nghĩa máy móc), nhưng gọi lại cả prompt dài 450 tokens tốn thêm 3-4s.
- **What:**
  1. Tối ưu Retry Loop thành **Micro-LLM Targeted Rewriter**: Khi phát hiện từ vi phạm trần CEFR, chỉ trích xuất đúng câu chứa lỗi + danh sách từ vượt trần và gửi vào 1 prompt tinh gọn cho Fast 8B model: *"Rewrite this sentence for CEFR Level {level} using simpler natural words replacing [{violating_words}]: '{sentence}'"*.
  2. Thời gian retry giảm từ 3.5s xuống còn **~120ms** mà câu vẫn giữ nguyên phong thái tự nhiên 100%.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Khi Heuristic Checker phát hiện vi phạm trần từ vựng, Micro-LLM hạ cấp câu tự nhiên trong < 200ms.
- [ ] Không làm phá vỡ văn phong nhân vật hay tạo ra câu chắp vá kỳ quặc.
- [ ] Pytest cho Micro-LLM Rewriter pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/core/heuristic_checker.py`, `app/core/ai_engine.py`, `tests/test_micro_rewrite.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_micro_rewrite.py
```

---

### 📌 TASK-013: Sentence-Level Streaming & Direct Chunked Audio Synthesis

#### Metadata
```
Task ID:         TASK-013
Task Name:       Sentence-Level Streaming & Direct Chunked Audio Synthesis
Phase:           Phase 4 (Ultra-Low-Latency & Real-Time Voice Streaming Optimization)
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-27
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Hiện tại frontend chờ đợi nhận toàn bộ đoạn văn, sau đó chờ TTS render 100% file MP3 rồi mới phát (mất thêm 2.0s - 3.0s).
- **What:**
  1. Tách stream LLM theo ranh giới câu đầu tiên (dấu chấm, chấm hỏi, chấm than).
  2. Bắn ngay câu 1 vào `stream_edge_tts()` để truyền audio stream về trình duyệt qua URL/SSE.
  3. Frontend phát âm thanh ngay từ chunk đầu tiên (Native Audio Streaming với TTFA < 200ms) trong khi các câu tiếp theo được tổng hợp nối tiếp mượt mà.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Time-To-First-Audio (TTFA) của toàn bộ hệ thống đạt dưới 1.0 giây từ lúc user dứt lời.
- [ ] Âm thanh phát mượt mà, không bị giật hay ngắt quãng giữa các câu.
- [ ] Pytest cho streaming audio pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/audio/tts_service.py`, `app/api/routers/audio.py`, `static/js/app.js`, `tests/test_sentence_stream.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_sentence_stream.py
```
"""

if "TASK-010" not in tasks_content:
    tasks_content += phase_4_tasks_detail
tasks_list_path.write_text(tasks_content, encoding="utf-8")
print("Tasks_list.md updated.")


# ==========================================
# 2. UPDATE PROJECT_BRIEF.md
# ==========================================
brief_path = BASE_DIR / "PROJECT_BRIEF.md"
brief_content = brief_path.read_text(encoding="utf-8")

if "Phase 4" not in brief_content:
    old_roadmap_tail = "Phase 3: Advanced Validation & Adaptive Level Detection (TASK-008 -> TASK-009)\n Phase Gate: Grammar Bank & ASR Adaptive Level Detector hoàn tất."
    new_roadmap_tail = """Phase 3: Advanced Validation & Adaptive Level Detection (TASK-008 -> TASK-009)
 Phase Gate: Grammar Bank & ASR Adaptive Level Detector hoàn tất.

Phase 4: Ultra-Low-Latency & Real-Time Voice Streaming Optimization (TASK-010 -> TASK-013)
 Phase Gate: Optimistic STT, Decoupled Fast Voice LLM, Micro-LLM Rewriter & Sentence-Level Chunked TTS hoàn tất (TTFA < 1.0s)."""
    brief_content = brief_content.replace(old_roadmap_tail, new_roadmap_tail)

    # Add Phase 4 to System Architecture
    old_arch = """┌────────────────────────────────────────────────────────┐
│ 5. User Feedback Rating ("hollow" / "out_of_context" / "good") │
│    ──> Cập nhật quality_score & Continuous DB Update   │
└────────────────────────────────────────────────────────┘"""

    new_arch = """┌────────────────────────────────────────────────────────┐
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
└────────────────────────────────────────────────────────┘"""
    brief_content = brief_content.replace(old_arch, new_arch)
    brief_path.write_text(brief_content, encoding="utf-8")
    print("PROJECT_BRIEF.md updated.")


# ==========================================
# 3. UPDATE TECH_CONTEXT.md
# ==========================================
tech_path = BASE_DIR / "TECH_CONTEXT.md"
tech_content = tech_path.read_text(encoding="utf-8")

if "Phase 4" not in tech_content:
    tech_update = """

---

## 5. Ultra-Low-Latency & Voice Streaming Architecture (Phase 4)

### Latency Budget Target
```
End-to-End Latency Target:   < 1.0s (Time-To-First-Audio / TTFA)
Client-Side Optimistic STT:  ~0ms - 50ms (Web Speech API)
Fast Voice LLM Inference:    100ms - 250ms (Llama-3.1-8B-Instant / Gemini-2.5-Flash)
Micro-LLM Rewrite (if needed): 100ms - 150ms (Targeted sentence simplification)
Chunked Edge-TTS Stream:     150ms - 250ms (Direct MP3 chunk streaming)
Async Background Evaluation: Offloaded to FastAPI BackgroundTasks (Non-blocking)
```

### Decoupled Voice vs Evaluation Flow
```
User Speech Ends
      │
      ├─► [Fast Voice Track]: LLM (35 tokens) ──► Sentence-Level Chunked TTS ──► Audio Plays (<1.0s)
      │
      └─► [Async Background Track]: Acoustic Extraction + Grammar Analysis + Scoring + VI Trans (Non-blocking)
```
"""
    tech_content += tech_update
    tech_path.write_text(tech_content, encoding="utf-8")
    print("TECH_CONTEXT.md updated.")


# ==========================================
# 4. UPDATE BOUNDARIES.md
# ==========================================
boundaries_path = BASE_DIR / "BOUNDARIES.md"
boundaries_content = boundaries_path.read_text(encoding="utf-8")

if "Phase 4" not in boundaries_content:
    boundaries_update = """

---

## 3. Real-Time Streaming & Latency Boundaries (Phase 4)

### AI được phép quyết định:
```
✅ Chuyển đổi giữa streaming chunk và full buffer trong TTS
✅ Cấu trúc prompt cho Micro-LLM Rewriter và Fast Voice Track
✅ Phân luồng giữa Synchronous Response và FastAPI BackgroundTasks
```

### Quy tắc bất di bất dịch:
```
🔒 Phải giữ chất lượng câu văn tự nhiên khi hạ cấp level (dùng Micro-LLM, không thay thế từ đồng nghĩa máy móc).
🔒 Toàn bộ chỉ số chấm điểm (Fluency, Grammar, Native Phrasing) phải tiếp tục hoạt động đầy đủ qua BackgroundTasks.
```
"""
    boundaries_content += boundaries_update
    boundaries_path.write_text(boundaries_content, encoding="utf-8")
    print("BOUNDARIES.md updated.")

print("ALL CONTEXT FILES REFRESHED SUCCESSFULLY!")
