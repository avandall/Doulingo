# Antigravity Workspace Rules - WSL Environment

## WSL Execution Mandatory
- This codebase and Git repository reside natively inside WSL Ubuntu (`/home/avandall/project/Doulingo`).
- **Git Operations**: ALL `git` commands (`git commit`, `git add`, `git status`, `git push`, `git diff`, etc.) MUST be executed inside WSL using `wsl <command>` (or `wsl git -C /home/avandall/project/Doulingo ...`).
- **Shell & Build Scripts**: Run all bash scripts and tests inside WSL.
- Do NOT use Windows `git.exe` on drive `Z:\` to avoid line-ending (`CRLF`/`LF`) and POSIX filemode (`chmod`) mismatches.
