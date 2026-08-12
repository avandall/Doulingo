"""
Backend Prompt Factory & Dynamic Sampling Engine for Duolingo Speak
Dynamically samples academic personas, vocabulary, questions, and grammar patterns
from MaterialBank, blending them with AI Character definitions to generate rich system prompts.
"""

import random
from typing import Any

from app.characters import get_character
from app.material_bank import (
    GrammarPattern,
    MaterialBank,
    Persona,
    Question,
    TopicBank,
    VocabularyItem,
    get_material_bank,
)


# Map numeric level (1-20) → IELTS band label for MaterialBank filtering.
# DB*.md files store vocab/questions under "Band 5.0 - 6.0" or "Band 6.5+".
# Level 1-8  = beginner/lower-intermediate → use Band 5.0-6.0 materials
# Level 9-20 = upper-intermediate/advanced → prefer Band 6.5+ materials,
#              fall back to 5.0-6.0 if 6.5+ pool is empty for this topic.
def _level_to_band(level: int) -> str:
    """Convert a numeric level (1-20) into a DB*.md band label for vocab filtering."""
    if level <= 8:
        return "5.0-6.0"
    return "6.5+"


# How many DB vocab items to sample depending on level depth.
def _vocab_count(level: int) -> int:
    if level <= 4:
        return 2
    elif level <= 8:
        return 3
    elif level <= 14:
        return 4
    else:
        return 5


class PromptFactory:
    """Dynamic Prompt Builder & Sampling Engine for IELTS / CEFR roleplay dialogues."""

    def __init__(self, material_bank: MaterialBank | None = None) -> None:
        self.material_bank = material_bank

    def _get_bank(self) -> MaterialBank:
        """Helper to get injected MaterialBank or global singleton instance."""
        if self.material_bank is not None:
            return self.material_bank
        return get_material_bank()

    def sample_materials(
        self,
        topic_id: str,
        level: str = "5.0-6.0"
    ) -> dict[str, Any]:
        """
        Sample materials for a given topic and target band level.

        'level' accepts either:
        - a numeric string like "7" or "15" (auto-converts to band)
        - a band string like "5.0-6.0" or "6.5+"

        Returns a dictionary containing sampled items with safe fallbacks.
        """
        bank = self._get_bank()
        topic: TopicBank | None = bank.get_topic(topic_id)

        if not topic:
            return {
                "topic_id": topic_id,
                "topic_name": topic_id.replace("_", " ").replace("-", " ").title(),
                "persona": None,
                "vocabulary": [],
                "questions": [],
                "grammar_patterns": []
            }

        # Normalize level: if numeric string, convert to band label
        try:
            numeric_level = int(level.strip())
            band = _level_to_band(numeric_level)
            n_vocab = _vocab_count(numeric_level)
        except (ValueError, AttributeError):
            # Already a band string like "5.0-6.0" or "6.5+"
            band = level.strip()
            n_vocab = 3

        # 1. Sample Persona (1 item)
        sampled_persona: Persona | None = None
        if topic.personas:
            sampled_persona = random.choice(topic.personas)

        # 2. Sample Vocabulary - prioritize target band, fallback to any available
        vocab_candidates = [
            v for v in topic.vocabulary
            if band in v.band or v.band.strip() == band
        ]
        if not vocab_candidates:
            vocab_candidates = list(topic.vocabulary)

        actual_count = min(len(vocab_candidates), n_vocab)
        sampled_vocab: list[VocabularyItem] = (
            random.sample(vocab_candidates, actual_count) if actual_count > 0 else []
        )

        # 3. Sample Questions (1-2 items) - prioritize target band, fallback to any
        question_candidates = [
            q for q in topic.questions
            if band in q.band or q.band.strip() == band
        ]
        if not question_candidates:
            question_candidates = list(topic.questions)

        question_count = min(len(question_candidates), random.randint(1, 2)) if question_candidates else 0
        sampled_questions: list[Question] = (
            random.sample(question_candidates, question_count) if question_count > 0 else []
        )

        # 4. Sample Grammar Patterns (1-2 items) - skip empty/placeholder patterns
        grammar_candidates = [
            g for g in topic.grammar_patterns
            if g.pattern.strip() and g.pattern.strip() != "--"
        ]
        grammar_count = min(len(grammar_candidates), random.randint(1, 2)) if grammar_candidates else 0
        sampled_grammar: list[GrammarPattern] = (
            random.sample(grammar_candidates, grammar_count) if grammar_count > 0 else []
        )

        return {
            "topic_id": topic.topic_id,
            "topic_name": topic.topic_name,
            "persona": sampled_persona,
            "vocabulary": sampled_vocab,
            "questions": sampled_questions,
            "grammar_patterns": sampled_grammar
        }

    def build_system_prompt(
        self,
        topic_id: str,
        level: str = "5.0-6.0",
        character_id: str = "lily",
        user_history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Assemble a System Prompt incorporating Character persona,
        sampled MaterialBank vocabulary/questions/grammar patterns.

        IMPORTANT: Length/difficulty constraints are applied SEPARATELY in
        ai_engine._build_level_constraint_block(). Do NOT add conflicting
        length/complexity instructions here.
        """
        character = get_character(character_id)
        sampled = self.sample_materials(topic_id, level)

        char_name = character.get("name", "AI Tutor")
        char_prompt = character.get("system_prompt", "")
        topic_name = sampled["topic_name"]

        # ── Section 1: Character Identity ──────────────────────────────────
        prompt_lines = [
            f"CHARACTER: You are {char_name}.",
            f"{char_prompt}",
            "",
        ]

        # ── Section 2: Topic Context ────────────────────────────────────────
        prompt_lines += [
            "### CONVERSATION TOPIC",
            f"Topic: {topic_name}",
            "",
        ]

        # -- Section 3: Persona role (if available) --------------------------
        persona: Persona | None = sampled.get("persona")
        if persona:
            prompt_lines += [
                "### YOUR ROLE THIS SESSION",
                f"Play the persona of: [{persona.id}] {persona.title} - {persona.description}",
                "",
            ]

        # -- Section 4: Mandatory Vocabulary Injection -----------------------
        # Phrased as MANDATORY to prevent AI from ignoring soft suggestions.
        vocab_items: list[VocabularyItem] = sampled.get("vocabulary", [])
        if vocab_items:
            prompt_lines += [
                "### MANDATORY VOCABULARY - USE THESE IN YOUR RESPONSES",
                "You MUST weave at least 1-2 of these phrases organically into the conversation:",
            ]
            for v in vocab_items:
                prompt_lines.append(f'  * "{v.phrase}" - {v.meaning}')
            prompt_lines.append("")

        # ── Section 5: Question seeds ────────────────────────────────────────
        question_items: list[Question] = sampled.get("questions", [])
        if question_items:
            prompt_lines += [
                "### QUESTION INSPIRATION (adapt freely, never ask verbatim)",
            ]
            for q in question_items:
                prompt_lines.append(f"  \u2192 {q.text}")
            prompt_lines.append("")

        # ── Section 6: Grammar patterns ──────────────────────────────────────
        grammar_items: list[GrammarPattern] = sampled.get("grammar_patterns", [])
        if grammar_items:
            prompt_lines += [
                "### GRAMMAR STRUCTURES TO MODEL IN YOUR SPEECH",
            ]
            for g in grammar_items:
                prompt_lines.append(f"  \u25b8 {g.pattern}")
            prompt_lines.append("")

        return "\n".join(prompt_lines)


_global_prompt_factory: PromptFactory | None = None


def get_prompt_factory(material_bank: MaterialBank | None = None) -> PromptFactory:
    """Singleton getter for PromptFactory instance."""
    global _global_prompt_factory
    if _global_prompt_factory is None:
        _global_prompt_factory = PromptFactory(material_bank=material_bank)
    return _global_prompt_factory
