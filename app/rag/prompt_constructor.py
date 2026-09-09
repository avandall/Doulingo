"""
app/prompt_constructor.py
==========================
Prompt Constructor Engine v1 (TASK-006).

Assembles User Profile context, target IELTS band level, retrieved RAG reference dialogues
(from app.rag.retrieval), anti-verbatim repetition rules, follow-up question constraints,
and structured JSON output schema into an optimal System Prompt for the Conversational Agent (TASK-007).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.rag.retrieval import RetrievedDialogue

log = logging.getLogger(__name__)

JSON_SCHEMA_INSTRUCTION = """### MANDATORY OUTPUT FORMAT
You MUST output ONLY a valid, raw JSON object matching the following structure exactly (without markdown backticks or commentary outside JSON):

{
  "ai_utterance": "<AI's natural spoken English response to the user, ending with 1 follow-up question>",
  "internal_band_signal": <float estimate of user's latest response quality between 4.0 and 9.0>,
  "topic_tag": "<current conversation topic tag>",
  "difficulty_adjustment": "<'increase' | 'hold' | 'decrease'>"
}
"""


@dataclass
class PromptContext:
    user_id: str
    band_estimate: float = 6.0
    topic_tag: str = "general_conversation"
    retrieved_dialogues: list[RetrievedDialogue] = field(default_factory=list)
    character_name: str = "Lily"
    difficulty_adjustment: str = "hold"
    entity_memory: dict[str, Any] | list[Any] | None = field(default_factory=dict)
    simulation_directives: str | None = None
    interleaved_directives: str | None = None
    level: int | None = None


def band_to_level(band: float) -> int:
    """Map IELTS band (4.0 - 9.0) to numeric difficulty level (1 - 20)."""
    b = max(4.0, min(9.0, float(band)))
    return max(1, min(20, round(1.0 + (b - 4.0) * (19.0 / 5.0))))


def level_to_band(level: int) -> float:
    """Map numeric level (1 - 20) to base IELTS band (4.0 - 9.0)."""
    lvl = max(1, min(20, int(level)))
    return round(4.0 + (lvl - 1) * (5.0 / 19.0), 1)


def construct_system_prompt(context: PromptContext) -> str:
    """
    Constructs the complete System Prompt for the Conversational Agent.
    Assembly execution time target: < 5ms.
    """
    from app.core.level_config import LEVEL_CONFIGS
    from app.core.persona_memory import (
        format_entity_memory_for_prompt,
        get_persona_identity,
    )

    start_time = time.perf_counter()

    persona = get_persona_identity(context.character_name or "Lily")
    char_name = persona["name"]

    if context.level is not None:
        lvl = max(1, min(20, int(context.level)))
        band = round(context.band_estimate, 1) if context.band_estimate != 6.0 else level_to_band(lvl)
    else:
        band = round(context.band_estimate, 1)
        lvl = band_to_level(band)

    cfg = LEVEL_CONFIGS.get(lvl, LEVEL_CONFIGS[1])
    topic = context.topic_tag or "general_conversation"

    sections: list[str] = []

    # 1. Persona & Identity
    sections.append(
        f"### PERSONA & ROLE\n"
        f"You are {char_name}, {persona['role']}.\n"
        f"Personality: {persona['personality']}.\n"
        f"Accent & Style: {persona['accent_style']}.\n"
        f"Core Trait: {persona['trait']}"
    )

    # 2. Target Profile & Context
    sections.append(
        f"### CONVERSATION CONTEXT\n"
        f"- Target Level: Level {lvl}/20 (CEFR {cfg['cefr']})\n"
        f"- Target IELTS Band Level: {band}\n"
        f"- Topic: {topic}\n"
        f"- Current Difficulty Signal: {context.difficulty_adjustment}"
    )

    # 2.1 Granular 20-Level Difficulty System Enforcement
    level_block = (
        f"=== STRICT DIFFICULTY ENFORCEMENT: LEVEL {lvl}/20 ({cfg['cefr']}) ===\n"
        f"YOU MUST WRITE EXACTLY LIKE THE EXAMPLE BELOW. DO NOT DEVIATE.\n\n"
        f"EXAMPLE OF A PERFECT LEVEL {lvl} RESPONSE:\n"
        f"\"{cfg['example_response']}\"\n\n"
        f"RULES (same style as the example above):\n"
        f"- LENGTH: Between {cfg['min_words']} and {cfg['max_words']} words. COUNT YOUR WORDS.\n"
        f"- VOCABULARY: {cfg['vocab_tier']}\n"
        f"- GRAMMAR: {cfg['grammar_allowed']}\n"
        f"- RESPONSE STYLE: {cfg['response_style']}\n"
        f"=== END LEVEL RULES ==="
    )
    sections.append(level_block)

    # 2.5 Long-Term User Entity Memory (TASK-017)
    memory_formatted = format_entity_memory_for_prompt(context.entity_memory)
    if memory_formatted:
        sections.append(memory_formatted)

    # 2.6 Simulation Engine Directives (TASK-019)
    if context.simulation_directives:
        sections.append(f"### ROLEPLAY SIMULATION DIRECTIVES\n{context.simulation_directives}")

    # 2.7 Interleaved Practice Directives (TASK-020)
    if context.interleaved_directives:
        sections.append(f"### INTERLEAVED PRACTICE DIRECTIVES\n{context.interleaved_directives}")

    # 3. Retrieved Reference Dialogues (RAG Context)
    if context.retrieved_dialogues:
        dialogue_lines = [
            "### REFERENCE DIALOGUES (Use for vocabulary & depth inspiration only):"
        ]
        for idx, d in enumerate(context.retrieved_dialogues, 1):
            dialogue_lines.append(
                f"[{idx}] (Band {d.band_level})\n"
                f"  AI Reference Line: \"{d.ai_line}\"\n"
                f"  User Model Answer: \"{d.user_model_answer}\""
            )
        sections.append("\n".join(dialogue_lines))
    else:
        sections.append(
            "### REFERENCE DIALOGUES\n"
            f"No specific sample dialogues retrieved for topic '{topic}'. "
            f"Adapt naturally using standard Band {band} level vocabulary and conversational structures."
        )

    # 4. Behavioral Directives & Rules
    directives = [
        "### BEHAVIORAL DIRECTIVES & CONSTRAINTS",
        "1. ANTI-VERBATIM REPETITION: DO NOT copy sentences or phrases verbatim from the reference dialogues. Use them as inspiration for vocabulary level and discourse depth.",
        f"2. FOLLOW-UP QUESTION REQUIREMENT: You MUST end your response (`ai_utterance`) with exactly 1 natural follow-up question appropriate for Band {band} / Level {lvl}.",
        f"3. BAND & LEVEL APPROPRIATENESS: Adjust your vocabulary complexity and sentence length (between {cfg['min_words']} and {cfg['max_words']} words) to match Level {lvl} ({cfg['cefr']}).",
        "4. NATURALITY: Speak in conversational, spoken English. Avoid robotic or textbook-sounding phrases."
    ]
    if memory_formatted:
        directives.append(
            "5. ENTITY RECALL: When appropriate, naturally weave the user's personal facts or past events into your conversational response."
        )
    sections.append("\n".join(directives))

    # 5. Output Schema
    sections.append(JSON_SCHEMA_INSTRUCTION)

    prompt = "\n\n".join(sections)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    if elapsed_ms > 5.0:
        log.warning("Prompt construction took %.2f ms (target < 5ms)", elapsed_ms)

    return prompt


def construct_messages(
    context: PromptContext,
    history: list[dict[str, str]] | None = None,
    user_utterance: str | None = None,
) -> list[dict[str, str]]:
    """
    Constructs full message payload for LLM API invocation.
    Includes System Prompt, conversation history, and latest user turn.
    """
    system_prompt = construct_system_prompt(context)
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

    if user_utterance:
        messages.append({"role": "user", "content": user_utterance})

    return messages


def build_static_cacheable_prefix(
    scenario: dict[str, Any],
    character: dict[str, Any],
    level: int = 1,
    scenario_angle: str | None = None,
    rag_dialogues: list[Any] | None = None,
) -> str:
    """
    Constructs the 100% Immutable Static Cacheable Prefix (~1,200 tokens).
    Covers Persona, Level Constraints, RAG Dialogues, Directives & Task Instructions.
    Designed for zero cache-busting and >=1,024 token count for Groq/OpenAI KV-Cache optimization.
    """
    from app.core.level_config import LEVEL_CONFIGS
    from app.core.prompt_factory import get_prompt_factory

    lvl = max(1, min(20, int(level)))
    cfg = LEVEL_CONFIGS.get(lvl, LEVEL_CONFIGS[1])
    scenario_key = scenario.get("id") or scenario.get("title", "")

    # 1. Base Domain System Prompt from Prompt Factory
    prompt_factory = get_prompt_factory()
    mb_system_prompt = prompt_factory.build_system_prompt(
        topic_id=scenario_key,
        level=f"{lvl}",
        character_id=character.get("id", "lily")
    )

    # 2. RAG Section (Book Reference Dialogues)
    rag_section = ""
    if rag_dialogues:
        rag_lines = [
            f'- [Band {d.band_level}] AI: "{d.ai_line}" | User Model Answer: "{d.user_model_answer}"'
            for d in rag_dialogues
        ]
        rag_section = (
            "=== REFERENCE DIALOGUES FROM BOOKS (Use for vocabulary & topic inspiration) ===\n"
            + "\n".join(rag_lines)
            + "\n=== END REFERENCE DIALOGUES ===\n\n"
        )

    # 3. Dynamic Scenario Angle (Fixed for the entire session)
    angle_block = ""
    if scenario_angle:
        angle_block = f"\nDynamic Session Angle: {scenario_angle}\nImprovise an open, creative roleplay! Bring unexpected twists, humorous situations, and vivid character interactions. Never use repetitive templates."

    story_guide = scenario.get("open_story_guide", "Improvise an exciting, unscripted roleplay with unexpected surprises and plot twists.")
    trait = character.get("trait", "Friendly")
    style = character.get("speech_style", "Conversational")

    # 4. Strict Level Constraints
    level_block = f"""=== STRICT DIFFICULTY ENFORCEMENT: LEVEL {lvl}/20 ({cfg['cefr']}) ===
YOU MUST WRITE EXACTLY LIKE THE EXAMPLE BELOW. DO NOT DEVIATE.

EXAMPLE OF A PERFECT LEVEL {lvl} RESPONSE:
"{cfg['example_response']}"

RULES (same style as the example above):
- LENGTH: Between {cfg['min_words']} and {cfg['max_words']} words. COUNT YOUR WORDS.
- VOCABULARY: {cfg['vocab_tier']}
- GRAMMAR: {cfg['grammar_allowed']}
=== END LEVEL RULES ==="""

    # Assemble Static Prefix
    prefix = f"""{mb_system_prompt}

{rag_section}CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
DO NOT USE ANY FOREIGN GREETINGS OR LOCAL WORDS.
DO NOT INTRODUCE YOURSELF IN CONVERSATION.

PERMANENT ROLE: You are {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
PERMANENT TOPIC: "{scenario.get('title', 'English Practice')}" - {scenario.get('description', '')}.
STORY GUIDE: {story_guide}{angle_block}

SMART CONVERSATION DIRECTIVES & OPEN QUESTION MANDATE (MUST OBEY):
1. ACTIVE LISTENING & EMPATHETIC MIRRORING DIRECTIVE:
   - Begin your response by actively reflecting the user's emotion or specific idea ("I hear how excited/frustrated you are about...", "That's such a great point about..."). Extract and validate at least 1 specific point or feeling from what the user just said in your opening sentence before adding your own thoughts.
2. ALWAYS END YOUR TURN WITH AN OPEN-ENDED QUESTION:
   - NEVER end your turn with just an affirmative statement, agreement, or comment! If you do not ask a question, the conversation dies.
   - Every single response MUST conclude with a compelling, OPEN-ENDED question (asking 'why', 'how', 'what led to...', 'what would you do if...', etc.) that inspires the user to speak more and share stories/details.
3. AUTHENTIC DUOLINGO ASR PHONETIC CLARIFICATION ("did you mean X? Is that right?"):
   - The user's input is transcribed from a microphone via Speech-to-Text (ASR).
   - Because of learner pronunciation errors or accents, the ASR may transcribe homophones or acoustically similar words (e.g., 'important' -> 'in portal', 'think' -> 'sink', 'beach' -> 'bitch', 'sheet' -> 'seat').
   - NEVER complain or say you don't understand an STT misrecognition!
   - Instead, naturally GUESS the user's intended word, politely CONFIRM it in character in your spoken reply (e.g., "Oh, did you mean 'important'? Is that right? Because I agree that..."), and seamlessly continue your response based on your guess!
   - In "user_feedback", praise their effort and give a gentle tip in Vietnamese on pronouncing that word clearer so ASR hears it accurately next time.
4. EMPATHETIC FEEDBACK & GENTLE GRAMMAR/PRONUNCIATION GUIDANCE:
   - Provide warm, supportive feedback in "user_feedback" (grammar_status, corrected_text, native_phrasing). Encourage the learner's effort, celebrate progress, and explain corrections gently without being overly critical or pedantic.
5. STRICT ANTI-REPETITION (NEVER ASK PREVIOUSLY DISCUSSED TOPICS):
   - NEVER repeat a question or circle back to an idea that was already asked or answered in the CONVERSATION HISTORY! Re-asking the same question/topic in slightly different words ("hỏi tới hỏi lui 1 vấn đề") is a CRITICAL ERROR.
   - Actively drive the dialogue FORWARD to a brand-new angle, an unexpected plot twist, or a fresh sub-topic every single turn.
6. UNSCRIPTED OPEN STORYTELLING: Follow story guide: '{story_guide}'. Improvise dynamic plot twists, humorous surprises, and unscripted developments!
7. BE PROACTIVE WITH SUGGESTIONS: If the user asks for recommendations or choices, immediately provide specific, interesting suggestions with reasons, then ask an open-ended question about their preference.
{level_block}

TASK & OUTPUT FORMAT SPECIFICATION:
1. Reply in 100% STANDARD NATURAL ENGLISH as {character['name']}. Your response MUST be between {cfg['min_words']} and {cfg['max_words']} words total (strictly obeying Level {lvl} - {cfg['cefr']} length and vocabulary rules). Express a rich 2-3 sentence thought/reaction matching the Level {lvl} example above, and end with ONE FRESH OPEN-ENDED QUESTION.
2. REWRITE USER SENTENCE ACCURATELY: In "corrected_text", fix ONLY grammar/spelling of the user's sentence while preserving their exact meaning 100%. In "native_phrasing", show how a native speaker would say that exact thought.

Output JSON ONLY with Structured CoT fields (Keep natural_draft and vocab_check concise, max 20 words each):
{{
  "natural_draft": "Concise 1-sentence draft thought (max 20 words)",
  "vocab_check": "1-sentence ceiling audit verifying Level {lvl} bounds (max 20 words)",
  "final_response": "Polished response in 100% STANDARD NATURAL ENGLISH strictly obeying all level rules",
  "user_feedback": {{
    "grammar_status": "Clean & Clear" or brief fix note,
    "corrected_text": "Grammatically corrected version of user's sentence preserving exact meaning",
    "native_phrasing": "Direct native speaker English rewrite of user's sentence",
    "duo_reaction": "celebrate"|"happy"|"encouraging"
  }}
}}"""
    return prefix.strip()


def build_dynamic_turn_suffix(
    history_str: str,
    user_transcript: str,
    turn_count: int,
) -> str:
    """
    Constructs the Dynamic Turn Suffix that changes per turn.
    Placed strictly AFTER the static prefix to guarantee uninterrupted KV-cache hits.
    """
    clean_transcript = user_transcript.strip() if user_transcript else ""
    return f"""=== DYNAMIC TURN CONTEXT ===
TURN NUMBER: {turn_count}

CONVERSATION HISTORY SO FAR:
{history_str}
USER JUST SPOKE: "{clean_transcript}"

NOW RESPOND:
Following all permanent instructions and level constraints above, provide your turn response as JSON."""

