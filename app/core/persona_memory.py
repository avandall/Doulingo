"""
app/persona_memory.py
======================
AI Persona Identity & Long-Term Entity Memory System (TASK-017).

Provides:
1. Long-term entity memory extraction from user turns (hobbies, occupation, personal events, preferences, background facts).
2. Persistence of user entity memory in user_profile DB table (JSON storage).
3. Prompt injection helper to present structured entity summary into system prompt.
4. Character persona identity configuration.
"""

import json
import logging
import re
import time
from typing import Any

from app.storage.db import get_db_connection, init_db

log = logging.getLogger(__name__)

# Default Persona Definitions
PERSONA_REGISTRY: dict[str, dict[str, Any]] = {
    "Lily": {
        "name": "Lily",
        "role": "Friendly English Speaking Coach",
        "personality": "Warm, encouraging, curious, and supportive",
        "accent_style": "Standard American English",
        "trait": "Loves asking thoughtful follow-up questions and remembering personal details shared by the user."
    },
    "Rajesh": {
        "name": "Rajesh",
        "role": "IELTS Examiner & Tech Specialist",
        "personality": "Professional, articulate, insightful, and structured",
        "accent_style": "Clear International English",
        "trait": "Focuses on topic depth, formal vocabulary, and nuanced discussion."
    },
    "Emma": {
        "name": "Emma",
        "role": "Casual Conversation Partner",
        "personality": "Upbeat, energetic, humorous, and empathetic",
        "accent_style": "British English",
        "trait": "Uses authentic everyday idioms and relatable stories."
    }
}


def get_persona_identity(character_name: str = "Lily") -> dict[str, Any]:
    """
    Returns the character persona metadata and identity configuration.
    """
    normalized_name = character_name.capitalize()
    return PERSONA_REGISTRY.get(
        normalized_name,
        {
            "name": character_name,
            "role": "AI English Partner",
            "personality": "Friendly, encouraging, and clear",
            "accent_style": "Standard English",
            "trait": "Helpful and conversational."
        }
    )


# Key phrase extraction patterns for heuristic entity extraction
PATTERNS: list[tuple[str, str]] = [
    # Hobbies & Interests
    (r"(?:i (?:really )?(?:love|like|enjoy|am into|am passionate about) ([^.,!?]+))", "hobbies"),
    (r"(?:my (?:favorite|main) (?:hobby|pastime|activity) is ([^.,!?]+))", "hobbies"),
    (r"(?:in my free time,? i (?:usually )?([^.,!?]+))", "hobbies"),

    # Occupation & Study
    (r"(?:i work as (?:a|an) ([^.,!?]+))", "occupation"),
    (r"(?:i am (?:a|an) ([^.,!?]+))", "occupation"),
    (r"(?:my job is ([^.,!?]+))", "occupation"),
    (r"(?:i study ([^.,!?]+))", "occupation"),
    (r"(?:my major is ([^.,!?]+))", "occupation"),

    # Personal Events & Plans
    (r"(?:i am planning to ([^.,!?]+))", "personal_events"),
    (r"(?:next (?:week|month|year),? i (?:will|am going to) ([^.,!?]+))", "personal_events"),
    (r"(?:recently,? i ([^.,!?]+))", "personal_events"),
    (r"(?:last (?:week|month|year),? i ([^.,!?]+))", "personal_events"),

    # Preferences & Opinions
    (r"(?:i prefer ([^.,!?]+))", "preferences"),
    (r"(?:i (?:don't|do not) (?:like|enjoy) ([^.,!?]+))", "preferences"),
    (r"(?:my favorite ([^.,!?]+) is ([^.,!?]+))", "preferences"),

    # Locations
    (r"(?:i live in ([^.,!?]+))", "locations"),
    (r"(?:i (?:am from|come from) ([^.,!?]+))", "locations"),
    (r"(?:i visited ([^.,!?]+))", "locations"),
]


STOP_CONJUNCTIONS_REGEX = re.compile(
    r"\s+(?:and|but|or|so|because|while|in my|daily|also|with|for)\b.*$",
    flags=re.IGNORECASE
)


def _clean_entity_phrase(phrase: str) -> str:
    cleaned = STOP_CONJUNCTIONS_REGEX.sub("", phrase).strip()
    return cleaned


def extract_entities_from_turn(
    user_utterance: str,
    existing_memory: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Extracts key user facts (hobbies, occupation, events, preferences, locations)
    from a user's utterance and merges them into existing_memory.
    Execution target: < 15ms.
    """
    start_time = time.perf_counter()

    if existing_memory is None:
        memory: dict[str, Any] = {}
    else:
        # Create shallow/deep copy of dict to avoid mutating original unexpected
        memory = {k: (list(v) if isinstance(v, list) else v) for k, v in existing_memory.items()}

    if not user_utterance or not user_utterance.strip():
        return memory

    text = user_utterance.strip()
    lowered = text.lower()

    extracted: dict[str, list[str]] = {}

    for pattern, category in PATTERNS:
        matches = re.findall(pattern, lowered)
        for match in matches:
            if isinstance(match, tuple):
                raw_item = " ".join([m.strip() for m in match if m.strip()])
            else:
                raw_item = match.strip()

            extracted_item = _clean_entity_phrase(raw_item)

            # Filter noise / overly long / trivial matches
            if 2 <= len(extracted_item) <= 60:
                if category not in extracted:
                    extracted[category] = []
                if extracted_item not in extracted[category]:
                    extracted[category].append(extracted_item)

    # Merge into memory structure
    for category, items in extracted.items():
        if category not in memory:
            memory[category] = []
        elif not isinstance(memory[category], list):
            memory[category] = [str(memory[category])]

        for item in items:
            # Deduplicate case-insensitively
            existing_lowered = [str(x).lower() for x in memory[category]]
            if item.lower() not in existing_lowered:
                memory[category].append(item)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    if elapsed_ms > 15.0:
        log.warning("Entity extraction took %.2f ms (target < 15ms)", elapsed_ms)

    return memory


def get_user_entity_memory(user_id: str, conn: Any = None) -> dict[str, Any]:
    """
    Retrieves user entity memory dictionary from user_profile table.
    Returns empty dict {} if user or entity memory not found.
    """
    should_close = False
    if conn is None:
        init_db()
        conn = get_db_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_memory FROM user_profile WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or not row["entity_memory"]:
            return {}

        raw_memory = row["entity_memory"]
        if isinstance(raw_memory, dict):
            return raw_memory

        parsed = json.loads(raw_memory)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as e:
        log.error("Failed to read user entity memory for %s: %s", user_id, e)
        return {}
    finally:
        if should_close and conn:
            conn.close()


def save_user_entity_memory(
    user_id: str,
    entity_memory: dict[str, Any],
    conn: Any = None
) -> None:
    """
    Saves or updates user entity memory dict in user_profile table.
    """
    should_close = False
    if conn is None:
        init_db()
        conn = get_db_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        json_str = json.dumps(entity_memory, ensure_ascii=False)

        # Check if user row exists
        cursor.execute("SELECT user_id FROM user_profile WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                "UPDATE user_profile SET entity_memory = ?, updated_at = datetime('now') WHERE user_id = ?",
                (json_str, user_id)
            )
        else:
            cursor.execute(
                """INSERT INTO user_profile (user_id, entity_memory, updated_at)
                   VALUES (?, ?, datetime('now'))""",
                (user_id, json_str)
            )

        conn.commit()
    except Exception as e:
        log.error("Failed to save user entity memory for %s: %s", user_id, e)
        raise
    finally:
        if should_close and conn:
            conn.close()


def update_user_memory_from_turn(
    user_id: str,
    user_utterance: str,
    conn: Any = None
) -> dict[str, Any]:
    """
    Convenience workflow: reads user's entity memory, extracts new entities
    from user_utterance, persists updated memory, and returns the updated memory.
    """
    existing_mem = get_user_entity_memory(user_id, conn=conn)
    updated_mem = extract_entities_from_turn(user_utterance, existing_memory=existing_mem)
    save_user_entity_memory(user_id, updated_mem, conn=conn)
    return updated_mem


def format_entity_memory_for_prompt(entity_memory: dict[str, Any] | list[Any] | None) -> str:
    """
    Formats user entity memory into structured bullet points for system prompt injection.
    Returns empty string if memory is empty.
    """
    if not entity_memory:
        return ""

    if isinstance(entity_memory, list):
        if not entity_memory:
            return ""
        items = [f"- {item}" for item in entity_memory]
        return "### USER ENTITY MEMORY & PERSONAL FACTS\n" + "\n".join(items)

    lines: list[str] = []

    category_labels = {
        "hobbies": "Hobbies & Interests",
        "occupation": "Occupation & Field of Study",
        "personal_events": "Personal Events & Future Plans",
        "preferences": "Preferences & Opinions",
        "locations": "Locations & Background",
        "general_facts": "General User Facts"
    }

    for cat_key, label in category_labels.items():
        if entity_memory.get(cat_key):
            val = entity_memory[cat_key]
            if isinstance(val, list):
                val_str = ", ".join(str(x) for x in val)
            else:
                val_str = str(val)
            lines.append(f"- {label}: {val_str}")

    # Process any leftover keys not in standard labels
    for key, val in entity_memory.items():
        if key not in category_labels and val:
            if isinstance(val, list):
                val_str = ", ".join(str(x) for x in val)
            else:
                val_str = str(val)
            lines.append(f"- {key.capitalize()}: {val_str}")

    if not lines:
        return ""

    return "### USER ENTITY MEMORY & PERSONAL FACTS\n" + "\n".join(lines)
