# TASKS LIST
# Danh sách tác vụ & Queue thực thi — Duolingo Speak Fix Pipeline

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-21
>
> ✏️ **HUMAN FILLS THIS FILE.** Bạn có thể thêm 1 hoặc nhiều tasks vào danh sách này.
> 🤖 **AI EXECUTION RULE:** AI sẽ đọc danh sách này từ trên xuống dưới, tìm task đầu tiên có trạng thái `[ ] TODO` hoặc `[/] IN_PROGRESS` để thực thi. Khi hoàn thành task, AI đánh dấu `[x] DONE` và chuyển sang task tiếp theo.

---

## 1. Task Queue & Backlog Overview

| Task ID | Tên Task | Phase | Ưu tiên | Trạng thái | Ghi chú / Blocker |
|---------|----------|-------|---------|------------|-------------------|
| `TASK-001` | Ingest dữ liệu sách từ `output/extracted/` vào SQLite DB | Phase 1 | P0 | `[x] DONE` | Nạp 492 content_units, 1078 sample_dialogues vào `data/custom_topics.db` |
| `TASK-002` | Tích hợp RAG Layer (`retrieve_dialogues`) vào `ai_engine.process_turn` | Phase 2 | P0 | `[x] DONE` | Nối `/api/process_turn` với RAG DB & quy đổi Level 1-20 sang IELTS Band |
| `TASK-003` | Nâng cấp Context-Aware Fallback Engine thay cho Mock Fallback tĩnh | Phase 3 | P0 | `[x] DONE` | Xử lý khi API rate-limit giữ nguyên ngữ cảnh & Level |
| `TASK-004` | Thống nhất 2 Pipeline (Pipeline A & Pipeline B) | Phase 4 | P1 | `[x] DONE` | Đồng bộ prompt construction & level rules |
| `TASK-005` | Kiểm thử E2E & Verification toàn bộ luồng hội thoại | Phase 5 | P0 | `[x] DONE` | Chạy test suite & verify 100% PASS |

> **Trạng thái hợp lệ:**
> - `[ ] TODO`: Chưa làm, chờ AI chọn
> - `[/] IN_PROGRESS`: AI đang thực hiện
> - `[x] DONE`: Hoàn thành, đã verify & proof
> - `[!] BLOCKED`: Bị kẹt, cần human intervention

---

## 2. Chi tiết các Tasks (Task Specs)

---

### 📌 TASK-001: Ingest dữ liệu sách từ `output/extracted/` vào SQLite DB

#### Metadata
```
Task ID:         TASK-001
Task Name:       Ingest dữ liệu sách từ output/extracted/ vào SQLite DB
Phase:           Phase 1 (Data Ingestion)
Task Type:       script / data
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-21
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Bảng `sample_dialogues` trong `data/custom_topics.db` hiện chỉ có 67 câu mẫu legacy, các sách trích xuất trong `output/extracted/` chưa bao giờ được nạp vào DB.
- **What:** Chạy và kiểm tra `scripts/insert_turso.py` để ingest toàn bộ YAML files từ `output/extracted/` vào SQLite `data/custom_topics.db`. Đảm bảo số lượng `content_units` và `sample_dialogues` tăng lên hàng nghìn bản ghi hợp lệ.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Chạy `insert_turso.py` thành công không có lỗi syntax/schema.
- [x] Bảng `sample_dialogues` và `content_units` trong `data/custom_topics.db` chứa > 500 bản ghi mới.
- [x] `retrieve_dialogues()` query được dữ liệu thực tế từ các topic sách mới (vd: `Childhood Memories`, `Enhance Your English...`).

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `scripts/insert_turso.py`, `data/custom_topics.db`
- **Files cấm đụng:** `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 scripts/insert_turso.py output/extracted/ --sqlite data/custom_topics.db
python3 -c "import sqlite3; conn=sqlite3.connect('data/custom_topics.db'); cur=conn.cursor(); cur.execute('SELECT count(*) FROM sample_dialogues'); print('sample_dialogues count:', cur.fetchone()[0])"
```

---

### 📌 TASK-002: Tích hợp RAG Layer (`retrieve_dialogues`) vào `ai_engine.process_turn`

#### Metadata
```
Task ID:         TASK-002
Task Name:       Tích hợp RAG Layer vào ai_engine.process_turn
Phase:           Phase 2 (RAG Integration)
Task Type:       feature / refactor
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-21
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Endpoint `/api/process_turn` (Web UI chính) hiện không hề gọi RAG `retrieve_dialogues()`, dẫn đến câu trả lời không tham khảo câu thoại mẫu từ sách.
- **What:** Trong `app/ai_engine.py`, cập nhật `_build_token_efficient_prompt()` để gọi `retrieve_dialogues()`, quy đổi level 1-20 sang band 4.0-9.0, và nhúng các reference dialogues tìm được vào System Prompt.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] `ai_engine.process_turn()` gọi `retrieve_dialogues()` trước khi dựng prompt.
- [x] Prompt gửi tới LLM chứa khối `REFERENCE DIALOGUES FROM BOOKS` đúng band level và topic tag.
- [x] RAG fallback cascade không bị crash khi topic rỗng.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/ai_engine.py`, `app/retrieval.py`
- **Files cấm đụng:** `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 -c "from app.ai_engine import ai_engine; res = ai_engine.process_turn('det_childhood_memory', 'lily', 'I love childhood memories', [], level=9); print(res)"
```

---

### 📌 TASK-003: Nâng cấp Context-Aware Fallback Engine thay cho Mock Fallback tĩnh

#### Metadata
```
Task ID:         TASK-003
Task Name:       Nâng cấp Context-Aware Fallback Engine
Phase:           Phase 3 (Fallback Overhaul)
Task Type:       feature / fix
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-21
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Khi API key rate-limit/lỗi (HTTP 429), `_get_mock_fallback_response()` tĩnh bốc câu ngẫu nhiên *"That sounds wonderful!"* bỏ qua `user_transcript` ("I lost my memory") và xóa bỏ ràng buộc độ khó Level 9.
- **What:** Xây dựng `_get_context_aware_fallback()` trong `app/ai_engine.py` nhận biết ngữ cảnh câu nói của user (positive/negative/confused), giữ nguyên topic hiện tại và tuân thủ số từ/ngữ pháp trong `LEVEL_CONFIGS`.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Khi user nói câu tiêu cực ("I lost my memory"), fallback phản hồi bằng sự cảm thông chứ không nói "That sounds wonderful!".
- [x] Fallback không bị bẻ lái sang topic ngẫu nhiên khác (như "Best Friends & Personality").
- [x] Số từ trong câu fallback tuân thủ range `min_words` và `max_words` của level tương ứng (ví dụ Level 9: 45-85 từ).

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/ai_engine.py`
- **Files cấm đụng:** `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/ -k fallback
```

---

### 📌 TASK-004: Thống nhất 2 Pipeline (Pipeline Consolidation)

#### Metadata
```
Task ID:         TASK-004
Task Name:       Thống nhất 2 Pipeline (Pipeline A & Pipeline B)
Phase:           Phase 4 (Refactoring)
Task Type:       refactor
Priority:        P1-High
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-21
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Hệ thống có 2 pipeline LLM đứt gãy (`ai_engine.py` và `conversational_agent.py` + `prompt_constructor.py`) làm hành vi giữa Web UI và Voice Turn không đồng nhất.
- **What:** Đồng bộ quy chuẩn dựng Prompt, bổ sung `LEVEL_CONFIGS` vào `prompt_constructor.py` và dùng chung data models cho response.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Cả `/api/process_turn` và `/api/voice/process_turn` đều tuân thủ `LEVEL_CONFIGS` 20 cấp độ.
- [x] Cả 2 pipeline đều sử dụng chung RAG retrieval layer.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `app/prompt_constructor.py`, `app/conversational_agent.py`, `app/main.py`
- **Files cấm đụng:** `pipeline/docs/core/**`

#### Verification Commands
```bash
pytest tests/
```

---

### 📌 TASK-005: Kiểm thử E2E & Verification toàn bộ luồng hội thoại

#### Metadata
```
Task ID:         TASK-005
Task Name:       Kiểm thử E2E & Verification toàn bộ luồng hội thoại
Phase:           Phase 5 (Verification & Hardening)
Task Type:       test / verification
Priority:        P0-Critical
Trạng thái:      [x] DONE
Ngày tạo:        2026-08-21
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Đảm bảo toàn bộ hệ thống sau khi refactor pass 100% kiểm thử và không có đứt gãy.
- **What:** Chạy test suite tổng hợp, chạy `pipeline/scripts/verify.py` và kiểm tra zero lints/errors.

#### Acceptance Criteria (Tiêu chí hoàn thành)
- [x] Toàn bộ unit tests & integration tests pass 100%.
- [x] `python3 pipeline/scripts/verify.py` pass Tier 1 checks.
- [x] Không có console error hay unhandled exception nào khi gọi API.

#### Scope (Phạm vi)
- **Files được sửa/tạo:** `tests/**`, `pipeline/docs/runtime/**`
- **Files cấm đụng:** `pipeline/docs/core/**`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py
```
