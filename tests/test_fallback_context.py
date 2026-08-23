from app.core.ai_engine import LEVEL_CONFIGS, ai_engine


def test_context_aware_fallback_negative_sentiment():
    """Verify context-aware fallback returns empathetic response for negative transcript without 'wonderful'."""
    scenario = {"id": "det_childhood_memory", "title": "Childhood Memories"}
    character = {"id": "lily", "name": "Lily"}
    user_transcript = "I lost my memory and I am feeling very sad about it."
    
    res = ai_engine._get_context_aware_fallback(scenario, character, user_transcript, level=9)
    ai_resp = res["ai_response"]
    
    # Must NOT contain inappropriate enthusiastic phrase
    assert "That sounds wonderful!" not in ai_resp
    assert "wonderful and exciting" not in ai_resp
    
    # Must contain empathetic phrasing
    ai_resp_lower = ai_resp.lower()
    empathy_keywords = ["sorry", "difficult", "difficulty", "challenging", "challenges", "tough", "stressful", "burden", "empathize", "support", "courage", "hardship", "feelings"]
    assert any(kw in ai_resp_lower for kw in empathy_keywords), f"No empathetic keyword in response: {ai_resp}"
    
    # duo_reaction should be encouraging for negative sentiment
    assert res["user_feedback"]["duo_reaction"] == "encouraging"

def test_context_aware_fallback_topic_continuity():
    """Verify fallback maintains scenario topic in response."""
    scenario = {"id": "vacation_travel", "title": "Summer Beach Vacation"}
    character = {"id": "rajesh", "name": "Rajesh"}
    user_transcript = "I don't know where to go this year."
    
    res = ai_engine._get_context_aware_fallback(scenario, character, user_transcript, level=5)
    
    assert "Summer Beach Vacation" in res["ai_response"]

def test_context_aware_fallback_level_word_count():
    """Verify word count compliance across different levels."""
    scenario = {"id": "everyday_chat", "title": "Everyday Practice"}
    character = {"id": "lily", "name": "Lily"}
    user_transcript = "I had a busy day."
    
    for level in [1, 9, 15]:
        cfg = LEVEL_CONFIGS[level]
        res = ai_engine._get_context_aware_fallback(scenario, character, user_transcript, level=level)
        word_count = len(res["ai_response"].split())
        assert cfg["min_words"] <= word_count <= cfg["max_words"], f"Level {level} word count {word_count} not in [{cfg['min_words']}, {cfg['max_words']}]"

def test_process_turn_fallback_integration(monkeypatch):
    """Verify process_turn uses context-aware fallback when API keys are unconfigured/exhausted."""
    monkeypatch.setattr(ai_engine, "reload_keys", lambda: None)
    monkeypatch.setattr(ai_engine, "groq_keys", [])
    monkeypatch.setattr(ai_engine, "gemini_keys", [])
    monkeypatch.setattr(ai_engine, "openai_keys", [])
    monkeypatch.setattr(ai_engine, "ollama_base_url", "")
    
    res = ai_engine.process_turn("det_childhood_memory", "lily", "I lost my dog last week", [], level=9)
    
    assert res is not None
    assert "ai_response" in res
    assert "That sounds wonderful!" not in res["ai_response"]
