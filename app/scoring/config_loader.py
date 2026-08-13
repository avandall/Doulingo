"""
Configuration loader for scoring anchor thresholds.
Discovers and loads active scoring anchor configs from `config/scoring_anchors.v*.json`.
Ensures fallback to v0 (expert estimate uncalibrated) if no calibrated version is present.
"""

import json
from pathlib import Path
from typing import Any

# Default uncalibrated anchors (v0 fallback)
FALLBACK_ANCHORS: dict[str, Any] = {
    "version": "v0",
    "calibrated_from": "expert_estimate_uncalibrated",
    "calibration_date": "2026-08-13",
    "sample_size": 0,
    "holdout_mae": 0.0,
    "status": "active",
    "anchors": {
        "wpm": [
            [4.0, 70.0],
            [5.5, 95.0],
            [6.5, 115.0],
            [7.5, 140.0],
            [9.0, 170.0],
        ],
        "pause_ratio": [
            [4.0, 0.35],
            [5.5, 0.25],
            [6.5, 0.18],
            [7.5, 0.10],
            [9.0, 0.05],
        ],
        "filler_density": [
            [4.0, 8.0],
            [5.5, 5.0],
            [6.5, 3.0],
            [7.5, 1.5],
            [9.0, 0.5],
        ],
        "mtld": [
            [4.0, 35.0],
            [5.5, 55.0],
            [6.5, 70.0],
            [7.5, 90.0],
            [9.0, 110.0],
        ],
    },
}


def load_active_anchors(config_dir: str | Path = "config") -> dict[str, Any]:
    """
    Search `config_dir` for files named `scoring_anchors.v*.json`.
    Find and return the config dictionary where `status == "active"`.
    If multiple active configs exist, select the highest version or fallback to v0.
    """
    dir_path = Path(config_dir)
    if not dir_path.exists() or not dir_path.is_dir():
        return FALLBACK_ANCHORS

    config_files = sorted(dir_path.glob("scoring_anchors.v*.json"), reverse=True)
    active_configs: list[dict[str, Any]] = []

    for file_path in config_files:
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("status") == "active":
                    active_configs.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    if active_configs:
        return active_configs[0]

    return FALLBACK_ANCHORS


def get_anchor_points(
    config: dict[str, Any], feature_name: str
) -> list[tuple[float, float]]:
    """Extract anchor points as a list of (band, metric) tuples for a given feature."""
    anchors_dict = config.get("anchors", {})
    raw_points = anchors_dict.get(feature_name, [])
    return [(float(p[0]), float(p[1])) for p in raw_points]
