"""
tests/test_micro_llm_rewriter.py
=================================
Unit tests for Micro-LLM Heuristic Retry Rewriter Engine (TASK-012)
"""

from app.core.ai_engine import ai_engine
from app.core.micro_llm_rewriter import MicroLLMRewriter, micro_llm_rewriter


def test_micro_llm_rewriter_heuristic_downgrade():
    """Verify natural deterministic downgrade replaces high-level violating words accurately."""
    original = "I contemplate philosophical ideas deeply every day."
    violating = ["contemplate", "philosophical", "deeply"]

    rewritten = micro_llm_rewriter._apply_heuristic_downgrade(original, violating)

    assert "contemplate" not in rewritten.lower()
    assert "philosophical" not in rewritten.lower()
    assert "think about" in rewritten.lower()
    assert "big" in rewritten.lower()
    assert rewritten.endswith("?") or "what" in rewritten.lower()


def test_micro_llm_rewriter_rewrite_naturally_fallback(monkeypatch):
    """Verify rewrite_naturally falls back cleanly to natural downgrade when LLM provider is unavailable."""
    original = "I contemplate philosophical ideas deeply every day."
    violating = ["contemplate", "philosophical", "deeply"]

    # When no ai_engine_ref is provided, it uses heuristic fallback
    res = micro_llm_rewriter.rewrite_naturally(
        original_text=original,
        violating_words=violating,
        target_level=2,
        character_name="Lily",
        scenario_title="Daily Life"
    )

    assert res["method"] == "heuristic_fallback"
    assert "rewritten_text" in res
    assert "contemplate" not in res["rewritten_text"].lower()
    assert "passed_heuristic" in res


def test_micro_llm_rewriter_rewrite_naturally_llm_mode(monkeypatch):
    """Verify rewrite_naturally uses LLM provider response when available."""
    original = "I contemplate philosophical ideas deeply."
    violating = ["contemplate", "philosophical", "deeply"]

    class MockAIEngine:
        def _call_llm_providers(self, prompt, temp=0.3):
            return {
                "natural_draft": "Drafting simple words",
                "vocab_check": "Verified basic A1 words",
                "final_response": "I think about big ideas a lot. What do you think?",
                "ai_response": "I think about big ideas a lot. What do you think?"
            }

    mock_engine = MockAIEngine()
    res = micro_llm_rewriter.rewrite_naturally(
        original_text=original,
        violating_words=violating,
        target_level=2,
        ai_engine_ref=mock_engine
    )

    assert res["method"] == "micro_llm"
    assert res["rewritten_text"] == "I think about big ideas a lot. What do you think?"
    assert res["passed_heuristic"] is True


def test_ai_engine_integration_with_micro_llm(monkeypatch):
    """Verify AIEngine._call_llm_with_heuristic_loop uses Micro-LLM Rewriter when vocabulary ceiling is violated."""
    calls = []

    violating_res = {
        "natural_draft": "High level draft",
        "vocab_check": "Unchecked",
        "final_response": "I contemplate complex philosophical topics deeply every single day.",
        "ai_response": "I contemplate complex philosophical topics deeply every single day.",
        "user_feedback": {"grammar_status": "Clean & Clear"}
    }

    micro_llm_res = {
        "natural_draft": "Micro-LLM downgrade draft",
        "vocab_check": "Verified simple A1 words",
        "final_response": "I think about big topics a lot. What do you think?",
        "ai_response": "I think about big topics a lot. What do you think?"
    }

    def mock_providers(prompt, temp=0.8):
        calls.append(prompt)
        if len(calls) == 1:
            return violating_res
        return micro_llm_res

    monkeypatch.setattr(ai_engine, "_call_llm_providers", mock_providers)

    res = ai_engine._call_llm_with_heuristic_loop("Test prompt", level=2, max_retries=2)
    assert res is not None
    assert res["heuristic_check"]["retries"] == 1
    assert res["heuristic_check"]["rewritten_by_micro_llm"] is True
    assert res["final_response"] == "I think about big topics a lot. What do you think?"
