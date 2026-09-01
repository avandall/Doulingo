#!/usr/bin/env bash
# =============================================================================
# plan.sh — Plan Sealer & Integrity Check (Harness Engineering Steps 3 & 4)
# Calculates and validates SHA-256 fingerprint over context specifications.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DOCS_DIR="$ROOT/docs"
RUNTIME_DIR="$DOCS_DIR/runtime"
CONTEXT_DIR="$DOCS_DIR/context"
SEAL_FILE="$RUNTIME_DIR/PLAN_SEAL.sha256"

mkdir -p "$RUNTIME_DIR"

compute_seal() {
  local files=()
  for f in "$CONTEXT_DIR/PROJECT_BRIEF.md" "$CONTEXT_DIR/Tasks_list.md" "$CONTEXT_DIR/BOUNDARIES.md" "$CONTEXT_DIR/TECH_CONTEXT.md"; do
    if [[ -f "$f" ]]; then
      files+=("$f")
    fi
  done
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "NO_CONTEXT_FILES"
    return
  fi
  sha256sum "${files[@]}" | sha256sum | awk '{print $1}'
}

case "${1:-seal}" in
  seal)
    SEAL_HASH="$(compute_seal)"
    echo "$SEAL_HASH" > "$SEAL_FILE"
    echo "🔒 [PLAN] Context specifications sealed with SHA-256: ${SEAL_HASH:0:16}..."
    ;;
  check)
    if [[ ! -f "$SEAL_FILE" ]]; then
      echo "⚠️ [PLAN] No seal file found at $SEAL_FILE (Unsealed Plan)."
      exit 0
    fi
    CURRENT_HASH="$(compute_seal)"
    EXPECTED_HASH="$(cat "$SEAL_FILE" | tr -d '[:space:]')"
    if [[ "$CURRENT_HASH" == "$EXPECTED_HASH" ]]; then
      echo "✅ [PLAN] Plan Seal Valid: ${CURRENT_HASH:0:16}... (No specification drift detected)"
      exit 0
    else
      echo "❌ [PLAN] SPECIFICATION DRIFT DETECTED!"
      echo "Expected: $EXPECTED_HASH"
      echo "Current:  $CURRENT_HASH"
      echo "Specifications were modified after plan seal. Re-run 'scripts/plan.sh seal' to acknowledge."
      exit 1
    fi
    ;;
  *)
    echo "Usage: scripts/plan.sh [seal|check]"
    exit 1
    ;;
esac
