"""Tests for Dialogue and Phonetic Evaluation Bounded Context."""

import time
import pytest
from pipeline.src.dialogue.cefr_catalog import CEFRScenarioCatalog
from pipeline.src.dialogue.scenario_compiler import ScenarioCompiler
from pipeline.src.dialogue.fsm_engine import DialogueFSMEngine
from pipeline.src.dialogue.phonetic_evaluator import PhoneticEvaluator, ErrorType


class TestDialogueFSMEngine:
    def test_process_turn_sub_15ms_latency(self):
        engine = DialogueFSMEngine()
        t0 = time.time()
        res = engine.process_turn("cafe_order", "order_drink", "I would like a hot latte please")
        latency_ms = (time.time() - t0) * 1000.0

        assert latency_ms < 15.0  # Must be sub-15ms
        assert res.matched_intent == "order_drink"
        assert res.detected_slots.get("item") == "latte"
        assert "latte" in res.reply_text
        assert res.next_node_id == "select_size"
        assert res.is_fallback is False

    def test_dialogue_transition_to_size(self):
        engine = DialogueFSMEngine()
        res = engine.process_turn("cafe_order", "select_size", "Make it a medium size please")
        assert res.matched_intent == "select_size"
        assert res.detected_slots.get("size") == "medium"
        assert "medium" in res.reply_text
        assert res.next_node_id == "customization"

    def test_default_fallback_node_on_unrecognized_input(self):
        engine = DialogueFSMEngine()
        # Say something completely nonsensical
        res = engine.process_turn("cafe_order", "order_drink", "xyz bla")
        assert res.is_fallback is True
        assert res.matched_intent in ("default_fallback", "scenario_fallback")
        # Ensure fallback provides clear guided prompt
        assert "coffee or tea" in res.reply_text

    def test_automated_scenario_compiler(self):
        scenario_data = {
            "scenario_id": "taxi_ride",
            "title": "Taking a Taxi",
            "cefr_level": "A2",
            "topic": "Transport",
            "initial_prompt": "Where can I take you today?",
            "nodes": [
                {
                    "node_id": "destination",
                    "prompt": "Where can I take you today?",
                    "expected_keywords": ["airport", "downtown", "station"],
                    "intent": "set_destination",
                    "response_template": "Sure thing! Heading to {dest}. Traffic looks good.",
                    "slot_keys": ["dest"],
                    "next_node_id": None,
                }
            ],
            "default_fallback_response": "Which location would you like to go to?",
        }
        compiled = ScenarioCompiler.compile_from_dict(scenario_data)
        assert compiled.scenario_id == "taxi_ride"

        engine = DialogueFSMEngine()
        res = engine.process_turn("taxi_ride", "destination", "Please drive me to the airport")
        assert res.detected_slots.get("dest") == "airport"
        assert "Heading to airport" in res.reply_text


class TestPhoneticEvaluator:
    def test_substitution_articulatory_guidance(self):
        fb = PhoneticEvaluator.analyze_phoneme("think", "/θ/", "/t/")
        assert fb.error_type == ErrorType.SUBSTITUTION
        assert fb.target_phoneme == "/θ/"
        assert fb.detected_phoneme == "/t/"
        assert "Tongue position error" in fb.guidance
        assert "teeth" in fb.guidance

    def test_final_consonant_deletion(self):
        fb = PhoneticEvaluator.analyze_phoneme("past", "/t/", None)
        assert fb.error_type == ErrorType.DELETION
        assert fb.detected_phoneme is None
        assert "Ending sound dropped" in fb.guidance

    def test_accurate_phoneme_evaluation(self):
        fb = PhoneticEvaluator.analyze_phoneme("cat", "/k/", "/k/")
        assert fb.error_type == ErrorType.NONE
        assert fb.guidance == "Pronounced accurately."

    def test_full_utterance_evaluation_scoring(self):
        targets = [("I", "/aɪ/"), ("think", "/θ/"), ("so", "/s/")]
        observed = ["/aɪ/", "/t/", "/s/"]  # 1 substitution error
        result = PhoneticEvaluator.evaluate_utterance(targets, observed)

        assert result.accuracy_score == 66  # 2 out of 3
        assert len(result.phoneme_feedback) == 1
        assert result.phoneme_feedback[0].error_type == ErrorType.SUBSTITUTION
