"""
Unit tests for app/db.py — Turso Cloud SQLite integration & local fallback
"""

from app.db import (
    init_db,
    get_db_connection,
    add_custom_scenario,
    get_custom_scenarios,
    save_translated_word,
    get_translated_word,
    get_all_saved_words,
    get_user_stats,
    add_user_xp
)


def test_init_db_and_tables():
    """Test initializing DB tables."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    for table_name in ["custom_scenarios", "word_dictionary", "saved_vocabulary", "user_stats"]:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        row = cursor.fetchone()
        assert row is not None, f"Table {table_name} should exist"

    conn.close()


def test_custom_scenario_crud():
    """Test adding and retrieving a custom scenario."""
    sc_data = {
        "id": "test_scenario_001",
        "title": "IELTS Speaking Practice",
        "category": "IELTS",
        "icon": "🎓",
        "color": "#FF8C00",
        "level": "Advanced",
        "level_code": "C1",
        "default_character": "victoria",
        "description": "Practice Part 2 cue cards",
        "objective": "Speak fluently for 2 minutes",
        "suggested_vocabulary": ["fluency", "cohesion", "lexical resource"]
    }

    added = add_custom_scenario(sc_data)
    assert added["id"] == "test_scenario_001"

    scenarios = get_custom_scenarios()
    matching = [s for s in scenarios if s["id"] == "test_scenario_001"]
    assert len(matching) == 1
    sc = matching[0]
    assert sc["title"] == "IELTS Speaking Practice"
    assert "fluency" in sc["suggested_vocabulary"]


def test_word_dictionary_crud():
    """Test saving and retrieving translated words."""
    save_translated_word(
        word="eloquent",
        target_lang="vi",
        target_label="Tiếng Việt",
        translation="hùng hồn, lưu loát",
        phonetic="/ˈel.ə.kwənt/"
    )

    result = get_translated_word("eloquent", "vi")
    assert result is not None
    assert result["word"] == "eloquent"
    assert result["translation"] == "hùng hồn, lưu loát"

    all_words = get_all_saved_words("vi")
    assert any(w["word"] == "eloquent" for w in all_words)


def test_user_stats_and_xp():
    """Test retrieving user stats and adding XP."""
    stats = get_user_stats()
    assert "total_xp" in stats
    assert "streak" in stats

    initial_xp = stats["total_xp"]
    updated_stats = add_user_xp(50)
    assert updated_stats["total_xp"] == initial_xp + 50


def test_turso_fallback_on_invalid_url(monkeypatch):
    """Test graceful fallback to local SQLite when TURSO_DATABASE_URL is invalid."""
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://invalid-turso-db-url-12345.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "invalid_token_xyz")

    conn = get_db_connection()
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    res = cursor.fetchone()
    assert res[0] == 1
    conn.close()
