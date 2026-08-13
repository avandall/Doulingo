# Iteration 34 Snapshot — TASK-006 Prompt Constructor Engine v1 (`app/prompt_constructor.py`)

## Context & Goal
Build `app/prompt_constructor.py` to construct the System Prompt and message sequence for the Conversational Agent (`TASK-007`). Integrates user profile band estimation, target topic, 2-4 retrieved sample dialogues from `app/retrieval.py` (`TASK-005`), anti-verbatim repetition rules, follow-up question constraints, and strict JSON output schema instructions.

## Verification & Test Evidence
- **Pytest:** `pytest tests/test_prompt_constructor.py` — 4/4 passed in 0.09s.
- **Tier 1 Verification (`python3 H_docs/scripts/verify.py`):** Status PASS (Ruff, Mypy, Bandit, Pytest 100% GREEN).
- **Reviewer Approval:** Ghi nhận tại `H_docs/runtime/DEBATE_LOG.md` (Review Session 2026-08-13 07:44 — APPROVED).

## Git Commit
- **Commit Hash:** `0f1aa05`
- **Message:** `[TASK-006] feat(prompt): implement prompt constructor engine v1 with context assembly and JSON schema instruction`

## Status & Next Step
- **TASK-006:** `[x] DONE`
- **Next Task:** `TASK-007: Conversational Agent & Structured JSON Parser (app/conversational_agent.py)`
