"""
Unit and Integration Tests for Weekly Performance Reporting Engine (`app/reporting.py`).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.storage.db import init_db, save_user_profile
from app.main import app
from app.analytics.reporting import generate_weekly_report, save_tier2_evaluation
from app.scoring.tier2_deep import Tier2ScoreResult


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_save_tier2_evaluation_dict():
    user_id = f"test_user_report_dict_{uuid.uuid4().hex[:8]}"
    eval_data = {
        "fluency_score": 7.5,
        "lexical_score": 7.0,
        "grammar_score": 6.5,
        "pronunciation_score": 8.0,
        "raw_score": 7.2,
    }
    saved = save_tier2_evaluation(user_id, eval_data)
    assert saved["user_id"] == user_id
    assert saved["fluency_score"] == 7.5
    assert saved["lexical_score"] == 7.0
    assert saved["grammar_score"] == 6.5
    assert saved["pronunciation_score"] == 8.0
    assert saved["raw_score"] == 7.2


def test_save_tier2_evaluation_dataclass():
    user_id = f"test_user_report_obj_{uuid.uuid4().hex[:8]}"
    obj = Tier2ScoreResult(
        fluency_score=8.0,
        lexical_score=7.5,
        grammar_score=7.0,
        pronunciation_score=8.5,
        raw_score=7.75,
        estimated_band=7.5,
        latency_ms=120.0,
    )
    saved = save_tier2_evaluation(user_id, obj)
    assert saved["user_id"] == user_id
    assert saved["fluency_score"] == 8.0
    assert saved["lexical_score"] == 7.5


def test_generate_weekly_report_with_history():
    user_id = f"test_user_weekly_hist_{uuid.uuid4().hex[:8]}"
    # Seed user profile
    save_user_profile(
        user_id,
        {
            "band_estimate_overall": 7.0,
            "recurring_errors": ["Subject-verb agreement error"],
        },
    )

    # Seed evaluation history
    save_tier2_evaluation(
        user_id,
        {
            "fluency_score": 7.0,
            "lexical_score": 7.5,
            "grammar_score": 6.0,
            "pronunciation_score": 8.0,
            "raw_score": 7.1,
        },
    )
    save_tier2_evaluation(
        user_id,
        {
            "fluency_score": 8.0,
            "lexical_score": 8.0,
            "grammar_score": 7.0,
            "pronunciation_score": 8.5,
            "raw_score": 7.9,
        },
    )

    report = generate_weekly_report(user_id, days=7)
    assert report["user_id"] == user_id
    assert report["evaluations_count"] == 2
    assert report["overall_band"] == 7.0
    assert report["axes_scores"]["fluency"] == 7.5
    assert report["axes_scores"]["lexical"] == 7.75
    assert report["axes_scores"]["grammar"] == 6.5
    assert report["axes_scores"]["pronunciation"] == 8.25
    assert report["strongest_axis"] == "pronunciation"
    assert report["weakest_axis"] == "grammar"
    assert len(report["recommendations"]) > 0
    assert "Weekly summary for user" in report["summary"]


def test_generate_weekly_report_empty_history_fallback():
    user_id = f"test_user_empty_hist_{uuid.uuid4().hex[:8]}"
    save_user_profile(
        user_id,
        {
            "band_estimate_overall": 6.5,
            "band_fluency": 6.5,
            "band_lexical": 6.0,
            "band_grammar": 6.0,
            "band_pronunciation": 7.0,
            "recurring_errors": [],
        },
    )

    report = generate_weekly_report(user_id, days=7)
    assert report["user_id"] == user_id
    assert report["evaluations_count"] == 0
    assert report["overall_band"] == 6.5
    assert report["axes_scores"]["fluency"] == 6.5
    assert report["axes_scores"]["pronunciation"] == 7.0
    assert report["strongest_axis"] == "pronunciation"
    assert report["latest_evaluation"] is None


def test_api_weekly_report_endpoint():
    client = TestClient(app)
    response = client.get("/api/reports/weekly?user_id=user_demo&days=7")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "axes_scores" in data
    assert "overall_band" in data
    assert "summary" in data

    # Test alias route
    alias_response = client.get("/api/reporting/weekly?user_id=user_demo&days=7")
    assert alias_response.status_code == 200
    assert alias_response.json()["user_id"] == "user_demo"
