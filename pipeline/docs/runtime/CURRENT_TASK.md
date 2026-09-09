# CURRENT TASK
# Task hiện tại đang thực thi — Context cho AI agent

> **Trạng thái:** RUNTIME (Auto-Generated / Synced) | **Cập nhật:** 2026-09-09 23:50

---

## 🎯 Task Spec: TASK-005
### 📌 TASK-005: Build Script & Tích Hợp SQLite3 WASM Tra Cứu Từ Điển 0ms

#### Metadata
```
Task ID:         TASK-005
Task Name:       Build Script & Tích Hợp SQLite3 WASM Tra Cứu Từ Điển 0ms
Phase:           Phase 3 (WebAssembly Client)
Task Type:       feat
Priority:        P1-Normal
Trạng thái:      [/] IN_PROGRESS
Ngày tạo:        2026-09-09
```

#### Bối cảnh & Mục tiêu (Why & What)
- **Why:** Loại bỏ độ trễ mạng 100-300ms khi tra nghĩa từ vựng trên bong bóng chat bằng cơ sở dữ liệu SQLite nhúng trực tiếp trong RAM trình duyệt.
- **What:**
  1. Tạo offline build script `scripts/build_vocab_wasm_db.py` trích xuất 3,000 từ vựng cốt lõi từ `data/dictionary.db` tạo thành `static/data/vocab_core.sqlite` (~1.1MB, có index `idx_word`).
  2. Tạo `static/js/dict_wasm.js` nạp `sqlite3.wasm` và mở file DB trong RAM.
  3. Kết nối sự kiện click từ vựng trên speech bubble với hàm `dict_wasm.lookup(word)`.
  4. Cơ chế Progressive Enhancement: nếu WASM chưa sẵn sàng hoặc từ không có trong 3,000 từ cốt lõi -> tự động gọi API `/api/dictionary/lookup`.

#### Acceptance Criteria
- [ ] Script `scripts/build_vocab_wasm_db.py` chạy độc lập và sinh ra file SQLite hợp lệ.
- [ ] Tra cứu 3,000 từ cốt lõi trên client phản hồi < 1ms (0ms network round-trip).
- [ ] Tự động fallback về API backend đối với các từ hiếm không nằm trong database RAM.

#### Scope
- **Files được sửa/tạo:** `scripts/build_vocab_wasm_db.py`, `static/js/dict_wasm.js`, `static/data/vocab_core.sqlite`, `static/js/app.js`

#### Verification Commands
```bash
python3 scripts/build_vocab_wasm_db.py
python3 pipeline/scripts/verify.py --quick
```


