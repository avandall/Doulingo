"""Automated Offline Scenario Compiler.

Enables content creators or LLM pipelines to decompose a raw topic into a
structured DialogueScenario schema that can be loaded into the FSM engine.
"""

from __future__ import annotations

import json
from typing import Any
from .cefr_catalog import DialogueScenario, DialogueNode, CEFRScenarioCatalog


class ScenarioCompiler:
    """Compiles JSON or dictionary definitions into validated DialogueScenario instances."""

    @staticmethod
    def compile_from_dict(data: dict[str, Any]) -> DialogueScenario:
        """Validates and compiles a dictionary into a DialogueScenario."""
        scenario_id = data["scenario_id"]
        title = data.get("title", scenario_id.replace("_", " ").title())
        cefr_level = data.get("cefr_level", "A2")
        topic = data.get("topic", "General Conversation")
        initial_prompt = data.get("initial_prompt", "Hello! How can I help you?")
        default_fallback = data.get(
            "default_fallback_response",
            "Could you please clarify your answer or say that again?",
        )

        nodes: dict[str, DialogueNode] = {}
        for node_raw in data.get("nodes", []):
            node_id = node_raw["node_id"]
            node = DialogueNode(
                node_id=node_id,
                prompt=node_raw.get("prompt", ""),
                expected_keywords=node_raw.get("expected_keywords", []),
                intent=node_raw.get("intent", "general_response"),
                response_template=node_raw.get("response_template", ""),
                slot_keys=node_raw.get("slot_keys", []),
                next_node_id=node_raw.get("next_node_id"),
            )
            nodes[node_id] = node

        scenario = DialogueScenario(
            scenario_id=scenario_id,
            title=title,
            cefr_level=cefr_level,
            topic=topic,
            initial_prompt=initial_prompt,
            nodes=nodes,
            default_fallback_response=default_fallback,
        )
        CEFRScenarioCatalog.register_scenario(scenario)
        return scenario

    @classmethod
    def compile_from_json(cls, json_str: str) -> DialogueScenario:
        """Compiles from a JSON serialized string."""
        data = json.loads(json_str)
        return cls.compile_from_dict(data)
