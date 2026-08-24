"""
SQLite / Turso Cloud Database Module for User Custom Topics & Permanent Vocabulary Dictionary Cache
Persists custom topics, dictionary translations, saved vocabulary, and user stats.
Supports Turso Cloud SQLite (libsql) via TURSO_DATABASE_URL & TURSO_AUTH_TOKEN with local SQLite fallback.
"""

import json
import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger("duolingo_speak.db")

try:
    import libsql_experimental as libsql  # type: ignore
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_DIR = os.path.join(PROJECT_ROOT, "data")
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
            cursor.execute("PRAGMA foreign_keys = ON;")
            return conn
        except Exception as e:
            logger.warning(f"[DB Warning] Turso Cloud connection failed: {e}. Falling back to local SQLite.")

    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _fetch_all_dicts(cursor) -> list[dict[str, Any]]:
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


def _fetch_one_dict(cursor) -> dict[str, Any] | None:
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
    """Initialize database tables for custom scenarios, word dictionary, saved vocabulary, user stats, and 12 schema tables."""
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

    # Cleanup any corrupt placeholder translations from past failed requests or untranslated original words
    cursor.execute("""
        DELETE FROM word_dictionary 
        WHERE translation LIKE 'Definition of %' 
           OR translation LIKE 'definition of %'
           OR LOWER(TRIM(translation)) = LOWER(TRIM(word))
    """)
    cursor.execute("DROP TABLE IF EXISTS core_dictionary")

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

    # ── 12 Turso/libSQL Schema Tables (TASK-000) ───────────────────────────

    # 1. content_units
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_units (
            id              TEXT PRIMARY KEY,
            template_type   TEXT NOT NULL CHECK(template_type IN
                                ('band_ladder','functional_bank','scenario')),
            title           TEXT NOT NULL,
            topic_tags      TEXT NOT NULL DEFAULT '[]',
            target_band_min REAL,
            target_band_max REAL,
            register        TEXT CHECK(register IN ('casual','neutral','formal')),
            source_citation TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            version         INTEGER DEFAULT 1
        )
    """)

    # 2. band_tiers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS band_tiers (
            id                      TEXT PRIMARY KEY,
            content_unit_id         TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
            band_min                REAL NOT NULL,
            band_max                REAL NOT NULL,
            can_do_description      TEXT,
            grammar_required        TEXT DEFAULT '[]',
            vocabulary_core         TEXT DEFAULT '[]',
            vocabulary_stretch      TEXT DEFAULT '[]',
            vocabulary_avoid        TEXT DEFAULT '[]',
            sentence_length_target  TEXT,
            common_errors_to_simulate TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_band_tiers_range ON band_tiers (band_min, band_max)")

    # 3. function_details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS function_details (
            id               TEXT PRIMARY KEY,
            content_unit_id  TEXT UNIQUE REFERENCES content_units(id) ON DELETE CASCADE,
            function_name    TEXT NOT NULL,
            applicable_topics TEXT DEFAULT '[]'
        )
    """)

    # 4. function_band_variants
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS function_band_variants (
            id              TEXT PRIMARY KEY,
            function_id     TEXT REFERENCES function_details(id) ON DELETE CASCADE,
            band_min        REAL NOT NULL,
            band_max        REAL NOT NULL,
            phrases         TEXT DEFAULT '[]',
            grammar_pattern TEXT
        )
    """)

    # 5. scenarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id               TEXT PRIMARY KEY,
            content_unit_id  TEXT UNIQUE REFERENCES content_units(id) ON DELETE CASCADE,
            setting          TEXT,
            ai_role          TEXT,
            user_role        TEXT,
            grammar_required TEXT DEFAULT '[]',
            vocabulary_core  TEXT DEFAULT '[]',
            vocabulary_stretch TEXT DEFAULT '[]'
        )
    """)

    # 6. scenario_branches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenario_branches (
            id              TEXT PRIMARY KEY,
            scenario_id     TEXT REFERENCES scenarios(id) ON DELETE CASCADE,
            branch_type     TEXT CHECK(branch_type IN ('low_band','high_band')),
            condition_rule  TEXT,
            ai_response_style TEXT,
            example_text    TEXT
        )
    """)

    # 7. evaluation_hooks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_hooks (
            id                TEXT PRIMARY KEY,
            scenario_id       TEXT REFERENCES scenarios(id) ON DELETE CASCADE,
            trigger_condition TEXT,
            ai_reaction       TEXT
        )
    """)

    # 8. sample_dialogues
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample_dialogues (
            id                TEXT PRIMARY KEY,
            content_unit_id   TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
            band_level        REAL NOT NULL,
            turn_type         TEXT CHECK(turn_type IN
                                  ('standalone','opening','elaborate','negotiation','closing')),
            function_tag      TEXT,
            ai_line           TEXT NOT NULL,
            user_model_answer TEXT NOT NULL,
            embedding         F32_BLOB(384),
            created_at        TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sd_band ON sample_dialogues (band_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sd_cu ON sample_dialogues (content_unit_id)")

    # 9. hook_bank
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hook_bank (
            id         TEXT PRIMARY KEY,
            topic_tags TEXT DEFAULT '[]',
            text       TEXT NOT NULL,
            type       TEXT CHECK(type IN ('hook','anti_cliche'))
        )
    """)

    # 10. vocabulary_lookup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_lookup (
            id       TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            tier     TEXT,
            terms    TEXT DEFAULT '[]'
        )
    """)

    # 11. user_profile
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id               TEXT PRIMARY KEY,
            band_estimate_overall REAL,
            band_fluency          REAL,
            band_lexical          REAL,
            band_grammar          REAL,
            band_pronunciation    REAL,
            recurring_errors      TEXT DEFAULT '[]',
            entity_memory         TEXT DEFAULT '{}',
            updated_at            TEXT DEFAULT (datetime('now'))
        )
    """)

    # Migration check for entity_memory column if table existed previously
    try:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN entity_memory TEXT DEFAULT '{}'")
    except Exception:
        pass  # Column already exists


    # 12. user_content_exposure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_content_exposure (
            id                 TEXT PRIMARY KEY,
            user_id            TEXT REFERENCES user_profile(user_id),
            sample_dialogue_id TEXT REFERENCES sample_dialogues(id),
            exposed_at         TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exposure_user_time ON user_content_exposure (user_id, exposed_at)")

    # 13. tier2_evaluations (TASK-018: Weekly Reporting Engine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tier2_evaluations (
            id                  TEXT PRIMARY KEY,
            user_id             TEXT NOT NULL,
            fluency_score       REAL NOT NULL,
            lexical_score       REAL NOT NULL,
            grammar_score       REAL NOT NULL,
            pronunciation_score REAL NOT NULL,
            raw_score           REAL NOT NULL,
            created_at          TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier2_user_time ON tier2_evaluations (user_id, created_at)")

    # 14. user_bandit_stats (TASK-021: Multi-Armed Bandit Engine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_bandit_stats (
            user_id     TEXT NOT NULL,
            arm_offset  REAL NOT NULL,
            pull_count  INTEGER DEFAULT 0,
            total_reward REAL DEFAULT 0.0,
            avg_reward  REAL DEFAULT 0.0,
            updated_at  TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, arm_offset)
        )
    """)

    # 15. user_spaced_repetition (TASK-021: Spaced Repetition Engine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_spaced_repetition (
            id              TEXT PRIMARY KEY,
            user_id         TEXT NOT NULL,
            item_id         TEXT NOT NULL,
            item_text       TEXT NOT NULL,
            item_type       TEXT DEFAULT 'vocabulary',
            easiness_factor REAL DEFAULT 2.5,
            interval_days   INTEGER DEFAULT 1,
            repetitions     INTEGER DEFAULT 0,
            next_review_at  TEXT DEFAULT (datetime('now')),
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sr_user_due ON user_spaced_repetition (user_id, next_review_at)")

    # 16. harvest_review_queue (TASK-023: Data Flywheel Staging)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvest_review_queue (
            id                      TEXT PRIMARY KEY,
            candidate_ai_line       TEXT NOT NULL,
            candidate_user_answer   TEXT NOT NULL,
            source_user_id          TEXT NOT NULL,
            source_turn_id          TEXT NOT NULL,
            topic_tag               TEXT DEFAULT '',
            tier2_scores            TEXT NOT NULL,
            pii_check_passed        INTEGER NOT NULL,
            pii_entities_found      TEXT DEFAULT '[]',
            dedup_max_similarity    REAL DEFAULT 0.0,
            dedup_status            TEXT CHECK (dedup_status IN ('unique','similar_variant','duplicate_rejected')),
            review_status           TEXT DEFAULT 'pending' CHECK (review_status IN ('pending','approved','rejected')),
            reviewed_by             TEXT DEFAULT NULL,
            created_at              TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hrq_topic_created ON harvest_review_queue (topic_tag, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hrq_status ON harvest_review_queue (review_status)")

    conn.commit()
    conn.close()





def add_custom_scenario(scenario_data: dict[str, Any]) -> dict[str, Any]:
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


def get_custom_scenarios() -> list[dict[str, Any]]:
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
    """Save word translation permanently into DB (skips corrupt placeholders or untranslated words)."""
    clean_w = word.strip()
    clean_trans = translation.strip()
    if not clean_trans or clean_trans.lower().startswith("definition of") or clean_trans.lower() == clean_w.lower():
        return
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    word_key = f"{clean_w.lower()}_{target_lang}"
    cursor.execute("""
        INSERT OR REPLACE INTO word_dictionary (word_key, word, target_lang, target_label, translation, phonetic)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (word_key, clean_w, target_lang, target_label, clean_trans, phonetic))
    conn.commit()
    conn.close()


def get_translated_word(word: str, target_lang: str) -> dict[str, str] | None:
    """Retrieve word translation permanently from DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_w = word.strip()
    word_key = f"{clean_w.lower()}_{target_lang}"
    cursor.execute("SELECT * FROM word_dictionary WHERE word_key = ?", (word_key,))
    row = _fetch_one_dict(cursor)
    conn.close()
    if row:
        trans = str(row.get("translation", "")).strip()
        if trans and not trans.lower().startswith("definition of") and trans.lower() != clean_w.lower():
            return {
                "word": row["word"],
                "target_lang": row["target_lang"],
                "target_label": row["target_label"],
                "translation": trans,
                "phonetic": row["phonetic"]
            }
    return None


def get_all_saved_words(target_lang: str | None = None) -> list[dict[str, Any]]:
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


def get_user_stats() -> dict[str, Any]:
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


def add_user_xp(xp_amount: int) -> dict[str, Any]:
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


def get_user_profile(user_id: str) -> dict[str, Any]:
    """Retrieve user profile from DB. Initializes default profile if missing."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    row = _fetch_one_dict(cursor)
    conn.close()
    if row:
        recurring_errors = row.get("recurring_errors")
        if isinstance(recurring_errors, str):
            try:
                recurring_errors = json.loads(recurring_errors)
            except Exception:
                recurring_errors = []
        return {
            "user_id": row["user_id"],
            "band_estimate_overall": row["band_estimate_overall"] if row["band_estimate_overall"] is not None else 6.0,
            "band_fluency": row["band_fluency"] if row["band_fluency"] is not None else 6.0,
            "band_lexical": row["band_lexical"] if row["band_lexical"] is not None else 6.0,
            "band_grammar": row["band_grammar"] if row["band_grammar"] is not None else 6.0,
            "band_pronunciation": row["band_pronunciation"] if row["band_pronunciation"] is not None else 6.0,
            "recurring_errors": recurring_errors or [],
            "updated_at": row.get("updated_at", "")
        }
    return {
        "user_id": user_id,
        "band_estimate_overall": 6.0,
        "band_fluency": 6.0,
        "band_lexical": 6.0,
        "band_grammar": 6.0,
        "band_pronunciation": 6.0,
        "recurring_errors": [],
        "updated_at": ""
    }


def save_user_profile(user_id: str, profile_data: dict[str, Any]) -> dict[str, Any]:
    """Save or update user profile into DB."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    band_overall = profile_data.get("band_estimate_overall", 6.0)
    band_fluency = profile_data.get("band_fluency", 6.0)
    band_lexical = profile_data.get("band_lexical", 6.0)
    band_grammar = profile_data.get("band_grammar", 6.0)
    band_pronunciation = profile_data.get("band_pronunciation", 6.0)
    recurring_errors = json.dumps(profile_data.get("recurring_errors", []))

    cursor.execute("""
        INSERT OR REPLACE INTO user_profile (
            user_id, band_estimate_overall, band_fluency, band_lexical,
            band_grammar, band_pronunciation, recurring_errors, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (user_id, band_overall, band_fluency, band_lexical, band_grammar, band_pronunciation, recurring_errors))

    conn.commit()
    conn.close()
    return get_user_profile(user_id)


def save_tier2_evaluation_record(
    user_id: str,
    fluency: float,
    lexical: float,
    grammar: float,
    pronunciation: float,
    raw_score: float,
    eval_id: str | None = None,
) -> dict[str, Any]:
    """Log a Tier 2 evaluation record into tier2_evaluations table."""
    import uuid

    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    record_id = eval_id or f"t2_eval_{uuid.uuid4().hex[:10]}"
    cursor.execute(
        """
        INSERT INTO tier2_evaluations (
            id, user_id, fluency_score, lexical_score, grammar_score,
            pronunciation_score, raw_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            record_id,
            user_id,
            float(fluency),
            float(lexical),
            float(grammar),
            float(pronunciation),
            float(raw_score),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": record_id,
        "user_id": user_id,
        "fluency_score": float(fluency),
        "lexical_score": float(lexical),
        "grammar_score": float(grammar),
        "pronunciation_score": float(pronunciation),
        "raw_score": float(raw_score),
    }


def get_tier2_evaluations_history(
    user_id: str, days: int = 7
) -> list[dict[str, Any]]:
    """Retrieve Tier 2 evaluations history for a user over the past N days."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, user_id, fluency_score, lexical_score, grammar_score,
               pronunciation_score, raw_score, created_at
        FROM tier2_evaluations
        WHERE user_id = ?
          AND created_at >= datetime('now', '-' || ? || ' days')
        ORDER BY created_at ASC
    """
    cursor.execute(query, (user_id, int(days)))
    rows = _fetch_all_dicts(cursor)
    conn.close()
    return rows


