# 🧹 docs/TECH_DEBT.md — Tech Debt Ledger (Generic Template)

> This ledger records non-blocking technical debt, legacy improvements, and TODOs (*Tip 6, 11*).

---

## 1. Technical Debt Register
| ID | Component | Description & Root Cause | Proposed Solution | Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEBT-01** | *Example Module* | *Description of technical debt or legacy constraint* | *Proposed clean refactor* | *OPEN / RESOLVED* |

---

## 2. Rules for Addressing Tech Debt (*Tip 6, 11*)
- **Do Not Refactor Silently:** Never refactor legacy code while working on a feature spec item (*Tip 15*).
- **Verify Intentional Constraints:** Always check git blame and git log before changing legacy patterns (*Tip 11*).
