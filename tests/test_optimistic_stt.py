"""
tests/test_optimistic_stt.py
=============================
Unit & Integration Test Suite for TASK-010:
Optimistic Client-Side STT & Asynchronous Acoustic Extraction.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_extract_acoustic_metrics_endpoint_with_audio():
    """Test POST /api/audio/extract_acoustic_metrics with audio blob and transcript."""
    dummy_audio = b"\x00" * 32000  # ~2 seconds of dummy PCM audio bytes
    response = client.post(
        "/api/audio/extract_acoustic_metrics",
        data={"transcript": "Hello, I am practicing my English speech fluency today."},
        files={"file": ("speech.webm", dummy_audio, "audio/webm")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["transcript"] == "Hello, I am practicing my English speech fluency today."
    assert "speech_metrics" in data

    metrics = data["speech_metrics"]
    assert "wpm" in metrics
    assert "pauses" in metrics
    assert "pronunciation_score" in metrics
    assert "fluency_tier" in metrics
    assert "acoustic_feedback" in metrics
    assert metrics["word_count"] == 9
    assert metrics["duration_sec"] > 0


def test_extract_acoustic_metrics_without_audio():
    """Test POST /api/audio/extract_acoustic_metrics with transcript only (text fallback)."""
    response = client.post(
        "/api/audio/extract_acoustic_metrics",
        data={"transcript": "Quick brown fox jumps over the lazy dog."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    metrics = data["speech_metrics"]
    assert metrics["word_count"] == 8
    assert metrics["wpm"] > 0
    assert metrics["fluency_tier"] is not None


def test_transcribe_audio_instant_fallback():
    """Test POST /api/transcribe_audio with fallback text."""
    response = client.post(
        "/api/transcribe_audio",
        data={"fallback_text": "Instant client transcript delivery"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "Instant client transcript delivery"
    assert data["source"] == "browser-stt"
    assert "speech_metrics" in data


def test_speech_js_contract():
    """Verify static/js/speech.js contains Optimistic STT and Async Acoustic Extraction logic."""
    project_root = Path(__file__).resolve().parent.parent
    speech_js_path = project_root / "static" / "js" / "speech.js"

    assert speech_js_path.exists(), "speech.js file must exist"
    content = speech_js_path.read_text(encoding="utf-8")

    assert "_extractAcousticMetricsAsync" in content
    assert "/api/audio/extract_acoustic_metrics" in content
    assert "Optimistic Client-Side STT" in content
