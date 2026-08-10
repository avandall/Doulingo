# CURRENT TASK
# Task hiện tại — TASK-003: Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-10

---

## Metadata
```
Task ID:         TASK-003
Task Name:       Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`)
Phase:           Phase 2 (Sampling & Prompt Factory)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [/] IN_PROGRESS
Ngày bắt đầu:    2026-08-10
```

---

## Bối cảnh & Mục tiêu
- **Why:** Cần một bộ lắp ráp System Prompt động dựa trên việc sample nguyên liệu ngẫu nhiên từ `MaterialBank` theo level của người dùng.
- **What:** Xây dựng module `app/prompt_factory.py` chứa class `PromptFactory`.

---

## Acceptance Criteria
- [ ] Class `PromptFactory` có hàm `sample_materials(topic_id, level)` thực hiện sample 1 Persona, 3-4 Vocab items, 1-2 Questions theo band điểm.
- [ ] Hàm `build_system_prompt(topic_id, level, character_id, user_history)` lắp ráp thành công System Prompt hoàn chỉnh.
- [ ] Hỗ trợ fallback an toàn nếu `topic_id` không tồn tại trong Material Bank.
- [ ] Code tuân thủ 100% Tier 1 CLI check (`python3 H_docs/scripts/verify.py`).
- [ ] Tier 2 Cognitive Review đạt `APPROVED`.
