"""
Unit tests for app/db.py — Turso Cloud SQLite integration & local fallback
"""

from app.storage.db import (
    add_custom_scenario,
    add_user_xp,
    get_all_saved_words,
    get_custom_scenarios,
    get_db_connection,
    get_translated_word,
    get_user_stats,
    init_db,
    save_translated_word,
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


def test_untranslated_word_prevention():
    """Verify that saving raw untranslated word is rejected and filtered."""
    test_w = "untranslateddummyword"
    save_translated_word(test_w, "vi", "Tiếng Việt", test_w, "/test/")
    assert get_translated_word(test_w, "vi") is None

    save_translated_word(test_w, "vi", "Tiếng Việt", "Từ giả lập", "/test/")
    res = get_translated_word(test_w, "vi")
    assert res is not None
    assert res["translation"] == "Từ giả lập"




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


def test_task_000_schema_tables_and_fk_cascade():
    """Test TASK-000: 12 Schema tables exist and Foreign Key Cascade functionality."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    schema_tables = [
        "content_units",
        "band_tiers",
        "function_details",
        "function_band_variants",
        "scenarios",
        "scenario_branches",
        "evaluation_hooks",
        "sample_dialogues",
        "hook_bank",
        "vocabulary_lookup",
        "user_profile",
        "user_content_exposure",
    ]

    for tbl in schema_tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
        row = cursor.fetchone()
        assert row is not None, f"Schema table {tbl} should exist"

    # Test FK Cascade
    cu_id = "test_cu_001"
    cursor.execute(
        """
        INSERT INTO content_units (id, template_type, title, topic_tags, target_band_min, target_band_max)
        VALUES (?, 'band_ladder', 'Test Topic', '["test"]', 5.0, 7.0)
        """,
        (cu_id,),
    )

    bt_id = "test_bt_001"
    cursor.execute(
        """
        INSERT INTO band_tiers (id, content_unit_id, band_min, band_max)
        VALUES (?, ?, 5.0, 6.0)
        """,
        (bt_id, cu_id),
    )

    sd_id = "test_sd_001"
    cursor.execute(
        """
        INSERT INTO sample_dialogues (id, content_unit_id, band_level, turn_type, ai_line, user_model_answer)
        VALUES (?, ?, 5.5, 'opening', 'Hello!', 'Hi there!')
        """,
        (sd_id, cu_id),
    )
    conn.commit()

    # Delete content unit and verify cascade
    cursor.execute("DELETE FROM content_units WHERE id = ?", (cu_id,))
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM band_tiers WHERE id = ?", (bt_id,))
    assert cursor.fetchone()[0] == 0, "band_tiers row should be deleted by cascade"

    cursor.execute("SELECT COUNT(*) FROM sample_dialogues WHERE id = ?", (sd_id,))
    assert cursor.fetchone()[0] == 0, "sample_dialogues row should be deleted by cascade"

    conn.close()

