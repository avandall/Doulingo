"""
tests/test_conversational_agent.py
==================================
Unit tests for app/conversational_agent.py (TASK-007).
"""

import json
from unittest.mock import MagicMock

from app.conversational_agent import (
    ConversationalAgent,
    ConversationalResponse,
    parse_conversational_response,
)
from app.prompt_constructor import PromptContext


def test_parse_valid_json_response():
    raw_json = json.dumps({
        "ai_utterance": "I really enjoy living in the city. What type of neighborhood do you live in?",
        "internal_band_signal": 6.5,
        "topic_tag": "accommodation",
        "difficulty_adjustment": "increase",
    })

    resp = parse_conversational_response(raw_json, fallback_topic="accommodation")

    assert isinstance(resp, ConversationalResponse)
    assert resp.ai_utterance == "I really enjoy living in the city. What type of neighborhood do you live in?"
    assert resp.internal_band_signal == 6.5
    assert resp.topic_tag == "accommodation"
    assert resp.difficulty_adjustment == "increase"
    assert resp.is_fallback is False
    assert resp.raw_json is not None


def test_parse_markdown_wrapped_json():
    raw_text = """```json
{
  "ai_utterance": "That sounds like a cozy place! Do you prefer apartments or houses?",
  "internal_band_signal": "7.0",
  "topic_tag": "housing",
  "difficulty_adjustment": "HOLD"
}
```"""

    resp = parse_conversational_response(raw_text, fallback_topic="housing")

    assert resp.ai_utterance == "That sounds like a cozy place! Do you prefer apartments or houses?"
    assert resp.internal_band_signal == 7.0
    assert resp.topic_tag == "housing"
    assert resp.difficulty_adjustment == "hold"
    assert resp.is_fallback is False


def test_parse_partial_and_missing_fields():
    raw_json = json.dumps({
        "ai_utterance": "I agree. Where would you like to travel next?",
        "difficulty_adjustment": "invalid_value",
    })

    resp = parse_conversational_response(raw_json, fallback_topic="travel", default_band=6.0)

    assert resp.ai_utterance == "I agree. Where would you like to travel next?"
    assert resp.internal_band_signal == 6.0
    assert resp.topic_tag == "travel"
    assert resp.difficulty_adjustment == "hold"  # Invalid normalized to hold


def test_parse_malformed_json_fallback():
    raw_text = "I think living in a house is great because you have space."

    resp = parse_conversational_response(raw_text, fallback_topic="general", default_band=5.5)

    assert resp.is_fallback is True
    assert resp.ai_utterance == raw_text
    assert resp.topic_tag == "general"
    assert resp.internal_band_signal == 5.5
    assert resp.difficulty_adjustment == "hold"


def test_parse_empty_string_fallback():
    resp = parse_conversational_response("", fallback_topic="hobbies", default_band=6.0)

    assert resp.is_fallback is True
    assert len(resp.ai_utterance) > 0
    assert resp.topic_tag == "hobbies"


def test_conversational_agent_with_callable_client():
    def mock_client(messages):
        assert len(messages) >= 1
        return json.dumps({
            "ai_utterance": "Hanoi is famous for its Street food. What is your favorite dish?",
            "internal_band_signal": 7.5,
            "topic_tag": "food",
            "difficulty_adjustment": "increase",
        })

    agent = ConversationalAgent(llm_client=mock_client)
    context = PromptContext(user_id="user_123", band_estimate=7.0, topic_tag="food")

    resp = agent.generate_response(context=context, user_utterance="I live in Hanoi.")

    assert resp.ai_utterance == "Hanoi is famous for its Street food. What is your favorite dish?"
    assert resp.internal_band_signal == 7.5
    assert resp.difficulty_adjustment == "increase"
    assert resp.is_fallback is False


def test_conversational_agent_with_object_client():
    mock_obj = MagicMock()
    mock_obj.generate.return_value = json.dumps({
        "ai_utterance": "Reading helps expand vocabulary. How often do you read books?",
        "internal_band_signal": 6.0,
        "topic_tag": "hobbies",
        "difficulty_adjustment": "hold",
    })

    agent = ConversationalAgent()
    context = PromptContext(user_id="user_456", band_estimate=6.0, topic_tag="hobbies")

    resp = agent.generate_response(
        context=context,
        history=[{"role": "user", "content": "I like reading."}],
        llm_client_override=mock_obj,
    )

    assert resp.ai_utterance == "Reading helps expand vocabulary. How often do you read books?"
    mock_obj.generate.assert_called_once()


def test_conversational_agent_client_exception_fallback():
    def failing_client(messages):
        raise RuntimeError("API connection timeout")

    agent = ConversationalAgent(llm_client=failing_client)
    context = PromptContext(user_id="user_789", band_estimate=6.0, topic_tag="sports")

    resp = agent.generate_response(context=context, user_utterance="I play football.")

    assert resp.is_fallback is True
    assert len(resp.ai_utterance) > 0
    assert resp.topic_tag == "sports"
    assert resp.difficulty_adjustment == "hold"


def test_no_score_leakage_in_ai_utterance():
    def mock_client(messages):
        return json.dumps({
            "ai_utterance": "That is wonderful! Do you enjoy playing video games?",
            "internal_band_signal": 8.0,
            "topic_tag": "entertainment",
            "difficulty_adjustment": "increase",
        })

    agent = ConversationalAgent(llm_client=mock_client)
    context = PromptContext(user_id="user_test", band_estimate=8.0, topic_tag="entertainment")

    resp = agent.generate_response(context=context)

    # Ensure internal metrics are not present in the public ai_utterance string
    assert "internal_band_signal" not in resp.ai_utterance
    assert "difficulty_adjustment" not in resp.ai_utterance
    assert "8.0" not in resp.ai_utterance
