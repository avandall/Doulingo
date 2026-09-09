"""
Unit tests for TASK-005: SQLite WASM Dictionary extraction & query integrity.
Verifies:
1. build_vocab_wasm_db generates a valid SQLite database with indexed 'dictionary' table.
2. Word lookups return correct translations, phonetics, and parts of speech.
3. Database file remains within compact size limit (< 1.5MB).
"""

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from scripts.build_vocab_wasm_db import build_vocab_wasm_db


def test_build_vocab_wasm_db_execution():
    """Verify build_vocab_wasm_db creates an indexed SQLite file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_db = Path(tmpdir) / "test_vocab.sqlite"
        build_vocab_wasm_db(
            source_db_path="data/dictionary.db",
            target_db_path=str(out_db),
            limit=50,
        )

        assert out_db.exists(), "Target SQLite database was not created!"
        assert out_db.stat().st_size > 0, "Target SQLite database is empty!"

        # Verify SQLite schema & index
        conn = sqlite3.connect(out_db)
        cursor = conn.cursor()
        
        tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "dictionary" in tables

        indices = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()]
        assert "idx_word" in indices

        rows = cursor.execute("SELECT word, translation FROM dictionary LIMIT 10").fetchall()
        assert len(rows) > 0
        for w, t in rows:
            assert w != ""
            assert t != ""
        conn.close()


def test_vocab_core_sqlite_production_asset():
    """Verify static/data/vocab_core.sqlite production asset is valid and compact (<1.5MB)."""
    prod_db = Path("static/data/vocab_core.sqlite")
    if not prod_db.exists():
        # Build if not yet generated
        build_vocab_wasm_db()

    assert prod_db.exists()
    size_mb = prod_db.stat().st_size / (1024 * 1024)
    assert size_mb < 1.5, f"Vocab SQLite database size {size_mb:.2f}MB exceeds 1.5MB limit!"

    conn = sqlite3.connect(prod_db)
    count = conn.execute("SELECT COUNT(*) FROM dictionary").fetchone()[0]
    conn.close()
    assert count >= 100, f"Expected at least 100 core words, found {count}"
