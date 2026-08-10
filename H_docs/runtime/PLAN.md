# PLAN
# Kế hoạch thực thi — TASK-000: Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite)

> **Trạng thái:** RUNTIME (Auto-generated) | **Tạo bởi:** AI | **Ngày tạo:** 2026-08-10

---

## Task Reference

```
Task ID:    TASK-000
Task Name:  Cloud DB Setup & Persistence Migration (`app/db.py` -> Turso Cloud SQLite)
Spec:       Thêm cấu hình TURSO_DATABASE_URL và TURSO_AUTH_TOKEN trong .env và app/db.py.
            Kết nối thành công đến Turso Cloud SQLite bằng libsql_experimental hoặc fallback local SQLite nếu thiếu credentials.
            Tự động khởi tạo/migrate các bảng custom_scenarios, word_dictionary, user_stats.
```

---

## Spec (Đặc tả)

### Acceptance Criteria
- [ ] Thêm `libsql-experimental` vào `requirements.txt`.
- [ ] Cập nhật `app/db.py` hỗ trợ đọc `TURSO_DATABASE_URL` và `TURSO_AUTH_TOKEN` từ môi trường (`os.getenv`).
- [ ] Hàm `get_db_connection()` trong `app/db.py` ưu tiên dùng `libsql_experimental.connect` khi có `TURSO_DATABASE_URL`, và tự động fallback về `sqlite3.connect(DB_PATH)` khi thiếu URL hoặc lỗi kết nối.
- [ ] Đảm bảo khởi tạo các bảng `custom_scenarios`, `word_dictionary`, `user_stats` hoạt động 100% không lỗi trên cả Turso DB và Local SQLite.
- [ ] Cập nhật các hàm thao tác DB trong `app/db.py` (`add_custom_scenario`, `get_custom_scenarios`, `save_translated_word`, `get_translated_word`, `get_all_saved_words`, `get_user_stats`, `add_user_xp`) tương thích với cả `libsql_experimental` và `sqlite3`.
- [ ] Viết unit tests trong `tests/test_db_turso.py` kiểm tra kết nối DB, migration bảng, và fallback mechanism.
- [ ] Chạy `python3 H_docs/scripts/verify.py` pass 100%.

### Verification Commands
```bash
pytest tests/test_db_turso.py
python3 H_docs/scripts/verify.py
```

---

## Execution Steps

### Step 1: Update Dependencies & DB Module (`requirements.txt`, `app/db.py`)
- **Mục tiêu:** Thêm `libsql-experimental>=0.0.55` vào `requirements.txt`. Refactor `app/db.py` để hỗ trợ Turso Cloud SQLite với graceful fallback về local SQLite.
- **Files sửa:** `requirements.txt`, `app/db.py`
- **Exit condition:** `app/db.py` import thành công, hàm `init_db()` khởi tạo được tất cả các bảng.

### Step 2: Unit Testing (`tests/test_db_turso.py`)
- **Mục tiêu:** Viết unit test kiểm tra khởi tạo bảng, CRUD operations, và fallback behavior.
- **Files tạo:** `tests/test_db_turso.py`
- **Exit condition:** `pytest tests/test_db_turso.py` pass 100%.

### Step 3: Tier 1 Verification & Tier 2 Cognitive Review
- **Mục tiêu:** Chạy `python3 H_docs/scripts/verify.py`, kiểm tra `VERIFICATION_REPORT.md`, sau đó thực hiện Tier 2 Review trên `git diff` và append vào `DEBATE_LOG.md`.
- **Files tạo/sửa:** `H_docs/runtime/VERIFICATION_REPORT.md`, `H_docs/runtime/DEBATE_LOG.md`
- **Exit condition:** `verify.py` report status PASS, `DEBATE_LOG.md` result APPROVED.

---

## Iteration Budget

```
Estimated iterations: 1
Maximum allowed:      2
Context refresh at:   Iteration 2
```

---

## Plan Revision History

| Revision | Ngày | Lý do thay đổi |
|----------|------|----------------|
| v1 | 2026-08-10 | Tạo plan cho TASK-000 |
