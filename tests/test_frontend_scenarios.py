"""
Unit tests for Frontend Scenario Curation & Topic Explorer (`TASK-006`).
Tests featured scenario filtering, category categorization, live search helper logic,
and API scenario metadata compatibility.
"""

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.scenarios import DEFAULT_SCENARIOS, list_scenarios


class TestFrontendScenariosHub(unittest.TestCase):
    """Test suite for TASK-006 Modern Curated Roleplay Hub & Explorer."""

    def setUp(self):
        self.client = TestClient(app)

    def test_default_scenarios_have_required_metadata(self):
        """Verify all default scenarios have required title, icon, category, and mode."""
        for sc in DEFAULT_SCENARIOS.values():
            self.assertIn("id", sc)
            self.assertIn("title", sc)
            self.assertIn("category", sc)
            self.assertIn("icon", sc)
            self.assertIn("mode", sc)
            self.assertTrue(sc["mode"] in ("roleplay", "ielts_exam"))

    def test_api_scenarios_returns_complete_list(self):
        """Verify GET /api/scenarios returns 200 with scenarios containing categories."""
        res = self.client.get("/api/scenarios")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("scenarios", data)
        scenarios = data["scenarios"]
        self.assertGreater(len(scenarios), 10)

        # Check category field presence across list
        categories = {s.get("category") for s in scenarios if "category" in s}
        self.assertGreater(len(categories), 3, "Scenarios should span multiple categories")

    def test_featured_roleplay_scenarios_curation(self):
        """Verify featured roleplay IDs match default roleplay set."""
        featured_ids = [
            'everyday_chat', 'cafe_dining', 'job_interview', 'travel_culture',
            'work_study_space', 'digital_lifestyle', 'debate_club', 'shopping_negotiation'
        ]
        all_scenarios = list_scenarios()
        roleplays = [s for s in all_scenarios if s.get("mode") != "ielts_exam"]

        featured_matches = [s for s in roleplays if s.get("id") in featured_ids or s.get("is_custom")]
        self.assertGreaterEqual(len(featured_matches), 8, "Featured topics must cover core curated roleplays")

    def test_explorer_category_filter_matching(self):
        """Verify category filtering rules match expected category groupings."""
        all_scenarios = list_scenarios()

        # Category: Everyday
        everyday_topics = [
            s for s in all_scenarios
            if "everyday" in s.get("category", "").lower()
            or "personal" in s.get("category", "").lower()
            or "chat" in s.get("title", "").lower()
            or "coffee" in s.get("title", "").lower()
        ]
        self.assertGreater(len(everyday_topics), 0)

        # Category: Career
        career_topics = [
            s for s in all_scenarios
            if "career" in s.get("category", "").lower()
            or "work" in s.get("category", "").lower()
            or "study" in s.get("category", "").lower()
            or "interview" in s.get("title", "").lower()
        ]
        self.assertGreater(len(career_topics), 0)

        # Category: IELTS
        ielts_topics = [
            s for s in all_scenarios
            if s.get("mode") == "ielts_exam"
            or s.get("source") == "material_bank"
            or "ielts" in s.get("category", "").lower()
        ]
        self.assertGreater(len(ielts_topics), 0)

    def test_explorer_live_search_matching(self):
        """Verify keyword search filters topics matching query strings accurately."""
        all_scenarios = list_scenarios()

        query = "coffee"
        matches = [
            s for s in all_scenarios
            if query in s.get("title", "").lower()
            or query in s.get("description", "").lower()
            or query in s.get("category", "").lower()
            or query in s.get("open_story_guide", "").lower()
        ]
        self.assertGreater(len(matches), 0, "Search for 'coffee' should return matching scenarios")
        self.assertTrue(any("coffee" in s.get("title", "").lower() or "coffee" in s.get("description", "").lower() for s in matches))


if __name__ == "__main__":
    unittest.main()
