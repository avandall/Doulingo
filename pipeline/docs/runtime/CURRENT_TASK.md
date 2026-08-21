# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-21

---

## Task đang thực hiện

```
Task ID:      TASK-005
Task Name:    Kiểm thử E2E & Verification toàn bộ luồng hội thoại
Phase:        Phase 5 (Verification & Hardening)
Priority:     P0-Critical
Started:      2026-08-21
```

---

## Mục tiêu (Why & What)

**Tại sao cần làm task này?**
- Đảm bảo toàn bộ hệ thống sau khi refactor (từ TASK-001 đến TASK-004) pass 100% kiểm thử (Unit, Integration, E2E) và không bị lỗi hay đứt gãy.

**Cụ thể cần làm gì?**
- Chạy test suite tổng hợp (`pytest tests/`), chạy `python3 pipeline/scripts/verify.py` kiểm tra zero lints/type errors/security issues/runtime failures, và đảm bảo mọi API endpoint hoạt động ổn định.

---

## Acceptance Criteria (Tiêu chí hoàn thành)

Task được coi là DONE khi:
- [x] Toàn bộ unit tests & integration tests pass 100%.
- [x] `python3 pipeline/scripts/verify.py` pass Tier 1 checks (Ruff, Mypy, Bandit, Pytest).
- [x] Không có console error hay unhandled exception nào khi gọi API.

---

## Verification Commands

```bash
python3 pipeline/scripts/verify.py
```
