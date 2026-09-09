# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced) | **Cập nhật:** 2026-09-09 23:40

---

## 🎯 Task Spec: TASK-003
### 📌 TASK-003: Phân Vùng Prompt & Tối Ưu Hóa Prompt Caching (~1,200 Tokens)

#### Metadata
```
Task ID:         TASK-003
Task Name:       Phân Vùng Prompt & Tối Ưu Hóa Prompt Caching (~1,200 Tokens)
Phase:           Phase 2 (Prompt Caching)
Task Type:       perf
Priority:        P0-Critical
Trạng thái:      [/] IN_PROGRESS
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Tối ưu hóa thời gian prefill của Groq/OpenAI xuống < 400ms bằng Prefix Caching, đồng thời giữ Gemini chạy mượt mà ở chế độ throughput tiêu chuẩn.
- **What:**
  1. Tách cấu trúc trong `app/rag/prompt_constructor.py` thành:
     - `build_static_cacheable_prefix(character_id, level, scenario, scenario_angle)`: Kích thước ~1,200 tokens, giữ nguyên bất biến trong suốt session.
     - `build_dynamic_turn_suffix(history, user_transcript)`: Chỉ chứa lịch sử đối thoại và câu nói mới nhất.
  2. Cố định `scenario_angle` ngay từ `start_roleplay_greeting` và lưu vào session, không sinh ngẫu nhiên ở giữa các turns.
  3. Đảm bảo rolling prune lịch sử chỉ thay đổi phần suffix, không chạm vào prefix.

#### Acceptance Criteria
- [ ] Static Prefix duy trì độ dài >= 1,024 tokens và nội dung bất biến giữa các turn của cùng một session.
- [ ] Đo lường TTFT trên Groq/OpenAI giảm xuống < 400ms từ turn 2 trở đi.
- [ ] Gemini 2.0 Flash xử lý prompt trơn tru mà không bị nghẽn prefill.

#### Scope
- **Files được sửa/tạo:** `app/rag/prompt_constructor.py`, `app/core/ai_engine.py`, `tests/test_prompt_caching.py`

#### Verification Commands
```bash
pytest tests/test_prompt_caching.py
```
