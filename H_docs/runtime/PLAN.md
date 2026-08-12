# Implementation Plan — TASK-003: Admin CLI & Content Validation Tool

## Goal
Build `scripts/admin_content_cli.py` to validate and import new IELTS book YAML template files into the Turso/SQLite database to prevent schema drift, missing metadata, invalid band levels, and answer formatting issues.

## Acceptance Criteria
- [x] CLI supports `validate <file_path>` command to check required fields (`content_unit`, `band_tiers`, `sample_dialogues`).
- [x] CLI emits warnings/errors for short/long answers (<5 or >300 words) and missing `function_tag`.
- [x] CLI supports `import <file_path>` command to insert validated content into the SQLite/Turso database (supports `--sqlite` and `--dry-run`).
- [x] Comprehensive unit tests created in `tests/test_admin_content_cli.py`.
- [x] `python3 H_docs/scripts/verify.py` passes 100%.

## Proposed Steps

### Step 1: Implement `scripts/admin_content_cli.py` [x] DONE
- Build CLI tool with `validate` and `import` subcommands using `argparse`.
- Implement validation logic to inspect `content_unit`, `band_tiers`, and `sample_dialogues`, checking required fields, band ranges, answer length, and `function_tag`.
- Implement DB import logic for valid YAML files supporting `--sqlite` DB path and `--dry-run` mode.

### Step 2: Implement Unit Tests & Run Verification [x] DONE
- Create `tests/test_admin_content_cli.py` testing `validate` (valid YAML, invalid YAML, warnings) and `import` commands.
- Execute `python3 H_docs/scripts/verify.py` to ensure Tier 1 quality checks pass.

## Status
- **Current Phase:** COMPLETED (Phase 6 & 7 Done)
- **Iteration:** 31
- **Git Commit:** `898e20c` `[TASK-003] feat(admin-cli): implement content validation and DB import tool`
