"""
app/prompt_constructor.py
==========================
Prompt Constructor Engine v1 (TASK-006).

Assembles User Profile context, target IELTS band level, retrieved RAG reference dialogues
(from app.retrieval), anti-verbatim repetition rules, follow-up question constraints,
and structured JSON output schema into an optimal System Prompt for the Conversational Agent (TASK-007).
"""

import logging
import time
from dataclasses import dataclass, field

from app.retrieval import RetrievedDialogue

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
    band_estimate: float
    topic_tag: str
    retrieved_dialogues: list[RetrievedDialogue] = field(default_factory=list)
    character_name: str = "Lily"
    difficulty_adjustment: str = "hold"


def construct_system_prompt(context: PromptContext) -> str:
    """
    Constructs the complete System Prompt for the Conversational Agent.
    Assembly execution time target: < 5ms.
    """
    start_time = time.perf_counter()

    char_name = context.character_name or "Lily"
    band = round(context.band_estimate, 1)
    topic = context.topic_tag or "general_conversation"

    sections: list[str] = []

    # 1. Persona & Identity
    sections.append(
        f"### PERSONA & ROLE\n"
        f"You are {char_name}, a friendly, encouraging, and highly competent AI English speaking partner.\n"
        f"Your goal is to conduct an interactive IELTS Speaking-style dialogue with the user."
    )

    # 2. Target Profile & Context
    sections.append(
        f"### CONVERSATION CONTEXT\n"
        f"- Target IELTS Band Level: {band}\n"
        f"- Topic: {topic}\n"
        f"- Current Difficulty Signal: {context.difficulty_adjustment}"
    )

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
    sections.append(
        f"### BEHAVIORAL DIRECTIVES & CONSTRAINTS\n"
        f"1. ANTI-VERBATIM REPETITION: DO NOT copy sentences or phrases verbatim from the reference dialogues. Use them as inspiration for vocabulary level and discourse depth.\n"
        f"2. FOLLOW-UP QUESTION REQUIREMENT: You MUST end your response (`ai_utterance`) with exactly 1 natural follow-up question appropriate for Band {band}.\n"
        f"3. BAND APPROPRIATENESS: Adjust your vocabulary complexity and sentence structures to match or slightly stretch Band {band}.\n"
        f"4. NATURALITY: Speak in conversational, spoken English. Avoid robotic or textbook-sounding phrases."
    )

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
