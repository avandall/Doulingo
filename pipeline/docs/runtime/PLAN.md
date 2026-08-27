# PLAN: TASK-005 — Refactor Decoupled 3-Tier Prompt System for All 9 Personas

> **Task ID:** TASK-005  
> **Phase:** Phase 2 (Architecture Harmonization)  
> **Priority:** P1-High  
> **Target Files:** `app/characters/__init__.py`, `app/core/prompt_factory.py`, `app/data/persona_definitions.json`, `tests/test_characters.py`

---

## 🎯 Goal & Acceptance Criteria
- [x] Cấu trúc prompt mới 3 tầng (Tier 1: Core Pedagogy & Warmth, Tier 2: Persona Overlay từ JSON, Tier 3: Adaptive CEFR Horizon) được áp dụng nhất quán cho toàn bộ nhân vật.
- [x] Loại bỏ hoàn toàn luật ép `min_words` cứng nhắc và các ví dụ mẫu gây lặp câu.
- [x] Pytest nghiệm thu `tests/test_characters.py` pass 100% cho tất cả nhân vật và Tier 1 verify script (`python3 pipeline/scripts/verify.py`) PASS 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Create `app/data/persona_definitions.json` & Refactor `app/characters/__init__.py` [x]
- Create `app/data/persona_definitions.json` containing standardized persona metadata and overlay instructions for all 9+ personas (Alex, Lily, Oscar, Viktor, Chanel, Kaelen, Colt, Zarina, Scarlet, Luigi).
- Update `app/characters/__init__.py` to load character definitions dynamically from `app/data/persona_definitions.json` with fallback to default dictionary.
- Ensure no character prompt contains rigid `min_words` or repetitive sample sentences.

### Step 2: Refactor `app/core/prompt_factory.py` to Implement 3-Tier Prompt System [x]
- Define Tier 1 (Core Pedagogy & Warmth), Tier 2 (Persona Overlay), Tier 3 (Adaptive CEFR Horizon).
- Implement `build_3tier_prompt()` and enhance `PromptFactory` to construct decoupled 3-tier system prompts.
- Ensure strict removal of rigid `min_words` constraints and template repetition.

### Step 3: Implement `tests/test_characters.py` & Verify [x]
- Create `tests/test_characters.py` testing character loading, 3-tier prompt generation, absence of `min_words`, and persona overlay consistency.
- Run `pytest tests/test_characters.py` and `python3 pipeline/scripts/verify.py`.
