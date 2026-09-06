"""
Integration test suite for Inngest Async Background Jobs & Polling API
"""

import time

from fastapi.testclient import TestClient

from app.main import app
from app.storage.db import (
    create_evaluation_job,
    get_evaluation_job,
    update_evaluation_job_status,
)

client = TestClient(app)


def test_async_evaluation_trigger_endpoint():
    """Verify POST /api/exams/{session_id}/evaluate-async returns 202 Accepted in <1s."""
    session_id = "test_session_123"
    start_time = time.time()

    response = client.post(f"/api/exams/{session_id}/evaluate-async")
    elapsed = time.time() - start_time

    assert response.status_code == 202
    assert elapsed < 1.0

    data = response.json()
    assert "job_id" in data
    assert data["session_id"] == session_id
    assert data["status"] == "pending"
    assert "status_url" in data
    assert data["status_url"] == f"/api/jobs/{data['job_id']}/status"


def test_job_status_polling_flow():
    """Verify status polling endpoint GET /api/jobs/{job_id}/status tracks pending -> done transition."""
    session_id = "test_session_polling"
    response = client.post(f"/api/exams/{session_id}/evaluate-async")
    assert response.status_code == 202
    data = response.json()
    job_id = data["job_id"]

    status_resp = client.get(f"/api/jobs/{job_id}/status")
    assert status_resp.status_code == 200
    job_data = status_resp.json()
    assert job_data["job_id"] == job_id
    assert job_data["status"] in ["pending", "processing", "done"]

    time.sleep(0.3)
    final_resp = client.get(f"/api/jobs/{job_id}/status")
    assert final_resp.status_code == 200
    final_data = final_resp.json()
    assert final_data["status"] == "done"
    assert "result" in final_data
    assert final_data["result"] is not None
    assert final_data["result"]["session_id"] == session_id


def test_job_status_404():
    """Verify GET /api/jobs/{job_id}/status returns 404 for nonexistent job ID."""
    response = client.get("/api/jobs/nonexistent_job_9999/status")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_db_job_helpers():
    """Verify db helper functions create_evaluation_job and update_evaluation_job_status."""
    job_id = "test_job_db_1"
    session_id = "test_session_db_1"

    created = create_evaluation_job(job_id, session_id, status="pending")
    assert created["id"] == job_id
    assert created["status"] == "pending"

    updated = update_evaluation_job_status(job_id, status="processing")
    assert updated["status"] == "processing"

    res_data = {"score": 8.0, "status": "completed"}
    done_job = update_evaluation_job_status(job_id, status="done", result=res_data)
    assert done_job["status"] == "done"
    assert done_job["result"] == res_data

    fetched = get_evaluation_job(job_id)
    assert fetched is not None
    assert fetched["id"] == job_id
    assert fetched["status"] == "done"
    assert fetched["result"] == res_data


def test_inngest_endpoint_mount():
    """Verify /api/inngest endpoint is mounted on FastAPI app."""
    response = client.get("/api/inngest")
    assert response.status_code in [200, 400, 405]
