# PLAN
# Kế hoạch thực thi — TASK-012

> **Task:** `TASK-012` Micro-LLM Heuristic Retry Rewriter (Natural Contextual Downgrade)
> **Trạng thái:** COMPLETED | **Cập nhật:** 2026-08-27

---

## 🎯 Task Spec Overview
Xây dựng engine Micro-LLM Heuristic Retry Rewriter để tự động hạ cấp từ vựng/cấu trúc (Contextual Downgrade) khi kết quả kiểm tra `HeuristicChecker.check_level_ceiling` báo lỗi vi phạm trần CEFR level. Thay vì thay từ cứng nhắc hoặc regenerate lại toàn bộ prompt nặng, Micro-LLM Rewriter sẽ rewrite tự nhiên trong <150ms, đảm bảo phong cách hội thoại, ngữ cảnh và câu hỏi mở ở cuối.

---

## 📌 Implementation Steps (Atomic Steps)

- [x] **Step 1: Build Micro-LLM Retry Rewriter Module (`app/core/micro_llm_rewriter.py`)**
  - Implement `MicroLLMRewriter` class with `rewrite_naturally(original_text, violating_words, target_level, ...)` method.
  - Create concise, low-latency prompt asking LLM to downgrade violating words naturally for the target CEFR level while preserving conversational tone and open-ended question ending.
  - Add fast fallback rewriting (heuristic synonym/phrase downgrade) if LLM call is unavailable/rate-limited.

- [x] **Step 2: Integrate Micro-LLM Rewriter into `AIEngine._call_llm_with_heuristic_loop` (`app/core/ai_engine.py`)**
  - Connect `MicroLLMRewriter` inside the retry loop when `check_res.is_violated` is detected.
  - Track `rewritten_by_micro_llm`, `retry_count`, and `violating_words` in the returned `heuristic_check` metadata.

- [x] **Step 3: Write Comprehensive Unit Tests (`tests/test_micro_llm_rewriter.py`)**
  - Test natural contextual downgrade with violating words.
  - Test preservation of open-ended questions and sentence structure.
  - Test fallback mode when LLM is unconfigured/rate-limited.
  - Test integration with `AIEngine._call_llm_with_heuristic_loop`.

- [x] **Step 4: Execute Verification & Mark TASK-012 DONE**
  - Run `python3 pipeline/scripts/verify.py` until PASS 100%.
  - Update `STATUS.md` and `PROGRESS_LOG.md`.
  - Mark `[x] DONE` line TASK-012 in `pipeline/docs/context/Tasks_list.md`.
