import pytest
from app.ai_engine import ai_engine, AIEngine
from app.scenarios import list_scenarios
from app.characters import list_characters

def test_summarize_or_prune_history_under_threshold():
    """Verify history under 30 messages (15 exchanges) is not truncated."""
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(20)
    ]
    recent_items, summary_block = ai_engine._summarize_or_prune_history(history, max_exchanges=15)
    assert len(recent_items) == 20
    assert summary_block == ""

def test_summarize_or_prune_history_over_threshold():
    """Verify history over 30 messages (15 exchanges) triggers truncation & summarization guard."""
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(34)
    ]
    recent_items, summary_block = ai_engine._summarize_or_prune_history(history, max_exchanges=15)
    assert len(recent_items) == 10
    assert "[MULTI-TURN CONTEXT SUMMARY" in summary_block
    assert "PRUNED 24 PREVIOUS MESSAGES (12 TURNS)" in summary_block

def test_build_token_efficient_prompt_with_truncation():
    """Verify _build_token_efficient_prompt incorporates context summary when history > 15 exchanges."""
    scenarios = list_scenarios()
    scenario = scenarios[0] if scenarios else {"title": "Coffee Shop", "description": "Ordering coffee", "open_story_guide": "Guide"}
    character = {"name": "Duo", "trait": "Friendly", "speech_style": "Casual", "country": "USA", "role": "Barista"}

    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Dialogue turn content {i}"}
        for i in range(36)
    ]
    prompt = ai_engine._build_token_efficient_prompt(
        scenario=scenario,
        character=character,
        user_transcript="I would like a cappuccino please.",
        history=history,
        turn_count=19,
        level=1
    )
    assert "[MULTI-TURN CONTEXT SUMMARY" in prompt
    assert "Dialogue turn content 35" in prompt
