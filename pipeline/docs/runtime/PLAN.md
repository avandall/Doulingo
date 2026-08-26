# PLAN
# Kế hoạch thực thi — TASK-003: Build Dialogue Exemplar Bank & Hybrid RAG Engine

> **Trạng thái:** COMPLETED | **Tạo bởi:** AI | **Cập nhật:** 2026-08-26 21:31

---

## Task Reference

```
Task ID:    TASK-003
Task Name:  Build Dialogue Exemplar Bank & Hybrid RAG Engine
Spec:       Chuẩn hóa app/data/sample_dialogue_bank.json và module app/core/exemplar_rag.py thực hiện Metadata filter (level + persona + topic + dialogue_act) kết hợp Semantic search / MMR diversity.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [x] Module `ExemplarRAG.retrieve(level, persona, topic, dialogue_act, state_summary)` trả về 2-3 câu mẫu chuẩn nhất.
- [x] Pytest cho RAG retrieval pass 100% (`tests/test_exemplar_rag.py`).

### Scope
- **Files được sửa/tạo:** `app/core/exemplar_rag.py`, `tests/test_exemplar_rag.py`
- **Files cấm đụng:** `.env`, `pipeline/docs/core/**`

### Verification Commands
```bash
pytest tests/test_exemplar_rag.py
python3 pipeline/scripts/verify.py --test-target tests/test_exemplar_rag.py
```

---

## Execution Steps

### Step 1: Implement `app/core/exemplar_rag.py` [DONE]
- **Mục tiêu:** Xây dựng class `ExemplarRAG` hỗ trợ Metadata Filtering (level, persona, topic, dialogue_act), Cosine Similarity Semantic Search (với `state_summary`), và MMR (Maximal Marginal Relevance) Diversity Ranking.
- **Result:** Module hoàn thành, đạt độ trễ < 1ms.

### Step 2: Implement Unit Tests in `tests/test_exemplar_rag.py` [DONE]
- **Mục tiêu:** Xây dựng bộ test suite kiểm tra metadata filtering, relaxation fallback, semantic search, MMR ranking, prompt formatting, và performance benchmark.
- **Result:** Test suite 11/11 tests pass 100%.

### Step 3: Run Verification (`pytest tests/test_exemplar_rag.py` & `python3 pipeline/scripts/verify.py`) [DONE]
- **Mục tiêu:** Đảm bảo tất cả ruff, mypy, pytest pass 100%.
- **Result:** Tier 1 Verification Report PASS 100%.

### Step 4: Update Progress & Complete Task [DONE]
- **Mục tiêu:** Đánh dấu [x] DONE TASK-003 trong `Tasks_list.md` và dừng phiên để harness commit git.
- **Result:** Cập nhật `Tasks_list.md`, `STATUS.md`, `PROGRESS_LOG.md` và `PLAN.md`.
