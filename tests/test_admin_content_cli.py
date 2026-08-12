"""
tests/test_admin_content_cli.py
================================
Unit tests for scripts/admin_content_cli.py (Admin CLI & Content Validation Tool)
"""

import argparse
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.admin_content_cli import (
    cmd_import,
    cmd_validate,
    import_docs_to_db,
    validate_file,
)


@pytest.fixture
def valid_yaml_file(tmp_path: Path) -> Path:
    data = {
        "content_unit": {
            "template_type": "band_ladder",
            "title": "Topic 1: Hobbies and Leisure",
            "topic_tags": ["hobbies", "leisure"],
            "target_band_min": 5.0,
            "target_band_max": 8.0,
            "register": "neutral",
            "source_citation": "IELTS Book 1",
        },
        "band_tiers": [
            {
                "band_min": 5.0,
                "band_max": 6.5,
                "can_do_description": "Can speak about simple hobbies",
                "grammar_required": ["Present Simple"],
                "vocabulary_core": ["reading", "sports"],
                "sentence_length_target": "10-15 words",
            }
        ],
        "sample_dialogues": [
            {
                "band_level": 6.0,
                "turn_type": "standalone",
                "function_tag": "expressing_preference",
                "ai_line": "What do you like to do in your free time?",
                "user_model_answer": "I really enjoy playing football with my close friends every weekend because it keeps me fit.",
            }
        ],
    }
    file_path = tmp_path / "valid_sample.yaml"
    file_path.write_text(yaml.dump(data), encoding="utf-8")
    return file_path


@pytest.fixture
def invalid_yaml_file(tmp_path: Path) -> Path:
    data = {
        "content_unit": {
            "template_type": "invalid_template",
            "title": "Invalid Topic",
            "topic_tags": [],
            "target_band_min": 9.0,
            "target_band_max": 5.0,
            "register": "invalid_register",
            "source_citation": "Unknown",
        },
        "band_tiers": [],
        "sample_dialogues": [],
    }
    file_path = tmp_path / "invalid_sample.yaml"
    file_path.write_text(yaml.dump(data), encoding="utf-8")
    return file_path


@pytest.fixture
def warning_yaml_file(tmp_path: Path) -> Path:
    data = {
        "content_unit": {
            "template_type": "band_ladder",
            "title": "Warning Topic",
            "topic_tags": ["topic"],
            "target_band_min": 5.0,
            "target_band_max": 7.0,
            "register": "casual",
            "source_citation": "Ref",
        },
        "band_tiers": [
            {
                "band_min": 5.0,
                "band_max": 7.0,
                "can_do_description": "Can discuss topic",
                "grammar_required": ["Grammar"],
                "vocabulary_core": ["Word"],
                "sentence_length_target": "Short",
            }
        ],
        "sample_dialogues": [
            {
                "band_level": 6.0,
                "turn_type": "standalone",
                # missing function_tag -> causes warning
                "ai_line": "Short question?",
                "user_model_answer": "Yes okay.",  # short answer (< 5 words) -> causes warning
            }
        ],
    }
    file_path = tmp_path / "warning_sample.yaml"
    file_path.write_text(yaml.dump(data), encoding="utf-8")
    return file_path


def test_validate_file_valid(valid_yaml_file: Path) -> None:
    passed, failed, issues = validate_file(valid_yaml_file)
    assert passed == 1
    assert failed == 0
    assert len([i for i in issues if not i["is_warning"]]) == 0


def test_validate_file_invalid(invalid_yaml_file: Path) -> None:
    passed, failed, issues = validate_file(invalid_yaml_file)
    assert failed >= 1
    errors = [i for i in issues if not i["is_warning"]]
    assert len(errors) > 0


def test_validate_file_warnings(warning_yaml_file: Path) -> None:
    passed, failed, issues = validate_file(warning_yaml_file)
    assert passed == 1
    assert failed == 0
    warnings = [i for i in issues if i["is_warning"]]
    assert len(warnings) >= 2


def test_cmd_validate(valid_yaml_file: Path, invalid_yaml_file: Path) -> None:
    args_valid = argparse.Namespace(input=valid_yaml_file, quiet=True)
    assert cmd_validate(args_valid) == 0

    args_invalid = argparse.Namespace(input=invalid_yaml_file, quiet=True)
    assert cmd_validate(args_invalid) == 1


def test_import_dry_run(valid_yaml_file: Path) -> None:
    cu, tiers, sds = import_docs_to_db([valid_yaml_file], db_path=None, dry_run=True)
    assert cu == 1
    assert tiers == 1
    assert sds == 1


def test_import_sqlite(valid_yaml_file: Path, tmp_path: Path) -> None:
    db_file = tmp_path / "test_import.db"
    cu, tiers, sds = import_docs_to_db(
        [valid_yaml_file], db_path=str(db_file), dry_run=False
    )

    assert cu == 1
    assert tiers == 1
    assert sds == 1

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM content_units")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM band_tiers")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM sample_dialogues")
    assert cur.fetchone()[0] == 1

    conn.close()


def test_cmd_import(valid_yaml_file: Path, invalid_yaml_file: Path, tmp_path: Path) -> None:
    db_file = tmp_path / "cmd_test.db"

    args_valid = argparse.Namespace(
        input=valid_yaml_file, sqlite=str(db_file), dry_run=False, force=False
    )
    assert cmd_import(args_valid) == 0

    args_invalid_no_force = argparse.Namespace(
        input=invalid_yaml_file, sqlite=str(db_file), dry_run=False, force=False
    )
    assert cmd_import(args_invalid_no_force) == 1
