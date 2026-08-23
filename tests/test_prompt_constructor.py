"""
tests/test_prompt_constructor.py
=================================
Unit tests for app.prompt_constructor (TASK-006).
"""

import time

from app.rag.prompt_constructor import (
    PromptContext,
    construct_messages,
    construct_system_prompt,
)
from app.rag.retrieval import RetrievedDialogue


def test_construct_system_prompt_with_retrieved_dialogues() -> None:
    dialogues = [
        RetrievedDialogue(
            id="sd_1",
            content_unit_id="cu_1",
            band_level=6.0,
            turn_type="elaborate",
            function_tag="expressing_opinions",
            ai_line="What is your favorite type of music?",
            user_model_answer="I am particularly fond of acoustic pop because of its soothing melodies.",
            score=0.85,
        ),
        RetrievedDialogue(
            id="sd_2",
            content_unit_id="cu_1",
            band_level=6.5,
            turn_type="elaborate",
            function_tag="expressing_opinions",
            ai_line="How often do you listen to music?",
            user_model_answer="I listen to music almost daily while commuting to work.",
            score=0.78,
        ),
    ]

    ctx = PromptContext(
        user_id="user_test_123",
        band_estimate=6.2,
        topic_tag="music",
        retrieved_dialogues=dialogues,
        character_name="Lily",
        difficulty_adjustment="hold",
    )

    prompt = construct_system_prompt(ctx)

    assert "Lily" in prompt
    assert "Target IELTS Band Level: 6.2" in prompt
    assert "Topic: music" in prompt
    assert "REFERENCE DIALOGUES" in prompt
    assert "What is your favorite type of music?" in prompt
    assert "soothing melodies" in prompt
    assert "ANTI-VERBATIM REPETITION" in prompt
    assert "FOLLOW-UP QUESTION REQUIREMENT" in prompt
    assert '"ai_utterance"' in prompt
    assert '"internal_band_signal"' in prompt
    assert '"topic_tag"' in prompt
    assert '"difficulty_adjustment"' in prompt


def test_construct_system_prompt_fallback_empty_retrieved_dialogues() -> None:
    ctx = PromptContext(
        user_id="user_test_456",
        band_estimate=5.5,
        topic_tag="hobbies",
        retrieved_dialogues=[],
        character_name="Lily",
    )

    prompt = construct_system_prompt(ctx)

    assert "No specific sample dialogues retrieved for topic 'hobbies'" in prompt
    assert "Target IELTS Band Level: 5.5" in prompt
    assert "MANDATORY OUTPUT FORMAT" in prompt
    assert '"ai_utterance"' in prompt


def test_construct_messages_formatting() -> None:
    ctx = PromptContext(
        user_id="user_test_789",
        band_estimate=7.0,
        topic_tag="technology",
    )

    history = [
        {"role": "user", "content": "Hi, I want to talk about smartphones."},
        {"role": "assistant", "content": "Sure! How often do you use your smartphone?"},
    ]

    messages = construct_messages(
        context=ctx,
        history=history,
        user_utterance="I use it constantly for both work and personal study.",
    )

    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert "Target IELTS Band Level: 7.0" in messages[0]["content"]
    assert messages[1]["content"] == "Hi, I want to talk about smartphones."
    assert messages[2]["content"] == "Sure! How often do you use your smartphone?"
    assert messages[3]["content"] == "I use it constantly for both work and personal study."


def test_prompt_construction_performance() -> None:
    ctx = PromptContext(
        user_id="perf_user",
        band_estimate=6.5,
        topic_tag="travel",
        retrieved_dialogues=[
            RetrievedDialogue(
                id="sd_p1",
                content_unit_id="cu_p",
                band_level=6.5,
                turn_type="opening",
                function_tag="intro",
                ai_line="Where did you go on your last holiday?",
                user_model_answer="I visited Da Nang last summer.",
            )
        ],
    )

    # Run 1000 iterations to test speed
    start = time.perf_counter()
    for _ in range(1000):
        _ = construct_system_prompt(ctx)
    elapsed_total_ms = (time.perf_counter() - start) * 1000.0

    avg_ms = elapsed_total_ms / 1000.0
    # Average construction time must be well under 5ms
    assert avg_ms < 1.0, f"Average assembly time too slow: {avg_ms:.4f} ms"


def test_construct_system_prompt_with_level_constraints() -> None:
    ctx = PromptContext(
        user_id="level_user",
        band_estimate=6.0,
        level=9,
        topic_tag="memories",
    )

    prompt = construct_system_prompt(ctx)

    assert "Target Level: Level 9/20" in prompt
    assert "STRICT DIFFICULTY ENFORCEMENT: LEVEL 9/20" in prompt
    assert "LENGTH: Between 45 and 85 words" in prompt
    assert "RULES" in prompt

