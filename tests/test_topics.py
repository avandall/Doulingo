"""
tests/test_topics.py
====================
Unit tests for TASK-006: Structured Topic Bank & Softening Scenario Angles.
"""

import json
import os

import pytest

from app.core.ai_engine import AIEngine


@pytest.fixture
def ai_engine():
    return AIEngine()


def test_topic_bank_json_structure():
    """Verify app/data/topic_bank.json exists, parses, and has expected categories."""
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "data", "topic_bank.json"))
    assert os.path.exists(file_path), "app/data/topic_bank.json must exist"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "topics" in data
    topics = data["topics"]
    assert len(topics) >= 5

    categories = {t.get("category") for t in topics}
    assert "free_conversation" in categories
    assert "structured_scenario" in categories


def test_topic_info_lookup(ai_engine):
    """Test get_topic_info for known and unknown topics."""
    greeting_info = ai_engine.get_topic_info("greeting")
    assert greeting_info is not None
    assert greeting_info["category"] == "free_conversation"
    assert greeting_info["enable_scenario_angle"] is False

    food_info = ai_engine.get_topic_info("ordering_food")
    assert food_info is not None
    assert food_info["category"] == "structured_scenario"
    assert food_info["enable_scenario_angle"] is True
    assert len(food_info.get("scenario_angles", [])) > 0

    unknown_info = ai_engine.get_topic_info("unknown_random_topic_xyz")
    assert unknown_info is None


def test_should_enable_scenario_angle_free_conversation(ai_engine):
    """Free conversation / greeting topics must NOT enable scenario angles."""
    assert ai_engine.should_enable_scenario_angle("greeting") is False
    assert ai_engine.should_enable_scenario_angle("free_chat") is False
    assert ai_engine.should_enable_scenario_angle("det_childhood_memory") is False
    assert ai_engine.should_enable_scenario_angle("det_best_friend") is False
    assert ai_engine.should_enable_scenario_angle("det_school_life") is False
    assert ai_engine.should_enable_scenario_angle("hobbies_interests") is False


def test_should_enable_scenario_angle_structured_scenario(ai_engine):
    """Structured roleplay scenarios MUST enable scenario angles."""
    assert ai_engine.should_enable_scenario_angle("ordering_food") is True
    assert ai_engine.should_enable_scenario_angle("job_interview") is True
    assert ai_engine.should_enable_scenario_angle("hotel_booking") is True
    assert ai_engine.should_enable_scenario_angle("airport_travel") is True
    assert ai_engine.should_enable_scenario_angle("shopping_bargaining") is True


def test_greeting_prompt_no_scenario_angle(ai_engine, monkeypatch):
    """
    Verify start_roleplay_greeting for a free conversation topic (e.g. greeting)
    does NOT inject 'Dynamic Session Angle:'.
    """
    captured_prompt = []

    def mock_call_llm_with_heuristic_loop(prompt, level=1, temp=0.8):
        captured_prompt.append(prompt)
        return {
            "natural_draft": "Hello! How are you today?",
            "vocab_check": "Verified",
            "final_response": "Hello! How are you today?",
            "ai_response": "Hello! How are you today?"
        }

    monkeypatch.setattr(ai_engine, "_call_llm_with_heuristic_loop", mock_call_llm_with_heuristic_loop)

    res = ai_engine.start_roleplay_greeting(scenario_id="greeting", character_id="lily", level=1)
    assert res is not None
    assert "final_response" in res or "ai_response" in res
    assert len(captured_prompt) == 1
    prompt_text = captured_prompt[0]

    assert "Dynamic Session Angle:" not in prompt_text
    assert "Keep the dialogue open, warm, and natural" in prompt_text


def test_structured_scenario_prompt_has_scenario_angle(ai_engine, monkeypatch):
    """
    Verify start_roleplay_greeting for a structured scenario topic (e.g. ordering_food)
    DOES inject 'Dynamic Session Angle:'.
    """
    captured_prompt = []

    def mock_call_llm_with_heuristic_loop(prompt, level=1, temp=0.8):
        captured_prompt.append(prompt)
        return {
            "natural_draft": "Welcome to our bistro! What would you like to order?",
            "vocab_check": "Verified",
            "final_response": "Welcome to our bistro! What would you like to order?",
            "ai_response": "Welcome to our bistro! What would you like to order?"
        }

    monkeypatch.setattr(ai_engine, "_call_llm_with_heuristic_loop", mock_call_llm_with_heuristic_loop)

    res = ai_engine.start_roleplay_greeting(scenario_id="ordering_food", character_id="lily", level=1)
    assert res is not None
    assert "final_response" in res or "ai_response" in res
    assert len(captured_prompt) == 1
    prompt_text = captured_prompt[0]

    assert "Dynamic Session Angle:" in prompt_text
