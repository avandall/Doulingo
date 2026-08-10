# TASKS LIST
# Danh sách tác vụ & Queue thực thi — Duolingo Speak Dynamic Material Bank Refactor

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-10
>
> ✏️ **HUMAN FILLS THIS FILE.** Bạn có thể thêm 1 hoặc nhiều tasks vào danh sách này.
> 🤖 **AI EXECUTION RULE:** AI sẽ đọc danh sách này từ trên xuống dưới, tìm task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS` để thực thi trong từng phiên Ralph Loop. Khi hoàn thành task, AI đánh dấu `[x] DONE` và chuyển sang task tiếp theo.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Ghi chú / Blocker |
|---------|----------|-------|---------|------------|-------------------|
| `TASK-000` | Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite) | Phase 0 | P0 | `[x] DONE` | Replace local SQLite file with Turso Cloud SQLite (9GB Free Tier) |
| `TASK-001` | Material Bank Data Models & Markdown Parser (`app/material_bank.py`) | Phase 1 | P0 | `[x] DONE` | Parse all 5 `DB*.md` files into Pydantic models |
| `TASK-002` | Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`) | Phase 1 | P0 | `[x] DONE` | Verify all topics, personas, questions & vocab parsed |
| `TASK-003` | Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`) | Phase 2 | P0 | `[x] DONE` | Implement sampling algorithm & prompt assembly |
| `TASK-004` | Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`) | Phase 2 | P0 | `[x] DONE` | Verify assembly speed (<5ms) and non-repetitive sampling |
| `TASK-005` | AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`) | Phase 3 | P1 | `[x] DONE` | Inject sampled prompts & set temperature 0.75-0.85 |
| `TASK-006` | FastAPI Endpoints Bridge & Scenario Registry (`app/main.py`) | Phase 3 | P1 | `[x] DONE` | Connect `/api/scenarios`, `/api/start_scenario`, `/api/process_turn` |
| `TASK-007` | End-to-End Integration Testing & Latency Benchmarks | Phase 4 | P1 | `[x] DONE` | Verify full conversation flow and response parsing |
| `TASK-008` | System Verification Evidence & Harness Documentation Update | Phase 4 | P2 | `[ ] TODO` | Final sanity checks, status update & walkthrough |

> **Trạng thái hợp lệ:**
> - `[ ] TODO`: Chưa làm, chờ AI chọn
> - `[/] IN_PROGRESS`: AI đang thực hiện
> - `[x] DONE`: Hoàn thành, đã verify & proof
> - `[!] BLOCKED`: Bị kẹt, cần human intervention

---

## 2. Chi tiết các Tasks (Task Specs)

---

### 📌 TASK-000: Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite)

#### Metadata
```
Task ID:         TASK-000
Task Name:       Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite)
Phase:           Phase 0 (Cloud Infrastructure & Database)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Render Free Tier sử dụng **Ephemeral Disk** (ổ đĩa tạm). Nếu dùng file SQLite local (`data/custom_topics.db`), mỗi lần ứng dụng khởi động lại hoặc redeploy trên Render, toàn bộ dữ liệu từ điển và custom scenarios sẽ bị xóa sạch.
- **What:** Chuyển đổi tầng lưu trữ dữ liệu trong `app/db.py` từ SQLite local sang **Turso DB (Managed Cloud SQLite - 9GB Free Tier)** sử dụng biến môi trường `TURSO_DATABASE_URL` và `TURSO_AUTH_TOKEN`. Turso hoàn toàn tương thích với cú pháp SQLite hiện tại và giữ nguyên 100% logic câu lệnh SQL.

#### Acceptance Criteria
- [ ] Thêm cấu hình `TURSO_DATABASE_URL` và `TURSO_AUTH_TOKEN` trong `.env` và `app/db.py`.
- [ ] Kết nối thành công đến Turso Cloud SQLite bằng `libsql_experimental` / `sqld` driver hoặc fallback local SQLite nếu thiếu token.
- [ ] Tự động khởi tạo/migrate bảng `custom_scenarios`, `word_dictionary`, `saved_vocabulary`, `user_stats` trên Turso Cloud.
- [ ] Đảm bảo dữ liệu custom scenarios và từ vựng tồn tại vĩnh viễn ngay cả khi container Render bị restart hoặc redeploy.

---

### 📌 TASK-001: Material Bank Data Models & Markdown Parser (`app/material_bank.py`)

#### Metadata
```
Task ID:         TASK-001
Task Name:       Material Bank Data Models & Markdown Parser (`app/material_bank.py`)
Phase:           Phase 1 (Ingestion & Models)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Hệ thống cần đọc các file `docs/DB1_*.md` đến `docs/DB5_*.md` chứa nguyên liệu học thuật IELTS và nạp vào bộ nhớ RAM để truy vấn 0ms.
- **What:** Tạo module `app/material_bank.py` chứa Pydantic models (`Persona`, `Question`, `VocabularyItem`, `GrammarPattern`, `TopicBank`) và lớp `MaterialBank` tự động parse tất cả 5 file markdown tại startup.

#### Acceptance Criteria
- [ ] File `app/material_bank.py` được tạo với các Pydantic models chuẩn hóa.
- [ ] Lớp `MaterialBank` có phương thức `load_all(docs_dir)` đọc thành công cả 5 file `DB1_*.md` đến `DB5_*.md`.
- [ ] Parser bóc tách chính xác các section: Persona Pool, Question Pool (by Band), Vocab Pool (by Band), Grammar Patterns.
- [ ] Hỗ trợ phương thức `get_topic(topic_id)` và `list_topics()` trả về dữ liệu nhanh chóng từ RAM.

---

### 📌 TASK-002: Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`)

#### Metadata
```
Task ID:         TASK-002
Task Name:       Unit Tests for Material Bank Parser & Indexer (`tests/test_material_bank.py`)
Phase:           Phase 1 (Ingestion & Models)
Task Type:       test
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Đảm bảo toàn bộ 5 file `DB*.md` được parse đầy đủ mà không bị sót Topic hoặc lỗi cú pháp Markdown.
- **What:** Tạo unit test `tests/test_material_bank.py` sử dụng `pytest`.

#### Acceptance Criteria
- [x] Test case nạp cả 5 file DB và kiểm tra số lượng Topic > 0.
- [x] Test case kiểm tra từng Topic có ít nhất 1 Persona, 1 Question và 1 Vocabulary item.
- [x] Test case kiểm tra việc lấy topic theo `topic_id` không phân biệt hoa thường.
- [x] Lệnh `pytest tests/test_material_bank.py` chạy qua 100% thành công.

---

### 📌 TASK-003: Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)

#### Metadata
```
Task ID:         TASK-003
Task Name:       Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)
Phase:           Phase 2 (Sampling & Prompt Factory)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Cần một bộ lắp ráp System Prompt động dựa trên việc sample nguyên liệu ngẫu nhiên từ `MaterialBank` theo level của người dùng.
- **What:** Xây dựng module `app/prompt_factory.py` chứa class `PromptFactory`.

#### Acceptance Criteria
- [x] Class `PromptFactory` có hàm `sample_materials(topic_id, level)` thực hiện sample 1 Persona, 3-4 Vocab items, 1-2 Questions theo band điểm.
- [x] Hàm `build_system_prompt(topic_id, level, character_id, user_history)` lắp ráp thành công System Prompt hoàn chỉnh.
- [x] Hỗ trợ fallback an toàn nếu `topic_id` không tồn tại trong Material Bank.

---

### 📌 TASK-004: Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`)

#### Metadata
```
Task ID:         TASK-004
Task Name:       Unit Tests for Prompt Factory & Sampling Diversity (`tests/test_prompt_factory.py`)
Phase:           Phase 2 (Sampling & Prompt Factory)
Task Type:       test
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Kiểm chứng tốc độ dựng prompt (< 5ms) và tính đa dạng không lặp lại khi gọi sample nhiều lần.
- **What:** Tạo unit test `tests/test_prompt_factory.py`.

#### Acceptance Criteria
- [x] Benchmark test chứng minh thời gian dựng prompt trung bình < 5ms.
- [x] Diversity test: Gọi `build_system_prompt` 5 lần liên tiếp trên cùng topic và xác nhận thu được các prompt có sự khác biệt ở Vocab/Persona/Question.
- [x] Lệnh `pytest tests/test_prompt_factory.py` chạy thành công.

---

### 📌 TASK-005: AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`)

#### Metadata
```
Task ID:         TASK-005
Task Name:       AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`)
Phase:           Phase 3 (Integration & API Bridge)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Tích hợp System Prompt từ Prompt Factory vào luồng gọi LLM trong `ai_engine.py` và tối ưu các tham số sinh text (`temperature: 0.8`, `presence_penalty: 0.6`).
- **What:** Refactor `start_roleplay_greeting` và `process_turn` trong `app/ai_engine.py`.

#### Acceptance Criteria
- [x] `ai_engine` tự động gọi `PromptFactory` khi nhận `scenario_id`/`topic_id`.
- [x] Các tham số `temperature` và `presence_penalty` được thiết lập đúng chuẩn trong LLM API call payload.
- [x] Luồng multi-key fallback và trace logger hoạt động mượt mà không bị ngắt quãng.

---

### 📌 TASK-006: FastAPI Endpoints Bridge & Scenario Registry (`app/main.py`)

#### Metadata
```
Task ID:         TASK-006
Task Name:       FastAPI Endpoints Bridge & Scenario Registry (`app/main.py`)
Phase:           Phase 3 (Integration & API Bridge)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Cập nhật các API endpoints hiện có trên FastAPI để phục vụ cả danh sách Topic từ Material Bank lẫn Custom Topics từ Turso DB.
- **What:** Cập nhật các endpoint `/api/scenarios`, `/api/start_scenario`, `/api/process_turn`, `/api/chat` trong `app/main.py`.

#### Acceptance Criteria
- [ ] Endpoint `/api/scenarios` trả về đầy đủ danh sách Topics từ 5 DB files.
- [ ] Endpoint `/api/start_scenario` và `/api/process_turn` hoạt động chính xác với `topic_id` mới.
- [ ] Đảm bảo tương thích ngược với các custom scenario lưu trong Turso Cloud Database.

---

### 📌 TASK-007: End-to-End Integration Testing & Latency Benchmarks

#### Metadata
```
Task ID:         TASK-007
Task Name:       End-to-End Integration Testing & Latency Benchmarks
Phase:           Phase 4 (Verification & Polish)
Task Type:       test
Priority:        P1-High
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Đảm bảo toàn bộ luồng hội thoại từ Client -> FastAPI -> Prompt Factory -> LLM Engine -> Structured Output vận hành chính xác.
- **What:** Tạo integration test suite `tests/test_integration_material_bank.py`.

#### Acceptance Criteria
- [ ] Integration test mô phỏng full turn conversation thành công.
- [ ] Kiểm tra JSON response có đủ fields `ai_response`, `ai_response_vi`, `user_feedback`.
- [ ] Benchmark tổng thời gian xử lý endpoint nằm trong ngưỡng cho phép.

---

### 📌 TASK-008: System Verification Evidence & Harness Documentation Update

#### Metadata
```
Task ID:         TASK-008
Task Name:       System Verification Evidence & Harness Documentation Update
Phase:           Phase 4 (Verification & Polish)
Task Type:       docs
Priority:        P2-Normal
Trạng thái:      [ ] TODO
Ngày tạo:        2026-08-10
```

#### Bối cảnh & Mục tiêu
- **Why:** Cập nhật trạng thái dự án và tài liệu runtime sẵn sàng nghiệm thu.
- **What:** Cập nhật `H_docs/runtime/STATUS.md` và tạo bằng chứng verification.

#### Acceptance Criteria
- [ ] Mọi test suite trong `tests/` đều pass 100%.
- [ ] File `H_docs/runtime/STATUS.md` được cập nhật trạng thái hoàn thành.
