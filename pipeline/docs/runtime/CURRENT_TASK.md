# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced) | **Cập nhật:** 2026-09-09 23:55

---

## 🎯 Task Spec: TASK-006
### 📌 TASK-006: Test Suite Tích Hợp Hermetic & Deterministic Verification (`verify.py`)

#### Metadata
```
Task ID:         TASK-006
Task Name:       Test Suite Tích Hợp Hermetic & Deterministic Verification (`verify.py`)
Phase:           Phase 4 (Quality & Verification)
Task Type:       test
Priority:        P0-Critical
Trạng thái:      [/] IN_PROGRESS
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Đảm bảo toàn bộ hệ thống đạt tiêu chuẩn kỹ thuật Harness Engineering, chạy cô lập không tốn token mạng (Hermetic) và kiểm chứng đầy đủ các kịch bản failover.
- **What:**
  1. Viết bộ unit tests `tests/test_schemas.py` và `tests/test_ai_engine.py` với Mock LLM responses (Gemini, Groq, OpenAI).
  2. Giả lập kịch bản Gemini trả về lỗi 429 Quota -> kiểm tra hệ thống chuyển sang Groq với cùng schema.
  3. Giả lập kịch bản model trả về JSON bị cắt cụt (Truncation) -> kiểm tra cơ chế chuyển provider kế tiếp.
  4. Viết script benchmark riêng ngoài CI: `scripts/benchmark_prompt_caching.py` để kiểm chứng độ trễ thực tế khi có API key.

#### Acceptance Criteria
- [ ] Toàn bộ test suite trong `tests/` chạy độc lập không phụ thuộc Internet và pass 100%.
- [ ] Giả lập lỗi quota và lỗi cắt cụt token được xử lý mượt mà qua failover logic.
- [ ] `python3 pipeline/scripts/verify.py` pass 100% (Tier 1 check).
- [ ] Git status sạch sẽ, tuân thủ đúng quy ước commit.

#### Scope
- **Files được sửa/tạo:** `tests/**`, `scripts/benchmark_prompt_caching.py`, `pipeline/docs/runtime/**`

#### Verification Commands
```bash
python3 pipeline/scripts/verify.py
```



