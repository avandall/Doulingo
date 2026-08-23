"""
Offline Dictionary Service for Duolingo Speak
Provides ultra-fast (0-2ms) local offline word translation and IPA lookup.

Storage Architecture:
- Primary SQLite Dictionary: `data/dictionary.db` (Table: `dictionary`)
- Optional JSON Dictionary: `data/dictionary.json`
- In-memory cache: `RAM_DICT_CACHE`
"""

import json
import logging
import os
import sqlite3
from typing import Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_DIR = os.path.join(PROJECT_ROOT, "data")
DICTIONARY_DB_PATH = os.path.join(DB_DIR, "dictionary.db")
DICTIONARY_JSON_PATH = os.path.join(DB_DIR, "dictionary.json")

# In-memory RAM cache for instant repeated lookups
RAM_DICT_CACHE: dict[str, dict[str, Any]] = {}


def get_dictionary_db_connection() -> sqlite3.Connection:
    """Get SQLite connection to data/dictionary.db."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DICTIONARY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_dictionary_db() -> None:
    """Ensure data/dictionary.db exists with the standard table schema."""
    conn = get_dictionary_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            word TEXT PRIMARY KEY,
            phonetic TEXT,
            pos TEXT,
            translation TEXT NOT NULL,
            definition TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_word ON dictionary(word)")
    conn.commit()
    conn.close()


class DictionaryService:
    """Unified service for offline dictionary lookups in data/dictionary.db and data/dictionary.json."""

    @classmethod
    def lookup(cls, raw_word: str) -> dict[str, Any] | None:
        """
        Lookup word in offline dictionaries:
        1. RAM Cache (0ms)
        2. SQLite DB `data/dictionary.db` (0ms)
        3. JSON file `data/dictionary.json` (if present)
        """
        if not raw_word or not raw_word.strip():
            return None

        clean_word = raw_word.strip().lower().strip(".,!?;:\"'()[]{}")
        if not clean_word:
            return None

        # 1. RAM Cache
        if clean_word in RAM_DICT_CACHE:
            return RAM_DICT_CACHE[clean_word]

        # 2. SQLite Database (data/dictionary.db)
        if os.path.exists(DICTIONARY_DB_PATH):
            try:
                conn = get_dictionary_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM dictionary WHERE lower(word) = ? LIMIT 1
                """, (clean_word,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    r_dict = dict(row)
                    res = {
                        "word": raw_word.strip(),
                        "translation": r_dict.get("translation") or r_dict.get("meaning") or r_dict.get("vietnamese", ""),
                        "phonetic": r_dict.get("phonetic") or r_dict.get("ipa") or f"/{clean_word}/",
                        "pos": r_dict.get("pos") or r_dict.get("part_of_speech") or "",
                        "definition": r_dict.get("definition") or r_dict.get("example") or ""
                    }
                    if res["translation"]:
                        RAM_DICT_CACHE[clean_word] = res
                        return res
            except Exception as e:
                logger.debug(f"[Dictionary] SQLite lookup error for '{clean_word}': {e}")

        # 3. Optional JSON Dictionary (data/dictionary.json)
        if os.path.exists(DICTIONARY_JSON_PATH):
            try:
                with open(DICTIONARY_JSON_PATH, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                    if isinstance(json_data, dict) and clean_word in json_data:
                        val = json_data[clean_word]
                        if isinstance(val, str):
                            res = {
                                "word": raw_word.strip(),
                                "translation": val,
                                "phonetic": f"/{clean_word}/",
                                "pos": "",
                                "definition": ""
                            }
                        elif isinstance(val, dict):
                            res = {
                                "word": raw_word.strip(),
                                "translation": val.get("translation") or val.get("meaning", ""),
                                "phonetic": val.get("phonetic") or val.get("ipa", f"/{clean_word}/"),
                                "pos": val.get("pos", ""),
                                "definition": val.get("definition", "")
                            }
                        else:
                            res = None

                        if res and res["translation"]:
                            RAM_DICT_CACHE[clean_word] = res
                            return res
            except Exception as e:
                logger.debug(f"[Dictionary] JSON lookup error for '{clean_word}': {e}")

        return None
