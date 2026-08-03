#!/usr/bin/env bash
# ==============================================================================
# 🦉 Duolingo Speak Clone - Ralph Loop Autonomous Engineering Script
# Inspired by "Harness Engineering: 29 Tips to Build the Systems That Build Software"
# (https://www.youtube.com/watch?v=rraHPF4ZgCw)
#
# Core Principles:
#   1. One Item, One Fresh Chat (Tip 15): Each iteration starts a fresh sub-process
#   2. Don't Describe Code, Point To It (Tip 4 & 5): Agent reads architecture docs
#   3. Never Compact Your Chat (Tip 8): Zero context degradation across loops
#   4. Recover with Git Reset (Tip 18): Automated rollback if syntax verification fails
# ==============================================================================

set -u

# --- Configuration & Environment Variables ---
# You can override these variables via export before running the script:
# e.g., export AGENT_CMD="claude -p 'Read docs/prompt.md and execute it'"
AGENT_CMD="${AGENT_CMD:-aider --message-file docs/prompt.md --yes}"
MAX_ITERATIONS="${MAX_ITERATIONS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-10}"
SPECS_FILE="docs/specs.md"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="logs/ralph_loop_${TIMESTAMP}"

# --- Colors for Output ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

mkdir -p "${LOG_DIR}"

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN} 🦉 STARTING RALPH LOOP (AUTONOMOUS HARNESS ENGINEERING) - OVERNIGHT MODE 🦉 ${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "${BLUE}▶ Project         :${NC} Duolingo Speak Clone"
echo -e "${BLUE}▶ Specs Backlog   :${NC} ${SPECS_FILE}"
echo -e "${BLUE}▶ Agent Command   :${NC} ${AGENT_CMD}"
echo -e "${BLUE}▶ Max Iterations  :${NC} ${MAX_ITERATIONS}"
echo -e "${BLUE}▶ Log Directory   :${NC} ${LOG_DIR}"
echo -e "${GREEN}==============================================================================${NC}"

# Check if git repository is clean before starting
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}[WARNING] Git working directory is not clean. Creating a backup commit before starting...${NC}"
    git add -A
    git commit -m "chore(ralph): save pre-loop working directory state" || true
fi

iteration=1
while [ ${iteration} -le ${MAX_ITERATIONS} ]; do
    echo -e "\n${CYAN}------------------------------------------------------------------------------${NC}"
    echo -e "${CYAN} 🔄 ITERATION ${iteration} of ${MAX_ITERATIONS} | $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}------------------------------------------------------------------------------${NC}"

    # 1. Check if there are any remaining tasks in specs.md
    if ! grep -q -- "- \[ \]" "${SPECS_FILE}"; then
        echo -e "${GREEN}🎉 ALL TASKS IN '${SPECS_FILE}' HAVE BEEN COMPLETED! (${NC}No remaining '- [ ]' checkboxes${GREEN})${NC}"
        echo -e "${GREEN}✨ Ralph Loop overnight run finished successfully with 100% completion! ✨${NC}"
        exit 0
    fi

    # Count remaining tasks
    REMAINING_TASKS=$(grep -c -- "- \[ \]" "${SPECS_FILE}")
    echo -e "${YELLOW}📌 Remaining tasks in backlog: ${REMAINING_TASKS}${NC}"

    # 2. Record the last known good git commit (Tip 18: Git Reset recovery point)
    LAST_GOOD_COMMIT=$(git rev-parse HEAD)
    LOG_FILE="${LOG_DIR}/iteration_${iteration}.log"

    echo -e "${BLUE}🚀 Launching Fresh Agent Session ('One Item, One Fresh Chat')...${NC}"
    echo -e "${BLUE}📝 Logging execution to: ${LOG_FILE}${NC}"

    # 3. Execute the AI CLI Agent and log output
    set +e
    eval "${AGENT_CMD}" 2>&1 | tee "${LOG_FILE}"
    AGENT_EXIT_CODE=${PIPESTATUS[0]}
    set -e

    # 4. Verification & Guard Check
    echo -e "${BLUE}🔍 Running Post-Iteration Verification Guard...${NC}"
    SYNTAX_OK=true

    if ! python3 -m py_compile main.py app/*.py 2>>"${LOG_FILE}"; then
        SYNTAX_OK=false
    fi

    # 5. Evaluate Result & Recover if Needed (Tip 18)
    if [ ${SYNTAX_OK} = true ] && [ ${AGENT_EXIT_CODE} -eq 0 ]; then
        echo -e "${GREEN}✔ Iteration ${iteration} verified successfully! Python syntax is valid.${NC}"
        
        # Check if agent created a commit
        CURRENT_COMMIT=$(git rev-parse HEAD)
        if [ "${CURRENT_COMMIT}" != "${LAST_GOOD_COMMIT}" ]; then
            echo -e "${GREEN}✔ New Git commit detected: $(git log -1 --oneline)${NC}"
        else
            echo -e "${YELLOW}ℹ No new Git commit created in this iteration. Check log if task was updated.${NC}"
        fi
    else
        echo -e "${RED}✖ ITERATION ${iteration} FAILED VERIFICATION OR SYNTAX CHECK!${NC}"
        echo -e "${RED}💥 Reverting to last known good commit (${LAST_GOOD_COMMIT:0:7}) via 'git reset --hard'... (Tip 18)${NC}"
        git reset --hard "${LAST_GOOD_COMMIT}" >> "${LOG_FILE}" 2>&1
        git clean -fd >> "${LOG_FILE}" 2>&1
        echo -e "${YELLOW}⚠ Repository restored to stable state. Continuing to next iteration...${NC}"
    fi

    # 6. Throttle / Sleep before next iteration (to prevent API rate limits overnight)
    echo -e "${BLUE}💤 Sleeping ${SLEEP_SECONDS} seconds before next iteration...${NC}"
    sleep "${SLEEP_SECONDS}"
    
    iteration=$((iteration + 1))
done

echo -e "\n${YELLOW}==============================================================================${NC}"
echo -e "${YELLOW} 🛑 REACHED MAX ITERATIONS (${MAX_ITERATIONS}). STOPPING RALPH LOOP. 🛑 ${NC}"
echo -e "${YELLOW}==============================================================================${NC}"
echo -e "Check remaining tasks in ${SPECS_FILE} and logs in ${LOG_DIR}."
exit 1
