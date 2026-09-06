"""
Integration test suite for Inngest Async Background Jobs & Polling API
"""

import os
import time

from fastapi.testclient import TestClient

from app.main import app
from app.services.cron_service import cleanup_audio_cache
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


def test_cron_cleanup_empty_or_missing_directory(tmp_path):
    """Verify cron cleanup function does not crash on empty or non-existent directories."""
    non_existent = tmp_path / "does_not_exist"
    res1 = cleanup_audio_cache(cache_dir=str(non_existent))
    assert res1["deleted_count"] == 0
    assert res1["freed_bytes"] == 0

    empty_dir = tmp_path / "empty_cache"
    empty_dir.mkdir()
    res2 = cleanup_audio_cache(cache_dir=str(empty_dir))
    assert res2["deleted_count"] == 0
    assert res2["freed_bytes"] == 0


def test_cron_cleanup_deletes_old_files_keeps_new(tmp_path):
    """Verify cron cleanup deletes audio files > 24h old and keeps newer files."""
    cache_dir = tmp_path / "audio_cache"
    cache_dir.mkdir()

    old_file1 = cache_dir / "temp_speech_old1.mp3"
    old_file2 = cache_dir / "temp_speech_old2.mp3"
    new_file1 = cache_dir / "temp_speech_new1.mp3"

    old_file1.write_bytes(b"OLD AUDIO CACHE CONTENT 1" * 10)
    old_file2.write_bytes(b"OLD AUDIO CACHE CONTENT 2" * 20)
    new_file1.write_bytes(b"NEW AUDIO CACHE CONTENT" * 5)

    now = time.time()
    old_mtime = now - (25 * 3600)  # 25 hours old
    new_mtime = now - (1 * 3600)   # 1 hour old

    os.utime(old_file1, (old_mtime, old_mtime))
    os.utime(old_file2, (old_mtime, old_mtime))
    os.utime(new_file1, (new_mtime, new_mtime))

    res = cleanup_audio_cache(cache_dir=str(cache_dir), max_age_hours=24.0)

    assert res["deleted_count"] == 2
    assert res["freed_bytes"] > 0
    assert not old_file1.exists()
    assert not old_file2.exists()
    assert new_file1.exists()

