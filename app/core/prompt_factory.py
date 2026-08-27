"""
app/core/prompt_factory.py
===========================
Decoupled 3-Tier Prompt System & Core Prompt Factory Engine (TASK-005)

Tầng 1: Core Pedagogy & Warmth (Active listening, ASR clarification, Empathetic feedback, Open question mandate)
Tầng 2: Persona Overlay (Dynamic loading from app/data/persona_definitions.json)
Tầng 3: Adaptive CEFR Horizon (Level ceiling & vocabulary guidance without rigid min_words rules)
"""

from typing import Any

from app.characters import get_character
from app.rag.prompt_factory import (
    GrammarPattern,
    MaterialBank,
    Persona,
    Question,
    TopicBank,
    VocabularyItem,
)
from app.rag.prompt_factory import (
    PromptFactory as BasePromptFactory,
)
from app.rag.prompt_factory import (
    get_prompt_factory as get_base_prompt_factory,
)

# ── Tier 1: Core Pedagogy & Warmth ──────────────────────────────────────────
TIER1_CORE_PEDAGOGY = """=== TIER 1: CORE PEDAGOGY & WARMTH ===
1. ACTIVE LISTENING & MIRRORING: Reflect at least 1 key idea or emotion from the user's speech in your opening sentence before giving your perspective.
2. ASR PHONETIC CLARIFICATION: Learner input is transcribed via Speech-to-Text (ASR) which may introduce phonetic errors or homophones. NEVER complain or claim you do not understand. Gently infer the intended meaning in context and keep the conversation flowing smoothly.
3. EMPATHETIC FEEDBACK: Maintain an encouraging, warm tone. Praise effort and support the learner without pedantry.
4. OPEN QUESTION MANDATE: Always end your spoken response with ONE relevant, natural, open-ended question to drive the conversation forward.
5. NATURAL CONVERSATION FLOW: Obey natural English phrasing. Do NOT enforce rigid word count minimums or use repetitive template phrases."""


def build_tier1_core_pedagogy() -> str:
    """Return Tier 1: Core Pedagogy & Warmth instruction block."""
    return TIER1_CORE_PEDAGOGY


# ── Tier 2: Persona Overlay ──────────────────────────────────────────────────
def build_tier2_persona_overlay(character_id: str = "lily") -> str:
    """Return Tier 2: Persona Overlay instruction block dynamically loaded from persona_definitions.json."""
    char = get_character(character_id)
    return (
        f"=== TIER 2: PERSONA OVERLAY ({char.get('name', 'AI Tutor').upper()}) ===\n"
        f"Name: {char.get('name', 'AI Tutor')}\n"
        f"Role: {char.get('role', 'Conversational Partner')}\n"
        f"Trait: {char.get('trait', 'Supportive')}\n"
        f"Speech Style: {char.get('speech_style', 'Clear and natural')}\n"
        f"Personality: {char.get('personality', 'Helpful AI tutor')}\n"
        f"Directives: {char.get('system_prompt', '')}"
    )


# ── Tier 3: Adaptive CEFR Horizon ─────────────────────────────────────────────
def build_tier3_cefr_horizon(target_level: str | int = 1) -> str:
    """Return Tier 3: Adaptive CEFR Horizon instruction block."""
    return (
        f"=== TIER 3: ADAPTIVE CEFR HORIZON ===\n"
        f"Target Level Ceiling: Level {target_level}\n"
        f"Vocabulary & Grammar: Keep vocabulary and sentence structures appropriate for Level {target_level}.\n"
        f"No Rigid Word Limits: Focus on clarity and natural rhythm without forcing artificial minimum word counts."
    )


# ── Full Decoupled 3-Tier System Prompt Builder ─────────────────────────────
def build_3tier_system_prompt(
    character_id: str = "lily",
    topic_name: str = "",
    target_level: str | int = 1
) -> str:
    """
    Construct a Decoupled 3-Tier System Prompt combining Core Pedagogy (Tier 1),
    Persona Overlay from persona_definitions.json (Tier 2), and Adaptive CEFR Horizon (Tier 3).
    """
    t1 = build_tier1_core_pedagogy()
    t2 = build_tier2_persona_overlay(character_id)
    t3 = build_tier3_cefr_horizon(target_level)

    topic_block = f"\n### CONVERSATION TOPIC\nTopic: {topic_name}\n" if topic_name else ""

    return f"{t1}\n\n{t2}{topic_block}\n\n{t3}"


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


class DecoupledPromptFactory(BasePromptFactory):
    """
    Decoupled 3-Tier Prompt Factory extending BasePromptFactory.
    Integrates Tier 1 Pedagogy, Tier 2 Persona Overlay, and Tier 3 CEFR Horizon.
    """

    def build_decoupled_prompt(
        self,
        character_id: str = "lily",
        topic_id: str = "general",
        level: str | int = 1
    ) -> str:
        sampled = self.sample_materials(topic_id, str(level))
        topic_name = sampled.get("topic_name", topic_id)
        base_3tier = build_3tier_system_prompt(
            character_id=character_id,
            topic_name=topic_name,
            target_level=level
        )

        prompt_lines = [base_3tier, ""]

        vocab_items: list[VocabularyItem] = sampled.get("vocabulary", [])
        if vocab_items:
            prompt_lines.append("### MANDATORY VOCABULARY TO MODEL")
            for v in vocab_items:
                prompt_lines.append(f'  * "{v.phrase}" - {v.meaning}')
            prompt_lines.append("")

        return "\n".join(prompt_lines)


PromptFactory = BasePromptFactory
get_prompt_factory = get_base_prompt_factory

__all__ = [
    "COT_SCHEMA_INSTRUCTIONS",
    "DecoupledPromptFactory",
    "GrammarPattern",
    "MaterialBank",
    "Persona",
    "PromptFactory",
    "Question",
    "TopicBank",
    "VocabularyItem",
    "build_3tier_system_prompt",
    "build_cot_prompt_instructions",
    "build_tier1_core_pedagogy",
    "build_tier2_persona_overlay",
    "build_tier3_cefr_horizon",
    "get_prompt_factory",
]
