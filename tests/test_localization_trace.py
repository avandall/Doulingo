"""
Automated Integration & Verification Tests for Trace Logging, Key Rotation & Vietnamese Localization Quality.
Run with: uv run python -m unittest discover -s tests -p "test_*.py"
"""

import os
import unittest
from app.ai_engine import ai_engine, mask_api_key, log_api_trace

class TestLocalizationAndTraceLog(unittest.TestCase):

    def test_masked_key_utility(self):
        self.assertEqual(mask_api_key("gsk_1234567890abcdef9aB"), "gsk_...f9aB")
        self.assertEqual(mask_api_key("AIzaSy1234567890x8A9"), "AIza...x8A9")
        self.assertEqual(mask_api_key("short"), "***")
        self.assertEqual(mask_api_key(None), "***")

    def test_trace_logging(self):
        raw_secret_key = "gsk_testsecretkey9999key"
        log_api_trace("TestProvider", "test-model-70b", raw_secret_key, 200, 150.5)
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        log_file = os.path.join(logs_dir, "api_trace.log")
        
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("gsk_...9key", content)
            self.assertIn("TestProvider", content)
            self.assertNotIn(raw_secret_key, content)  # Raw secret key MUST NEVER be in logs!

    def test_quota_rotation_logging(self):
        mock_exhausted_key = "gsk_quota429key12345"
        log_api_trace("Groq", "llama-3.3-70b", mock_exhausted_key, 429, 85.0, error_msg="Rate limit reached")
        health = ai_engine.get_trace_quota_health()
        masked_key = mask_api_key(mock_exhausted_key)
        self.assertIn(masked_key, health["key_statuses"])
        self.assertEqual(health["key_statuses"][masked_key]["status"], "EXHAUSTED")

    def test_vietnamese_localization(self):
        result = ai_engine._professional_vietnamese_localization(
            english_text="That sounds awesome! What time should we meet at the cafe?",
            character_name="Lily",
            scenario_title="Coffee Chat"
        )
        self.assertIsNotNone(result)
        # Verify no quotes or raw wrappers
        self.assertFalse(result.startswith('"') and result.endswith('"'))
        self.assertFalse(result.startswith("'") and result.endswith("'"))

if __name__ == "__main__":
    unittest.main()
