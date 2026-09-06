# 📓 LEARNINGS — Durable Knowledge Inbox

> **Harness Engineering Principle (Tip 7 & 21):**
> Collect hard-won discoveries, tricky edge cases, and systemic tool errors here.
> After a Ralph Loop execution, `scripts/ralph-retro.sh` reviews this inbox and promotes actionable lessons into permanent documentation (`docs/*`), routers (`AGENT_GUIDE.md`), or prompt templates (`prompts/*`).

---

## Format for New Entries
```markdown
### [YYYY-MM-DD] <Topic / Symptom>
- **Context / Task:** [TASK-XXX] <Brief context>
- **Root Cause:** What actually went wrong or was missing.
- **Resolution:** What fixed it.
- **Promoted To:** (e.g. `docs/context/TECH_CONTEXT.md` / `scripts/verify.py` / None)
```

---

## Historical Learnings

### [2026-08-31] Ralph Loop Task-Bound Sessions & Memory Flush
- **Context / Task:** Multi-task overnight execution.
- **Root Cause:** Resetting conversation per iteration caused unnecessary reload overhead; keeping conversation across multiple tasks caused context drift & compaction.
- **Resolution:** Adopted Task-Bound Sessions — sustain 1 clean session per Task (maximizing prompt cache), then flush memory completely when switching tasks.
- **Promoted To:** `pipeline/docs/core/HARNESS_PROTOCOL.md` & `pipeline/scripts/harness.sh`.

### [2026-09-07] CLI & Verification Subprocess Execution Timeout Protection
- **Context / Task:** Ralph Loop execution run (20260906-230618) encountering `Error: timeout waiting for response` in iter-3.
- **Root Cause:** Subprocess test runs and Playwright headless engine tasks executed via `verify.py` lacked explicit timeout limits in `run_command()`, causing long-running or hanging subprocesses to block until the parent CLI runner hit print-timeout.
- **Resolution:** Added 60s timeout limit with `subprocess.TimeoutExpired` handling in `verify.py`, updated `TECH_CONTEXT.md` with Playwright & pytest timeout guidelines, updated `AGENT_GUIDE.md` and `PROMPT.md` with rapid targeted verification rules (`--quick` / `--test-target`), updated `BOUNDARIES.md` to prohibit unbounded blocking subprocess calls, and updated `python_backend/preset.yaml`.
- **Promoted To:** `pipeline/scripts/verify.py`, `pipeline/docs/context/TECH_CONTEXT.md`, `pipeline/docs/context/BOUNDARIES.md`, `pipeline/AGENT_GUIDE.md`, `pipeline/prompts/PROMPT.md`, `pipeline/presets/python_backend/preset.yaml`.
