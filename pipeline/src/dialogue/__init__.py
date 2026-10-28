"""Dialogue and Phonetic Evaluation Bounded Context.

Provides in-memory dialogue FSM (<20MB RAM), pre-packaged CEFR A1-B2 scenario catalog,
automated offline scenario compiler, and phoneme-level acoustic evaluation.
"""

from .cefr_catalog import CEFRScenarioCatalog, DialogueScenario, DialogueNode
from .scenario_compiler import ScenarioCompiler
from .fsm_engine import DialogueFSMEngine, FSMResponse
from .phonetic_evaluator import PhoneticEvaluator, PhonemeFeedback, ErrorType

__all__ = [
    "CEFRScenarioCatalog",
    "DialogueScenario",
    "DialogueNode",
    "ScenarioCompiler",
    "DialogueFSMEngine",
    "FSMResponse",
    "PhoneticEvaluator",
    "PhonemeFeedback",
    "ErrorType",
]
