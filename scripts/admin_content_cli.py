"""
admin_content_cli.py
====================
Admin CLI & Content Validation Tool for IELTS content YAML templates.

Usage:
    # Validate a single file or directory
    python scripts/admin_content_cli.py validate output/extracted/

    # Import validated YAML files into SQLite database
    python scripts/admin_content_cli.py import output/extracted/ --sqlite data/custom_topics.db

    # Dry-run import
    python scripts/admin_content_cli.py import output/extracted/ --dry-run
"""

import argparse
import json
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

VALID_TEMPLATE_TYPES = {"band_ladder", "functional_bank", "scenario"}
VALID_REGISTERS = {"casual", "neutral", "formal"}
VALID_TURN_TYPES = {"standalone", "opening", "elaborate", "negotiation", "closing"}
BAND_MIN, BAND_MAX = 1.0, 9.0
MIN_ANSWER_WORDS = 5
MAX_ANSWER_WORDS = 300

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS content_units (
    id              TEXT PRIMARY KEY,
    template_type   TEXT NOT NULL CHECK(template_type IN ('band_ladder','functional_bank','scenario')),
    title           TEXT NOT NULL,
    topic_tags      TEXT NOT NULL DEFAULT '[]',
    target_band_min REAL,
    target_band_max REAL,
    register        TEXT,
    source_citation TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    version         INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS band_tiers (
    id                    TEXT PRIMARY KEY,
    content_unit_id       TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
    band_min              REAL NOT NULL,
    band_max              REAL NOT NULL,
    can_do_description    TEXT,
    grammar_required      TEXT DEFAULT '[]',
    vocabulary_core       TEXT DEFAULT '[]',
    vocabulary_stretch    TEXT DEFAULT '[]',
    vocabulary_avoid      TEXT DEFAULT '[]',
    sentence_length_target TEXT,
    common_errors_to_simulate TEXT
);
CREATE INDEX IF NOT EXISTS idx_band_tiers_range ON band_tiers (band_min, band_max);

CREATE TABLE IF NOT EXISTS sample_dialogues (
    id              TEXT PRIMARY KEY,
    content_unit_id TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
    band_level      REAL NOT NULL,
    turn_type       TEXT,
    function_tag    TEXT,
    ai_line         TEXT NOT NULL,
    user_model_answer TEXT NOT NULL,
    embedding       BLOB,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sd_band ON sample_dialogues (band_level);
CREATE INDEX IF NOT EXISTS idx_sd_cu   ON sample_dialogues (content_unit_id);
"""


def err(path: str, msg: str, is_warning: bool = False) -> dict[str, Any]:
    return {"file": path, "error": msg, "is_warning": is_warning}


def check_band(val: Any, field: str) -> str | None:
    if not isinstance(val, (int, float)):
        return f"{field} phải là số, nhận được: {type(val).__name__}"
    if not (BAND_MIN <= float(val) <= BAND_MAX):
        return f"{field}={val} ngoài khoảng [{BAND_MIN}, {BAND_MAX}]"
    if round(float(val) * 2) != float(val) * 2:
        return f"{field}={val} không phải bội của 0.5"
    return None


def word_count(text: Any) -> int:
    return len(str(text).split())


def validate_doc(doc: dict[str, Any], filepath: str) -> list[dict[str, Any]]:
    issues = []

    cu = doc.get("content_unit")
    if not cu:
        issues.append(err(filepath, "Thiếu khối `content_unit`"))
        return issues

    for f in (
        "template_type",
        "title",
        "topic_tags",
        "target_band_min",
        "target_band_max",
        "register",
        "source_citation",
    ):
        if f not in cu:
            issues.append(err(filepath, f"content_unit: thiếu field `{f}`"))

    if cu.get("template_type") not in VALID_TEMPLATE_TYPES:
        issues.append(
            err(
                filepath,
                f"content_unit.template_type không hợp lệ: {cu.get('template_type')!r}",
            )
        )

    if cu.get("register") not in VALID_REGISTERS:
        issues.append(
            err(filepath, f"content_unit.register không hợp lệ: {cu.get('register')!r}")
        )

    for f in ("target_band_min", "target_band_max"):
        if f in cu:
            e = check_band(cu[f], f"content_unit.{f}")
            if e:
                issues.append(err(filepath, e))

    if (
        "target_band_min" in cu
        and "target_band_max" in cu
        and isinstance(cu["target_band_min"], (int, float))
        and isinstance(cu["target_band_max"], (int, float))
        and cu["target_band_min"] >= cu["target_band_max"]
    ):
        issues.append(err(filepath, "target_band_min >= target_band_max"))

    tags = cu.get("topic_tags", [])
    if not isinstance(tags, list) or len(tags) == 0:
        issues.append(err(filepath, "content_unit.topic_tags phải là list không rỗng"))

    tiers = doc.get("band_tiers", [])
    if not isinstance(tiers, list) or len(tiers) == 0:
        issues.append(err(filepath, "Thiếu hoặc rỗng `band_tiers`"))
    else:
        for i, t in enumerate(tiers):
            prefix = f"band_tiers[{i}]"
            for f in (
                "band_min",
                "band_max",
                "can_do_description",
                "grammar_required",
                "vocabulary_core",
                "sentence_length_target",
            ):
                if f not in t:
                    issues.append(err(filepath, f"{prefix}: thiếu field `{f}`"))
            for f in ("band_min", "band_max"):
                if f in t:
                    e = check_band(t[f], f"{prefix}.{f}")
                    if e:
                        issues.append(err(filepath, e))
            for f in ("grammar_required", "vocabulary_core"):
                if not isinstance(t.get(f), list):
                    issues.append(err(filepath, f"{prefix}.{f} phải là list"))

    sds = doc.get("sample_dialogues", [])
    if not isinstance(sds, list) or len(sds) == 0:
        issues.append(err(filepath, "Thiếu hoặc rỗng `sample_dialogues`"))
    else:
        for i, sd in enumerate(sds):
            prefix = f"sample_dialogues[{i}]"
            for f in ("band_level", "turn_type", "ai_line", "user_model_answer"):
                if f not in sd:
                    issues.append(err(filepath, f"{prefix}: thiếu field `{f}`"))

            if "band_level" in sd:
                e = check_band(sd["band_level"], f"{prefix}.band_level")
                if e:
                    issues.append(err(filepath, e))

            if sd.get("turn_type") not in VALID_TURN_TYPES:
                issues.append(
                    err(
                        filepath,
                        f"{prefix}.turn_type không hợp lệ: {sd.get('turn_type')!r}",
                    )
                )

            # Warning/Error for missing function_tag
            func_tag = sd.get("function_tag")
            if not func_tag:
                issues.append(
                    err(
                        filepath,
                        f"{prefix}: thiếu `function_tag`",
                        is_warning=True,
                    )
                )

            answer = str(sd.get("user_model_answer", "")).strip()
            wc = word_count(answer)
            if wc < MIN_ANSWER_WORDS:
                issues.append(
                    err(
                        filepath,
                        f"{prefix}.user_model_answer quá ngắn ({wc} từ): {answer!r}",
                        is_warning=True,
                    )
                )
            if wc > MAX_ANSWER_WORDS:
                issues.append(
                    err(filepath, f"{prefix}.user_model_answer quá dài ({wc} từ)")
                )

            for sig in [" (n)=", " (v)=", " (adj)=", "(n): "]:
                if sig in answer:
                    issues.append(
                        err(filepath, f"{prefix}: còn nhiễu vocab-column ({sig!r})")
                    )
                    break

    return issues


def validate_file(path: Path) -> tuple[int, int, list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8")
    try:
        docs = [d for d in yaml.safe_load_all(text) if d is not None]
    except yaml.YAMLError as e:
        return 0, 1, [err(str(path), f"YAML parse error: {e}")]

    if not docs:
        return 0, 1, [err(str(path), "File YAML rỗng")]

    passed = failed = 0
    all_issues = []
    for i, doc in enumerate(docs):
        if isinstance(doc, str) and doc.strip() == "SKIP":
            continue
        if not isinstance(doc, dict):
            failed += 1
            all_issues.append(
                err(
                    f"{path.name}[doc {i}]",
                    f"Unsupported YAML document type: {type(doc).__name__}",
                )
            )
            continue
        doc_issues = validate_doc(doc, f"{path.name}[doc {i}]")
        has_errors = any(not item["is_warning"] for item in doc_issues)
        if has_errors:
            failed += 1
        else:
            passed += 1
        all_issues.extend(doc_issues)
    return passed, failed, all_issues


def get_yaml_files(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(input_path.glob("*.yaml")) + sorted(input_path.glob("*.yml"))
    return [input_path] if input_path.exists() else []


def cmd_validate(args: argparse.Namespace) -> int:
    files = get_yaml_files(args.input)
    if not files:
        print(f"Error: Không tìm thấy file YAML tại {args.input}")
        return 1

    total_pass = total_fail = 0
    all_issues = []
    for f in files:
        p, fail, issues = validate_file(f)
        total_pass += p
        total_fail += fail
        all_issues.extend(issues)

    if not args.quiet:
        for issue in all_issues:
            icon = "⚠️" if issue["is_warning"] else "❌"
            print(f"  {icon} [{issue['file']}] {issue['error']}")

    errors_count = sum(1 for item in all_issues if not item["is_warning"])
    warnings_count = sum(1 for item in all_issues if item["is_warning"])

    print(f"\n{'=' * 60}")
    print(
        f"Validation Result: {total_pass} PASS | {total_fail} FAIL | "
        f"{errors_count} Errors | {warnings_count} Warnings"
    )
    print("=" * 60)
    return 0 if errors_count == 0 else 1


def import_docs_to_db(
    files: list[Path], db_path: str | None, dry_run: bool
) -> tuple[int, int, int]:
    total_cu = 0
    total_tiers = 0
    total_sds = 0

    if dry_run:
        for f in files:
            text = f.read_text(encoding="utf-8")
            docs = [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]
            for doc in docs:
                total_cu += 1
                total_tiers += len(doc.get("band_tiers", []))
                total_sds += len(doc.get("sample_dialogues", []))
        return total_cu, total_tiers, total_sds

    if not db_path:
        db_path = "data/custom_topics.db"

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)

    cursor = conn.cursor()

    for f in files:
        text = f.read_text(encoding="utf-8")
        docs = [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]
        for doc in docs:
            cu = doc.get("content_unit", {})
            cu_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO content_units (
                    id, template_type, title, topic_tags, target_band_min,
                    target_band_max, register, source_citation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cu_id,
                    cu.get("template_type"),
                    cu.get("title"),
                    json.dumps(cu.get("topic_tags", [])),
                    cu.get("target_band_min"),
                    cu.get("target_band_max"),
                    cu.get("register"),
                    cu.get("source_citation"),
                ),
            )
            total_cu += 1

            for tier in doc.get("band_tiers", []):
                tier_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO band_tiers (
                        id, content_unit_id, band_min, band_max, can_do_description,
                        grammar_required, vocabulary_core, vocabulary_stretch,
                        vocabulary_avoid, sentence_length_target, common_errors_to_simulate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tier_id,
                        cu_id,
                        tier.get("band_min"),
                        tier.get("band_max"),
                        tier.get("can_do_description"),
                        json.dumps(tier.get("grammar_required", [])),
                        json.dumps(tier.get("vocabulary_core", [])),
                        json.dumps(tier.get("vocabulary_stretch", [])),
                        json.dumps(tier.get("vocabulary_avoid", [])),
                        tier.get("sentence_length_target"),
                        tier.get("common_errors_to_simulate"),
                    ),
                )
                total_tiers += 1

            for sd in doc.get("sample_dialogues", []):
                sd_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO sample_dialogues (
                        id, content_unit_id, band_level, turn_type, function_tag,
                        ai_line, user_model_answer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sd_id,
                        cu_id,
                        sd.get("band_level"),
                        sd.get("turn_type"),
                        sd.get("function_tag"),
                        sd.get("ai_line"),
                        sd.get("user_model_answer"),
                    ),
                )
                total_sds += 1

    conn.commit()
    conn.close()
    return total_cu, total_tiers, total_sds


def cmd_import(args: argparse.Namespace) -> int:
    files = get_yaml_files(args.input)
    if not files:
        print(f"Error: Không tìm thấy file YAML tại {args.input}")
        return 1

    if not args.force:
        print("Checking validation before import...")
        all_issues = []
        for f in files:
            _, _, issues = validate_file(f)
            all_issues.extend(issues)
        errors = [i for i in all_issues if not i["is_warning"]]
        if errors:
            print(
                f"❌ Import aborted due to {len(errors)} validation errors. Use --force to override."
            )
            return 1

    mode_str = "(DRY-RUN)" if args.dry_run else f"into DB: {args.sqlite or 'data/custom_topics.db'}"
    print(f"Importing {len(files)} files {mode_str}...")

    cu_count, tier_count, sd_count = import_docs_to_db(
        files, db_path=args.sqlite, dry_run=args.dry_run
    )
    print(f"\nImport Completed Successfully {mode_str}:")
    print(f"  - Content Units:   {cu_count}")
    print(f"  - Band Tiers:      {tier_count}")
    print(f"  - Sample Dialogues: {sd_count}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Admin CLI & Content Validation Tool for IELTS content"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate subcommand
    val_parser = subparsers.add_parser(
        "validate", help="Validate YAML content template files"
    )
    val_parser.add_argument(
        "input", type=Path, help="File or directory containing YAML templates"
    )
    val_parser.add_argument(
        "--quiet", action="store_true", help="Suppress detailed error list output"
    )

    # import subcommand
    imp_parser = subparsers.add_parser(
        "import", help="Import validated YAML content templates into Database"
    )
    imp_parser.add_argument(
        "input", type=Path, help="File or directory containing YAML templates"
    )
    imp_parser.add_argument(
        "--sqlite", type=str, default=None, help="Path to local SQLite DB file"
    )
    imp_parser.add_argument(
        "--dry-run", action="store_true", help="Parse files without modifying database"
    )
    imp_parser.add_argument(
        "--force", action="store_true", help="Import even if validation errors exist"
    )

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(cmd_validate(args))
    elif args.command == "import":
        sys.exit(cmd_import(args))


if __name__ == "__main__":
    main()
