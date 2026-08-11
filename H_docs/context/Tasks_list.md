# TASKS LIST (v2 — đã hiệu chỉnh)
# Danh sách tác vụ & Queue thực thi — Master Refactoring Plan (`docs/plan.md`)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-11 (v2)
>
> ✏️ **HUMAN FILLS THIS FILE.** Danh sách task được thiết kế hoàn chỉnh từ `docs/plan.md`.
> 🤖 **AI EXECUTION RULE:** AI sẽ đọc danh sách này từ trên xuống dưới, tìm task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS` để thực thi trong từng phiên Ralph Loop. Khi hoàn thành task, AI đánh dấu `[x] DONE` và chuyển sang task tiếp theo.
> ⚠️ **LƯU Ý:** Không push code lên GitHub.
>
> **Thay đổi so với bản v1** (lý do sửa, xem chi tiết đánh giá trong chat):
> 1. Thêm `TASK-010` mới — **Scoring Threshold Bootstrap & Calibration Config** — chuyển phần hiệu chỉnh ngưỡng lên TRƯỚC Tier 1/Tier 2 thay vì để cuối Phase 5. Mọi TASK từ Tier 1 trở đi được đánh số lại (dịch xuống 1 bậc).
> 2. Thêm `TASK-022` mới — **PII Scrubbing Module** — tách riêng khỏi Data Flywheel thành module độc lập, test được riêng.
> 3. `TASK-008` (TTS) nâng từ P1 → P0 vì nằm trong đường găng MVP.
> 4. `TASK-001` bổ sung rõ acceptance criteria cho `hook_bank` và `vocabulary_lookup`.
> 5. Sửa dependency thiếu ở `TASK-016`, `TASK-017`, `TASK-018`, `TASK-020`, `TASK-019` (theo số mới).
> 6. `TASK-024` (cũ TASK-022) thu hẹp phạm vi — chỉ còn giám sát trôi lệch định kỳ, vì phần bootstrap ban đầu đã tách sang `TASK-010`.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Phụ thuộc |
|---------|----------|-------|---------|------------|-----------|
| `TASK-000` | Database Schema Design & Migration (`content_units`, `sample_dialogues`, etc.) | Phase 0 | P0 | `[ ] TODO` | None |
| `TASK-001` | Template Ingestion Engine & Vector Embeddings (`scripts/ingest_templates.py`) | Phase 0 | P0 | `[ ] TODO` | TASK-000 |
| `TASK-002` | Data Ingestion Verification & Retrieval Unit Tests (`tests/test_ingestion.py`) | Phase 0 | P0 | `[ ] TODO` | TASK-001 |
| `TASK-003` | Admin CLI & Content Validation Tool (`scripts/admin_content_cli.py`) | Phase 0 | P2 | `[ ] TODO` | TASK-001 |
| `TASK-004` | Streaming ASR Ingestion & Chunk Processor (`app/asr_processor.py`) | Phase 1 | P0 | `[ ] TODO` | TASK-000 |
| `TASK-005` | RAG Retrieval Layer v1 (`app/retrieval.py`) | Phase 1 | P0 | `[ ] TODO` | TASK-001 |
| `TASK-006` | Prompt Constructor Engine v1 (`app/prompt_constructor.py`) | Phase 1 | P0 | `[ ] TODO` | TASK-005 |
| `TASK-007` | Conversational Agent & Structured JSON Parser (`app/conversational_agent.py`) | Phase 1 | P0 | `[ ] TODO` | TASK-006 |
| `TASK-008` | TTS Audio Output Streamer (`app/tts_streamer.py`) | Phase 1 | **P0** ⬆️ | `[ ] TODO` | TASK-007 |
| `TASK-009` | MVP End-to-End Pipeline & API Endpoints Bridge (`app/main.py`) | Phase 1 | P0 | `[ ] TODO` | TASK-004..008 |
| `TASK-010` | 🆕 **Scoring Threshold Bootstrap & Calibration Config** (`scripts/calibrate_thresholds.py`) | Phase 1.5 | P0 | `[ ] TODO` | TASK-000 |
| `TASK-011` | Real-Time Scoring Agent — Tier 1 Scorer (<300ms) (`app/scoring/tier1_realtime.py`) | Phase 2 | P0 | `[ ] TODO` | TASK-004, TASK-010 |
| `TASK-012` | Deep Scoring Agent — Tier 2 Scorer & Grammar Check (`app/scoring/tier2_deep.py`) | Phase 2 | P1 | `[ ] TODO` | TASK-004, TASK-010 |
| `TASK-013` | Dynamic User Profile & EMA Band Smoothing Engine (`app/user_profile_engine.py`) | Phase 2 | P0 | `[ ] TODO` | TASK-012 |
| `TASK-014` | Cold-Start Diagnostic Probe System (`app/scoring/cold_start.py`) | Phase 2 | P1 | `[ ] TODO` | TASK-013 |
| `TASK-015` | Adaptive Retrieval & Difficulty Adjustment Integration (`app/retrieval.py`) | Phase 2 | P0 | `[ ] TODO` | TASK-005, TASK-011, TASK-013 |
| `TASK-016` | Embedding Anti-Repetition Engine (`app/anti_repetition.py`) | Phase 3 | P1 | `[ ] TODO` | TASK-005, **TASK-007** ⬅️ sửa |
| `TASK-017` | AI Persona Identity & Long-Term Entity Memory System (`app/persona_memory.py`) | Phase 3 | P1 | `[ ] TODO` | TASK-007, **TASK-006** ⬅️ sửa |
| `TASK-018` | Weekly Performance Reporting Engine & Hidden Scoring UI (`app/reporting.py`) | Phase 3 | P2 | `[ ] TODO` | TASK-013, **TASK-012** ⬅️ sửa |
| `TASK-019` | Real-World Roleplay Simulation Engine (`app/scenarios/simulation_engine.py`) | Phase 4 | P1 | `[ ] TODO` | TASK-017, **TASK-001, TASK-015** ⬅️ sửa |
| `TASK-020` | Personal Error Journal & Interleaved Practice Weaver (`app/error_journal.py`) | Phase 4 | P1 | `[ ] TODO` | TASK-012, **TASK-006** ⬅️ sửa |
| `TASK-021` | Multi-Armed Bandit / Adaptive Spaced Repetition Engine (`app/adaptive_engine.py`) | Phase 4 | P2 | `[ ] TODO` | TASK-015, **TASK-001** ⬅️ sửa |
| `TASK-022` | 🆕 **PII Scrubbing Module** (`app/data_quality/pii_scrubber.py`) | Phase 5 | P0 | `[ ] TODO` | None |
| `TASK-023` | High-Band User Answer Harvest Pipeline (`app/data_flywheel.py`) | Phase 5 | P2 | `[ ] TODO` | TASK-013, TASK-012, **TASK-022** ⬅️ sửa |
| `TASK-024` | Scoring Model Drift Benchmark (định kỳ, không phải bootstrap ban đầu) (`scripts/benchmark_calibration.py`) | Phase 5 | P2 | `[ ] TODO` | TASK-012, TASK-010 |

---

## 2. Chi tiết các Tasks (Task Specs)

---

### 📌 TASK-000: Database Schema Design & Migration (`content_units`, `sample_dialogues`, etc.)

#### Metadata
```
Task ID:         TASK-000
Task Name:       Database Schema Design & Migration (`content_units`, `sample_dialogues`, etc.)
Phase:           Phase 0 (Data Foundation)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Toàn bộ dữ liệu Template A, B, C từ sách IELTS và thông tin người dùng cần được lưu trữ trong Database quan hệ hỗ trợ Vector Search (PostgreSQL + pgvector) theo Schema thiết kế tại mục 7 của `docs/plan.md`.
- **What:** Tạo module migration `app/db.py` khởi tạo đầy đủ các bảng: `content_units`, `band_tiers`, `function_details`, `function_band_variants`, `scenarios`, `scenario_branches`, `evaluation_hooks`, `sample_dialogues`, `hook_bank`, `vocabulary_lookup`, `user_profile`, `user_content_exposure`.

#### Acceptance Criteria
- [ ] Thiết kế và tạo thành công DDL cho 12 bảng trong `app/db.py`.
- [ ] Bảng `sample_dialogues` có cột `embedding` kiểu Vector(1536) và chỉ mục HNSW cosine vector index.
- [ ] Bảng `content_units` hỗ trợ chỉ mục GIN trên `topic_tags` và B-Tree trên `target_band_min/max`.
- [ ] Đảm bảo script khởi tạo DB chạy mượt mà không lỗi foreign key hay constraint.

---

### 📌 TASK-001: Template Ingestion Engine & Vector Embeddings (`scripts/ingest_templates.py`)

#### Metadata
```
Task ID:         TASK-001
Task Name:       Template Ingestion Engine & Vector Embeddings (`scripts/ingest_templates.py`)
Phase:           Phase 0 (Data Foundation)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Các file template tĩnh `.md` (hoặc YAML/JSON bóc tách từ sách) cần được convert tự động và nạp vào DB kèm vector embeddings cho `sample_dialogues`.
- **What:** Viết script `scripts/ingest_templates.py` đọc dữ liệu Template A (Progressive Band Ladder), Template B (Functional Bank), và Template C (Scenario), tạo record vào `content_units` và tạo vector embedding qua API/Local model cho từng `sample_dialogue`.

#### Acceptance Criteria
- [ ] Parse thành công 100% dữ liệu từ các file template mẫu.
- [ ] Map chính xác thông tin vào `content_units`, `band_tiers`, `function_details`, `scenarios`.
- [ ] **Map chính xác dữ liệu phụ lục vào `hook_bank` (hook + anti_cliche) và `vocabulary_lookup` (theo category/tier) — 2 bảng này hay bị bỏ sót vì không nằm trong nội dung chính của mỗi file template.** ⬅️ bổ sung
- [ ] Sinh vector embedding 1536 chiều cho mỗi `sample_dialogue` và lưu vào DB.
- [ ] Với Template B (gộp nhiều function trong 1 file): mỗi function phải tách thành 1 `content_unit` riêng biệt, KHÔNG gộp chung 1 row.
- [ ] Xử lý transaction batching để tối ưu thời gian nạp dữ liệu.

---

### 📌 TASK-002: Data Ingestion Verification & Retrieval Unit Tests (`tests/test_ingestion.py`)

#### Metadata
```
Task ID:         TASK-002
Task Name:       Data Ingestion Verification & Retrieval Unit Tests (`tests/test_ingestion.py`)
Phase:           Phase 0 (Data Foundation)
Task Type:       test
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Đảm bảo dữ liệu được nạp vào DB đầy đủ, đúng ràng buộc và câu query mẫu tại mục 7.4 `docs/plan.md` hoạt động chính xác.
- **What:** Tạo unit test `tests/test_ingestion.py`.

#### Acceptance Criteria
- [ ] Verify số lượng `content_units` và `sample_dialogues` trong DB > 0.
- [ ] Test câu query retrieval mẫu (SQL filter topic + band + exclude exposed + vector search) đạt kết quả đúng.
- [ ] Test integrity của các ràng buộc khoá ngoại (Foreign Keys).
- [ ] Chạy `pytest tests/test_ingestion.py` pass 100%.

---

### 📌 TASK-003: Admin CLI & Content Validation Tool (`scripts/admin_content_cli.py`)

#### Metadata
```
Task ID:         TASK-003
Task Name:       Admin CLI & Content Validation Tool (`scripts/admin_content_cli.py`)
Phase:           Phase 0 (Data Foundation)
Task Type:       tool
Priority:        P2-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Tránh lệch chuẩn schema khi người nhập liệu tiếp tục thêm các cuốn sách IELTS khác vào Database.
- **What:** Viết công cụ dòng lệnh `scripts/admin_content_cli.py` để validate file template mới trước khi nạp vào DB.

#### Acceptance Criteria
- [ ] CLI hỗ trợ lệnh `validate <file_path>` kiểm tra các trường bắt buộc (metadata, band_tiers, sample_dialogues).
- [ ] Cảnh báo nếu câu mẫu quá ngắn hoặc thiếu tag chức năng.
- [ ] CLI hỗ trợ lệnh `import <file_path>` nạp file đã validate vào DB.

---

### 📌 TASK-004: Streaming ASR Ingestion & Chunk Processor (`app/asr_processor.py`)

#### Metadata
```
Task ID:         TASK-004
Task Name:       Streaming ASR Ingestion & Chunk Processor (`app/asr_processor.py`)
Phase:           Phase 1 (MVP Pipeline)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Nhận giọng nói từ user theo từng chunk câu, giữ lại audio + word-level timestamps để làm đầu vào cho ASR transcript và Scoring Agent.
- **What:** Xây dựng `app/asr_processor.py` xử lý streaming audio input, trích xuất text transcript và mảng `word_timestamps`.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 3 — bắt buộc tính `cumulative_offset_sec` từ số sample audio (`len(chunk)/sample_rate`), KHÔNG từ wall-clock thời điểm server nhận chunk.

#### Acceptance Criteria
- [ ] Xử lý audio stream theo chunk câu ngắn (khuyến nghị cắt theo VAD/silence, không cắt cứng theo thời gian cố định — xem SPEC 3 mục 3.2).
- [ ] Trả về transcript văn bản và word-level timestamps (`word`, `start_time`, `end_time`, `confidence`), timestamps đơn điệu tăng qua toàn bộ session.
- [ ] Giữ đệm audio gốc phục vụ tính điểm phát âm (Pronunciation GOP).

---

### 📌 TASK-005: RAG Retrieval Layer v1 (`app/retrieval.py`)

#### Metadata
```
Task ID:         TASK-005
Task Name:       RAG Retrieval Layer v1 (`app/retrieval.py`)
Phase:           Phase 1 (MVP Pipeline)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Thực hiện bước [3] trong pipeline 5 bước — lấy 2-4 `sample_dialogues` liên quan nhất từ DB theo band, topic và loại trừ nội dung lặp.
- **What:** Xây dựng `app/retrieval.py` thực thi SQL hybrid query (Lọc cứng metadata band + topic + SQL NOT IN exposure history 30 ngày + Vector similarity search) **trong CÙNG MỘT câu SQL**, không lọc 2 pha bằng Python sau khi lấy top-K vector.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 2 — bao gồm cơ chế fallback cascade bắt buộc khi query strict trả về quá ít kết quả.
- **Lưu ý thiết kế cho tương lai:** hàm nên nhận tham số `band_min`/`band_max` truyền vào từ ngoài (không hardcode trong hàm), để `TASK-015` sau này chỉ cần truyền band window đã điều chỉnh mà không phải viết lại query.

#### Acceptance Criteria
- [ ] Lấy chính xác 2-4 đoạn thoại tham khảo phù hợp nhất cho lượt hội thoại, dùng 1 câu SQL kết hợp filter + vector rank.
- [ ] Có cơ chế fallback cascade (nới exposure window → nới band → bỏ topic filter) khi kết quả strict < 2 items, có log cảnh báo mỗi lần fallback kích hoạt.
- [ ] Tự động ghi log lượt xuất hiện vào bảng `user_content_exposure`.
- [ ] Tốc độ truy vấn RAG < 30ms ở tập dữ liệu nhỏ, < 500ms ở p95 với > 100k rows (test riêng bằng dataset lớn, không chỉ DB rỗng/nhỏ).

---

### 📌 TASK-006: Prompt Constructor Engine v1 (`app/prompt_constructor.py`)

#### Metadata
```
Task ID:         TASK-006
Task Name:       Prompt Constructor Engine v1 (`app/prompt_constructor.py`)
Phase:           Phase 1 (MVP Pipeline)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Thực hiện bước [4] trong pipeline — lắp ráp Hồ sơ user + Các đoạn thoại tham khảo từ Retrieval Layer + Quy tắc chống lặp/motif thành System Prompt tối ưu.
- **What:** Xây dựng `app/prompt_constructor.py` tạo System Prompt cho Conversational Agent.

#### Acceptance Criteria
- [ ] Ghép đúng thông tin band hiện tại, topic đang chọn và 2-4 sample dialogues.
- [ ] Cài đặt chỉ dẫn cấm lặp lại nguyên văn phrase bank và bắt buộc đặt 1 câu hỏi tiếp theo phù hợp band.
- [ ] Xử lý an toàn trường hợp Retrieval Layer (TASK-005) trả về danh sách rỗng (fallback cạn kiệt) — không được để prompt rỗng hoặc lỗi, phải có fallback prompt mặc định.
- [ ] Tốc độ lắp ráp prompt < 5ms.

---

### 📌 TASK-007: Conversational Agent & Structured JSON Parser (`app/conversational_agent.py`)

#### Metadata
```
Task ID:         TASK-007
Task Name:       Conversational Agent & Structured JSON Parser (`app/conversational_agent.py`)
Phase:           Phase 1 (MVP Pipeline)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Thực hiện bước [5] trong pipeline — LLM đóng vai diễn viên sinh câu tự nhiên, output theo Schema JSON có cấu trúc.
- **What:** Module `app/conversational_agent.py` gọi LLM API với System Prompt từ Prompt Constructor và parse kết quả JSON (`ai_utterance`, `internal_band_signal`, `topic_tag`, `difficulty_adjustment`).

#### Acceptance Criteria
- [ ] Trả về đúng JSON Schema đã định nghĩa tại mục 2 `docs/plan.md`.
- [ ] Cấu trúc JSON không chứa điểm số công khai cho user.
- [ ] Hỗ trợ fallback an toàn nếu LLM trả về JSON lỗi.

---

### 📌 TASK-008: TTS Audio Output Streamer (`app/tts_streamer.py`)

#### Metadata
```
Task ID:         TASK-008
Task Name:       TTS Audio Output Streamer (`app/tts_streamer.py`)
Phase:           Phase 1 (MVP Pipeline)
Task Type:       feature
Priority:        P0-Critical ⬆️ (nâng từ P1 — nằm trong đường găng MVP, nếu thiếu thì "MVP end-to-end" ở TASK-009 không thể demo bằng giọng nói)
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Chuyển văn bản trả lời (`ai_utterance`) của Conversational Agent thành giọng nói phát lại cho user.
- **What:** Module `app/tts_streamer.py` tích hợp Edge TTS / Streaming Audio TTS.

#### Acceptance Criteria
- [ ] Sinh file audio MP3/WAV hoặc audio stream từ `ai_utterance`.
- [ ] Độ trễ phát âm thanh thấp, giọng đọc tự nhiên chuẩn Anh/Mỹ.
- [ ] Nếu vì lý do hạ tầng chưa kịp tích hợp TTS thật, `TASK-009` phải có cờ fallback rõ ràng (`text_only_mode`) chứ không được âm thầm bỏ qua bước audio.

---

### 📌 TASK-009: MVP End-to-End Pipeline & API Endpoints Bridge (`app/main.py`)

#### Metadata
```
Task ID:         TASK-009
Task Name:       MVP End-to-End Pipeline & API Endpoints Bridge (`app/main.py`)
Phase:           Phase 1 (MVP Pipeline)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Nối toàn bộ pipeline 5 bước thành API endpoint hoạt động end-to-end cho Client.
- **What:** Cập nhật FastAPI endpoints trong `app/main.py` (`/api/voice/process_turn`, `/api/topics`).

#### Acceptance Criteria
- [ ] Endpoint `/api/voice/process_turn` nhận audio voice user, chạy full 5 bước pipeline và trả về JSON + audio AI response.
- [ ] Viết integration test `tests/test_mvp_pipeline.py` mô phỏng full turn.
- [ ] Integration test pass 100%.

---

### 📌 TASK-010: 🆕 Scoring Threshold Bootstrap & Calibration Config (`scripts/calibrate_thresholds.py`)

#### Metadata
```
Task ID:         TASK-010
Task Name:       Scoring Threshold Bootstrap & Calibration Config
Phase:           Phase 1.5 (tiền đề bắt buộc trước Phase 2 — Scoring Agent)
Task Type:       script + config infra
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11 (mới thêm ở v2)
```

#### Bối cảnh & Mục tiêu
- **Why:** Các ngưỡng WPM/pause_ratio/filler_density/MTLD dùng trong Tier 1 & Tier 2 (`TASK-011`, `TASK-012`) không được phép là số đoán cứng trong code ("magic numbers"). Ở bản kế hoạch v1, việc hiệu chỉnh (`TASK-022` cũ) nằm tận Phase 5 — nghĩa là hệ thống chạy production hàng tháng với ngưỡng chưa kiểm chứng trước khi biết có đúng không. Task này tách phần "khởi tạo ngưỡng ban đầu từ dữ liệu thật" ra làm tiền đề, đặt trước Tier 1/Tier 2.
- **What:** Viết script `scripts/calibrate_thresholds.py` dùng corpus công khai có nhãn CEFR (ICNALE Spoken, NICT JLE — map sang IELTS band proxy qua bảng quy đổi CEFR↔IELTS) để fit anchor points bằng Isotonic Regression, xuất ra config versioned `config/scoring_anchors.v{N}.json`.
- **Spec chi tiết đầy đủ:** xem `spec-5-task-rui-ro-cao.md`, **SPEC 0**.

#### Acceptance Criteria
- [ ] Script import 100% hàm tính đặc trưng (WPM/pause/filler/MTLD) từ `app/scoring/features.py` — KHÔNG viết lại riêng cho calibration (tránh lệch công thức giữa calibration và production).
- [ ] Output đúng schema JSON versioned (`version`, `calibrated_from`, `sample_size`, `holdout_mae`, `status`, `anchors`).
- [ ] Có `calibration_report.md` báo cáo MAE trên tập validation.
- [ ] `TASK-011` và `TASK-012` đọc anchor points từ config này (hot-reload hoặc load ở startup), không hardcode.
- [ ] Nếu chưa kịp có dữ liệu thật, ship `v0` với `"calibrated_from": "expert_estimate_uncalibrated"` — nhưng hạ tầng version/switch-active phải hoạt động đầy đủ để nâng cấp lên `v1` sau này không cần sửa code.

---

### 📌 TASK-011: Real-Time Scoring Agent — Tier 1 Scorer (<300ms) (`app/scoring/tier1_realtime.py`)

#### Metadata
```
Task ID:         TASK-011
Task Name:       Real-Time Scoring Agent — Tier 1 Scorer (<300ms)
Phase:           Phase 2 (Scoring Agent & Adaptive Difficulty)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Đo tín hiệu nhẹ (WPM, pause ratio, fillers, self-correction, MTLD) dưới 300ms để đưa ra `difficulty_adjustment` tức thì.
- **What:** Xây dựng `app/scoring/tier1_realtime.py` tính toán các chỉ số từ ASR timestamps & transcript, dùng anchor points từ `TASK-010`.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 1.
- **⚠️ Ranh giới kiến trúc quan trọng:** Tier 1 chỉ tạo tín hiệu tạm thời (ephemeral, sống trong session cache), **KHÔNG được gọi trực tiếp hàm EMA của `TASK-013`** và không ghi đè `user_profile.band_estimate_overall`. Band chính thức chỉ cập nhật qua Tier 2.

#### Acceptance Criteria
- [ ] Tính WPM, pause ratio (`pause > 0.5s / total_speech_time`), filler density, và self-correction pattern.
- [ ] Tính MTLD (thuật toán chuẩn 2 chiều forward/backward, không dùng TTR thô).
- [ ] Đọc anchor points từ `config/scoring_anchors.v{active}.json` (không hardcode).
- [ ] Thời gian xử lý < 300ms.
- [ ] Đưa ra signal `difficulty_adjustment` ("increase" | "hold" | "decrease"), trả "hold" khi `word_count < 5` hoặc `avg_asr_confidence < 0.6`.

---

### 📌 TASK-012: Deep Scoring Agent — Tier 2 Scorer & Grammar Check (`app/scoring/tier2_deep.py`)

#### Metadata
```
Task ID:         TASK-012
Task Name:       Deep Scoring Agent — Tier 2 Scorer & Grammar Check
Phase:           Phase 2 (Scoring Agent & Adaptive Difficulty)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Phân tích sâu ngữ pháp (spaCy parser), phát âm (GOP score) và gọi LLM-as-judge định kỳ 5-10 lượt để tính `raw_score` đầy đủ 4 trục — nguồn duy nhất được phép gọi EMA update ở `TASK-013`.
- **What:** Module `app/scoring/tier2_deep.py` chạy nền sau mỗi 5-10 lượt hội thoại, đọc anchor points/rubric từ `TASK-010`.

#### Acceptance Criteria
- [ ] Sử dụng spaCy đếm số mệnh đề phụ/cấu trúc phức tạp và đếm lỗi ngữ pháp.
- [ ] Chấm điểm Pronunciation (GOP score hoặc ASR confidence score).
- [ ] Trả về điểm 4 trục (Fluency, Lexical, Grammar, Pronunciation) quy về thang 0-9.
- [ ] Đọc ngưỡng/rubric mapping từ config của `TASK-010`, không hardcode song song một bộ số khác với Tier 1.

---

### 📌 TASK-013: Dynamic User Profile & EMA Band Smoothing Engine (`app/user_profile_engine.py`)

#### Metadata
```
Task ID:         TASK-013
Task Name:       Dynamic User Profile & EMA Band Smoothing Engine
Phase:           Phase 2 (Scoring Agent & Adaptive Difficulty)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Cập nhật band ước lượng trong `user_profile` bằng thuật toán Exponential Moving Average (EMA, α=0.2) để tránh dao động band do 1 câu bất thường. Hàm này **chỉ được gọi bởi Tier 2 (`TASK-012`)**, không phải Tier 1.
- **What:** Module `app/user_profile_engine.py` tính toán `raw_score = 0.3*FC + 0.25*LR + 0.25*GRA + 0.2*PRON` và áp dụng EMA với confidence weighting động.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 4.

#### Acceptance Criteria
- [ ] Áp dụng đúng công thức `EMA(band_cu, raw_score, alpha=effective_alpha)`.
- [ ] `effective_alpha` tính động theo `word_count_factor × confidence_factor`, KHÔNG áp `alpha=0.2` mù quáng.
- [ ] Có cơ chế floor-alpha chống "đứng hình" band khi bị skip liên tục ≥ 5 lượt.
- [ ] Clamp `band` trong khoảng [4.0, 9.0] sau mỗi lần update.
- [ ] Lưu trữ và cập nhật thành công vào DB `user_profile`.

---

### 📌 TASK-014: Cold-Start Diagnostic Probe System (`app/scoring/cold_start.py`)

#### Metadata
```
Task ID:         TASK-014
Task Name:       Cold-Start Diagnostic Probe System
Phase:           Phase 2 (Scoring Agent & Adaptive Difficulty)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** 3 lượt đầu tiên của người dùng mới cần câu hỏi diagnostic probe để đo nhanh band ngôn ngữ thay vì để band trôi tự do.
- **What:** Module `app/scoring/cold_start.py` quản lý 3 lượt hỏi mở đầu tiên với α=0.5.

#### Acceptance Criteria
- [ ] Phát hiện user mới và đưa ra 2-3 câu hỏi "diagnostic probe" mở, lấy từ trường `diagnostic_signals` trong content DB (không hardcode câu hỏi trong code).
- [ ] Đặt trọng số α=0.5 cho 3 lượt này để hội tụ band nhanh (gọi qua `TASK-013`).
- [ ] Tự động chuyển về α=0.2 từ lượt thứ 4 trở đi.

---

### 📌 TASK-015: Adaptive Retrieval & Difficulty Adjustment Integration (`app/retrieval.py`)

#### Metadata
```
Task ID:         TASK-015
Task Name:       Adaptive Retrieval & Difficulty Adjustment Integration
Phase:           Phase 2 (Scoring Agent & Adaptive Difficulty)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
```

#### Bối cảnh & Mục tiêu
- **Why:** Thay thế retrieval band tự chọn bằng retrieval theo `band_estimate` thực tế (`TASK-013`) + tín hiệu `difficulty_adjustment` từ Tầng 1 Scorer (`TASK-011`).
- **What:** Cập nhật `app/retrieval.py` (đã build ở `TASK-005`) để nhúng band thực tế và nấc độ khó vào điều kiện query SQL + Vector.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 2 mục 2.4 — công thức `compute_band_window()`.

#### Acceptance Criteria
- [ ] Retrieval query tự động điều chỉnh dải band (`increase` → band window dịch lên; `decrease` → dịch xuống; `hold` → cửa sổ mặc định lệch nhẹ lên).
- [ ] Đảm bảo câu hỏi lượt tiếp theo phản ánh đúng mức độ điều chỉnh độ khó.
- [ ] Không phá vỡ cơ chế fallback cascade đã có ở `TASK-005`.

---

### 📌 TASK-016: Embedding Anti-Repetition Engine (`app/anti_repetition.py`)

#### Metadata
```
Task ID:         TASK-016
Task Name:       Embedding Anti-Repetition Engine
Phase:           Phase 3 (Anti-Repetition, Persona & Memory)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-005, TASK-007 ⬅️ bổ sung TASK-007 (cần ai_utterance thật để so sánh, không chỉ dữ liệu retrieval)
```

#### Bối cảnh & Mục tiêu
- **Why:** Trước khi trả câu AI về cho user, so sánh embedding của câu AI vừa sinh (output của `TASK-007`) với N câu AI đã nói với user trong 30 ngày để chống lặp motif.
- **What:** Xây dựng `app/anti_repetition.py` kiểm tra cosine similarity embedding.

#### Acceptance Criteria
- [ ] Đếm cosine similarity giữa `ai_utterance` mới sinh (từ `TASK-007`) và danh sách câu quá khứ.
- [ ] Nếu similarity > threshold (0.85), gửi yêu cầu cho LLM re-generate với directive "diễn đạt khác đi".
- [ ] Thời gian check embedding < 15ms.

---

### 📌 TASK-017: AI Persona Identity & Long-Term Entity Memory System (`app/persona_memory.py`)

#### Metadata
```
Task ID:         TASK-017
Task Name:       AI Persona Identity & Long-Term Entity Memory System
Phase:           Phase 3 (Anti-Repetition, Persona & Memory)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-007, TASK-006 ⬅️ bổ sung TASK-006 (cần ghép entity memory vào system prompt)
```

#### Bối cảnh & Mục tiêu
- **Why:** Cho AI một nhân vật cố định (tên, tính cách) và trí nhớ dài hạn về các sự kiện user từng kể.
- **What:** Module `app/persona_memory.py` tóm tắt các entity/sự kiện từ hội thoại past và lưu vào `user_profile.entity_memory`.

#### Acceptance Criteria
- [ ] Tự động trích xuất các thông tin quan trọng của user (sở thích, sự kiện cá nhân) dưới dạng entity summary JSON.
- [ ] Nhúng thông tin entity memory vào System Prompt của Prompt Constructor (`TASK-006`).
- [ ] AI biết nhắc lại các sự kiện cũ trong hội thoại tự nhiên.

---

### 📌 TASK-018: Weekly Performance Reporting Engine & Hidden Scoring UI (`app/reporting.py`)

#### Metadata
```
Task ID:         TASK-018
Task Name:       Weekly Performance Reporting Engine & Hidden Scoring UI
Phase:           Phase 3 (Anti-Repetition, Persona & Memory)
Task Type:       feature
Priority:        P2-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-013, TASK-012 ⬅️ bổ sung TASK-012 (báo cáo cần điểm 4 trục chi tiết, không chỉ band tổng)
```

#### Bối cảnh & Mục tiêu
- **Why:** Ẩn điểm real-time trên giao diện chính, chỉ tổng hợp thành Báo cáo tuần để giảm áp lực thi cử cho người dùng.
- **What:** Xây dựng `app/reporting.py` sinh báo cáo tuần và cập nhật UI (`static/js/app.js`).

#### Acceptance Criteria
- [ ] Giao diện hội thoại chính KHÔNG hiển thị điểm band từng câu.
- [ ] Sinh báo cáo tuần tổng hợp tiến trình 4 trục (Fluency, Lexical, Grammar, Pronunciation) lấy từ dữ liệu Tier 2 (`TASK-012`), không chỉ band tổng từ `TASK-013`.

---

### 📌 TASK-019: Real-World Roleplay Simulation Engine (`app/scenarios/simulation_engine.py`)

#### Metadata
```
Task ID:         TASK-019
Task Name:       Real-World Roleplay Simulation Engine
Phase:           Phase 4 (Real-World Simulations & Interleaved Practice)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-017, TASK-001, TASK-015 ⬅️ bổ sung TASK-001 (cần dữ liệu scenario đã ingest) và TASK-015 (cần retrieval để lấy nội dung scenario theo band)
```

#### Bối cảnh & Mục tiêu
- **Why:** Đóng khung hội thoại thành các tình huống sống thật (gọi Grab, phỏng vấn, quầy lễ tân) dựa trên Template C.
- **What:** Xây dựng `app/scenarios/simulation_engine.py` quản lý các branch `low_band` và `high_band` cũng như `evaluation_hooks`.

#### Acceptance Criteria
- [ ] Hỗ trợ các tình huống nhập vai rẽ nhánh linh hoạt theo chất lượng câu trả lời của user.
- [ ] Kích hoạt `evaluation_hooks` khi user sử dụng cấu trúc target thành công.
- [ ] Lấy đúng scenario/branch tương ứng qua Retrieval Layer đã adaptive theo band (`TASK-015`).

---

### 📌 TASK-020: Personal Error Journal & Interleaved Practice Weaver (`app/error_journal.py`)

#### Metadata
```
Task ID:         TASK-020
Task Name:       Personal Error Journal & Interleaved Practice Weaver
Phase:           Phase 4 (Real-World Simulations & Interleaved Practice)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-012, TASK-006 ⬅️ bổ sung TASK-006 (cần cài chỉ dẫn vào prompt constructor)
```

#### Bối cảnh & Mục tiêu
- **Why:** Lưu lại các lỗi ngữ pháp/từ vựng lặp lại của user (từ Tier 2, `TASK-012`) và dệt lại vào các tình huống mới để ôn tập xen kẽ.
- **What:** Xây dựng `app/error_journal.py` ghi nhận `recurring_errors` và cài bẫy ôn tập vào Prompt Constructor (`TASK-006`).

#### Acceptance Criteria
- [ ] Tự động ghi nhận lỗi sai lặp lại (>2 lần) vào `user_profile.recurring_errors`.
- [ ] Prompt Constructor tự động cài chỉ dẫn gài bẫy ngữ pháp/từ vựng tương ứng ở chủ đề tiếp theo.

---

### 📌 TASK-021: Multi-Armed Bandit / Adaptive Spaced Repetition Engine (`app/adaptive_engine.py`)

#### Metadata
```
Task ID:         TASK-021
Task Name:       Multi-Armed Bandit / Adaptive Spaced Repetition Engine
Phase:           Phase 4 (Real-World Simulations & Interleaved Practice)
Task Type:       feature
Priority:        P2-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-015, TASK-001 ⬅️ bổ sung TASK-001 (item pool lấy từ content_units đã ingest)
```

#### Bối cảnh & Mục tiêu
- **Why:** Nâng cấp difficulty engine từ tăng/giảm 1 nấc đơn giản sang thuật toán adaptive multi-armed bandit.
- **What:** Xây dựng `app/adaptive_engine.py` chọn item pool phù hợp nhất từ DB.

#### Acceptance Criteria
- [ ] Chọn độ khó câu hỏi tối ưu hóa giữa việc vừa sức và thử thách, dựa trên item pool từ `content_units`/`band_tiers` (`TASK-001`).
- [ ] Tích hợp cơ chế Spaced Repetition cho các cấu trúc từ vựng cần ôn lại.

---

### 📌 TASK-022: 🆕 PII Scrubbing Module (`app/data_quality/pii_scrubber.py`)

#### Metadata
```
Task ID:         TASK-022
Task Name:       PII Scrubbing Module
Phase:           Phase 5 (Data Flywheel & Quality Control)
Task Type:       feature (standalone utility)
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11 (mới thêm ở v2)
```

#### Bối cảnh & Mục tiêu
- **Why:** Ở bản v1, việc xoá PII chỉ là 1 bullet trong acceptance criteria của Data Flywheel (`TASK-023`) — đây là phần rủi ro nhất (rò rỉ dữ liệu cá nhân không thể thu hồi), cần tách thành module độc lập, test riêng, dùng chung được cho bất kỳ pipeline nào cần xử lý text do user tạo ra (không chỉ Data Flywheel).
- **What:** Module `app/data_quality/pii_scrubber.py` phát hiện PII (tên người, địa danh, tổ chức, số điện thoại, email) bằng NER (spaCy) + regex, theo chính sách **REJECT hoàn toàn** (không cố redact) nếu phát hiện bất kỳ PII nào.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 5 mục 5.2.

#### Acceptance Criteria
- [ ] Hàm `check_pii(text) -> (passed: bool, entities_found: list[str])` hoạt động độc lập, không phụ thuộc pipeline Data Flywheel.
- [ ] Phát hiện đủ 4 loại PII: PERSON, GPE/địa danh, ORG, và pattern số điện thoại/email qua regex.
- [ ] Chính sách reject-first: bất kỳ entity nào thuộc `PII_ENTITY_TYPES` bị phát hiện → `passed=False`, không cố redact rồi giữ lại câu.
- [ ] Có unit test xác nhận false positive (tên hư cấu trong câu chuyện kể) vẫn bị reject đúng theo chính sách — đây là hành vi ĐÚNG, không phải bug.

---

### 📌 TASK-023: High-Band User Answer Harvest Pipeline (`app/data_flywheel.py`)

#### Metadata
```
Task ID:         TASK-023
Task Name:       High-Band User Answer Harvest Pipeline
Phase:           Phase 5 (Data Flywheel & Quality Control)
Task Type:       feature
Priority:        P2-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11
Phụ thuộc:       TASK-013, TASK-012, TASK-022 ⬅️ bổ sung TASK-022 (dùng module PII riêng, không viết lại)
```

#### Bối cảnh & Mục tiêu
- **Why:** Thu hoạch các câu trả lời band cao thực tế của user thật để đưa ngược vào DB `sample_dialogues`, tạo vòng lặp tự làm giàu dữ liệu.
- **What:** Module `app/data_flywheel.py` lọc câu trả lời điểm cao (Band 7.5+, MỌI trục ≥ 7.0 — không cho phép 1 trục thấp được bù bởi trục khác), qua bộ lọc an toàn 3 lớp (PII từ `TASK-022`, Grammar/Lexical Verification, Vector Dedup), rồi đưa vào `harvest_review_queue` chờ duyệt — **KHÔNG insert thẳng vào `sample_dialogues`**.
- **Spec chi tiết:** xem `spec-5-task-rui-ro-cao.md`, SPEC 5.

#### Acceptance Criteria
- [ ] Tự động phát hiện các lượt nói xuất sắc của user (Band 7.5+, đạt ngưỡng min-axis).
- [ ] Gọi `check_pii()` từ `TASK-022` làm bước đầu tiên trong pipeline (trước cả bước check chất lượng/dedup).
- [ ] Vector dedup so với TOÀN BỘ `sample_dialogues` hiện có (cả từ sách gốc lẫn đã harvest trước đó), threshold 0.92 = loại.
- [ ] Có rate cap (tối đa N mẫu/topic/tuần) để tránh feedback loop thiên lệch nội dung.
- [ ] Mọi candidate hợp lệ đều dừng ở `harvest_review_queue` với `review_status='pending'`, TUYỆT ĐỐI không có đường insert thẳng vào `sample_dialogues`.

---

### 📌 TASK-024: Scoring Model Drift Benchmark (`scripts/benchmark_calibration.py`)

#### Metadata
```
Task ID:         TASK-024
Task Name:       Scoring Model Drift Benchmark (định kỳ — KHÔNG phải bootstrap ban đầu)
Phase:           Phase 5 (Data Flywheel & Quality Control)
Task Type:       script
Priority:        P2-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-11 (thu hẹp phạm vi so với v1 — phần bootstrap ban đầu đã tách sang TASK-010)
Phụ thuộc:       TASK-012, TASK-010
```

#### Bối cảnh & Mục tiêu
- **Why:** Định kỳ (đề xuất: hàng tháng) đối chiếu kết quả chấm của Scoring Agent với dữ liệu production thật đã có người review, để phát hiện model bị trôi điểm (drift) so với lúc mới calibrate ở `TASK-010`. **Đây không phải lần hiệu chỉnh đầu tiên** (việc đó đã làm ở `TASK-010`) — task này chỉ giám sát và đề xuất recalibrate khi cần.
- **What:** Viết script `scripts/benchmark_calibration.py` chạy benchmark định kỳ, so sánh điểm hệ thống chấm với điểm người review chấm tay trên mẫu ngẫu nhiên từ `harvest_review_queue` (`TASK-023`).

#### Acceptance Criteria
- [ ] Lấy mẫu ngẫu nhiên các turn đã có `reviewed_by='human:*'` để làm ground truth so sánh.
- [ ] Tính chỉ số sai số (MAE / RMSE) giữa điểm model chấm (Tier 2) và điểm human rater.
- [ ] Cảnh báo nếu MAE vượt ngưỡng đã đặt ở `TASK-010` (`holdout_mae` ban đầu) — đề xuất chạy lại `calibrate_thresholds.py` để sinh phiên bản config mới (`v2`, `v3`...).

---

## 3. Ghi chú vận hành sau khi cập nhật v2

- **Thứ tự Phase 1.5 mới** (`TASK-010`) chèn giữa Phase 1 và Phase 2 — nếu AI Ralph Loop đọc tuần tự theo bảng ở mục 1, thứ tự này đã tự động đúng, không cần chỉnh thêm gì trong logic đọc queue.
- **`app/scoring/features.py`** là module dùng chung bắt buộc giữa `TASK-010` (calibration), `TASK-011` (Tier 1), `TASK-012` (Tier 2) — nếu AI code viết trùng lặp hàm tính năng ở nhiều nơi, đây là dấu hiệu sai cần dừng lại và refactor về 1 module duy nhất trước khi tiếp tục.
- **`app/data_quality/pii_scrubber.py`** (`TASK-022`) nên được thiết kế đủ tổng quát để tái sử dụng cho các tính năng tương lai ngoài Data Flywheel (vd nếu sau này có tính năng cho phép user chia sẻ đoạn hội thoại công khai, cũng cần qua module này).