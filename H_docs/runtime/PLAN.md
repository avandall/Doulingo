# PLAN
# Kế hoạch thực thi — TASK-005: AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-005
Task Name:  AI Engine Prompt Integration & Parameter Tuning (`app/ai_engine.py`)
Spec:       Tích hợp System Prompt động từ PromptFactory (MaterialBank) vào luồng gọi LLM trong `ai_engine.py` (`start_roleplay_greeting` & `process_turn`), đồng thời thiết lập các tham số sinh text tối ưu (`temperature: 0.8`, `presence_penalty: 0.6`).
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] `ai_engine` tự động kết nối và sử dụng `PromptFactory` để sample nguyên liệu (Vocabulary, Questions, Grammar, Personas) khi nhận `scenario_id` hoặc `topic_id`.
- [ ] Bổ sung tham số `presence_penalty: 0.6` và tinh chỉnh `temperature: 0.8` (hoặc 0.85 cho creative roleplay) đồng bộ trên các adapter LLM (Groq, Gemini, OpenAI, Ollama).
- [ ] Đảm bảo tương thích ngược: nếu `scenario_id` là custom scenario cũ không nằm trong MaterialBank thì fallback an toàn sang `get_scenario()`.
- [ ] Luồng multi-key fallback và trace logger hoạt động mượt mà không bị ngắt quãng.
- [ ] Thêm unit tests bổ sung trong `tests/test_ai_engine.py` kiểm tra tích hợp `PromptFactory` và tham số payload.
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.
- [ ] Tier 2 Cognitive Review được ghi nhận trong `H_docs/runtime/DEBATE_LOG.md`.

### Verification Commands
```bash
pytest tests/test_ai_engine.py
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Refactor `app/ai_engine.py`
- **Mục tiêu:** Tích hợp `PromptFactory` vào `start_roleplay_greeting` và `_build_token_efficient_prompt` / `process_turn`, đồng thời thêm `presence_penalty: 0.6` và tuning `temperature: 0.8` trong tất cả LLM API call payloads.
- **Files sửa:** `app/ai_engine.py`
- **Exit condition:** Logic gọi API thành công, sử dụng prompt từ `PromptFactory` và truyền đúng payload parameters.

### Step 2: Add Unit Tests in `tests/test_ai_engine.py`
- **Mục tiêu:** Thêm test case kiểm chứng `ai_engine` gọi `PromptFactory` nạp material bank prompt và payload chứa `presence_penalty`.
- **Files sửa:** `tests/test_ai_engine.py`
- **Exit condition:** `pytest tests/test_ai_engine.py` pass 100%.

### Step 3: Verification (Tier 1 & Tier 2)
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit). Thực hiện Tier 2 Cognitive Review dựa trên `git diff` và ghi log vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` pass 100%, `DEBATE_LOG.md` result APPROVED.

### Step 4: Documentation & State Update
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-005` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, và thực hiện atomic git commit.
- **Files tạo/sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`
- **Exit condition:** Git commit thành công.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 7
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-005 |
