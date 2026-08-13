# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-13

---

## Task đang thực thi

```
Task ID:      TASK-018
Task Name:    Weekly Performance Reporting Engine & Hidden Scoring UI (`app/reporting.py`)
Phase:        Phase 3 (Anti-Repetition, Persona & Memory)
Priority:     P2-Normal
Started:      2026-08-13
Status:       [/] IN_PROGRESS
```

---

## Acceptance Criteria (TASK-018)

- [ ] Giao diện hội thoại chính KHÔNG hiển thị điểm band từng câu (Hidden scoring on main conversation UI).
- [ ] Sinh báo cáo tuần tổng hợp tiến trình 4 trục (Fluency, Lexical, Grammar, Pronunciation) lấy từ dữ liệu Tier 2 (`TASK-012`), không chỉ band tổng từ `TASK-013`.
- [ ] Log & persist Tier 2 evaluation history in DB table `tier2_evaluations` so weekly trends across 4 axes can be queried accurately.
- [ ] Module `app/reporting.py` provides `save_tier2_evaluation` and `generate_weekly_report(user_id, days=7)`.
- [ ] API endpoint `GET /api/reports/weekly` (hoặc `/api/reporting/weekly`) returns weekly performance report JSON.
- [ ] Unit tests in `tests/test_reporting.py` cover weekly report generation, 4-axis breakdown, empty/sparse evaluation cases, and API endpoint integration.
- [ ] `python3 H_docs/scripts/verify.py` passes 100% (Ruff, Mypy, Bandit, Pytest).

---

## Verification Commands

```bash
python3 H_docs/scripts/verify.py
pytest tests/test_reporting.py
```

