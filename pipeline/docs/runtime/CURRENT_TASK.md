# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-22
>
> ✏️ **HUMAN & AI ALIGNED CONTEXT.** Task đang được giao cho vòng lặp `harness.sh`.

---

## Task đang thực hiện

```
Task ID:      TASK-007
Task Name:    End-to-End Test Suite & MCP Browser Interactive Testing (<10 Calls)
Phase:        Phase 7 (E2E Verification & Browser QA)
Priority:     P0-Critical
Started:      2026-08-22
```

---

## Mục tiêu (Why & What)

**Tại sao cần làm task này?**
- Kiểm thử toàn bộ hệ thống như 1 real user trên giao diện và backend thực tế, đảm bảo tất cả các tính năng thuộc Phases 1-6 hoạt động mượt mà, không lỗi, không crash, đồng thời kiểm soát nghiêm ngặt tổng số lần gọi API thử nghiệm thực tế < 10 lần.

**Cụ thể cần làm gì?**
1. **Viết End-to-End Test Suite (`tests/test_e2e_conversational_system.py`):**
   - Kịch bản 1: Conversational AI Roleplay (Topic shift, Empathy active listening, Anti-repetition fallback).
   - Kịch bản 2: IELTS Exam Read-Then-Speak recording, transcribing state sync, and score evaluation flow.
   - Kịch bản 3: Modern Topic Explorer search & category filtering UI behavior.
   - Kịch bản 4: Observability, real-time logging trace (`logs/api_trace.log`), masked keys & status tracking.
   - Kịch bản 5: Edge-TTS natural voice parameters & Instant filler audio response (<100ms budget).
2. **Thực thi verification test suite & browser / system checks:**
   - Chạy E2E test suite và Tier 1 verification (`python3 pipeline/scripts/verify.py`).
   - Đảm bảo 100% pass, không còn bất cứ warning hay traceback rác.
3. **Cập nhật báo cáo tiến độ & documentation:**
   - Đánh dấu `[x] DONE` trong `Tasks_list.md`, cập nhật `STATUS.md`, `PROGRESS_LOG.md`, `PLAN.md` và `PROOF_OF_SOLUTION.md`.

---

## Acceptance Criteria (Tiêu chí hoàn thành)

Task được coi là DONE khi:
- [x] Test file `tests/test_e2e_conversational_system.py` được tạo và cover đầy đủ 5 kịch bản E2E chính.
- [x] Tất cả 7 phases trong Task Queue hoàn thành và verified pass 100%.
- [x] `pytest tests/test_e2e_conversational_system.py -v` pass 100%.
- [x] `python3 pipeline/scripts/verify.py` pass 100% (0 linter errors, 0 type errors, 0 test failures).
- [x] Tổng số API calls thử nghiệm thực tế < 10 lần.

---

## Verification Commands

```bash
pytest tests/test_e2e_conversational_system.py -v
python3 pipeline/scripts/verify.py
```
