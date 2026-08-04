# 🛑 docs/BLOCKED.md — The Handbrake Log (Generic Template)

> **The Handbrake**: When an AI coding agent encounters an unresolvable error after 2 reasonable attempts, it must **STOP**, log the failure here, and exit with code `2` (*Tip 16, 19*).

---

## 🚨 Blocked Items Log

| Date | Spec Item | Error Description | Last Command Run | Status |
| :--- | :--- | :--- | :--- | :--- |
| *YYYY-MM-DD* | *Example Item* | *Example error description* | *Command executed* | *RESOLVED / BLOCKED* |

---

## 🔓 Resolution Workflow for Engineers
1. Review the error description in the table above.
2. Fix the underlying dependency, API credential, or requirement in `docs/specs.md`.
3. Update the item's Status from `BLOCKED` to `RESOLVED`.
4. Re-run the target spec item in a **fresh chat session** (*Tip 15*).
