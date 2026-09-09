"""
Unit tests for app.core.schemas and strict mode JSON schema conversion.
"""

from typing import Any

import pytest
from pydantic import BaseModel, Field

from app.core.ai_engine import AIEngine
from app.core.schemas import (
    GreetingResponseSchema,
    QuickTranslationSchema,
    RoleplayTurnResponseSchema,
    UserFeedbackSchema,
    to_strict_json_schema,
)


def test_user_feedback_schema_validation():
    fb = UserFeedbackSchema(
        grammar_status="Clean & Clear",
        corrected_text="I want to order coffee.",
        native_phrasing="I'd like to order a coffee, please.",
        duo_reaction="happy",
        grammar_explanation="No errors detected."
    )
    assert fb.grammar_status == "Clean & Clear"
    assert fb.duo_reaction == "happy"
    assert fb.grammar_explanation == "No errors detected."


def test_user_feedback_schema_default_values():
    fb = UserFeedbackSchema(
        grammar_status="Minor Error",
        corrected_text="I am going home.",
        native_phrasing="I'm heading home."
    )
    assert fb.duo_reaction == "happy"
    assert fb.grammar_explanation is None


def test_roleplay_turn_response_schema():
    turn = RoleplayTurnResponseSchema(
        natural_draft="Acknowledge order politely",
        vocab_check="Level A2 vocabulary ok",
        final_response="Sure! What kind of coffee would you like?",
        user_feedback=UserFeedbackSchema(
            grammar_status="Clean",
            corrected_text="Can I get coffee?",
            native_phrasing="Could I get a coffee?"
        )
    )
    assert turn.final_response.startswith("Sure!")
    assert turn.user_feedback.grammar_status == "Clean"


def test_greeting_response_schema():
    greeting = GreetingResponseSchema(
        natural_draft="Welcome customer to cafe",
        vocab_check="A1 vocab",
        final_response="Hello! Welcome to Duo Cafe. What can I get for you today?"
    )
    assert greeting.final_response.startswith("Hello!")


def test_quick_translation_schema():
    trans = QuickTranslationSchema(
        vietnamese_translation="Tôi muốn gọi một tách cà phê."
    )
    assert trans.vietnamese_translation == "Tôi muốn gọi một tách cà phê."


def test_to_strict_json_schema_root_and_defs():
    schema = to_strict_json_schema(RoleplayTurnResponseSchema)

    # 1. Root checks
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"natural_draft", "vocab_check", "final_response", "user_feedback"}

    # 2. $defs checks
    assert "$defs" in schema
    assert "UserFeedbackSchema" in schema["$defs"]
    user_fb_def = schema["$defs"]["UserFeedbackSchema"]

    assert user_fb_def["type"] == "object"
    assert user_fb_def["additionalProperties"] is False
    assert set(user_fb_def["required"]) == {
        "grammar_status",
        "corrected_text",
        "native_phrasing",
        "duo_reaction",
        "grammar_explanation"
    }

    # 3. Nullable field check
    grammar_exp_prop = user_fb_def["properties"]["grammar_explanation"]
    assert "anyOf" in grammar_exp_prop
    null_type_present = any(
        item.get("type") == "null" for item in grammar_exp_prop["anyOf"] if isinstance(item, dict)
    )
    assert null_type_present is True


def test_to_strict_json_schema_custom_nested_model():
    class ChildModel(BaseModel):
        name: str
        tag: str | None = Field(default=None)

    class ParentModel(BaseModel):
        title: str
        child: ChildModel
        optional_note: str | None = Field(default=None)

    strict_schema = to_strict_json_schema(ParentModel)
    assert strict_schema["additionalProperties"] is False
    assert set(strict_schema["required"]) == {"title", "child", "optional_note"}

    child_def = strict_schema["$defs"]["ChildModel"]
    assert child_def["additionalProperties"] is False
    assert set(child_def["required"]) == {"name", "tag"}


def test_provider_adapters_accept_schema(monkeypatch):
    engine = AIEngine()
    engine.gemini_keys = ["fake_gemini_key"]
    engine.groq_keys = ["fake_groq_key"]
    engine.openai_keys = ["fake_openai_key"]

    captured_payloads = {}

    def mock_post(url, headers=None, json=None, timeout=None):
        class DummyResponse:
            status_code = 200
            def json(self):
                if "generativelanguage" in url:
                    return {"candidates": [{"content": {"parts": [{"text": '{"vietnamese_translation": "Xin chào"}'}]}}]}
                elif "groq" in url or "openai" in url:
                    return {"choices": [{"message": {"content": '{"vietnamese_translation": "Xin chào"}'}}]}
                elif "generate" in url:
                    return {"response": '{"vietnamese_translation": "Xin chào"}'}
                return {}
        captured_payloads[url] = json
        return DummyResponse()

    monkeypatch.setattr("requests.post", mock_post)

    res = engine._call_gemini("test prompt", "fake_key", "gemini-2.0-flash", schema=QuickTranslationSchema)
    assert res is not None

    res_groq = engine._call_groq("test prompt", "fake_key", "llama-3.3-70b-versatile", schema=QuickTranslationSchema)
    assert res_groq is not None

    res_openai = engine._call_openai("test prompt", "fake_key", schema=QuickTranslationSchema)
    assert res_openai is not None

    # Check payload formatting
    gemini_payload = [v for k, v in captured_payloads.items() if "generativelanguage" in k][0]
    assert "responseSchema" in gemini_payload["generationConfig"]

    groq_payload = [v for k, v in captured_payloads.items() if "groq" in k][0]
    assert groq_payload["response_format"]["type"] == "json_schema"
    assert groq_payload["response_format"]["json_schema"]["strict"] is True

    openai_payload = [v for k, v in captured_payloads.items() if "openai" in k][0]
    assert openai_payload["response_format"]["type"] == "json_schema"
    assert openai_payload["response_format"]["json_schema"]["strict"] is True
