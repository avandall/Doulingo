"""
Smoke test suite for Duolingo Speak API endpoints.
Tests /api/scenarios, /api/characters, /api/chat, and /api/tts.
Run with: python3 -m unittest discover -s tests -p "test_*.py"
"""

import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestSmokeAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_scenarios_endpoint(self):
        response = self.client.get("/api/scenarios")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scenarios", data)
        self.assertGreater(len(data["scenarios"]), 0)

    def test_characters_endpoint(self):
        response = self.client.get("/api/characters")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("characters", data)
        self.assertGreater(len(data["characters"]), 0)

    def test_chat_endpoint(self):
        payload = {
            "scenario_id": "det_childhood_memory",
            "character_id": "lily",
            "user_transcript": "Hello, I would like to order a cappuccino please.",
            "conversation_history": [],
            "level": 1
        }
        response = self.client.post("/api/chat", json=payload)
        if response.status_code != 200:
            print("Chat API Error response:", response.status_code, response.text)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("audio_url", data)
        self.assertIn("fluency_score", data)
        self.assertIn("native_suggestion", data)

    def test_tts_endpoint(self):
        response = self.client.get("/api/tts?text=Hello+world&char_id=lily")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("audio/"))
        self.assertGreater(len(response.content), 50)

if __name__ == "__main__":
    unittest.main()
