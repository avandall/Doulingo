"""
Backend Prompt Factory & Dynamic Sampling Engine for Duolingo Speak
Dynamically samples academic personas, vocabulary, questions, and grammar patterns
from MaterialBank, blending them with AI Character definitions to generate rich system prompts.
"""

import random
from typing import Dict, List, Optional, Any
from app.material_bank import (
    MaterialBank,
    TopicBank,
    Persona,
    Question,
    VocabularyItem,
    GrammarPattern,
    get_material_bank,
)
from app.characters import get_character


class PromptFactory:
    """Dynamic Prompt Builder & Sampling Engine for IELTS / CEFR roleplay dialogues."""

    def __init__(self, material_bank: Optional[MaterialBank] = None) -> None:
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
    ) -> Dict[str, Any]:
        """
        Sample materials for a given topic and target band level:
        - 1 Persona (randomly selected from topic persona pool)
        - 3-4 Vocabulary items (prioritizing target level band)
        - 1-2 Questions (prioritizing target level band)
        - 1-2 Grammar patterns (if available)

        Returns a dictionary containing sampled items with safe fallbacks.
        """
        bank = self._get_bank()
        topic: Optional[TopicBank] = bank.get_topic(topic_id)

        if not topic:
            return {
                "topic_id": topic_id,
                "topic_name": topic_id.replace("_", " ").replace("-", " ").title(),
                "persona": None,
                "vocabulary": [],
                "questions": [],
                "grammar_patterns": []
            }

        # 1. Sample Persona (1 item)
        sampled_persona: Optional[Persona] = None
        if topic.personas:
            sampled_persona = random.choice(topic.personas)

        # 2. Sample Vocabulary (3-4 items)
        vocab_candidates = [
            v for v in topic.vocabulary
            if v.band.strip() == level.strip() or level.strip() in v.band
        ]
        if not vocab_candidates:
            vocab_candidates = list(topic.vocabulary)

        vocab_count = min(len(vocab_candidates), random.randint(3, 4)) if vocab_candidates else 0
        sampled_vocab: List[VocabularyItem] = (
            random.sample(vocab_candidates, vocab_count) if vocab_count > 0 else []
        )

        # 3. Sample Questions (1-2 items)
        question_candidates = [
            q for q in topic.questions
            if q.band.strip() == level.strip() or level.strip() in q.band
        ]
        if not question_candidates:
            question_candidates = list(topic.questions)

        question_count = min(len(question_candidates), random.randint(1, 2)) if question_candidates else 0
        sampled_questions: List[Question] = (
            random.sample(question_candidates, question_count) if question_count > 0 else []
        )

        # 4. Sample Grammar Patterns (1-2 items)
        grammar_candidates = list(topic.grammar_patterns)
        grammar_count = min(len(grammar_candidates), random.randint(1, 2)) if grammar_candidates else 0
        sampled_grammar: List[GrammarPattern] = (
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
        user_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Assemble a complete System Prompt incorporating Character persona,
        sampled MaterialBank components, target level instructions, and pedagogical guidelines.
        """
        character = get_character(character_id)
        sampled = self.sample_materials(topic_id, level)

        char_name = character.get("name", "AI Tutor")
        char_role = character.get("role", "Language Partner")
        char_trait = character.get("trait", "Helpful")
        char_prompt = character.get("system_prompt", "")

        topic_name = sampled["topic_name"]

        prompt_lines = [
            f"You are {char_name}, playing the role of a {char_role} ({char_trait}).",
            f"{char_prompt}",
            "",
            "### TOPIC & SCENARIO CONTEXT",
            f"- Topic: {topic_name} (ID: {topic_id})",
            f"- Target IELTS Band / CEFR Level: {level}",
        ]

        # Add sampled persona roleplay context if available
        persona: Optional[Persona] = sampled.get("persona")
        if persona:
            prompt_lines.append(f"- Roleplay Character Persona: [{persona.id}] {persona.title} — {persona.description}")

        # Add sampled vocabulary section
        vocab_items: List[VocabularyItem] = sampled.get("vocabulary", [])
        if vocab_items:
            prompt_lines.extend([
                "",
                "### TARGET VOCABULARY TO WEAVE NATURALLY IN CONVERSATION",
                "Try to naturally incorporate 1-2 of these words/phrases per turn when relevant:"
            ])
            for v in vocab_items:
                prompt_lines.append(f"  • {v.phrase}: {v.meaning} (Band {v.band})")

        # Add sampled question seeds section
        question_items: List[Question] = sampled.get("questions", [])
        if question_items:
            prompt_lines.extend([
                "",
                "### SUGGESTED QUESTION SEEDS TO ADVANCE DIALOGUE",
                "Use or adapt these open-ended questions to probe deeper:"
            ])
            for q in question_items:
                prompt_lines.append(f"  • [{q.id}] {q.text}")

        # Add sampled grammar patterns section
        grammar_items: List[GrammarPattern] = sampled.get("grammar_patterns", [])
        if grammar_items:
            prompt_lines.extend([
                "",
                "### TARGET GRAMMAR PATTERNS TO ENCOURAGE",
                "Model these high-scoring sentence structures during the conversation:"
            ])
            for g in grammar_items:
                prompt_lines.append(f"  • [{g.pattern_id}] {g.pattern}")

        # Add pedagogical rules
        prompt_lines.extend([
            "",
            "### PEDAGOGICAL & CONVERSATIONAL GUIDELINES",
            f"1. Always remain strictly in character as {char_name}.",
            f"2. Adapt sentence structure and vocabulary complexity to Band {level}.",
            "3. Keep each response conversational, engaging, and concise (2-4 sentences max).",
            "4. Gently correct major grammar or vocabulary errors if necessary, but keep conversation flow smooth.",
            "5. Do NOT introduce yourself repeatedly in ongoing turns."
        ])

        return "\n".join(prompt_lines)


_global_prompt_factory: Optional[PromptFactory] = None


def get_prompt_factory(material_bank: Optional[MaterialBank] = None) -> PromptFactory:
    """Singleton getter for PromptFactory instance."""
    global _global_prompt_factory
    if _global_prompt_factory is None:
        _global_prompt_factory = PromptFactory(material_bank=material_bank)
    return _global_prompt_factory
