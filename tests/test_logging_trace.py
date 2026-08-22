"""
Unit Test Suite for Comprehensive Real-Time API Trace & Diagnostic Logging System (TASK-001)
Verify:
1. Console trace output format & log file generation in logs/api_trace.log
2. Key masking security (gsk_..., xi_..., AIza...)
3. Quota warning & auto-rotation logging on 429/402
4. Health & trace endpoints API status response
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.ai_engine import KEY_STATUS_CACHE, ai_engine, log_api_trace, mask_api_key
from app.tts_service import (
    generate_elevenlabs_tts_multi_key,
)


class TestLoggingTraceSystem(unittest.TestCase):

    def setUp(self):
        self.logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        self.log_file = os.path.join(self.logs_dir, "api_trace.log")

    def test_masked_api_key_security(self):
        self.assertEqual(mask_api_key("gsk_1234567890abcdef9aB"), "gsk_...f9aB")
        self.assertEqual(mask_api_key("xi_key_abcdef123456789A"), "xi_k...789A")
        self.assertEqual(mask_api_key("AIzaSy1234567890x8A9"), "AIza...x8A9")
        self.assertEqual(mask_api_key("short"), "***")
        self.assertEqual(mask_api_key(None), "***")

    def test_log_api_trace_file_and_cache(self):
        raw_secret_key = "gsk_testsecretkey9999key"
        log_api_trace("TestProvider", "test-model-70b", raw_secret_key, 200, 150.5, step="LLM")
        
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Step=LLM", content)
            self.assertIn("TestProvider", content)
            self.assertIn("gsk_...9key", content)
            self.assertNotIn(raw_secret_key, content)

        masked = mask_api_key(raw_secret_key)
        self.assertIn(masked, KEY_STATUS_CACHE)
        self.assertEqual(KEY_STATUS_CACHE[masked]["status"], "ACTIVE")
        self.assertEqual(KEY_STATUS_CACHE[masked]["step"], "LLM")

    def test_elevenlabs_quota_exhaustion_logging(self):
        mock_exhausted_key = "xi_quota429key12345"
        log_api_trace("ElevenLabs", "eleven_multilingual_v2", mock_exhausted_key, 429, 85.0, error_msg="Quota Exceeded", step="TTS")
        
        health = ai_engine.get_trace_quota_health()
        masked_key = mask_api_key(mock_exhausted_key)
        self.assertIn(masked_key, health["key_statuses"])
        self.assertEqual(health["key_statuses"][masked_key]["status"], "EXHAUSTED")
        self.assertEqual(health["key_statuses"][masked_key]["step"], "TTS")

    @patch("app.tts_service.requests.post")
    def test_elevenlabs_multi_key_rotation(self, mock_post):
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.text = "Quota exceeded"
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.content = b"fake_mp3_audio_data_stream_content_padding_bytes_here" * 20
        
        mock_post.side_effect = [mock_response_429, mock_response_200]
        
        keys = ["xi_key_1_exhausted_1234", "xi_key_2_working_5678"]
        result = generate_elevenlabs_tts_multi_key("Hello test", "lily", keys)
        self.assertIsNotNone(result)

    def test_get_trace_quota_health_response_structure(self):
        health = ai_engine.get_trace_quota_health()
        self.assertIn("active_groq_keys_count", health)
        self.assertIn("active_gemini_keys_count", health)
        self.assertIn("active_openai_keys_count", health)
        self.assertIn("active_elevenlabs_keys_count", health)
        self.assertIn("key_statuses", health)
        self.assertIn("recent_trace_logs", health)
        self.assertIsInstance(health["recent_trace_logs"], list)


if __name__ == "__main__":
    unittest.main()
