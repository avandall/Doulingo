"""
tests/test_persona_memory.py
=============================
Unit tests for AI Persona Identity & Long-Term Entity Memory System (TASK-017).
"""

import time

import pytest

from app.db import init_db
from app.persona_memory import (
    extract_entities_from_turn,
    format_entity_memory_for_prompt,
    get_persona_identity,
    get_user_entity_memory,
    save_user_entity_memory,
    update_user_memory_from_turn,
)
from app.prompt_constructor import PromptContext, construct_system_prompt


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """
    Sets up a clean temporary SQLite database for testing.
    """
    db_file = tmp_path / "test_duolingo.db"
    monkeypatch.setattr("app.db.DB_PATH", db_file)
    init_db()
    yield db_file


def test_get_persona_identity():
    lily = get_persona_identity("Lily")
    assert lily["name"] == "Lily"
    assert "Friendly" in lily["role"]

    rajesh = get_persona_identity("rajesh")
    assert rajesh["name"] == "Rajesh"

    unknown = get_persona_identity("UnknownPersona")
    assert unknown["name"] == "UnknownPersona"


def test_extract_entities_from_turn_basic():
    text = "I really enjoy playing guitar and I work as a software engineer in my daily life."
    memory = extract_entities_from_turn(text)

    assert "hobbies" in memory
    assert "playing guitar" in memory["hobbies"]

    assert "occupation" in memory
    assert "software engineer" in memory["occupation"]


def test_extract_entities_from_turn_merging():
    initial_memory = {
        "hobbies": ["reading fiction"],
        "locations": ["Hanoi"]
    }
    text = "In my free time I love playing tennis and I am planning to visit Tokyo next month."
    updated = extract_entities_from_turn(text, existing_memory=initial_memory)

    assert "reading fiction" in updated["hobbies"]
    assert "playing tennis" in updated["hobbies"]
    assert "Hanoi" in updated["locations"]
    assert "personal_events" in updated
    assert any("visit tokyo" in item for item in updated["personal_events"])


def test_extract_entities_edge_cases():
    assert extract_entities_from_turn("") == {}
    assert extract_entities_from_turn("   ") == {}
    assert extract_entities_from_turn("Hello how are you today?") == {}

    # Test deduplication
    existing = {"hobbies": ["coding"]}
    result = extract_entities_from_turn("I am into coding.", existing_memory=existing)
    assert result["hobbies"].count("coding") == 1


def test_db_get_and_save_entity_memory():
    user_id = "user_test_127"
    mem_data = {
        "hobbies": ["photography"],
        "occupation": ["architect"]
    }

    # Save to DB
    save_user_entity_memory(user_id, mem_data)

    # Retrieve from DB
    retrieved = get_user_entity_memory(user_id)
    assert retrieved == mem_data

    # Update memory
    mem_data["hobbies"].append("biking")
    save_user_entity_memory(user_id, mem_data)
    retrieved2 = get_user_entity_memory(user_id)
    assert "biking" in retrieved2["hobbies"]


def test_update_user_memory_from_turn():
    user_id = "user_test_456"
    text1 = "I work as a doctor and I live in Chicago."
    res1 = update_user_memory_from_turn(user_id, text1)

    assert "doctor" in res1.get("occupation", [])
    assert "chicago" in res1.get("locations", [])

    text2 = "I love swimming in my free time."
    res2 = update_user_memory_from_turn(user_id, text2)

    assert "swimming" in res2.get("hobbies", [])
    # Check persistence
    from_db = get_user_entity_memory(user_id)
    assert "doctor" in from_db.get("occupation", [])
    assert "swimming" in from_db.get("hobbies", [])


def test_format_entity_memory_for_prompt():
    assert format_entity_memory_for_prompt(None) == ""
    assert format_entity_memory_for_prompt({}) == ""

    mem_dict = {
        "hobbies": ["guitar", "chess"],
        "occupation": ["teacher"]
    }
    formatted = format_entity_memory_for_prompt(mem_dict)
    assert "### USER ENTITY MEMORY & PERSONAL FACTS" in formatted
    assert "Hobbies & Interests: guitar, chess" in formatted
    assert "Occupation & Field of Study: teacher" in formatted

    # List input
    mem_list = ["Loves coffee", "Lives in Paris"]
    formatted_list = format_entity_memory_for_prompt(mem_list)
    assert "### USER ENTITY MEMORY & PERSONAL FACTS" in formatted_list
    assert "- Loves coffee" in formatted_list


def test_prompt_constructor_with_entity_memory():
    mem_data = {"hobbies": ["baking sourdough"], "locations": ["Seattle"]}
    ctx = PromptContext(
        user_id="user_777",
        band_estimate=6.5,
        topic_tag="hobbies",
        character_name="Lily",
        entity_memory=mem_data
    )

    prompt = construct_system_prompt(ctx)
    assert "Lily" in prompt
    assert "USER ENTITY MEMORY & PERSONAL FACTS" in prompt
    assert "baking sourdough" in prompt
    assert "ENTITY RECALL" in prompt


def test_performance_benchmark():
    text = "I really enjoy coding in Python and I am planning to build a web application next week."
    start = time.perf_counter()
    for _ in range(100):
        extract_entities_from_turn(text)
    duration_ms = (time.perf_counter() - start) * 1000.0 / 100.0

    assert duration_ms < 15.0, f"Extraction averaged {duration_ms:.2f}ms (>15ms)"
