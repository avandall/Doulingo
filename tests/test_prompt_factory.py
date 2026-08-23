"""
Unit tests for Backend Prompt Factory & Dynamic Sampling Engine (`app/prompt_factory.py`).
Tests material sampling, system prompt assembly, prompt generation latency (< 5ms benchmark),
diversity of sampled outputs, and safety fallback behavior for non-existent topics.
"""

import time
import unittest

from app.rag.material_bank import MaterialBank, get_material_bank
from app.rag.prompt_factory import PromptFactory, get_prompt_factory


class TestPromptFactory(unittest.TestCase):
    """Test suite for PromptFactory dynamic sampling and prompt generation."""

    bank: MaterialBank
    factory: PromptFactory
    sample_topic_id: str

    @classmethod
    def setUpClass(cls) -> None:
        """Load MaterialBank once for performance across tests."""
        cls.bank = get_material_bank(docs_dir="docs")
        cls.bank.load_all()
        cls.factory = PromptFactory(material_bank=cls.bank)
        # Select first valid topic ID for tests
        cls.sample_topic_id = list(cls.bank.topics.keys())[0]

    def test_singleton_getter(self) -> None:
        """Verify get_prompt_factory returns singleton instance."""
        pf1 = get_prompt_factory(self.bank)
        pf2 = get_prompt_factory()
        self.assertIs(pf1, pf2)

    def test_sample_materials_structure_and_types(self) -> None:
        """Verify sample_materials returns expected keys and non-empty components for valid topic."""
        sampled = self.factory.sample_materials(topic_id=self.sample_topic_id, level="5.0-6.0")

        self.assertIn("topic_id", sampled)
        self.assertIn("topic_name", sampled)
        self.assertIn("persona", sampled)
        self.assertIn("vocabulary", sampled)
        self.assertIn("questions", sampled)
        self.assertIn("grammar_patterns", sampled)

        self.assertIsInstance(sampled["vocabulary"], list)
        self.assertIsInstance(sampled["questions"], list)
        self.assertIsInstance(sampled["grammar_patterns"], list)

    def test_sample_materials_fallback_nonexistent_topic(self) -> None:
        """Verify sample_materials handles unknown topic ID gracefully with empty lists."""
        dummy_topic_id = "non_existent_topic_id_xyz999"
        sampled = self.factory.sample_materials(topic_id=dummy_topic_id)

        self.assertEqual(sampled["topic_id"], dummy_topic_id)
        self.assertIsNone(sampled["persona"])
        self.assertEqual(sampled["vocabulary"], [])
        self.assertEqual(sampled["questions"], [])
        self.assertEqual(sampled["grammar_patterns"], [])

    def test_build_system_prompt_structure(self) -> None:
        """Verify build_system_prompt injects character traits, topic, vocabulary, and guidelines."""
        prompt = self.factory.build_system_prompt(
            topic_id=self.sample_topic_id,
            level="5.0-6.0",
            character_id="lily"
        )

        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)
        self.assertIn("Lily", prompt)
        self.assertIn("CONVERSATION TOPIC", prompt)

    def test_build_system_prompt_fallback_topic(self) -> None:
        """Verify build_system_prompt produces valid output even for nonexistent topic."""
        dummy_id = "non_existent_topic_id_xyz999"
        prompt = self.factory.build_system_prompt(topic_id=dummy_id, character_id="lily")

        self.assertIn("Lily", prompt)
        self.assertIn("CONVERSATION TOPIC", prompt)

    def test_prompt_assembly_benchmark(self) -> None:
        """Benchmark prompt assembly latency to ensure average time < 5ms."""
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            self.factory.build_system_prompt(
                topic_id=self.sample_topic_id,
                level="5.0-6.0",
                character_id="lily"
            )

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_elapsed_ms / iterations

        self.assertLess(
            avg_latency_ms,
            5.0,
            f"Average prompt assembly latency {avg_latency_ms:.3f}ms exceeded limit of 5.0ms"
        )

    def test_sampling_diversity(self) -> None:
        """Verify repeated sampling calls produce non-repetitive/varied prompt content."""
        # Find a topic with multiple personas, questions, or vocabulary
        rich_topic_id = None
        for t_id, t_obj in self.bank.topics.items():
            if len(t_obj.vocabulary) >= 5 or len(t_obj.questions) >= 3 or len(t_obj.personas) >= 2:
                rich_topic_id = t_id
                break

        if not rich_topic_id:
            rich_topic_id = self.sample_topic_id

        sampled_prompts = [
            self.factory.build_system_prompt(topic_id=rich_topic_id, level="5.0-6.0")
            for _ in range(5)
        ]

        # Check that not all 5 prompts are identical (diversity check)
        unique_prompts = set(sampled_prompts)
        topic_obj = self.bank.topics.get(rich_topic_id)

        # If the topic has candidate pools larger than sample size, diversity should be present
        if topic_obj and (len(topic_obj.vocabulary) > 4 or len(topic_obj.questions) > 2):
            self.assertGreater(
                len(unique_prompts),
                1,
                "Expected sampling diversity across 5 prompt factory calls"
            )
        else:
            self.assertGreaterEqual(len(sampled_prompts), 5)


if __name__ == "__main__":
    unittest.main()
