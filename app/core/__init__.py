"""Core Conversation Engine & Agent Orchestration"""
from app.core.level_config import LEVEL_CONFIGS, SCENARIO_ANGLES
from app.core.ai_engine import ai_engine, AIEngine
from app.core.conversational_agent import ConversationalAgent
from app.core.adaptive_engine import BanditDifficultyEngine
from app.core.persona_memory import (
    PERSONA_REGISTRY,
    extract_entities_from_turn,
    format_entity_memory_for_prompt,
    get_persona_identity,
    get_user_entity_memory,
    save_user_entity_memory,
    update_user_memory_from_turn,
)
from app.core.anti_repetition import (
    RepetitionCheckResult,
    check_repetition,
    cosine_similarity,
    get_embedding,
)
