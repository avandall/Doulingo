"""
SQLite / Turso Cloud Database Module for User Custom Topics & Permanent Vocabulary Dictionary Cache
Persists custom topics, dictionary translations, saved vocabulary, and user stats.
Supports Turso Cloud SQLite (libsql) via TURSO_DATABASE_URL & TURSO_AUTH_TOKEN with local SQLite fallback.
"""

import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

try:
    import libsql_experimental as libsql  # type: ignore
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "custom_topics.db")


def get_db_connection():
    """Connect to Turso Cloud SQLite if credentials present, otherwise fallback to local SQLite."""
    turso_url = os.getenv("TURSO_DATABASE_URL", "").strip()
    turso_token = os.getenv("TURSO_AUTH_TOKEN", "").strip()

    if turso_url and HAS_LIBSQL:
        try:
            conn = libsql.connect(database=turso_url, auth_token=turso_token)
            # Verify connection is functional
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return conn
        except Exception as e:
            print(f"[DB Warning] Turso Cloud connection failed: {e}. Falling back to local SQLite.")

    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_all_dicts(cursor) -> List[Dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows or not cursor.description:
        return []
    cols = [col[0] for col in cursor.description]
    results = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            results.append(dict(r))
        elif isinstance(r, dict):
            results.append(r)
        else:
            results.append(dict(zip(cols, r)))
    return results


def _fetch_one_dict(cursor) -> Optional[Dict[str, Any]]:
    row = cursor.fetchone()
    if not row or not cursor.description:
        return None
    cols = [col[0] for col in cursor.description]
    if isinstance(row, sqlite3.Row):
        return dict(row)
    if isinstance(row, dict):
        return row
    return dict(zip(cols, row))


def init_db():
    """Initialize database tables for custom scenarios, word dictionary, saved vocabulary, and user stats."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: Custom Scenarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_scenarios (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            icon TEXT,
            color TEXT,
            level TEXT,
            level_code TEXT,
            default_character TEXT,
            description TEXT,
            objective TEXT,
            suggested_vocabulary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: Permanent Word Dictionary Cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_dictionary (
            word_key TEXT PRIMARY KEY,
            word TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            target_label TEXT NOT NULL,
            translation TEXT NOT NULL,
            phonetic TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: Saved Vocabulary List
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_vocabulary (
            id TEXT PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT,
            example TEXT,
            topic_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 4: User Gamification Stats (XP & Streak Counter)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY DEFAULT 1,
            total_xp INTEGER DEFAULT 150,
            streak_days INTEGER DEFAULT 5,
            last_active_date TEXT DEFAULT (DATE('now'))
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO user_stats (id, total_xp, streak_days, last_active_date) VALUES (1, 150, 5, DATE('now'))")
    conn.commit()
    conn.close()


def add_custom_scenario(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    sc_id = scenario_data["id"]
    title = scenario_data["title"]
    category = scenario_data.get("category", "Custom Topic")
    icon = scenario_data.get("icon", "✨")
    color = scenario_data.get("color", "#1CB0F6")
    level = scenario_data.get("level", "Intermediate")
    level_code = scenario_data.get("level_code", "B1")
    default_character = scenario_data.get("default_character", "rajesh")
    description = scenario_data.get("description", "Custom user topic")
    objective = scenario_data.get("objective", "Express your thoughts freely.")
    suggested_vocab = json.dumps(scenario_data.get("suggested_vocabulary", ["Free expression", "Topic discussion"]))

    cursor.execute("""
        INSERT OR REPLACE INTO custom_scenarios 
        (id, title, category, icon, color, level, level_code, default_character, description, objective, suggested_vocabulary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sc_id, title, category, icon, color, level, level_code, default_character, description, objective, suggested_vocab))

    conn.commit()
    conn.close()
    return scenario_data


def delete_custom_scenario(sc_id: str) -> bool:
    """Delete a custom scenario from DB by ID."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM custom_scenarios WHERE id = ?", (sc_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_custom_scenarios() -> List[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_scenarios ORDER BY created_at DESC")
    rows = _fetch_all_dicts(cursor)
    conn.close()

    scenarios = []
    for r in rows:
        scenarios.append({
            "id": r["id"],
            "title": r["title"],
            "category": r["category"],
            "icon": r["icon"],
            "color": r["color"],
            "level": r["level"],
            "level_code": r["level_code"],
            "default_character": r["default_character"],
            "description": r["description"],
            "objective": r["objective"],
            "suggested_vocabulary": json.loads(r["suggested_vocabulary"]) if r.get("suggested_vocabulary") else [],
            "mode": "ielts_exam" if str(r["id"]).startswith("det_") else "roleplay",
            "is_custom": True
        })
    return scenarios


def save_translated_word(word: str, target_lang: str, target_label: str, translation: str, phonetic: str):
    """Save word translation permanently into DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    word_key = f"{word.strip().lower()}_{target_lang}"
    cursor.execute("""
        INSERT OR REPLACE INTO word_dictionary (word_key, word, target_lang, target_label, translation, phonetic)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (word_key, word.strip(), target_lang, target_label, translation, phonetic))
    conn.commit()
    conn.close()


def get_translated_word(word: str, target_lang: str) -> Optional[Dict[str, str]]:
    """Retrieve word translation permanently from DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    word_key = f"{word.strip().lower()}_{target_lang}"
    cursor.execute("SELECT * FROM word_dictionary WHERE word_key = ?", (word_key,))
    row = _fetch_one_dict(cursor)
    conn.close()
    if row:
        return {
            "word": row["word"],
            "target_lang": row["target_lang"],
            "target_label": row["target_label"],
            "translation": row["translation"],
            "phonetic": row["phonetic"]
        }
    return None


def get_all_saved_words(target_lang: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all saved vocabulary words sorted by most recent."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    if target_lang:
        cursor.execute("SELECT * FROM word_dictionary WHERE target_lang = ? ORDER BY created_at DESC", (target_lang,))
    else:
        cursor.execute("SELECT * FROM word_dictionary ORDER BY created_at DESC")
    rows = _fetch_all_dicts(cursor)
    conn.close()

    return [
        {
            "word": r["word"],
            "target_lang": r["target_lang"],
            "target_label": r["target_label"],
            "translation": r["translation"],
            "phonetic": r["phonetic"],
            "created_at": r["created_at"]
        }
        for r in rows
    ]


def get_user_stats() -> Dict[str, Any]:
    """Retrieve user XP total and Streak days from DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_xp, streak_days, last_active_date FROM user_stats WHERE id = 1")
    row = _fetch_one_dict(cursor)
    conn.close()
    if row:
        return {
            "total_xp": row["total_xp"],
            "streak": row["streak_days"],
            "last_active_date": row["last_active_date"]
        }
    return {"total_xp": 150, "streak": 5, "last_active_date": ""}


def add_user_xp(xp_amount: int) -> Dict[str, Any]:
    """Increment user total XP and update active streak."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_stats
        SET total_xp = total_xp + ?,
            streak_days = CASE
                WHEN last_active_date < DATE('now', '-1 day') THEN 1
                WHEN last_active_date = DATE('now', '-1 day') THEN streak_days + 1
                ELSE streak_days
            END,
            last_active_date = DATE('now')
        WHERE id = 1
    """, (xp_amount,))
    conn.commit()
    conn.close()
    return get_user_stats()
