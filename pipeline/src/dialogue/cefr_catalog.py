"""Pre-Packaged CEFR A1-B2 Standard Dialogue Scenario Catalog.

Ships built-in with standard communicative language teaching scenarios
so users and developers do NOT need to download or inject external documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class DialogueNode:
    """Represents a discrete state node in the dialogue graph."""

    node_id: str
    prompt: str
    expected_keywords: list[str] = field(default_factory=list)
    intent: str = "general_response"
    response_template: str = ""
    slot_keys: list[str] = field(default_factory=list)
    next_node_id: Optional[str] = None


@dataclass(slots=True)
class DialogueScenario:
    """Represents an entire conversation scenario with a dialogue decision tree."""

    scenario_id: str
    title: str
    cefr_level: str  # A1, A2, B1, B2
    topic: str
    initial_prompt: str
    nodes: dict[str, DialogueNode] = field(default_factory=dict)
    default_fallback_response: str = (
        "Could you please tell me more about that, or clarify your answer?"
    )


class CEFRScenarioCatalog:
    """In-memory repository of standard language learning scenarios."""

    _SCENARIOS: dict[str, DialogueScenario] = {}

    @classmethod
    def initialize_defaults(cls) -> None:
        """Loads standard CEFR scenarios into memory."""
        if cls._SCENARIOS:
            return

        # 1. Cafe Order (A1-A2)
        cafe_nodes = {
            "order_drink": DialogueNode(
                node_id="order_drink",
                prompt="Welcome to Sunshine Cafe! What would you like to drink today?",
                expected_keywords=["coffee", "latte", "espresso", "tea", "cappuccino", "juice", "water"],
                intent="order_drink",
                response_template="A {item}! Excellent choice. What size would you like: small, medium, or large?",
                slot_keys=["item"],
                next_node_id="select_size",
            ),
            "select_size": DialogueNode(
                node_id="select_size",
                prompt="What size would you like: small, medium, or large?",
                expected_keywords=["small", "medium", "large", "regular"],
                intent="select_size",
                response_template="Got it, a {size} size. Would you like to add milk or sugar?",
                slot_keys=["size"],
                next_node_id="customization",
            ),
            "customization": DialogueNode(
                node_id="customization",
                prompt="Would you like to add milk or sugar?",
                expected_keywords=["milk", "sugar", "sweetener", "nothing", "black", "no"],
                intent="customization",
                response_template="Perfect. Your drink will be ready in just a few minutes. Anything else?",
                slot_keys=["custom"],
                next_node_id=None,
            ),
        }
        cls._SCENARIOS["cafe_order"] = DialogueScenario(
            scenario_id="cafe_order",
            title="Ordering at a Coffee Shop",
            cefr_level="A1",
            topic="Food & Dining",
            initial_prompt="Welcome to Sunshine Cafe! What would you like to drink today?",
            nodes=cafe_nodes,
            default_fallback_response="I'm sorry, I didn't quite catch your order. Could you tell me what drink you would like, such as coffee or tea?",
        )

        # 2. Hotel Check-in (A2-B1)
        hotel_nodes = {
            "checkin_start": DialogueNode(
                node_id="checkin_start",
                prompt="Good evening! Welcome to the Grand Palace Hotel. How may I assist you?",
                expected_keywords=["check in", "reservation", "booking", "room", "have a room"],
                intent="check_in",
                response_template="Welcome! May I please have your full name and reservation number?",
                slot_keys=["name"],
                next_node_id="provide_name",
            ),
            "provide_name": DialogueNode(
                node_id="provide_name",
                prompt="May I please have your name?",
                expected_keywords=["name", "i am", "my name", "reservation"],
                intent="provide_name",
                response_template="Thank you, {name}. Your deluxe room on the 5th floor is ready. Here is your room card!",
                slot_keys=["name"],
                next_node_id=None,
            ),
        }
        cls._SCENARIOS["hotel_checkin"] = DialogueScenario(
            scenario_id="hotel_checkin",
            title="Checking into a Hotel",
            cefr_level="A2",
            topic="Travel & Hospitality",
            initial_prompt="Good evening! Welcome to the Grand Palace Hotel. How may I assist you?",
            nodes=hotel_nodes,
            default_fallback_response="Could you please confirm if you have an existing room reservation with us?",
        )

        # 3. Asking Directions (A2-B1)
        direction_nodes = {
            "ask_direction": DialogueNode(
                node_id="ask_direction",
                prompt="Excuse me, you look a bit lost. Where are you trying to go?",
                expected_keywords=["museum", "station", "train", "airport", "hospital", "bank", "library"],
                intent="ask_location",
                response_template="The {destination} is just two blocks down this street on your left. Can I help you with anything else?",
                slot_keys=["destination"],
                next_node_id=None,
            ),
        }
        cls._SCENARIOS["directions"] = DialogueScenario(
            scenario_id="directions",
            title="Asking for Directions in the City",
            cefr_level="A2",
            topic="City Navigation",
            initial_prompt="Excuse me, you look a bit lost. Where are you trying to go?",
            nodes=direction_nodes,
            default_fallback_response="Which place or landmark are you trying to reach?",
        )

    @classmethod
    def get_scenario(cls, scenario_id: str) -> Optional[DialogueScenario]:
        """Retrieves a scenario by its ID, initializing catalog if empty."""
        cls.initialize_defaults()
        return cls._SCENARIOS.get(scenario_id)

    @classmethod
    def register_scenario(cls, scenario: DialogueScenario) -> None:
        """Registers a compiled scenario into the catalog."""
        cls._SCENARIOS[scenario.scenario_id] = scenario

    @classmethod
    def list_scenarios(cls) -> list[str]:
        cls.initialize_defaults()
        return list(cls._SCENARIOS.keys())
