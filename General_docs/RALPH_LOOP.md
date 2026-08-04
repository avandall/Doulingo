# 🔁 docs/RALPH_LOOP.md — Autonomous Build-Test-Fix Manual (Generic Template)

> This manual defines the operational guidelines for running **The Ralph Loop** — the autonomous build-test-fix cycle for any project (*Tip 17*).

---

## 1. What is The Ralph Loop? (*Tip 17*)
The Ralph Loop is an autonomous workflow where an AI coding agent executes tasks from `docs/specs.md` unattended while maintaining strict quality and error boundaries.

```mermaid
graph TD
    A[Start Fresh Session - Tip 15] --> B[Read AGENTS.md & docs/rules.md]
    B --> C[Pick 1 Unfinished Item from docs/specs.md]
    C --> D[Implement Logical Unit - Tip 14]
    D --> E{Run Verification Tests}
    E -->|Success| F[Commit with Structured Message - Tip 10]
    F --> G[Mark Spec Checkbox [x] & Update WORK_BOARD.md]
    G --> H[Exit Code 0: SUCCESS]
    E -->|Failure - Attempt 1| I[Analyze Error & Retry Fix]
    I --> D
    E -->|Failure - Attempt 2| J[git reset --hard HEAD - Tip 18]
    J --> K[Log Error to docs/BLOCKED.md - Tip 16]
    K --> L[Exit Code 2: BLOCKED - Tip 19]
```

---

## 2. Core Execution Disciplines
1. **Recover With Git Reset (*Tip 18*):**
   * If tests fail after 2 attempts, execute `git reset --hard HEAD`.
2. **Exit Codes for Every Ending (*Tip 19*):**
   * **`0` (`SUCCESS`)**: Spec item implemented, verified, and committed.
   * **`1` (`RETRY_NEEDED`)**: Non-critical verification failure.
   * **`2` (`BLOCKED`)**: Handbrake pulled; logged to `docs/BLOCKED.md`.
3. **Log Every Iteration (*Tip 20, 24*):**
   * Append execution entry to `ralph.log` with timestamp, spec item, test command, exit code, and commit hash.
