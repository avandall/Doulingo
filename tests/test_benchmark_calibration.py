"""
tests/test_benchmark_calibration.py — Unit Tests for TASK-024 Scoring Model Drift Benchmark
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from scripts.benchmark_calibration import (
    compute_drift_metrics,
    evaluate_drift,
    extract_human_rating,
    generate_benchmark_report,
    load_human_reviewed_samples,
    run_benchmark,
)


def test_extract_human_rating():
    assert extract_human_rating("human:7.5", {}) == 7.5
    assert extract_human_rating("human:score=8.0", {}) == 8.0
    assert extract_human_rating("human:evaluator1:band=6.5", {}) == 6.5
    assert extract_human_rating("admin:john", {}) is None
    assert extract_human_rating(None, {}) is None


def test_compute_drift_metrics():
    samples = [
        {"model_overall": 7.0, "human_overall": 7.0, "source": "db_human_review"},
        {"model_overall": 8.0, "human_overall": 7.5, "source": "synthetic_ground_truth"},
        {"model_overall": 6.0, "human_overall": 6.5, "source": "db_human_review"},
    ]
    metrics = compute_drift_metrics(samples)
    assert metrics["sample_size"] == 3
    assert metrics["db_count"] == 2
    assert metrics["synthetic_count"] == 1
    # Errors: |7-7|=0, |8-7.5|=0.5, |6-6.5|=0.5 -> Mean = 1.0 / 3 = 0.3333
    assert abs(metrics["mae"] - 0.3333) < 0.001
    assert metrics["max_error"] == 0.5


def test_evaluate_drift_pass_and_alert():
    baseline_mae = 0.30

    # PASS scenario (MAE 0.32 <= 0.30 * 1.2 = 0.36)
    status, rec = evaluate_drift(0.32, baseline_mae, threshold_multiplier=1.2)
    assert status == "PASS"
    assert "No recalibration required" in rec

    # DRIFT_DETECTED scenario (MAE 0.45 > 0.36)
    status_drift, rec_drift = evaluate_drift(0.45, baseline_mae, threshold_multiplier=1.2)
    assert status_drift == "DRIFT_DETECTED"
    assert "DRIFT WARNING" in rec_drift
    assert "calibrate_thresholds.py" in rec_drift


def test_load_human_reviewed_samples_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE harvest_review_queue (
            id TEXT PRIMARY KEY,
            tier2_scores TEXT,
            reviewed_by TEXT,
            review_status TEXT
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO harvest_review_queue (id, tier2_scores, reviewed_by, review_status)
        VALUES ('hrq_1', '{"fluency": 7.5, "lexical": 7.5, "grammar": 7.5, "pronunciation": 7.5}', 'human:7.5', 'approved')
        """
    )
    conn.commit()

    samples = load_human_reviewed_samples(
        conn=conn, min_samples=1, allow_synthetic=False
    )
    assert len(samples) == 1
    assert samples[0]["id"] == "hrq_1"
    assert samples[0]["model_overall"] == 7.5
    assert samples[0]["human_overall"] == 7.5
    assert samples[0]["source"] == "db_human_review"
    conn.close()


def test_generate_benchmark_report():
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_path = Path(tmp_dir) / "benchmark_report.md"
        metrics = {
            "sample_size": 20,
            "db_count": 5,
            "synthetic_count": 15,
            "mae": 0.28,
            "rmse": 0.32,
            "max_error": 0.5,
        }
        active_config = {
            "version": "v1",
            "holdout_mae": 0.25,
            "status": "active",
            "calibrated_from": "test_corpus",
        }
        content = generate_benchmark_report(
            metrics=metrics,
            active_config=active_config,
            status="PASS",
            recommendation="Test recommendation PASS",
            threshold_multiplier=1.2,
            report_path=report_path,
        )

        assert report_path.exists()
        assert "# Scoring Model Drift Benchmark Report" in content
        assert "v1" in content
        assert "PASS" in content
        assert "0.2800" in content


def test_run_benchmark_end_to_end():
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_file = Path(tmp_dir) / "report.md"
        res = run_benchmark(
            config_dir="config",
            report_path=str(report_file),
            threshold_multiplier=1.2,
            allow_synthetic=True,
            simulate_drift=False,
        )

        assert res["status"] in ("PASS", "DRIFT_DETECTED")
        assert report_file.exists()
        assert "metrics" in res
        assert res["metrics"]["sample_size"] >= 10
