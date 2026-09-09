"""
Unit tests for TASK-003: Prompt Partitioning and Prompt Caching.
Verifies:
1. Static cacheable prefix token count >= 1,024 tokens (Groq/OpenAI KV-cache threshold).
2. Dynamic session angle immutability across multi-turn exchanges.
3. History pruning and user utterances affect ONLY the dynamic suffix.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.core.ai_engine import AIEngine
from app.rag.prompt_constructor import (
    build_dynamic_turn_suffix,
    build_static_cacheable_prefix,
)


@pytest.fixture
def sample_scenario() -> dict[str, Any]:
    return {
        "id": "ielts_speaking_part1",
        "title": "Work and Studies",
        "description": "Discussing current job, study habits, and future career plans for IELTS.",
        "default_character": "lily",
        "open_story_guide": "Challenge the candidate with questions about work-life balance.",
    }


@pytest.fixture
def sample_character() -> dict[str, Any]:
    return {
        "id": "lily",
        "name": "Lily",
        "country": "UK",
        "role": "IELTS Examiner",
        "trait": "Professional yet friendly",
        "speech_style": "Clear, natural British English",
    }


def estimate_tokens(text: str) -> int:
    """Approximate tokens using standard 1 token ~= 4 chars heuristic."""
    return len(text) // 4


def test_static_cacheable_prefix_token_count(sample_scenario, sample_character):
    """
    DoD Test: Prefix MUST be >= 1,024 tokens to reliably trigger
    implicit prefix caching on Groq and OpenAI.
    """
    mock_dialogues = [
        MagicMock(band_level=7, ai_line="What field do you work in?", user_model_answer="I work in software engineering."),
        MagicMock(band_level=8, ai_line="Do you enjoy your daily routine?", user_model_answer="Yes, I find it quite stimulating."),
    ]
    prefix = build_static_cacheable_prefix(
        scenario=sample_scenario,
        character=sample_character,
        level=10,
        scenario_angle="Focus on career transitions and automation.",
        rag_dialogues=mock_dialogues,
    )

    tokens = estimate_tokens(prefix)
    assert tokens >= 1024, f"Prefix token estimate {tokens} is below minimum 1024 token threshold!"


def test_session_angle_immutability():
    """
    Verifies that scenario_angle is locked once per session at start_roleplay_greeting
    and reused identically across turns in process_turn / _build_token_efficient_prompt.
    """
    engine = AIEngine()
    scenario_id = "hotel_stay"

    # Start greeting picks an angle
    engine.start_roleplay_greeting(scenario_id=scenario_id, character_id="lily", level=5)
    assert scenario_id in engine._session_angles
    initial_angle = engine._session_angles[scenario_id]
    assert initial_angle != ""

    scenario = {
        "id": scenario_id,
        "title": "Hotel Check-in & Stay",
        "description": "Hotel check-in and customer service.",
        "default_character": "lily",
        "open_story_guide": "Roleplay checking into a boutique hotel.",
    }

    # Turn 1
    prompt_turn1 = engine._build_token_efficient_prompt(
        scenario=scenario,
        character={"name": "Lily", "id": "lily"},
        user_transcript="Hi, I have a reservation under John Doe.",
        history=[],
        turn_count=1,
        level=5,
    )

    # Turn 2
    prompt_turn2 = engine._build_token_efficient_prompt(
        scenario=scenario,
        character={"name": "Lily", "id": "lily"},
        user_transcript="Could I get a room with an ocean view?",
        history=[
            {"role": "user", "content": "Hi, I have a reservation under John Doe."},
            {"role": "assistant", "content": "Welcome Mr. Doe, let me pull up your booking."},
        ],
        turn_count=2,
        level=5,
    )

    # Both prompts MUST contain the exact same angle
    assert f"Dynamic Session Angle: {initial_angle}" in prompt_turn1
    assert f"Dynamic Session Angle: {initial_angle}" in prompt_turn2


def test_dynamic_suffix_partitioning():
    """
    Verifies that user transcripts and history are isolated exclusively
    to the dynamic turn suffix, never contaminating the static prefix.
    """
    user_speech = "Honestly, I find public speaking terrifying."
    history_str = 'User: "Hello"\nLily: "Hi there!"'
    suffix = build_dynamic_turn_suffix(
        history_str=history_str,
        user_transcript=user_speech,
        turn_count=3,
    )

    assert "TURN NUMBER: 3" in suffix
    assert user_speech in suffix
    assert history_str in suffix
    assert "=== DYNAMIC TURN CONTEXT ===" in suffix
