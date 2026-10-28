"""Automated Mutation Testing Engine for Pipeline Invariants.

Applies AST and semantic mutation operators to:
1. pipeline/src/ingestion/validator.py (Payload & boundary invariants)
2. pipeline/src/gamification/streak_engine.py (Exactly-once & monotonic streak invariants)
3. pipeline/src/resilience/circuit_breaker.py (Non-sticky self-healing invariants)

Calculates the official Mutation Score:
    Mutation Score = (Killed Mutants / Total Mutants) * 100%
Enforces the QA Acceptance Gate: >= 85%.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass
class MutationCandidate:
    target_file: str
    description: str
    original_snippet: str
    mutated_snippet: str


MUTATION_SUITE: list[MutationCandidate] = [
    # --- Ingestion & Validator Mutants ---
    MutationCandidate(
        target_file="pipeline/src/ingestion/validator.py",
        description="Mutant 1: Invert payload size limit check (allows oversized audio)",
        original_snippet="if len(audio_bytes) > cls.MAX_BYTES:",
        mutated_snippet="if len(audio_bytes) < cls.MAX_BYTES:",
    ),
    MutationCandidate(
        target_file="pipeline/src/ingestion/validator.py",
        description="Mutant 2: Alter maximum duration boundary from 30.0s to 300.0s",
        original_snippet="MAX_DURATION_SECONDS: float = 30.0",
        mutated_snippet="MAX_DURATION_SECONDS: float = 300.0",
    ),
    MutationCandidate(
        target_file="pipeline/src/ingestion/validator.py",
        description="Mutant 3: Nullify audio format magic byte inspection",
        original_snippet='if audio_bytes.startswith(cls.OGG_MAGIC):',
        mutated_snippet='if False and audio_bytes.startswith(cls.OGG_MAGIC):',
    ),
    # --- Gamification & Streak Invariant Mutants ---
    MutationCandidate(
        target_file="pipeline/src/gamification/streak_engine.py",
        description="Mutant 4: Bypass Invariant 1 (allow duplicate streak increment on same day)",
        original_snippet="if activity_key in self._daily_activities:",
        mutated_snippet="if False and activity_key in self._daily_activities:",
    ),
    MutationCandidate(
        target_file="pipeline/src/gamification/streak_engine.py",
        description="Mutant 5: Invert consecutive day check (day_diff == 1 -> day_diff != 1)",
        original_snippet="if day_diff == 1:",
        mutated_snippet="if day_diff != 1:",
    ),
    MutationCandidate(
        target_file="pipeline/src/gamification/streak_engine.py",
        description="Mutant 6: Disable streak freeze consumption when skipping a day",
        original_snippet="user.freeze_count -= 1",
        mutated_snippet="pass # user.freeze_count -= 1",
    ),
    MutationCandidate(
        target_file="pipeline/src/gamification/streak_engine.py",
        description="Mutant 7: Corrupt streak increment arithmetic (+1 to +0)",
        original_snippet="user.current_streak += 1",
        mutated_snippet="user.current_streak += 0",
    ),
    # --- Resilience & Circuit Breaker Mutants ---
    MutationCandidate(
        target_file="pipeline/src/resilience/circuit_breaker.py",
        description="Mutant 8: Invert circuit breaker failure threshold (never trips to OPEN)",
        original_snippet="if failure_rate >= self.failure_rate_threshold:",
        mutated_snippet="if failure_rate < self.failure_rate_threshold:",
    ),
    MutationCandidate(
        target_file="pipeline/src/resilience/circuit_breaker.py",
        description="Mutant 9: Prevent self-healing reset from HALF_OPEN back to CLOSED",
        original_snippet="self._state = CircuitState.CLOSED",
        mutated_snippet="self._state = CircuitState.OPEN",
    ),
    MutationCandidate(
        target_file="pipeline/src/resilience/circuit_breaker.py",
        description="Mutant 10: Invert can_execute logic for CLOSED circuit state",
        original_snippet="if current_state == CircuitState.CLOSED:\n            return True",
        mutated_snippet="if current_state == CircuitState.CLOSED:\n            return False",
    ),
]


def run_tests() -> bool:
    """Runs the invariant test suite. Returns True if all tests pass, False if any fail."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--tb=no",
        "pipeline/tests/test_mutation_invariants.py",
        "pipeline/tests/test_ingestion.py",
        "pipeline/tests/test_gamification.py",
        "pipeline/tests/test_resilience.py",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def execute_mutation_testing() -> int:
    """Executes all mutation candidates, logs survival/death, and asserts quality gate."""
    print("=" * 80)
    print("🔬 QA ENGINEER — EXECUTING MUTATION TESTING SUITE (VITAL INVARIANTS)")
    print("=" * 80)

    # 1. Baseline verification: Original code MUST pass all tests
    print("\n[Step 0] Running baseline tests on original clean code...")
    if not run_tests():
        print("❌ FATAL: Clean codebase failed tests before mutation! Aborting.")
        return 1
    print("✅ Baseline verified: Clean code passes 100% of test cases.")

    killed_mutants = 0
    survived_mutants = 0
    total_mutants = len(MUTATION_SUITE)

    print(f"\n[Step 1] Seeding {total_mutants} critical AST / Semantic Mutations...")

    for idx, mutant in enumerate(MUTATION_SUITE, start=1):
        file_path = mutant.target_file
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: Target file {file_path} not found. Skipping.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            original_code = f.read()

        if mutant.original_snippet not in original_code:
            print(f"⚠️ Warning: Snippet for Mutant {idx} not found in {file_path}. Skipping.")
            continue

        # Inject mutation
        mutated_code = original_code.replace(mutant.original_snippet, mutant.mutated_snippet, 1)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(mutated_code)

            # Run test suite against mutated code
            tests_passed = run_tests()

            if not tests_passed:
                # Tests failed -> Mutant was successfully detected and KILLED!
                killed_mutants += 1
                status = "💥 KILLED (Caught by test suite)"
            else:
                # Tests passed -> Mutant SURVIVED!
                survived_mutants += 1
                status = "⚠️ SURVIVED (Weak test coverage)"

            print(f"  [{idx:02d}/{total_mutants:02d}] {mutant.description} -> {status}")

        finally:
            # Revert mutation cleanly
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(original_code)

    # Calculate Mutation Score
    mutation_score = (killed_mutants / total_mutants) * 100.0

    print("\n" + "=" * 80)
    print("📊 MUTATION TESTING RESULTS & QUALITY GATE REPORT")
    print("=" * 80)
    print(f"Total Mutants Evaluated: {total_mutants}")
    print(f"Mutants Killed:          {killed_mutants}")
    print(f"Mutants Survived:        {survived_mutants}")
    print(f"Mutation Score:          {mutation_score:.2f}%")
    print(f"Required QA Gate:        >= 85.00%")

    if mutation_score >= 85.0:
        print("\n🎉 QUALITY GATE PASSED: The test suite exhibits high mutation resilience.")
        print("   All vital invariants are strictly guarded against regressions.")
        return 0
    else:
        print("\n❌ QUALITY GATE FAILED: Mutation Score is below 85%. Test suite needs refinement.")
        return 1


if __name__ == "__main__":
    sys.exit(execute_mutation_testing())
