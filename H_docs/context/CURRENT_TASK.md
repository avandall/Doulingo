# CURRENT TASK
# Task hiện tại — TASK-009: UI Roleplay Simplification & Random Roleplay Placement

> **Trạng thái:** CONTEXT (Mutable) | **Cập nhật:** 2026-08-10

---

## Metadata
```
Task ID:         TASK-009
Task Name:       UI Roleplay Simplification & Random Roleplay Placement
Phase:           Phase 5 (UI Refinement & Minimalization)
Task Type:       feature
Priority:        P1-High
Trạng thái:      [/] IN_PROGRESS
Ngày bắt đầu:    2026-08-10
```

---

## Bối cảnh & Mục tiêu
- **Why:** Trên UI hiện có quá nhiều roleplay tràn lan và lặp lại giống nhau. Cần tối giản roleplay, chuyển nút random roleplay xuống section roleplay và xóa các nút category filter trong roleplay.
- **What:**
  1. Move `#btn-random-roleplay` (`🎲 RANDOM ROLEPLAY`) down into the `EVERYDAY & CREATIVE ROLEPLAY` section.
  2. Remove `#roleplay-category-filter-bar` (category buttons in roleplay section).
  3. Streamline static default roleplays in `app/scenarios.py` to avoid repetitive/duplicate roleplays.
  4. Ensure `startRandomRoleplay()` works smoothly when clicked.

---

## Acceptance Criteria
- [ ] Nút `🎲 RANDOM ROLEPLAY` được di chuyển từ hero banner xuống trực tiếp section Roleplay.
- [ ] Các nút category filter trong section Roleplay (`#roleplay-category-filter-bar`) đã bị xóa hoàn toàn.
- [ ] Danh sách roleplay được tối giản gọn gàng, không bị trùng lặp lặp đi lặp lại.
- [ ] Nút `🎲 RANDOM ROLEPLAY` khởi tạo thành công một roleplay ngẫu nhiên với nhân vật AI.
- [ ] Chạy `python3 H_docs/scripts/verify.py` pass 100%.
