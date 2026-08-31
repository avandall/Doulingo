"""
End-to-End Integration Testing & Latency Benchmarks for Material Bank (`TASK-007`).
Tests full multi-turn conversation flow, JSON response structure validation,
and latency performance for Material Bank topics integrated into FastAPI endpoints.
"""

import time
import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.scenarios import list_scenarios


class TestIntegrationMaterialBank(unittest.TestCase):
    """End-to-end integration and latency benchmark test suite for MaterialBank scenarios."""

    def setUp(self):
        self.client = TestClient(app)
        from app.rag.material_bank import get_material_bank
        mb_topics = get_material_bank().topics
        self.assertTrue(len(mb_topics) > 0, "Material Bank topics must be populated")
        self.mb_topic_id = list(mb_topics.keys())[0]

    def test_full_turn_conversation_flow(self):
        """Simulate a complete 2-turn conversation flow with a MaterialBank topic."""
        topic_id = self.mb_topic_id

        # Step 1: Start scenario greeting
        start_payload = {
            "scenario_id": topic_id,
            "character_id": "lily",
            "level": 3
        }
        res_start = self.client.post("/api/start_scenario", json=start_payload)
        self.assertEqual(res_start.status_code, 200)
        start_data = res_start.json()
        self.assertIn("ai_response", start_data)
        self.assertTrue(len(start_data["ai_response"]) > 0)

        # Step 2: Turn 1
        history = [
            {"role": "assistant", "content": start_data["ai_response"]}
        ]
        turn1_payload = {
            "scenario_id": topic_id,
            "character_id": "lily",
            "user_transcript": "I believe continuous learning is essential for professional growth.",
            "conversation_history": history,
            "level": 3
        }
        res_turn1 = self.client.post("/api/process_turn", json=turn1_payload)
        self.assertEqual(res_turn1.status_code, 200)
        turn1_data = res_turn1.json()

        # Structured response validation
        self.assertIn("ai_response", turn1_data)
        self.assertIn("user_feedback", turn1_data)

        # Step 3: Turn 2 with accumulated history
        history.append({"role": "user", "content": turn1_payload["user_transcript"]})
        history.append({"role": "assistant", "content": turn1_data["ai_response"]})

        turn2_payload = {
            "scenario_id": topic_id,
            "character_id": "lily",
            "user_transcript": "Online courses provide great flexibility for working professionals.",
            "conversation_history": history,
            "level": 3
        }
        res_turn2 = self.client.post("/api/process_turn", json=turn2_payload)
        self.assertEqual(res_turn2.status_code, 200)
        turn2_data = res_turn2.json()
        self.assertIn("ai_response", turn2_data)
        self.assertIn("user_feedback", turn2_data)

    def test_structured_json_response_fields(self):
        """Verify presence and valid typing of all key JSON fields in process_turn response."""
        topic_id = self.mb_topic_id
        payload = {
            "scenario_id": topic_id,
            "character_id": "rajesh",
            "user_transcript": "I prefer hybrid work environments because they offer better work-life balance.",
            "conversation_history": [],
            "level": 5
        }
        res = self.client.post("/api/process_turn", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Core response fields
        self.assertIn("ai_response", data)
        self.assertIsInstance(data["ai_response"], str)
        self.assertTrue(len(data["ai_response"]) > 0)

        # Feedback block
        self.assertIn("user_feedback", data)
        fb = data["user_feedback"]
        self.assertIsInstance(fb, dict)
        self.assertIn("fluency_score", fb)
        self.assertIsInstance(fb["fluency_score"], (int, float))

    def test_api_chat_integration_with_material_bank(self):
        """Verify POST /api/chat works seamlessly with MaterialBank topic_id."""
        topic_id = self.mb_topic_id
        payload = {
            "scenario_id": topic_id,
            "character_id": "victor",
            "user_transcript": "Could you tell me more about effective study techniques?",
            "conversation_history": [],
            "level": 2
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("response", data)
        self.assertIn("audio_url", data)
        self.assertIn("fluency_score", data)
        self.assertIn("user_feedback", data)

    def test_latency_benchmarks(self):
        """Benchmark response times for MaterialBank topic initialization and turn processing."""
        topic_id = self.mb_topic_id

        # Measure start_scenario latency
        start_time = time.time()
        res_start = self.client.post("/api/start_scenario", json={
            "scenario_id": topic_id,
            "character_id": "lily",
            "level": 1
        })
        start_latency = (time.time() - start_time) * 1000
        self.assertEqual(res_start.status_code, 200)

        # Measure process_turn latency
        start_time = time.time()
        res_turn = self.client.post("/api/process_turn", json={
            "scenario_id": topic_id,
            "character_id": "lily",
            "user_transcript": "I am interested in improving my vocabulary.",
            "conversation_history": [],
            "level": 1
        })
        turn_latency = (time.time() - start_time) * 1000
        self.assertEqual(res_turn.status_code, 200)

        # Print latency benchmark report
        print(f"\n[LATENCY BENCHMARK] Start Scenario: {start_latency:.2f} ms")
        print(f"[LATENCY BENCHMARK] Process Turn: {turn_latency:.2f} ms")

        # Sanity check: Ensure local processing overhead does not crash or timeout
        self.assertLess(start_latency, 30000, "Start scenario should complete under 30s")
        self.assertLess(turn_latency, 30000, "Process turn should complete under 30s")


if __name__ == "__main__":
    unittest.main()
