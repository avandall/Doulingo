# CURRENT TASK
# Task hiện tại — TASK-000: Database Schema Design & Migration (`content_units`, `sample_dialogues`, etc.)

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-11 (Dựa trên `Tasks_list.md` v2 & `6_important_tasks_solution.md`)

---

## Metadata
```
Task ID:         TASK-000
Task Name:       Database Schema Design & Migration (`content_units`, `sample_dialogues`, etc.)
Phase:           Phase 0 (Data Foundation)
Task Type:       feature
Priority:        P0-Critical
Trạng thái:      [ ] TODO
Ngày bắt đầu:    2026-08-11
Tài liệu tham khảo: H_docs/context/Tasks_list.md & H_docs/context/6_important_tasks_solution.md
```

---

## Bối cảnh & Mục tiêu
- **Why:** Toàn bộ dữ liệu Template A, B, C từ các nguồn tài liệu IELTS và thông tin hồ sơ người dùng cần được lưu trữ trong Database quan hệ hỗ trợ Vector Search (Turso/libSQL) theo Schema cập nhật tại `H_docs/context/Tasks_list.md` (TASK-000).
- **What:**
  1. Thiết kế DDL khởi tạo 12 bảng theo chuẩn libSQL/Turso (`content_units`, `band_tiers`, `function_details`, `function_band_variants`, `scenarios`, `scenario_branches`, `evaluation_hooks`, `sample_dialogues`, `hook_bank`, `vocabulary_lookup`, `user_profile`, `user_content_exposure`).
  2. Dùng cột `embedding` kiểu `F32_BLOB(384)` và tạo index `libsql_vector_idx(embedding, 'metric=cosine')`.
  3. Cấu hình `topic_tags` dạng JSON text, query filter qua JSON/LIKE.
  4. Chuẩn bị script nạp dữ liệu và embedded replica sync cho Render free tier.

---

## Acceptance Criteria
- [ ] DDL 12 bảng chạy không lỗi trên Turso thật (kiểm tra bằng `turso db shell`)
- [ ] Cột `embedding` kiểu `F32_BLOB(384)` — KHÔNG dùng BLOB chung hoặc TEXT
- [ ] Vector index `sd_vec_idx` tạo được sau khi có ít nhất 1 row có embedding
- [ ] `topic_tags` lưu JSON string, query được bằng `LIKE '%"<tag>"%'`
- [ ] Foreign key cascade hoạt động: xoá `content_units` → cascade xoá `band_tiers` và `sample_dialogues`
- [ ] Script `insert_turso.py --turso-url ... --turso-token ...` insert thành công không lỗi
- [ ] Script `generate_embeddings.py --turso-url ...` cập nhật được embedding, `length(embedding) = 1536` (384 float × 4 bytes)
- [ ] Query `vector_top_k` trả về kết quả sau khi đủ data + index
