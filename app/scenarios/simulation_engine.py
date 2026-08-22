"""
Real-World Roleplay Simulation Engine (TASK-019)
Manages dynamic branching (low_band vs high_band), evaluation hooks, adaptive dialogue retrieval,
and system prompt directives for real-world roleplay scenarios (Template C).
"""

import json
import logging
import re
from dataclasses import asdict
from typing import Any

from app.db import _fetch_all_dicts, _fetch_one_dict, get_db_connection
from app.retrieval import compute_band_window, retrieve_dialogues
from app.scenarios import get_scenario

logger = logging.getLogger(__name__)


class RealWorldSimulationEngine:
    """Simulation engine for managing roleplay scenarios, dynamic branching, and evaluation hooks."""

    def __init__(self, db_conn: Any = None):
        self._conn = db_conn

    def _get_connection(self) -> Any:
        if self._conn is not None:
            return self._conn
        return get_db_connection()

    def get_active_scenario(
        self, scenario_id: str, conn: Any | None = None
    ) -> dict[str, Any]:
        """
        Load scenario metadata from DB (content_units, scenarios, scenario_branches, evaluation_hooks)
        or fallback to static scenarios.
        """
        active_conn = conn or self._get_connection()
        scenario_data: dict[str, Any] | None = None

        if active_conn is not None:
            try:
                cursor = active_conn.cursor()
                # Query content_units & scenarios tables
                cursor.execute(
                    """
                    SELECT cu.id as content_unit_id, cu.title, cu.topic_tags, cu.target_band_min,
                           cu.target_band_max, cu.register, s.id as scenario_id, s.setting,
                           s.ai_role, s.user_role, s.grammar_required, s.vocabulary_core,
                           s.vocabulary_stretch
                    FROM content_units cu
                    JOIN scenarios s ON s.content_unit_id = cu.id
                    WHERE cu.id = ? OR s.id = ? OR cu.title LIKE ?
                    LIMIT 1
                    """,
                    (scenario_id, scenario_id, f"%{scenario_id}%"),
                )
                row = _fetch_one_dict(cursor)
                if row:
                    scenario_pk = row["scenario_id"]

                    # Fetch scenario branches
                    cursor.execute(
                        """
                        SELECT id, branch_type, condition_rule, ai_response_style, example_text
                        FROM scenario_branches
                        WHERE scenario_id = ?
                        """,
                        (scenario_pk,),
                    )
                    branches = _fetch_all_dicts(cursor)

                    # Fetch evaluation hooks
                    cursor.execute(
                        """
                        SELECT id, trigger_condition, ai_reaction
                        FROM evaluation_hooks
                        WHERE scenario_id = ?
                        """,
                        (scenario_pk,),
                    )
                    hooks = _fetch_all_dicts(cursor)

                    def parse_json_list(val: Any) -> list[str]:
                        if isinstance(val, list):
                            return val
                        if isinstance(val, str) and val.strip():
                            try:
                                parsed = json.loads(val)
                                return parsed if isinstance(parsed, list) else []
                            except Exception:
                                return [val]
                        return []

                    scenario_data = {
                        "id": row["scenario_id"] or row["content_unit_id"],
                        "content_unit_id": row["content_unit_id"],
                        "title": row["title"],
                        "setting": row["setting"] or f"Roleplay setting for {row['title']}",
                        "ai_role": row["ai_role"] or "Roleplay Conversation Partner",
                        "user_role": row["user_role"] or "Learner",
                        "register": row["register"] or "neutral",
                        "target_band_min": row["target_band_min"] or 4.0,
                        "target_band_max": row["target_band_max"] or 9.0,
                        "grammar_required": parse_json_list(row["grammar_required"]),
                        "vocabulary_core": parse_json_list(row["vocabulary_core"]),
                        "vocabulary_stretch": parse_json_list(row["vocabulary_stretch"]),
                        "branches": branches,
                        "evaluation_hooks": hooks,
                        "is_db": True,
                    }
            except Exception as e:
                logger.warning(f"[simulation_engine] DB fetch warning for '{scenario_id}': {e}")

        # Fallback to static scenario if not found in DB
        if not scenario_data:
            static_sc = get_scenario(scenario_id) or get_scenario("everyday_chat") or {}
            scenario_data = {
                "id": static_sc.get("id", scenario_id),
                "title": static_sc.get("title", scenario_id.capitalize()),
                "setting": static_sc.get("description") or static_sc.get("open_story_guide") or "Everyday real-world situation.",
                "ai_role": "Interactive Roleplay Partner",
                "user_role": "English Learner",
                "register": "neutral",
                "target_band_min": 4.0,
                "target_band_max": 9.0,
                "grammar_required": [],
                "vocabulary_core": static_sc.get("suggested_vocabulary", []),
                "vocabulary_stretch": [],
                "branches": [],
                "evaluation_hooks": [],
                "is_db": False,
            }

        return scenario_data

    def select_branch(
        self,
        scenario: dict[str, Any] | str,
        user_band: float,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """
        Dynamically select branch ('low_band' vs 'high_band') based on user's current band rating.
        """
        if isinstance(scenario, str):
            sc_dict = self.get_active_scenario(scenario, conn)
        else:
            sc_dict = scenario

        branches = sc_dict.get("branches", [])
        target_branch_type = "low_band" if user_band < 6.0 else "high_band"

        # Check DB defined branches
        for b in branches:
            b_type = b.get("branch_type", "").lower()
            if b_type == target_branch_type:
                return {
                    "branch_type": b_type,
                    "condition_rule": b.get("condition_rule") or f"user_band {'<' if user_band < 6.0 else '>='} 6.0",
                    "ai_response_style": b.get("ai_response_style", ""),
                    "example_text": b.get("example_text", ""),
                }

        # Fallback default branch directives if none in DB
        if user_band < 6.0:
            return {
                "branch_type": "low_band",
                "condition_rule": "user_band < 6.0",
                "ai_response_style": (
                    "Supportive & patient. Use accessible vocabulary, clear phrasing, and shorter sentences. "
                    "Provide gentle guidance and simple follow-up questions."
                ),
                "example_text": "That sounds interesting! Could you tell me more about what happened?",
            }

        return {
            "branch_type": "high_band",
            "condition_rule": "user_band >= 6.0",
            "ai_response_style": (
                "Challenging & sophisticated. Incorporate idiomatic expressions, complex sentence structures, "
                "and ask open-ended analytical or follow-up questions to stretch the user's proficiency."
            ),
            "example_text": "Indeed, that perspective highlights a key dilemma. How would you justify your approach?",
        }

    def evaluate_hooks(
        self,
        scenario: dict[str, Any] | str,
        user_utterance: str,
        conn: Any | None = None,
    ) -> list[dict[str, Any]]:
        """
        Evaluate user utterance against scenario evaluation hooks and target grammar/vocabulary.
        Returns list of triggered hook reactions.
        """
        if not user_utterance or not user_utterance.strip():
            return []

        if isinstance(scenario, str):
            sc_dict = self.get_active_scenario(scenario, conn)
        else:
            sc_dict = scenario

        triggered: list[dict[str, Any]] = []
        user_text_lower = user_utterance.lower()

        # 1. Custom DB evaluation hooks
        hooks = sc_dict.get("evaluation_hooks", [])
        for h in hooks:
            cond = (h.get("trigger_condition") or "").strip()
            reaction = h.get("ai_reaction") or ""
            if not cond:
                continue

            matched = False
            # Check simple string or regex
            if cond.lower() in user_text_lower:
                matched = True
            else:
                try:
                    if re.search(r"\b" + re.escape(cond) + r"\b", user_text_lower, re.IGNORECASE):
                        matched = True
                except Exception:
                    pass

            if matched:
                triggered.append({
                    "id": h.get("id", "hook_custom"),
                    "trigger_condition": cond,
                    "ai_reaction": reaction,
                    "type": "custom_hook",
                })

        # 2. Target vocabulary / grammar usage detection
        target_vocab = sc_dict.get("vocabulary_core", []) + sc_dict.get("vocabulary_stretch", [])
        for word in target_vocab:
            word_clean = word.strip().lower()
            if len(word_clean) > 2 and word_clean in user_text_lower:
                triggered.append({
                    "id": f"vocab_{word_clean}",
                    "trigger_condition": f"Used target vocabulary: '{word}'",
                    "ai_reaction": f"Acknowledge natural usage of target term '{word}' and seamlessly continue the roleplay.",
                    "type": "target_vocab",
                })

        target_grammar = sc_dict.get("grammar_required", [])
        for g_rule in target_grammar:
            g_clean = g_rule.strip().lower()
            if len(g_clean) > 2 and g_clean in user_text_lower:
                triggered.append({
                    "id": f"grammar_{g_clean}",
                    "trigger_condition": f"Used target grammar structure: '{g_rule}'",
                    "ai_reaction": f"Acknowledge appropriate use of '{g_rule}' structure in conversation.",
                    "type": "target_grammar",
                })

        return triggered

    def get_scenario_retrieval_context(
        self,
        scenario_id: str,
        user_id: str,
        user_band: float,
        difficulty_adjustment: str = "hold",
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve reference dialogue lines filtered for the scenario via the adaptive retrieval layer (TASK-015).
        """
        try:
            active_conn = conn or self._get_connection()
            band_min, band_max = compute_band_window(user_band, difficulty_adjustment)
            dialogues = retrieve_dialogues(
                user_id=user_id,
                topic_tags=scenario_id,
                band_min=band_min,
                band_max=band_max,
                conn=active_conn,
            )
            dialogues_dict = [
                asdict(d) if hasattr(d, "__dataclass_fields__") else (d if isinstance(d, dict) else {})
                for d in dialogues
            ]
            return {"scenario_id": scenario_id, "dialogues": dialogues_dict}
        except Exception as e:
            logger.warning(f"[simulation_engine] Retrieval error for '{scenario_id}': {e}")
            return {"scenario_id": scenario_id, "dialogues": []}

    def build_simulation_directives(
        self,
        scenario_id: str,
        user_id: str,
        user_band: float,
        user_utterance: str = "",
        difficulty_adjustment: str = "hold",
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """
        Assemble roleplay instructions, branch directives, triggered hook reactions, and retrieval context
        into a structured directive package for the Prompt Constructor.
        """
        scenario = self.get_active_scenario(scenario_id, conn)
        branch = self.select_branch(scenario, user_band, conn)
        triggered_hooks = self.evaluate_hooks(scenario, user_utterance, conn) if user_utterance else []
        retrieval_ctx = self.get_scenario_retrieval_context(
            scenario_id, user_id, user_band, difficulty_adjustment, conn
        )

        lines = [
            f"=== REAL-WORLD ROLEPLAY SIMULATION: {scenario.get('title', 'Scenario')} ===",
            f"Setting: {scenario.get('setting', 'Roleplay scenario')}",
            f"AI Role: {scenario.get('ai_role', 'Partner')} | User Role: {scenario.get('user_role', 'Learner')}",
            f"Register / Tone: {scenario.get('register', 'neutral')}",
            f"Active Branch Mode ({branch['branch_type'].upper()}): {branch['ai_response_style']}",
        ]

        if scenario.get("grammar_required"):
            lines.append(f"Target Grammar Structures: {', '.join(scenario['grammar_required'])}")
        if scenario.get("vocabulary_core"):
            lines.append(f"Target Vocabulary (Core): {', '.join(scenario['vocabulary_core'])}")
        if scenario.get("vocabulary_stretch"):
            lines.append(f"Target Vocabulary (Stretch): {', '.join(scenario['vocabulary_stretch'])}")

        if triggered_hooks:
            lines.append("Triggered Evaluation Hooks:")
            for h in triggered_hooks:
                lines.append(f"  - [{h['trigger_condition']}] -> Reaction: {h['ai_reaction']}")

        dialogues = retrieval_ctx.get("dialogues", [])
        if dialogues:
            lines.append("Reference Roleplay Dialogues:")
            for d in dialogues[:3]:
                lines.append(f"  * AI: {d.get('ai_line', '')} | Model Answer: {d.get('user_model_answer', '')}")

        directives_prompt = "\n".join(lines)

        return {
            "scenario_id": scenario_id,
            "title": scenario.get("title"),
            "setting": scenario.get("setting"),
            "ai_role": scenario.get("ai_role"),
            "user_role": scenario.get("user_role"),
            "branch": branch,
            "triggered_hooks": triggered_hooks,
            "retrieved_dialogues": dialogues,
            "directives_prompt": directives_prompt,
        }


# Convenience module-level instances & functions
default_engine = RealWorldSimulationEngine()


def get_active_scenario(scenario_id: str, conn: Any | None = None) -> dict[str, Any]:
    return default_engine.get_active_scenario(scenario_id, conn)


def select_branch(
    scenario: dict[str, Any] | str, user_band: float, conn: Any | None = None
) -> dict[str, Any]:
    return default_engine.select_branch(scenario, user_band, conn)


def evaluate_hooks(
    scenario: dict[str, Any] | str, user_utterance: str, conn: Any | None = None
) -> list[dict[str, Any]]:
    return default_engine.evaluate_hooks(scenario, user_utterance, conn)


def build_simulation_directives(
    scenario_id: str,
    user_id: str,
    user_band: float,
    user_utterance: str = "",
    difficulty_adjustment: str = "hold",
    conn: Any | None = None,
) -> dict[str, Any]:
    return default_engine.build_simulation_directives(
        scenario_id, user_id, user_band, user_utterance, difficulty_adjustment, conn
    )
