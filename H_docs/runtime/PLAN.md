# PLAN
# Kế hoạch thực thi — TASK-006: FastAPI Endpoints Bridge & Scenario Registry (`app/main.py` & `app/scenarios.py`)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-006
Task Name:  FastAPI Endpoints Bridge & Scenario Registry (`app/main.py`)
Spec:       Cập nhật các API endpoints hiện có trên FastAPI (`/api/scenarios`, `/api/start_scenario`, `/api/process_turn`, `/api/chat`) để phục vụ cả danh sách Topic từ Material Bank (5 DB markdown files) lẫn Custom Topics từ Turso DB.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Endpoint `/api/scenarios` trả về đầy đủ danh sách Topics từ 5 DB files (hơn 100 topics từ `MaterialBank`) kết hợp với default scenarios và custom scenarios.
- [ ] Endpoint `/api/scenarios/{scenario_id}` truy vấn chính xác scenario/topic details bất kể ID đến từ DEFAULT_SCENARIOS, MaterialBank topic_id, hay Turso custom scenarios.
- [ ] Endpoint `/api/start_scenario` và `/api/process_turn` (và `/api/chat`) hoạt động chính xác với `topic_id` từ MaterialBank.
- [ ] Đảm bảo tương thích ngược 100% với các custom scenario lưu trong Turso Cloud Database (`get_custom_scenarios()`).
- [ ] Unit tests bổ sung trong `tests/test_scenarios_bridge.py` kiểm tra `/api/scenarios` nạp đầy đủ MaterialBank topics và khởi tạo scenario thành công.
- [ ] Tier 1 verification (`python3 H_docs/scripts/verify.py`) pass 100%.
- [ ] Tier 2 Cognitive Review được ghi nhận trong `H_docs/runtime/DEBATE_LOG.md`.

### Verification Commands
```bash
pytest tests/test_scenarios_bridge.py tests/test_smoke.py
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Update `app/scenarios.py` to Bridge `MaterialBank`
- **Mục tiêu:** Cập nhật `list_scenarios()` và `get_scenario(scenario_id)` trong `app/scenarios.py` để tự động tích hợp danh sách topics từ `MaterialBank` (`get_material_bank()`).
- **Files sửa:** `app/scenarios.py`
- **Exit condition:** `list_scenarios()` trả về danh sách đầy đủ (> 100 topics) và `get_scenario(topic_id)` hỗ trợ nạp topic từ `MaterialBank`.

### Step 2: Ensure Endpoint Compatibility in `app/main.py`
- **Mục tiêu:** Rà soát và đảm bảo các endpoint `/api/scenarios`, `/api/start_scenario`, `/api/process_turn`, `/api/chat` xử lý mượt mà cả standard scenarios, MaterialBank topic_ids và custom scenarios.
- **Files sửa:** `app/main.py`
- **Exit condition:** Endpoints phản hồi 200 OK với đúng schema.

### Step 3: Add Unit Tests in `tests/test_scenarios_bridge.py`
- **Mục tiêu:** Tạo unit test kiểm tra `/api/scenarios`, `/api/scenarios/{scenario_id}`, `/api/start_scenario` với `topic_id` từ `MaterialBank`.
- **Files tạo:** `tests/test_scenarios_bridge.py`
- **Exit condition:** `pytest tests/test_scenarios_bridge.py` pass 100%.

### Step 4: Verification (Tier 1 & Tier 2)
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py` kiểm tra Tier 1 (ruff, mypy, pytest, bandit). Thực hiện Tier 2 Cognitive Review dựa trên `git diff` và ghi log vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` pass 100%, `DEBATE_LOG.md` result APPROVED.

### Step 5: Documentation & State Update
- **Mục tiêu:** Cập nhật `H_docs/context/Tasks_list.md` (`TASK-006` -> `[x] DONE`), `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`, và thực hiện atomic git commit.
- **Files sửa:** `H_docs/context/Tasks_list.md`, `H_docs/runtime/STATUS.md`, `H_docs/runtime/PROGRESS_LOG.md`
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
| v1 | 2026-08-10 | Tạo plan cho TASK-006 |
