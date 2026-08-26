"""
app/core/prompt_factory.py
===========================
Core Prompt Factory Module (TASK-004)

Re-exports PromptFactory and get_prompt_factory from app.rag.prompt_factory,
and provides Structured CoT (Chain-of-Thought) output instructions and helpers.
"""

from typing import Any

from app.rag.prompt_factory import (
    GrammarPattern,
    MaterialBank,
    Persona,
    PromptFactory,
    Question,
    TopicBank,
    VocabularyItem,
    get_prompt_factory,
)

COT_SCHEMA_INSTRUCTIONS = """
=== STRUCTURED OUTPUT CoT (CHAIN-OF-THOUGHT) MANDATE ===
You MUST think through the response using Chain-of-Thought in Call 1 and return a JSON object with:
1. "natural_draft": A raw, conversational first draft of your response in standard English.
2. "vocab_check": Self-audit analysis checking whether vocabulary stays within the target CEFR level ceiling and meets length rules.
3. "final_response": The polished, final response text to speak to the user.

Output JSON ONLY with the exact keys:
{
  "natural_draft": "Your raw initial draft",
  "vocab_check": "Self-audit verifying vocabulary ceiling and length constraints",
  "final_response": "Polished English response line matching exact level rules",
  "user_feedback": {
    "grammar_status": "Clean & Clear" or brief fix note,
    "corrected_text": "Grammatically corrected version of user's sentence preserving exact meaning",
    "native_phrasing": "Direct native speaker English rewrite of user's sentence",
    "duo_reaction": "celebrate"|"happy"|"encouraging"
  }
}
"""


def build_cot_prompt_instructions(target_level: str | int = 1) -> str:
    """Return Structured Output CoT instructions for AI prompt injection."""
    return f"\n{COT_SCHEMA_INSTRUCTIONS.strip()}\nTarget CEFR Level Ceiling: {target_level}\n"


__all__ = [
    "COT_SCHEMA_INSTRUCTIONS",
    "GrammarPattern",
    "MaterialBank",
    "Persona",
    "PromptFactory",
    "Question",
    "TopicBank",
    "VocabularyItem",
    "build_cot_prompt_instructions",
    "get_prompt_factory",
]
