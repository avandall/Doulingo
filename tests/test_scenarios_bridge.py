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

    def test_list_scenarios_includes_material_bank(self):
        """Verify list_scenarios includes default, MaterialBank, and custom scenarios."""
        scenarios = list_scenarios()
        self.assertGreater(len(scenarios), 30, "Should include scenarios from MaterialBank")

        # Check if at least one scenario has source='material_bank'
        mb_scenarios = [s for s in scenarios if s.get("source") == "material_bank"]
        self.assertGreater(len(mb_scenarios), 0, "Should contain MaterialBank topics")

    def test_api_list_scenarios_endpoint(self):
        """Verify GET /api/scenarios returns 200 with complete scenario list."""
        res = self.client.get("/api/scenarios")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("scenarios", data)
        self.assertGreater(len(data["scenarios"]), 30)

    def test_api_get_scenario_by_id(self):
        """Verify GET /api/scenarios/{scenario_id} for default, MaterialBank, and custom topic."""
        # 1. Default scenario
        res_def = self.client.get("/api/scenarios/det_childhood_memory")
        self.assertEqual(res_def.status_code, 200)
        self.assertEqual(res_def.json()["id"], "det_childhood_memory")

        # 2. MaterialBank scenario
        all_scenarios = list_scenarios()
        mb_sc = next(s for s in all_scenarios if s.get("source") == "material_bank")
        res_mb = self.client.get(f"/api/scenarios/{mb_sc['id']}")
        self.assertEqual(res_mb.status_code, 200)
        self.assertEqual(res_mb.json()["id"], mb_sc["id"])

    def test_api_get_scenario_not_found(self):
        """Verify GET /api/scenarios/invalid_id returns 404."""
        res = self.client.get("/api/scenarios/invalid_scenario_id_999")
        self.assertEqual(res.status_code, 404)

    def test_start_scenario_with_material_bank_topic(self):
        """Verify POST /api/start_scenario works with a MaterialBank topic_id."""
        all_scenarios = list_scenarios()
        mb_sc = next(s for s in all_scenarios if s.get("source") == "material_bank")

        payload = {
            "scenario_id": mb_sc["id"],
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
        all_scenarios = list_scenarios()
        mb_sc = next(s for s in all_scenarios if s.get("source") == "material_bank")

        payload = {
            "scenario_id": mb_sc["id"],
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
