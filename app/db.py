"""
SQLite Database Module for User Custom Topics & Permanent Vocabulary Dictionary Cache
Persists custom topics and dictionary translations in data/custom_topics.db
"""

import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "custom_topics.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    conn.commit()
    conn.close()

def add_custom_scenario(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
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

def get_custom_scenarios() -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_scenarios ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
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
            "suggested_vocabulary": json.loads(r["suggested_vocabulary"]) if r["suggested_vocabulary"] else [],
            "mode": "ielts_exam" if r["id"].startswith("det_") else "roleplay",
            "is_custom": True
        })
    conn.close()
    return scenarios

def save_translated_word(word: str, target_lang: str, target_label: str, translation: str, phonetic: str):
    """Save word translation permanently into SQLite DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    word_key = f"{word.strip().lower()}_{target_lang}"
    cursor.execute("""
        INSERT OR REPLACE INTO word_dictionary (word_key, word, target_lang, target_label, translation, phonetic)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (word_key, word.strip(), target_lang, target_label, translation, phonetic))
    conn.commit()
    conn.close()

def get_translated_word(word: str, target_lang: str) -> Optional[Dict[str, str]]:
    """Retrieve word translation permanently from SQLite DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    word_key = f"{word.strip().lower()}_{target_lang}"
    cursor.execute("SELECT * FROM word_dictionary WHERE word_key = ?", (word_key,))
    row = cursor.fetchone()
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if target_lang:
        cursor.execute("SELECT * FROM word_dictionary WHERE target_lang = ? ORDER BY created_at DESC", (target_lang,))
    else:
        cursor.execute("SELECT * FROM word_dictionary ORDER BY created_at DESC")
    rows = cursor.fetchall()
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
