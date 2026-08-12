"""
Unit tests for Material Bank Parser & Indexer (`app/material_bank.py`).
Tests loading markdown files, parsing schemas, case-insensitive index lookups,
and singleton management.
"""

import os
import tempfile
import unittest

from app.material_bank import (
    GrammarPattern,
    MaterialBank,
    Persona,
    Question,
    TopicBank,
    VocabularyItem,
    get_material_bank,
)


class TestMaterialBank(unittest.TestCase):
    """Test suite for MaterialBank loading, parsing, and retrieval."""

    def setUp(self):
        self.bank = MaterialBank(docs_dir="docs")
        self.bank.load_all()

    def test_load_all_real_docs(self):
        """Verify loading extracted IELTS topics populates > 0 topics."""
        self.assertGreater(len(self.bank.topics), 0, "Topics bank should not be empty")
        self.assertGreaterEqual(len(self.bank.topics), 30, "Should load all extracted IELTS topics")

    def test_topic_structure_and_completeness(self):
        """Verify topics contain expected personas, questions, vocabulary, and grammar."""
        sample_topic_id = list(self.bank.topics.keys())[0]
        topic: TopicBank = self.bank.topics[sample_topic_id]

        self.assertIsInstance(topic, TopicBank)
        self.assertTrue(topic.topic_id)
        self.assertTrue(topic.topic_name)
        self.assertIsInstance(topic.target_levels, list)
        self.assertGreater(len(topic.target_levels), 0)

        # Check at least one topic has personas, questions, and vocabulary items populated
        has_persona = False
        has_question = False
        has_vocab = False
        has_grammar = False

        for t in self.bank.topics.values():
            if t.personas:
                has_persona = True
                self.assertIsInstance(t.personas[0], Persona)
            if t.questions:
                has_question = True
                self.assertIsInstance(t.questions[0], Question)
            if t.vocabulary:
                has_vocab = True
                self.assertIsInstance(t.vocabulary[0], VocabularyItem)
            if t.grammar_patterns:
                has_grammar = True
                self.assertIsInstance(t.grammar_patterns[0], GrammarPattern)

        self.assertTrue(has_persona, "At least one topic should have parsed personas")
        self.assertTrue(has_question, "At least one topic should have parsed questions")
        self.assertTrue(has_vocab, "At least one topic should have parsed vocabulary")
        self.assertTrue(has_grammar, "At least one topic should have parsed grammar patterns")

    def test_get_topic_case_and_slug_insensitivity(self):
        """Verify case-insensitive and dash/underscore insensitive lookups."""
        # Find a topic with a multi-word slug
        first_topic_id = list(self.bank.topics.keys())[0]
        topic_obj = self.bank.topics[first_topic_id]

        # Test exact match
        found1 = self.bank.get_topic(first_topic_id)
        self.assertIsNotNone(found1)
        self.assertEqual(found1.topic_id, first_topic_id)

        # Test upper case with underscores
        upper_id = first_topic_id.upper().replace("-", "_")
        found2 = self.bank.get_topic(upper_id)
        self.assertIsNotNone(found2)
        self.assertEqual(found2.topic_id, first_topic_id)

        # Test lookup by topic_name
        found3 = self.bank.get_topic(topic_obj.topic_name)
        self.assertIsNotNone(found3)
        self.assertEqual(found3.topic_id, first_topic_id)

    def test_get_topic_non_existent(self):
        """Verify get_topic returns None for unknown topic IDs."""
        result = self.bank.get_topic("non_existent_topic_id_99999")
        self.assertIsNone(result)

    def test_list_topics(self):
        """Verify list_topics returns structured summary dictionaries for all topics."""
        summaries = self.bank.list_topics()
        self.assertEqual(len(summaries), len(self.bank.topics))

        for item in summaries[:5]:
            self.assertIn("topic_id", item)
            self.assertIn("topic_name", item)
            self.assertIn("target_levels", item)
            self.assertIn("persona_count", item)
            self.assertIn("question_count", item)
            self.assertIn("vocab_count", item)
            self.assertIn("grammar_count", item)

    def test_get_material_bank_singleton(self):
        """Verify get_material_bank returns the singleton instance."""
        mb1 = get_material_bank("docs")
        mb2 = get_material_bank("docs")
        self.assertIs(mb1, mb2)

    def test_normalize_id(self):
        """Verify normalize_id static method handles spaces, punctuation, and casing."""
        self.assertEqual(MaterialBank.normalize_id("Shopping Mall"), "shopping-mall")
        self.assertEqual(MaterialBank.normalize_id("SHOPPING_MALL"), "shopping-mall")
        self.assertEqual(MaterialBank.normalize_id("  Topic_Name#01! "), "topic-name01")

    def test_parse_custom_markdown_block(self):
        """Verify parsing a custom mock markdown topic block."""
        custom_md = """# TOPIC: Mock Test Topic
`topic_id: "mock-test-topic"`
`topic_name: "Mock Test Topic"`
`target_levels: ["5.0-6.0", "6.5+"]`

1. PERSONA POOL
- [P1] **Test Examiner**: Friendly IELTS Examiner

2. QUESTION POOL
Band 5.0-6.0:
- Q_1: Tell me about your mock test.

Band 6.5+:
- Q_2: How do mock tests affect performance?

3. VOCABULARY & COLLOCATIONS
Band 5.0-6.0:
- `mock test`: practice examination

4. GRAMMAR & RESPONSE PATTERNS
- Pattern_1: "In my opinion, mock tests are beneficial."
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "DB99_Mock.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(custom_md)

            custom_bank = MaterialBank(docs_dir=tmpdir)
            loaded_count = custom_bank.load_all()

            self.assertEqual(loaded_count, 1)
            topic = custom_bank.get_topic("mock-test-topic")
            self.assertIsNotNone(topic)
            self.assertEqual(topic.topic_name, "Mock Test Topic")
            self.assertEqual(len(topic.personas), 1)
            self.assertIsInstance(topic.personas[0], Persona)
            self.assertEqual(topic.personas[0].id, "P1")
            self.assertEqual(len(topic.questions), 2)
            self.assertIsInstance(topic.questions[0], Question)
            self.assertEqual(len(topic.vocabulary), 1)
            self.assertIsInstance(topic.vocabulary[0], VocabularyItem)
            self.assertEqual(topic.vocabulary[0].phrase, "mock test")
            self.assertEqual(len(topic.grammar_patterns), 1)
            self.assertIsInstance(topic.grammar_patterns[0], GrammarPattern)


if __name__ == "__main__":
    unittest.main()
