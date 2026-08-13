#!/usr/bin/env python3
"""
Scoring Threshold Bootstrap & Calibration Script.
Fits IsotonicRegression on CEFR-labeled speaking corpus or synthetic bootstrap proxy data
to determine anchor points for WPM, Pause Ratio, Filler Density, and MTLD.
"""

import argparse
import json
import logging
import random
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import train_test_split

from app.scoring.features import (
    WordTimestamp,
    compute_filler_density,
    compute_mtld,
    compute_pause_ratio,
    compute_wpm,
    interpolate_band,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("calibrate_thresholds")

CEFR_TO_IELTS_BAND = {
    "A2": 3.5,
    "B1": 4.5,
    "B2": 6.0,
    "C1": 7.5,
    "C2": 8.5,
}

TARGET_BANDS = [4.0, 5.5, 6.5, 7.5, 9.0]


def extract_item_features(item: dict[str, Any]) -> dict[str, float]:
    """Extract or calculate features from raw item timestamps/tokens if present."""
    features = item.get("features", {})
    if not features and "words" in item:
        words = item["words"]
        ts_words = [
            WordTimestamp(w["word"], w["start_time"], w["end_time"])
            for w in words
        ]
        tokens = [w["word"] for w in words]
        features = {
            "wpm": compute_wpm(ts_words),
            "pause_ratio": compute_pause_ratio(ts_words),
            "filler_density": compute_filler_density(ts_words),
            "mtld": compute_mtld(tokens) or 50.0,
        }
    return features


def generate_bootstrap_dataset(
    sample_size: int = 500, seed: int = 42
) -> list[dict[str, Any]]:
    """Generate realistic bootstrap samples mapped from CEFR levels for proxy calibration."""
    random.seed(seed)
    np.random.seed(seed)

    cefr_levels = ["A2", "B1", "B2", "C1", "C2"]
    dataset = []

    for _ in range(sample_size):
        cefr = random.choice(cefr_levels)
        band = CEFR_TO_IELTS_BAND[cefr]

        # Generate realistic features with noise centered on CEFR levels
        wpm = float(np.clip(np.random.normal(30.0 + band * 15.0, 10.0), 30, 220))
        pause_ratio = float(
            np.clip(np.random.normal(0.45 - band * 0.045, 0.05), 0.02, 0.6)
        )
        filler_density = float(
            np.clip(np.random.normal(12.0 - band * 1.3, 1.5), 0.1, 15.0)
        )
        mtld = float(
            np.clip(np.random.normal(15.0 + band * 11.0, 8.0), 15, 140)
        )

        dataset.append(
            {
                "cefr_label": cefr,
                "ielts_band_proxy": band,
                "features": {
                    "wpm": wpm,
                    "pause_ratio": pause_ratio,
                    "filler_density": filler_density,
                    "mtld": mtld,
                },
            }
        )

    return dataset


def load_corpus(file_path: Path) -> list[dict[str, Any]]:
    """Load external corpus JSON dataset."""
    if not file_path.exists():
        logger.warning(
            f"Corpus file {file_path} not found. Returning empty dataset."
        )
        return []

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception as e:
        logger.error(f"Failed to load corpus JSON: {e}")

    return []


def calibrate(
    corpus_path: Path | None = None,
    output_dir: Path = Path("config"),
    report_path: Path = Path("calibration_report.md"),
) -> dict[str, Any]:
    """Run calibration pipeline and output scoring_anchors.v1.json + report."""
    dataset = []
    calibrated_from = "Bootstrap proxy simulation (ICNALE / NICT JLE distribution profile)"

    if corpus_path and corpus_path.exists():
        raw_data = load_corpus(corpus_path)
        for item in raw_data:
            cefr = item.get("cefr_label")
            if cefr in CEFR_TO_IELTS_BAND:
                item["ielts_band_proxy"] = CEFR_TO_IELTS_BAND[cefr]
                item["features"] = extract_item_features(item)
                if item["features"]:
                    dataset.append(item)
        if dataset:
            calibrated_from = f"External Corpus ({corpus_path.name})"

    if not dataset:
        logger.info("Using generated bootstrap proxy dataset for calibration.")
        dataset = generate_bootstrap_dataset(sample_size=600)

    # Filter out items missing valid labels
    valid_dataset = [
        d for d in dataset if d.get("ielts_band_proxy") is not None
    ]
    if len(valid_dataset) < 20:
        raise ValueError("Insufficient dataset size for isotonic calibration.")

    train_data, val_data = train_test_split(
        valid_dataset, test_size=0.2, random_state=42
    )

    feature_specs = {
        "wpm": {"increasing": True, "inverse": False},
        "pause_ratio": {"increasing": False, "inverse": True},
        "filler_density": {"increasing": False, "inverse": True},
        "mtld": {"increasing": True, "inverse": False},
    }

    anchors_result: dict[str, list[list[float]]] = {}

    for feat_name, spec in feature_specs.items():
        X_train = np.array([d["features"][feat_name] for d in train_data])
        y_train = np.array([d["ielts_band_proxy"] for d in train_data])

        # Check expected relationship direction
        corr = np.corrcoef(X_train, y_train)[0, 1]
        expected_positive = spec["increasing"]
        if (corr < 0 and expected_positive) or (corr > 0 and not expected_positive):
            logger.warning(
                f"Feature '{feat_name}' correlation ({corr:.2f}) contradicts expected direction."
            )

        # Fit IsotonicRegression mapping metric -> band or band -> metric
        iso = IsotonicRegression(
            increasing=spec["increasing"], out_of_bounds="clip"
        )
        iso.fit(X_train, y_train)

        # Evaluate predicted values for standard target bands
        metric_anchors = []
        for band in TARGET_BANDS:
            # Find feature value corresponding to target band
            # Sample across metric range and pick closest predicted band
            metric_samples = np.linspace(X_train.min(), X_train.max(), 500)
            predicted_bands = iso.predict(metric_samples)
            closest_idx = int(np.argmin(np.abs(predicted_bands - band)))
            target_metric = float(metric_samples[closest_idx])
            metric_anchors.append([float(band), round(target_metric, 4)])

        anchors_result[feat_name] = metric_anchors

    # Validate overall MAE on holdout set
    val_errors = []
    for d in val_data:
        actual_band = d["ielts_band_proxy"]
        predicted_proxy_bands = []
        for feat_name, spec in feature_specs.items():
            feat_val = d["features"][feat_name]
            p_band = interpolate_band(
                feat_val, anchors_result[feat_name], inverse=spec["inverse"]
            )
            predicted_proxy_bands.append(p_band)
        pred_band = sum(predicted_proxy_bands) / len(predicted_proxy_bands)
        val_errors.append(abs(pred_band - actual_band))

    mae = float(np.mean(val_errors))

    # Deactivate existing v0 config if present
    v0_path = output_dir / "scoring_anchors.v0.json"
    if v0_path.exists():
        try:
            with v0_path.open("r", encoding="utf-8") as f:
                v0_data = json.load(f)
            v0_data["status"] = "inactive"
            with v0_path.open("w", encoding="utf-8") as f:
                json.dump(v0_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not deactivate v0 config: {e}")

    # Build v1 config
    config_v1 = {
        "version": "v1",
        "calibrated_from": calibrated_from,
        "calibration_date": "2026-08-13",
        "sample_size": len(valid_dataset),
        "holdout_mae": round(mae, 4),
        "status": "active",
        "anchors": anchors_result,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    v1_path = output_dir / "scoring_anchors.v1.json"
    with v1_path.open("w", encoding="utf-8") as f:
        json.dump(config_v1, f, indent=2)

    # Write calibration report
    report_content = f"""# Calibration Report — v1

- **Calibrated From:** {calibrated_from}
- **Sample Size:** {len(valid_dataset)} records ({len(train_data)} train / {len(val_data)} validation)
- **Holdout MAE:** {mae:.4f} IELTS Band
- **Status:** active

## Calibrated Anchor Points

### WPM Anchors
{json.dumps(anchors_result['wpm'], indent=2)}

### Pause Ratio Anchors
{json.dumps(anchors_result['pause_ratio'], indent=2)}

### Filler Density Anchors
{json.dumps(anchors_result['filler_density'], indent=2)}

### MTLD Anchors
{json.dumps(anchors_result['mtld'], indent=2)}
"""

    report_path.write_text(report_content, encoding="utf-8")
    logger.info(f"Calibration completed. Output written to {v1_path} and {report_path}")

    return config_v1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scoring Threshold Bootstrap & Calibration"
    )
    parser.add_argument(
        "--corpus", type=str, default=None, help="Path to CEFR corpus JSON"
    )
    parser.add_argument(
        "--output-dir", type=str, default="config", help="Config output directory"
    )
    parser.add_argument(
        "--report-path",
        type=str,
        default="calibration_report.md",
        help="Report path",
    )

    args = parser.parse_args()
    calibrate(
        corpus_path=Path(args.corpus) if args.corpus else None,
        output_dir=Path(args.output_dir),
        report_path=Path(args.report_path),
    )


if __name__ == "__main__":
    main()
