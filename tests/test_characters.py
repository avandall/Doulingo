"""
tests/test_characters.py
=========================
Unit and Integration Test Suite for 3-Tier Prompt System & Character Personas (TASK-005)
"""

import pytest

from app.characters import (
    CHARACTERS,
    DEFAULT_CHARACTERS,
    get_character,
    list_characters,
    load_persona_definitions,
)
from app.core.prompt_factory import (
    DecoupledPromptFactory,
    build_3tier_system_prompt,
    build_tier1_core_pedagogy,
    build_tier2_persona_overlay,
    build_tier3_cefr_horizon,
)


def test_load_persona_definitions():
    """Verify loading persona definitions from JSON file."""
    personas = load_persona_definitions()
    assert isinstance(personas, dict)
    assert len(personas) >= 9
    assert "lily" in personas
    assert "oscar" in personas
    assert "viktor" in personas


@pytest.mark.parametrize("char_id", [
    "lily", "oscar", "viktor", "chanel",
    "kaelen", "colt", "zarina", "scarlet", "luigi"
])
def test_get_character_all_personas(char_id: str):
    """Test retrieving each of the 9 characters returns valid data."""
    char = get_character(char_id)
    assert char["id"] == char_id
    assert "name" in char and len(char["name"]) > 0
    assert "role" in char and len(char["role"]) > 0
    assert "trait" in char and len(char["trait"]) > 0
    assert "system_prompt" in char and len(char["system_prompt"]) > 0


def test_unknown_character_fallback():
    """Test unknown character ID falls back safely to default (Lily)."""
    unknown = get_character("non_existent_character_123")
    assert unknown["id"] == "lily"
    assert unknown["name"] == "Lily"


def test_list_characters():
    """Test listing all characters returns formatted dictionary objects."""
    chars_list = list_characters()
    assert isinstance(chars_list, list)
    assert len(chars_list) >= 9
    for c in chars_list:
        assert "id" in c
        assert "name" in c
        assert "role" in c
        assert "avatar_icon" in c


@pytest.mark.parametrize("char_id", [
    "lily", "oscar", "viktor", "chanel",
    "kaelen", "colt", "zarina", "scarlet", "luigi"
])
def test_3tier_prompt_generation_all_personas(char_id: str):
    """Verify Decoupled 3-Tier prompt system generates complete system prompts for all personas."""
    prompt = build_3tier_system_prompt(character_id=char_id, topic_name="Hobbies", target_level=3)
    
    # Tier 1 checks
    assert "=== TIER 1: CORE PEDAGOGY & WARMTH ===" in prompt
    assert "ACTIVE LISTENING & MIRRORING" in prompt
    assert "ASR PHONETIC CLARIFICATION" in prompt
    assert "OPEN QUESTION MANDATE" in prompt

    # Tier 2 checks
    assert "=== TIER 2: PERSONA OVERLAY" in prompt
    char = get_character(char_id)
    assert char["name"] in prompt

    # Tier 3 checks
    assert "=== TIER 3: ADAPTIVE CEFR HORIZON ===" in prompt
    assert "Level 3" in prompt


def test_no_rigid_min_words_rule():
    """Verify that 3-Tier prompt outputs contain no rigid min_words rules."""
    for char_id in CHARACTERS:
        prompt = build_3tier_system_prompt(character_id=char_id, target_level=2)
        assert "min_words" not in prompt.lower()
        assert "count your words" not in prompt.lower()


def test_decoupled_prompt_factory():
    """Test DecoupledPromptFactory builds prompt incorporating materials and 3-tier structure."""
    factory = DecoupledPromptFactory()
    prompt = factory.build_decoupled_prompt(character_id="oscar", topic_id="sports", level=5)
    assert "TIER 1" in prompt
    assert "TIER 2" in prompt
    assert "TIER 3" in prompt
    assert "Oscar" in prompt
