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
- **Why:** Toàn bộ dữ liệu Template A, B, C từ các nguồn tài liệu IELTS và thông tin hồ sơ người dùng cần được lưu trữ trong Database quan hệ hỗ trợ Vector Search (PostgreSQL + pgvector) theo Schema hợp nhất được thiết kế tại mục 7 của `docs/plan.md`.
- **What:**
  1. Thiết kế DDL khởi tạo 12 bảng trong `app/db.py` (`content_units`, `band_tiers`, `function_details`, `function_band_variants`, `scenarios`, `scenario_branches`, `evaluation_hooks`, `sample_dialogues`, `hook_bank`, `vocabulary_lookup`, `user_profile`, `user_content_exposure`).
  2. Tạo HNSW Vector Cosine Index trên `sample_dialogues(embedding)`.
  3. Tạo GIN Index trên `content_units(topic_tags)` và B-Tree Index trên `target_band_min/max`.
  4. Đảm bảo script migration khởi tạo DB chạy mượt mà trên môi trường dev/cloud.

---

## Acceptance Criteria
- [ ] Thiết kế và tạo thành công DDL cho 12 bảng trong `app/db.py`.
- [ ] Bảng `sample_dialogues` có cột `embedding` kiểu Vector(1536) và chỉ mục HNSW cosine vector index.
- [ ] Bảng `content_units` hỗ trợ chỉ mục GIN trên `topic_tags` và B-Tree trên `target_band_min/max`.
- [ ] Bảng `hook_bank` và `vocabulary_lookup` được khởi tạo chuẩn schema phụ lục.
- [ ] Script khởi tạo DB chạy không bị lỗi foreign key hay constraint.
