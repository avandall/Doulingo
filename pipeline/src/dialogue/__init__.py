"""Dialogue and Phonetic Evaluation Bounded Context.

Provides in-memory dialogue FSM (<20MB RAM), pre-packaged CEFR A1-B2 scenario catalog,
automated offline scenario compiler, and phoneme-level acoustic evaluation.
"""

from .cefr_catalog import CEFRScenarioCatalog, DialogueNode, DialogueScenario
from .fsm_engine import DialogueFSMEngine, FSMResponse
from .phonetic_evaluator import ErrorType, PhonemeFeedback, PhoneticEvaluator
from .scenario_compiler import ScenarioCompiler

__all__ = [
    "CEFRScenarioCatalog",
    "DialogueFSMEngine",
    "DialogueNode",
    "DialogueScenario",
    "ErrorType",
    "FSMResponse",
    "PhonemeFeedback",
    "PhoneticEvaluator",
    "ScenarioCompiler",
]
