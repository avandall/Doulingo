# Implementation Plan — TASK-009: UI Roleplay Simplification & Random Roleplay Placement

## Goal
Optimize the Roleplay section in the UI by removing redundant/duplicate roleplay topics, moving the "🎲 RANDOM ROLEPLAY" button into the Roleplay section, and removing category filter pills in the Roleplay section.

## Proposed Changes

### 1. `static/index.html`
- Remove `#btn-random-roleplay` from the hero banner (`.hero-actions`).
- In Section 2 (`EVERYDAY & CREATIVE ROLEPLAY`), insert `#btn-random-roleplay` into the section header box or next to section title.
- Remove `#roleplay-category-filter-bar` completely (deleting category filter buttons: "Tất cả Roleplay", "Giao tiếp hàng ngày", "Tình huống sáng tạo").

### 2. `static/js/app.js`
- Update `initCategoryFilterBar()` to remove event listeners for `#roleplay-category-filter-bar`.
- Simplify `renderScenarios()` to render roleplay scenarios directly into `#roleplay-scenarios-grid` without checking `roleplayCat`.
- Ensure `startRandomRoleplay()` selects randomly from available non-IELTS roleplay scenarios (or all roleplays).

### 3. `app/scenarios.py`
- Streamline `DEFAULT_SCENARIOS` roleplay topics (non-IELTS) to eliminate redundant/repetitive items. Keep a clean, essential set of 4-6 distinct everyday roleplay scenarios (e.g. Daily Chat, Cafe & Dining, Travel, Work/Study).

## Verification Plan
- Run `python3 H_docs/scripts/verify.py` to ensure all Python tests pass.
- Test server runtime via `uv run python main.py` or `pytest`.
