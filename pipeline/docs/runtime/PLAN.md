# TASK EXECUTION PLAN
# Task TASK-006: Test Suite Tích Hợp Hermetic & Deterministic Verification (`verify.py`)

> **Trạng thái:** COMPLETED | **Ngày:** 2026-09-09

---

## 🎯 Task Goal
Đảm bảo toàn bộ hệ thống đạt tiêu chuẩn kỹ thuật Harness Engineering, chạy cô lập không tốn token mạng (Hermetic), kiểm chứng đầy đủ các kịch bản failover và pass 100% verification checks.

---

## 📋 Atomic Steps

### [x] Step 1: Implement Hermetic Tests in `tests/test_ai_engine.py`
- Mock LLM responses for Gemini, Groq, OpenAI.
- Simulate Gemini 429 quota exhaustion and verify automatic pool failover to Groq.
- Simulate truncation/ValidationError and verify fallback.

### [x] Step 2: Implement Benchmark Script
- Create `scripts/benchmark_prompt_caching.py` to measure real-time TTFT differences outside CI.

### [x] Step 3: Verification & Milestone Completion
- Run `python3 pipeline/scripts/verify.py` (ensure PASS 100%).
- Mark `TASK-006` as `[x] DONE` in `Tasks_list.md`.
- Commit Git cleanly.

