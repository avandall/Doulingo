"""
Unit tests for Empathetic Prompting & ASR Phonetic Clarification Pipeline (TASK-003).
Verifies active listening & mirroring directives, ASR phonetic clarification rules,
open question mandates, and empathetic feedback structure across PromptFactory and AIEngine.
"""

import unittest

from app.core.ai_engine import AIEngine
from app.rag.prompt_factory import get_prompt_factory


class TestEmpathyPrompt(unittest.TestCase):
    """Test suite for Empathetic Prompting & ASR Phonetic Clarification Pipeline."""

    def setUp(self) -> None:
        self.factory = get_prompt_factory()
        self.ai_engine = AIEngine()
        self.sample_scenario = {
            "id": "coffee_chat",
            "title": "Casual Coffee Chat",
            "description": "Discuss coffee preferences and cafe routines.",
            "open_story_guide": "Explore morning habits and favorite drinks."
        }
        self.sample_character = {
            "id": "lily",
            "name": "Lily",
            "country": "UK",
            "role": "Coffee Enthusiast",
            "trait": "Friendly & Empathetic",
            "speech_style": "Conversational"
        }

    def test_prompt_factory_empathy_directives(self) -> None:
        """Verify PromptFactory injects Active Listening, ASR Clarification & Open Question directives."""
        prompt = self.factory.build_system_prompt(
            topic_id="coffee_chat",
            level="5.0-6.0",
            character_id="lily"
        )

        self.assertIn("EMPATHETIC & ACTIVE LISTENING DIRECTIVES", prompt)
        self.assertIn("ACTIVE LISTENING & MIRRORING", prompt)
        self.assertIn("ASR PHONETIC CLARIFICATION", prompt)
        self.assertIn("EMPATHETIC FEEDBACK", prompt)
        self.assertIn("OPEN QUESTION MANDATE", prompt)

    def test_ai_engine_token_efficient_prompt_directives(self) -> None:
        """Verify AIEngine._build_token_efficient_prompt contains all TASK-003 mandates."""
        prompt = self.ai_engine._build_token_efficient_prompt(
            scenario=self.sample_scenario,
            character=self.sample_character,
            user_transcript="I think finding in portal info about coffee is hard.",
            history=[],
            turn_count=1,
            level=5
        )

        self.assertIn("ACTIVE LISTENING & EMPATHETIC MIRRORING DIRECTIVE", prompt)
        self.assertIn("AUTHENTIC DUOLINGO ASR PHONETIC CLARIFICATION", prompt)
        self.assertIn("EMPATHETIC FEEDBACK & GENTLE GRAMMAR/PRONUNCIATION GUIDANCE", prompt)
        self.assertIn("ALWAYS END YOUR TURN WITH AN OPEN-ENDED QUESTION", prompt)

    def test_asr_phonetic_misrecognition_context(self) -> None:
        """Verify prompt specifically guides ASR phonetic misrecognitions like 'in portal' -> 'important'."""
        prompt = self.ai_engine._build_token_efficient_prompt(
            scenario=self.sample_scenario,
            character=self.sample_character,
            user_transcript="I want to go to the bitch in summer.",
            history=[],
            turn_count=2,
            level=3
        )

        # Confirm ASR homophone/phonetic examples are in the prompt
        self.assertIn("'beach' -> 'bitch'", prompt)
        self.assertIn("'important' -> 'in portal'", prompt)
        self.assertIn("did you mean", prompt)

    def test_empathy_feedback_schema_requirements(self) -> None:
        """Verify user_feedback instructions demand warm, encouraging feedback."""
        prompt = self.ai_engine._build_token_efficient_prompt(
            scenario=self.sample_scenario,
            character=self.sample_character,
            user_transcript="I am very sad today because exam was bad.",
            history=[],
            turn_count=3,
            level=2
        )

        self.assertIn("user_feedback", prompt)
        self.assertIn("grammar_status", prompt)
        self.assertIn("corrected_text", prompt)
        self.assertIn("duo_reaction", prompt)


if __name__ == "__main__":
    unittest.main()
