#!/usr/bin/env python3
"""
scripts/benchmark_calibration.py — Scoring Model Drift Benchmark (TASK-024)

Periodically benchmarks the scoring model by comparing Tier 2 model evaluation scores
against human-reviewed ground truth ratings from `harvest_review_queue`.
Calculates MAE and RMSE metrics, compares MAE against the baseline `holdout_mae` in the
active calibration config, and issues a drift warning if accuracy degrades beyond tolerance.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import math
import random
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import get_db_connection
from app.scoring.config_loader import load_active_anchors

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark_calibration")


def load_active_config(config_dir: Path | str = "config") -> dict[str, Any]:
    """Loads the currently active scoring anchors config JSON."""
    return load_active_anchors(config_dir)


def extract_human_rating(reviewed_by: str | None, tier2_scores: dict[str, float]) -> float | None:
    """
    Extracts human ground-truth rating score from `reviewed_by` string or payload.
    Supports formats like:
      - "human:7.5"
      - "human:score=7.5"
      - "human:alice@example.com:band=7.0"
      - JSON string inside reviewed_by
    """
    if not reviewed_by:
        return None

    str_val = str(reviewed_by).strip()
    if not str_val.startswith("human:"):
        return None

    # Check for direct numeric trailing match: human:7.5 or human:alice:7.5
    parts = str_val.split(":")
    for part in reversed(parts):
        part_clean = part.replace("score=", "").replace("band=", "").strip()
        try:
            val = float(part_clean)
            if 0.0 <= val <= 9.0:
                return val
        except ValueError:
            continue

    return None


def generate_synthetic_samples(
    sample_size: int = 30, seed: int = 42, simulate_drift: bool = False
) -> list[dict[str, Any]]:
    """Generates synthetic human-reviewed ground truth samples for testing when DB has few reviews."""
    random.seed(seed)
    samples: list[dict[str, Any]] = []

    axes = ["fluency", "lexical", "grammar", "pronunciation"]

    for i in range(sample_size):
        base_band = round(random.uniform(5.0, 8.5), 1)
        model_scores = {axis: round(base_band + random.uniform(-0.4, 0.4), 1) for axis in axes}
        model_overall = sum(model_scores.values()) / len(model_scores)

        # Apply noise; if simulate_drift=True, add systematic bias + higher variance
        if simulate_drift:
            human_noise = random.gauss(0.5, 0.4)  # Systematic +0.5 drift bias
        else:
            human_noise = random.gauss(0.0, 0.2)  # Low noise matching baseline

        human_overall = max(4.0, min(9.0, round(model_overall + human_noise, 1)))

        samples.append(
            {
                "id": f"hrq_syn_{i:03d}",
                "model_scores": model_scores,
                "model_overall": model_overall,
                "human_overall": human_overall,
                "source": "synthetic_ground_truth",
            }
        )

    return samples


def load_human_reviewed_samples(
    conn: Any = None,
    min_samples: int = 10,
    allow_synthetic: bool = True,
    simulate_drift: bool = False,
) -> list[dict[str, Any]]:
    """
    Queries `harvest_review_queue` for human-reviewed turns (`reviewed_by LIKE 'human:%'`).
    If fewer than `min_samples` are found and `allow_synthetic` is True, falls back to synthetic dataset.
    """
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    samples: list[dict[str, Any]] = []

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, tier2_scores, reviewed_by, review_status
            FROM harvest_review_queue
            WHERE reviewed_by IS NOT NULL AND reviewed_by LIKE 'human:%'
            """
        )
        rows = cursor.fetchall()

        for row in rows:
            record_id = row["id"] if isinstance(row, dict) or hasattr(row, "__getitem__") else row[0]
            scores_raw = row["tier2_scores"] if isinstance(row, dict) or hasattr(row, "__getitem__") else row[1]
            rev_by = row["reviewed_by"] if isinstance(row, dict) or hasattr(row, "__getitem__") else row[2]

            try:
                model_scores = json.loads(scores_raw) if isinstance(scores_raw, str) else (scores_raw or {})
            except Exception:
                model_scores = {}

            if isinstance(model_scores, dict) and model_scores:
                axes_vals = [float(v) for v in model_scores.values() if isinstance(v, (int, float))]
                model_overall = sum(axes_vals) / len(axes_vals) if axes_vals else 6.0
            else:
                model_overall = 6.0

            human_score = extract_human_rating(rev_by, model_scores)
            if human_score is not None:
                samples.append(
                    {
                        "id": record_id,
                        "model_scores": model_scores,
                        "model_overall": model_overall,
                        "human_overall": human_score,
                        "source": "db_human_review",
                    }
                )
    except Exception as e:
        logger.warning("Database query for human reviews failed: %s", e)
    finally:
        if close_conn:
            conn.close()

    if len(samples) < min_samples and allow_synthetic:
        logger.info(
            "Found %d human DB reviews (< min %d). Supplementing with synthetic benchmark samples.",
            len(samples),
            min_samples,
        )
        needed = min_samples - len(samples)
        syn_samples = generate_synthetic_samples(
            sample_size=max(30, needed), simulate_drift=simulate_drift
        )
        samples.extend(syn_samples)

    return samples


def compute_drift_metrics(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Computes MAE and RMSE metrics comparing model overall score vs human ground truth.
    """
    if not samples:
        return {
            "sample_size": 0,
            "mae": 0.0,
            "rmse": 0.0,
            "max_error": 0.0,
            "db_count": 0,
            "synthetic_count": 0,
        }

    errors: list[float] = []
    sq_errors: list[float] = []
    db_count = 0
    syn_count = 0

    for s in samples:
        if s.get("source") == "db_human_review":
            db_count += 1
        else:
            syn_count += 1

        m_score = float(s["model_overall"])
        h_score = float(s["human_overall"])
        err = abs(m_score - h_score)

        errors.append(err)
        sq_errors.append(err * err)

    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(sq_errors) / len(sq_errors))
    max_err = max(errors) if errors else 0.0

    return {
        "sample_size": len(samples),
        "db_count": db_count,
        "synthetic_count": syn_count,
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "max_error": round(max_err, 4),
    }


def evaluate_drift(
    mae: float, baseline_mae: float, threshold_multiplier: float = 1.2
) -> tuple[str, str]:
    """
    Evaluates whether current benchmark MAE exceeds allowed tolerance baseline * multiplier.
    Returns (status, recommendation):
        status: "PASS" | "DRIFT_DETECTED"
    """
    tolerance = baseline_mae * threshold_multiplier

    if mae > tolerance:
        status = "DRIFT_DETECTED"
        recommendation = (
            f"DRIFT WARNING: Benchmark MAE ({mae:.4f}) exceeds allowable tolerance ({tolerance:.4f}). "
            f"Model drift detected relative to baseline holdout MAE ({baseline_mae:.4f}). "
            f"Action Recommended: Run `python3 scripts/calibrate_thresholds.py` to recalibrate anchor points."
        )
    else:
        status = "PASS"
        recommendation = (
            f"Scoring model performance is stable. Benchmark MAE ({mae:.4f}) is within tolerance ({tolerance:.4f}). "
            f"No recalibration required."
        )

    return status, recommendation


def generate_benchmark_report(
    metrics: dict[str, Any],
    active_config: dict[str, Any],
    status: str,
    recommendation: str,
    threshold_multiplier: float,
    report_path: Path | str = "benchmark_report.md",
) -> str:
    """Generates markdown report `benchmark_report.md`."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    baseline_mae = float(active_config.get("holdout_mae", 0.35))
    tolerance = baseline_mae * threshold_multiplier

    report_lines = [
        "# Scoring Model Drift Benchmark Report",
        "",
        f"- **Benchmark Date:** {now_str}",
        f"- **Config Version:** {active_config.get('version', 'unknown')}",
        f"- **Config Status:** {active_config.get('status', 'active')}",
        f"- **Config Calibrated From:** {active_config.get('calibrated_from', 'N/A')}",
        f"- **Drift Status:** **{status}** {'✅' if status == 'PASS' else '⚠️'}",
        "",
        "## Evaluation Metrics",
        "",
        f"- **Sample Size:** {metrics['sample_size']} ({metrics['db_count']} DB Human Reviews / {metrics['synthetic_count']} Synthetic)",
        f"- **Evaluated MAE:** `{metrics['mae']:.4f}` IELTS Band",
        f"- **Evaluated RMSE:** `{metrics['rmse']:.4f}` IELTS Band",
        f"- **Max Absolute Error:** `{metrics['max_error']:.4f}` IELTS Band",
        f"- **Baseline Holdout MAE:** `{baseline_mae:.4f}`",
        f"- **Drift Tolerance Limit ({threshold_multiplier}x):** `{tolerance:.4f}`",
        "",
        "## Assessment & Recommendation",
        "",
        f"> {recommendation}",
        "",
    ]

    report_content = "\n".join(report_lines)
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_content, encoding="utf-8")
    return report_content


def run_benchmark(
    config_dir: str = "config",
    report_path: str = "benchmark_report.md",
    threshold_multiplier: float = 1.2,
    allow_synthetic: bool = True,
    simulate_drift: bool = False,
    conn: Any = None,
) -> dict[str, Any]:
    """Runs the full benchmark pipeline and outputs report."""
    active_cfg = load_active_config(config_dir)
    baseline_mae = float(active_cfg.get("holdout_mae", 0.35))

    samples = load_human_reviewed_samples(
        conn=conn,
        min_samples=10,
        allow_synthetic=allow_synthetic,
        simulate_drift=simulate_drift,
    )

    metrics = compute_drift_metrics(samples)
    status, rec = evaluate_drift(
        metrics["mae"], baseline_mae, threshold_multiplier=threshold_multiplier
    )

    generate_benchmark_report(
        metrics=metrics,
        active_config=active_cfg,
        status=status,
        recommendation=rec,
        threshold_multiplier=threshold_multiplier,
        report_path=report_path,
    )

    logger.info(
        "Benchmark complete. Status: %s | MAE: %.4f | Baseline: %.4f | Report: %s",
        status,
        metrics["mae"],
        baseline_mae,
        report_path,
    )

    return {
        "status": status,
        "metrics": metrics,
        "baseline_mae": baseline_mae,
        "recommendation": rec,
        "report_path": report_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scoring Model Drift Benchmark Pipeline"
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="Path to scoring config directory",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="benchmark_report.md",
        help="Path to benchmark markdown report output",
    )
    parser.add_argument(
        "--threshold-multiplier",
        type=float,
        default=1.2,
        help="Multiplier on baseline holdout MAE to trigger drift alert",
    )
    parser.add_argument(
        "--no-synthetic",
        action="store_true",
        help="Disable synthetic fallback samples if DB human reviews are few",
    )
    parser.add_argument(
        "--simulate-drift",
        action="store_true",
        help="Simulate high model drift for testing alert trigger",
    )

    args = parser.parse_args()

    res = run_benchmark(
        config_dir=args.config_dir,
        report_path=args.output_report,
        threshold_multiplier=args.threshold_multiplier,
        allow_synthetic=not args.no_synthetic,
        simulate_drift=args.simulate_drift,
    )

    if res["status"] == "DRIFT_DETECTED":
        print(f"\n⚠️ {res['recommendation']}\n")
    else:
        print(f"\n✅ {res['recommendation']}\n")


if __name__ == "__main__":
    main()
