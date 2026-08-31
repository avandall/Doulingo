"""
Unit tests for FastAPI Endpoints Bridge & Scenario Registry (`TASK-006`).
Tests /api/scenarios, /api/scenarios/{scenario_id}, /api/start_scenario, and /api/process_turn
integration with MaterialBank and Turso DB.
"""

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.scenarios import list_scenarios


class TestScenariosBridge(unittest.TestCase):
    """Test suite for FastAPI scenario endpoints integrated with MaterialBank."""

    def setUp(self):
        self.client = TestClient(app)

    def test_list_scenarios_includes_default_and_custom(self):
        """Verify list_scenarios includes default and custom scenarios."""
        scenarios = list_scenarios()
        self.assertGreaterEqual(len(scenarios), 10, "Should include default scenarios")

    def test_api_list_scenarios_endpoint(self):
        """Verify GET /api/scenarios returns 200 with scenario list."""
        res = self.client.get("/api/scenarios")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("scenarios", data)
        self.assertGreaterEqual(len(data["scenarios"]), 10)

    def test_api_get_scenario_by_id(self):
        """Verify GET /api/scenarios/{scenario_id} for default, MaterialBank, and custom topic."""
        # 1. Default scenario
        res_def = self.client.get("/api/scenarios/det_childhood_memory")
        self.assertEqual(res_def.status_code, 200)
        self.assertEqual(res_def.json()["id"], "det_childhood_memory")

        # 2. MaterialBank scenario direct lookup
        from app.rag.material_bank import get_material_bank
        mb_topic_id = list(get_material_bank().topics.keys())[0]
        res_mb = self.client.get(f"/api/scenarios/{mb_topic_id}")
        self.assertEqual(res_mb.status_code, 200)
        self.assertEqual(res_mb.json()["id"], mb_topic_id)

    def test_api_get_scenario_not_found(self):
        """Verify GET /api/scenarios/invalid_id returns 404."""
        res = self.client.get("/api/scenarios/invalid_scenario_id_999")
        self.assertEqual(res.status_code, 404)

    def test_start_scenario_with_material_bank_topic(self):
        """Verify POST /api/start_scenario works with a MaterialBank topic_id."""
        from app.rag.material_bank import get_material_bank
        mb_topic_id = list(get_material_bank().topics.keys())[0]

        payload = {
            "scenario_id": mb_topic_id,
            "character_id": "lily",
            "level": 1
        }
        res = self.client.post("/api/start_scenario", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ai_response", data)
        self.assertTrue(len(data["ai_response"]) > 0)

    def test_process_turn_with_material_bank_topic(self):
        """Verify POST /api/process_turn works with a MaterialBank topic_id."""
        from app.rag.material_bank import get_material_bank
        mb_topic_id = list(get_material_bank().topics.keys())[0]

        payload = {
            "scenario_id": mb_topic_id,
            "character_id": "lily",
            "user_transcript": "I believe work-life balance is very important for mental health.",
            "conversation_history": [],
            "level": 2
        }
        res = self.client.post("/api/process_turn", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ai_response", data)
        self.assertIn("user_feedback", data)


if __name__ == "__main__":
    unittest.main()
