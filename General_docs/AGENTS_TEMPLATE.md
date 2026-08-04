# 🤖 AGENTS.md — Agent Execution Constitution & Harness Rules (Generic Template)

This document defines the non-negotiable behavioral boundaries and operating instructions for all AI coding agents (Antigravity, Claude Code, Cursor, Aider, etc.) working in this project repository.

---

## 1. Core Directives (*Tips 1, 7, 28*)
1. **You Make the Decisions, AI Executes (*Tip 1*):**
   * The human engineer owns system architecture, API schemas, design tokens, and product decisions.
   * Do **not** invent new frameworks or libraries unless explicitly requested in `docs/specs.md`.
2. **Choose Your Shipping Mode (*Tip 28*):**
   * **Interactive Pair Mode:** Ask clarifying questions for ambiguous user intent.
   * **Autonomous Loop Mode (`Ralph Loop`):** Do not ask questions. Execute the single target item from `docs/specs.md`, run verification tests, update `docs/WORK_BOARD.md`, commit changes, or pull the handbrake (`docs/BLOCKED.md`).
3. **Smarter With Every Repetition (*Tip 7*):**
   * If you discover a recurring bug or confusing pattern, document the lesson in `docs/rules.md` or `docs/TECH_DEBT.md`.

---

## 2. Context & Session Hygiene (*Tips 8, 9, 15*)
1. **Never Compact Your Chat (*Tip 8*):**
   * Summarizing or compacting long conversation histories degrades agent reasoning. When context limits approach, commit progress and start a fresh session.
2. **One Item, One Fresh Chat (*Tip 15*):**
   * Pick **one** uncompleted checkbox item (`[ ]` -> `[/]`) from `docs/specs.md`. Complete it, run tests, mark `[x]`, commit, and finish your turn.
3. **Spawn Helper Agents (*Tip 9*):**
   * Use subagents for parallel research or codebase searches (`grep_search`, `list_dir`).

---

## 3. Error Handling & Loop Recovery (*Tips 11, 16, 18, 19*)
1. **Fix a Bug Older Than You (*Tip 11*):**
   * Trace git history (`git log`, `git blame`) before modifying legacy code. Check `docs/TECH_DEBT.md` first.
2. **The `BLOCKED.md` Handbrake (*Tip 16*):**
   * If you encounter an unresolvable error after 2 reasonable attempts, **STOP**. Document details in `docs/BLOCKED.md` and exit with code `2`.
3. **Recover With Git Reset (*Tip 18*):**
   * In automated loop executions, if verification tests fail after an implementation attempt, use `git reset --hard HEAD` to restore a clean state.
4. **Exit Codes for Every Ending (*Tip 19*):**
   * Ensure scripts return `0` on success, `1` on retryable failure, and `2` when blocked.
