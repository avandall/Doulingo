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
