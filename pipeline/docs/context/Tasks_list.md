# TASKS LIST
# Danh sách tác vụ & Queue thực thi — Doulingo Speaking AI Engine Redesign

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-26
>
> 🤖 **AI EXECUTION RULE:** AI sẽ đọc danh sách này từ trên xuống dưới, tìm task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS` để thực thi. Khi hoàn thành task, AI đánh dấu `[x] DONE` và chuyển sang task tiếp theo.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Ghi chú / Blocker |
|---------|----------|-------|---------|------------|-------------------|
| `TASK-001` | Crawl & Seed Initial Datasets (CEFR Vocab & Dialogue Exemplars) | Phase 1 | P0 | `[x] DONE` | Cào/Seed từ vựng CEFR + Câu thoại mẫu |
| `TASK-002` | Build Vocabulary Bank & Heuristic Level Checker | Phase 1 | P0 | `[x] DONE` | Dữ liệu từ vựng A1-B1 & Heuristic Checker |
| `TASK-003` | Build Dialogue Exemplar Bank & Hybrid RAG Engine | Phase 1 | P0 | `[ ] TODO` | Ngân hàng câu mẫu + Hybrid Retrieval |
| `TASK-004` | Implement Structured Output CoT & Heuristic Validation Loop Engine | Phase 1 | P0 | `[ ] TODO` | Prompt JSON CoT ngay call 1 + Heuristic verification loop |
| `TASK-005` | Refactor Decoupled 3-Tier Prompt System for All 9 Personas | Phase 2 | P1 | `[ ] TODO` | Tách 3 tầng Pedagogy -> Persona -> CEFR Horizon |
| `TASK-006` | Build Structured Topic Bank & Soften Scenario Angles | Phase 2 | P1 | `[ ] TODO` | Phân loại topic tự do vs nhập vai |
| `TASK-007` | Implement Response Rating API & Continuous Feedback Logger | Phase 2 | P1 | `[ ] TODO` | Đánh giá câu (hollow, out_of_context, good) & Update DB |
| `TASK-008` | Build Grammar Structure Bank & CEFR Constraint Validator | Phase 3 | P2 | `[ ] TODO` | Ngữ pháp theo CEFR level |
| `TASK-009` | Implement ASR Adaptive Level Detector (IRT Model) | Phase 3 | P2 | `[ ] TODO` | Đo trình độ động từ transcript user |

---

## 2. Chi tiết các Tasks (Task Specs)

---

### 📌 TASK-001: Crawl & Seed Initial Datasets (CEFR Vocab & Dialogue Exemplars)

#### Metadata
```
Task ID:         TASK-001
Task Name:       Crawl & Seed Initial Datasets (CEFR Vocab & Dialogue Exemplars)
Phase:           Phase 1 (Data Seeding)
Task Type:       feat / script
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Hệ thống cần bộ dữ liệu gốc (seed data) ban đầu về từ vựng CEFR (A1-B1) và câu thoại mẫu hội thoại để User có file thực tế tiến hành duyệt trong `to_do.md`.
- **What:** Viết script `scripts/seed_data.py` tự động cào/tổng hợp từ vựng CEFR mở (Cambridge EVP/Oxford) và dùng LLM sinh ngân hàng câu thoại mẫu khởi tạo theo (level, persona, topic, dialogue_act).

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Script `python3 scripts/seed_data.py` chạy thành công không lỗi.
- [x] Sinh ra file `app/data/vocab_bank.json` thô với > 1000 từ vựng A1-B1.
- [x] Sinh ra file `app/data/sample_dialogue_bank.json` thô với > 100 câu thoại mẫu khởi tạo.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `scripts/seed_data.py`, `app/data/vocab_bank.json`, `app/data/sample_dialogue_bank.json`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 scripts/seed_data.py
```

---

### 📌 TASK-002: Build Vocabulary Bank & Heuristic Level Checker

#### Metadata
```
Task ID:         TASK-002
Task Name:       Build Vocabulary Bank & Heuristic Level Checker
Phase:           Phase 1 (Core Infrastructure)
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Cần cơ chế kiểm tra nhanh (Heuristic Check - không tốn API LLM) xem câu trả lời của AI có vi phạm trần từ vựng CEFR Level hay không.
- **What:** Đọc dữ liệu từ `app/data/vocab_bank.json` và viết module `app/core/heuristic_checker.py` đếm từ, tính độ dài câu, tra từ vựng vượt trần.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Module `HeuristicChecker.check_level_ceiling(text, target_level)` trả về `is_violated: bool` và danh sách từ vi phạm trong < 5ms.
- [x] Pytest cho `HeuristicChecker` pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/core/heuristic_checker.py`, `tests/test_heuristic_checker.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_heuristic_checker.py
```

---

### 📌 TASK-003: Build Dialogue Exemplar Bank & Hybrid RAG Engine

#### Metadata
```
Task ID:         TASK-003
Task Name:       Build Dialogue Exemplar Bank & Hybrid RAG Engine
Phase:           Phase 1 (Core Infrastructure)
Task Type:       feat
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Để AI bám sát câu tự nhiên chuẩn sư phạm mà không bị nói lặp/gượng gạo, cần hệ thống RAG động lấy câu thoại mẫu theo ngữ cảnh.
- **What:** Chuẩn hóa `app/data/sample_dialogue_bank.json` và module `app/core/exemplar_rag.py` thực hiện Metadata filter (level + persona + topic + dialogue_act) kết hợp Semantic search / MMR diversity.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] `ExemplarRAG.retrieve(level, persona, topic, dialogue_act, state_summary)` trả về 2-3 câu mẫu chuẩn nhất.
- [ ] Pytest cho RAG retrieval pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/core/exemplar_rag.py`, `tests/test_exemplar_rag.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_exemplar_rag.py
```

---

### 📌 TASK-004: Implement Structured Output CoT & Heuristic Validation Loop Engine

#### Metadata
```
Task ID:         TASK-004
Task Name:       Implement Structured Output CoT & Heuristic Validation Loop Engine
Phase:           Phase 1 (Core Execution)
Task Type:       feat / refactor
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Ngay ở lượt gọi LLM đầu tiên, yêu cầu trả về Structured Output JSON (`natural_draft`, `vocab_check`, `final_response`). Sau đó qua Heuristic Check: nếu PASS thì trả về kết quả luôn; nếu FAIL thì phản hồi lỗi cụ thể vào retry loop nhỏ cho đến khi PASS.
- **What:** Cập nhật `app/core/ai_engine.py` để xử lý luồng: Call 1 (JSON CoT) $\rightarrow$ Heuristic Check $\rightarrow$ Pass? Return `final_response` : Retry Loop với feedback lỗi.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Ngay Call 1 yêu cầu LLM sinh JSON CoT (`natural_draft`, `vocab_check`, `final_response`).
- [ ] Heuristic Check kiểm tra `final_response`: nếu PASS thì xuất kết quả ngay (chiếm đa số trường hợp, tốn đúng 1 API call).
- [ ] Nếu Heuristic Check FAIL, hệ thống tự động feed back lỗi từ vi phạm cho LLM hạ cấp lại tới khi PASS.
- [ ] Pytest cho AI Engine pipeline pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/core/ai_engine.py`, `app/core/prompt_factory.py`, `tests/test_ai_engine.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_ai_engine.py
```

---

### 📌 TASK-005: Refactor Decoupled 3-Tier Prompt System for All 9 Personas

#### Metadata
```
Task ID:         TASK-005
Task Name:       Refactor Decoupled 3-Tier Prompt System for All 9 Personas
Phase:           Phase 2 (Architecture Harmonization)
Task Type:       refactor
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Prompt hiện tại bị over-engineering, nhồi nhét quy tắc gây ảnh hưởng toàn bộ 9 nhân vật.
- **What:** Tái cấu trúc Prompt System thành 3 tầng độc lập: Tầng 1 (Core Pedagogy & Warmth), Tầng 2 (Persona Overlay từ `app/data/persona_definitions.json`), Tầng 3 (Adaptive CEFR Horizon).

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Cấu trúc prompt mới được áp dụng nhất quán cho cả 9 nhân vật (Alex, Lily, Oscar, Viktor...).
- [ ] Loại bỏ hoàn toàn luật ép `min_words` cứng nhắc và các ví dụ mẫu làm lặp câu.
- [ ] Pytest nghiệm thu cả 9 characters pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/characters/__init__.py`, `app/core/prompt_factory.py`, `app/data/persona_definitions.json`, `tests/test_characters.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_characters.py
```

---

### 📌 TASK-006: Build Structured Topic Bank & Soften Scenario Angles

#### Metadata
```
Task ID:         TASK-006
Task Name:       Build Structured Topic Bank & Soften Scenario Angles
Phase:           Phase 2 (Architecture Harmonization)
Task Type:       feat
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Hệ thống hiện tại ép `SCENARIO_ANGLES` ngẫu nhiên vào mọi chủ đề (như chào hỏi), gây ra câu lộn xộn.
- **What:** Tạo `app/data/topic_bank.json` phân định rõ topic tự do (`free_conversation`) vs nhập vai (`structured_scenario`). Chỉ kích hoạt kịch bản khi topic yêu cầu.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Các chủ đề chào hỏi/giao tiếp tự do không còn bị ép kịch bản lễ hội/âm nhạc gượng gạo.
- [ ] Scenario Angles chỉ kích hoạt đúng các topic nhập vai thực tế (ví dụ: order đồ ăn, phỏng vấn).

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/data/topic_bank.json`, `app/core/ai_engine.py`, `tests/test_topics.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_topics.py
```

---

### 📌 TASK-007: Implement Response Rating API & Continuous Feedback Logger

#### Metadata
```
Task ID:         TASK-007
Task Name:       Implement Response Rating API & Continuous Feedback Logger
Phase:           Phase 2 (Continuous Improvement)
Task Type:       feat
Priority:        P1-High
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Cho phép User/Học viên đánh giá chất lượng mỗi câu do AI sinh ra (`hollow` - Sáo rỗng, `out_of_context` - Sai ngữ cảnh, `good` - Tốt) để liên tục cập nhật DB, hạ điểm hoặc bổ sung vào ngân hàng câu mẫu.
- **What:** 
  1. Thêm API endpoint `POST /api/v1/feedback/rate-response` xử lý rating (`hollow`, `out_of_context`, `good`).
  2. Lưu nhật ký đánh giá vào `app/data/feedback_log.json`.
  3. Cập nhật trực tiếp `quality_score` trong `sample_dialogue_bank.json` (nếu câu đó xuất phát từ RAG) hoặc thêm câu được rate "Tốt" vào Dialogue Bank cho các lượt sau.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Endpoint `POST /api/v1/feedback/rate-response` ghi log thành công vào `app/data/feedback_log.json`.
- [ ] Câu bị đánh giá "Sáo rỗng" (`hollow`) hoặc "Sai ngữ cảnh" (`out_of_context`) sẽ bị hạ điểm `quality_score` hoặc đưa vào blacklist không dùng lại trong Exemplar RAG.
- [ ] Câu được đánh giá "Tốt" (`good`) với điểm cao tự động được cân nhắc đưa vào Dialogue Exemplar Bank.
- [ ] Pytest cho feedback router & service pass 100%.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/api/feedback_router.py`, `app/services/feedback_service.py`, `app/data/feedback_log.json`, `tests/test_feedback.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_feedback.py
```

---

### 📌 TASK-008: Build Grammar Structure Bank & CEFR Constraint Validator

#### Metadata
```
Task ID:         TASK-008
Task Name:       Build Grammar Structure Bank & CEFR Constraint Validator
Phase:           Phase 3 (Advanced Validation)
Task Type:       feat
Priority:        P2-Medium
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Thay thế quy tắc cứng "Present Simple only" bằng danh mục cấu trúc ngữ pháp CEFR linh hoạt (`introduced_at_level` và `mastered_at_level`).
- **What:** Tạo `app/data/grammar_bank.json` và tích hợp kiểm tra ngữ pháp vào Validator.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Validator nhận diện được số mệnh đề (`max_clauses`) và cấu trúc ngữ pháp cho phép theo level.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/data/grammar_bank.json`, `app/core/grammar_validator.py`, `tests/test_grammar_validator.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_grammar_validator.py
```

---

### 📌 TASK-009: Implement ASR Adaptive Level Detector (IRT Model)

#### Metadata
```
Task ID:         TASK-009
Task Name:       Implement ASR Adaptive Level Detector (IRT Model)
Phase:           Phase 3 (Advanced Adaptive Engine)
Task Type:       feat
Priority:        P2-Medium
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-26
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Người dùng chọn Level tĩnh thường không phản ánh đúng trình độ thực tế.
- **What:** Viết module `app/core/adaptive_level_detector.py` phân tích transcript lời nói của user (tốc độ, độ dài câu, từ vựng) để cập nhật động level CEFR thực tế sau mỗi vài turn.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [ ] Detector tính toán được level thực tế của user dựa trên transcript ASR.
- [ ] AI Engine tự động điều chỉnh độ khó theo level đo được thay vì level tĩnh.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/core/adaptive_level_detector.py`, `tests/test_adaptive_level.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/test_adaptive_level.py
```
