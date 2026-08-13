"""
Real-Time Scoring Agent — Tier 1 Scorer (<300ms).
Evaluates lightweight fluency and lexical signals (WPM, Pause Ratio, Filler Density, Self-Corrections, MTLD).
Uses anchor points from `config_loader` to interpolate band sub-scores and emit `difficulty_adjustment` signals.
"""

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from app.scoring.config_loader import get_anchor_points, load_active_anchors
from app.scoring.features import (
    WordTimestamp,
    compute_filler_density,
    compute_mtld,
    compute_pause_ratio,
    compute_wpm,
    interpolate_band,
)

DifficultyAdjustment = Literal["increase", "hold", "decrease"]

SELF_CORRECTION_MARKERS = {
    "i mean",
    "sorry",
    "or rather",
    "rather",
    "let me rephrase",
    "what i meant",
    "i mean to say",
    "let me see",
    "actually",
}


def detect_self_corrections(
    words_or_tokens: Sequence[WordTimestamp | str],
) -> int:
    """
    Detect self-correction patterns in spoken text.
    Identifies marker phrases (e.g. 'i mean', 'sorry', 'or rather')
    as well as immediate word repetitions (e.g., 'the the', 'went went').
    """
    if not words_or_tokens:
        return 0

    tokens = [
        w.word.lower().strip(".,!?")
        if isinstance(w, WordTimestamp)
        else w.lower().strip(".,!?")
        for w in words_or_tokens
        if (w.word if isinstance(w, WordTimestamp) else w).strip(".,!?")
    ]

    count = 0
    text_lower = " ".join(tokens)

    # Check phrase markers
    for marker in SELF_CORRECTION_MARKERS:
        if marker in text_lower:
            count += text_lower.count(marker)

    # Check immediate word repetitions (stuttering/self-correction: "the the")
    for i in range(len(tokens) - 1):
        if (
            tokens[i]
            and tokens[i] == tokens[i + 1]
            and tokens[i] not in {"um", "uh", "umm", "erm", "hmm"}
        ):
            count += 1

    return count


@dataclass
class Tier1ScoreResult:
    """Result returned by Tier 1 Real-Time Scorer (<300ms)."""

    wpm: float
    pause_ratio: float
    filler_density: float
    mtld: float | None
    self_correction_count: int
    estimated_band: float
    difficulty_adjustment: DifficultyAdjustment
    latency_ms: float
    metrics_detail: dict[str, Any] = field(default_factory=dict)


def evaluate_tier1(
    words: Sequence[WordTimestamp],
    transcript: str | None = None,
    avg_asr_confidence: float = 1.0,
    target_band: float = 6.0,
    config: dict[str, Any] | None = None,
) -> Tier1ScoreResult:
    """
    Evaluate Tier 1 real-time metrics (<300ms latency requirement).

    Computes:
    - WPM (Words Per Minute)
    - Pause Ratio (>0.5s pause / total speech duration)
    - Filler Density (um, uh per 100 words)
    - Self-Correction Count (marker phrases & immediate repetitions)
    - MTLD (Lexical Diversity) if word count >= 10, else None

    Interpolates sub-bands using active anchor thresholds from `config_loader`.
    Outputs `difficulty_adjustment` signal ("increase" | "hold" | "decrease"):
    - Returns "hold" if word count < 5 or avg_asr_confidence < 0.6.
    - Returns "increase" if estimated_band >= target_band + 0.5.
    - Returns "decrease" if estimated_band <= target_band - 0.5.
    - Otherwise returns "hold".
    """
    start_time = time.perf_counter()

    if config is None:
        config = load_active_anchors()

    # Extract tokens for MTLD & self-correction
    if transcript:
        tokens = [t for t in transcript.split() if t.strip(".,!?")]
    else:
        tokens = [w.word for w in words if w.word.strip(".,!?")]

    # Calculate raw feature values
    wpm = compute_wpm(words)
    pause_ratio = compute_pause_ratio(words)
    filler_density = compute_filler_density(words)
    mtld = compute_mtld(tokens) if len(tokens) >= 10 else None
    self_correction_count = detect_self_corrections(words)

    # Sub-band interpolation using anchors
    wpm_anchors = get_anchor_points(config, "wpm")
    pause_anchors = get_anchor_points(config, "pause_ratio")
    filler_anchors = get_anchor_points(config, "filler_density")
    mtld_anchors = get_anchor_points(config, "mtld")

    band_wpm = interpolate_band(wpm, wpm_anchors, inverse=False)
    band_pause = interpolate_band(pause_ratio, pause_anchors, inverse=True)
    band_filler = interpolate_band(filler_density, filler_anchors, inverse=True)

    bands_to_average = [band_wpm, band_pause, band_filler]

    band_mtld: float | None = None
    if mtld is not None and mtld_anchors:
        band_mtld = interpolate_band(mtld, mtld_anchors, inverse=False)
        bands_to_average.append(band_mtld)

    # Calculate overall estimated band for Tier 1
    estimated_band = round(sum(bands_to_average) / len(bands_to_average), 2)
    estimated_band = max(4.0, min(9.0, estimated_band))

    # Guardrails for difficulty adjustment
    word_count = len(words)
    difficulty_adjustment: DifficultyAdjustment

    if word_count < 5 or avg_asr_confidence < 0.6:
        difficulty_adjustment = "hold"
    elif estimated_band >= target_band + 0.5:
        difficulty_adjustment = "increase"
    elif estimated_band <= target_band - 0.5:
        difficulty_adjustment = "decrease"
    else:
        difficulty_adjustment = "hold"

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    metrics_detail = {
        "word_count": word_count,
        "avg_asr_confidence": avg_asr_confidence,
        "sub_bands": {
            "wpm": round(band_wpm, 2),
            "pause_ratio": round(band_pause, 2),
            "filler_density": round(band_filler, 2),
            "mtld": round(band_mtld, 2) if band_mtld is not None else None,
        },
    }

    return Tier1ScoreResult(
        wpm=round(wpm, 2),
        pause_ratio=round(pause_ratio, 4),
        filler_density=round(filler_density, 2),
        mtld=round(mtld, 2) if mtld is not None else None,
        self_correction_count=self_correction_count,
        estimated_band=estimated_band,
        difficulty_adjustment=difficulty_adjustment,
        latency_ms=round(elapsed_ms, 3),
        metrics_detail=metrics_detail,
    )
