"""
Feature extraction module for IELTS spoken evaluation.
Contains standard functions for WPM, pause ratio, filler density, MTLD, and linear band interpolation.
Used identically by calibration scripts and production real-time/deep scoring agents.
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class WordTimestamp:
    """Represents a single word with ASR timing and confidence information."""

    word: str
    start_time: float
    end_time: float
    confidence: float = 1.0


FILLER_LEXICON = {"um", "uh", "umm", "erm", "hmm"}


def compute_wpm(words: Sequence[WordTimestamp]) -> float:
    """Calculate Words Per Minute (WPM) from a sequence of word timestamps."""
    if not words:
        return 0.0

    speech_duration_sec = words[-1].end_time - words[0].start_time
    if speech_duration_sec <= 0:
        return 0.0

    return (len(words) / speech_duration_sec) * 60.0


def compute_pause_ratio(
    words: Sequence[WordTimestamp], pause_threshold: float = 0.5
) -> float:
    """Calculate the ratio of significant pause time (> pause_threshold sec) to total speech duration."""
    if len(words) < 2:
        return 0.0

    speech_duration_sec = words[-1].end_time - words[0].start_time
    if speech_duration_sec <= 0:
        return 0.0

    total_pause = 0.0
    for i in range(len(words) - 1):
        gap = words[i + 1].start_time - words[i].end_time
        if gap > pause_threshold:
            total_pause += gap

    ratio = total_pause / speech_duration_sec
    return max(0.0, min(1.0, ratio))


def compute_filler_density(
    words: Sequence[WordTimestamp | str]
) -> float:
    """Calculate filler word density per 100 words using a fixed lexicon (um, uh, umm, erm, hmm)."""
    if not words:
        return 0.0

    raw_tokens = [w.word if isinstance(w, WordTimestamp) else w for w in words]
    filler_count = sum(
        1
        for token in raw_tokens
        if token.lower().strip(".,!?") in FILLER_LEXICON
    )
    return (filler_count / len(raw_tokens)) * 100.0


def compute_mtld(
    tokens: Sequence[str], ttr_threshold: float = 0.72
) -> float | None:
    """
    Calculate Measure of Textual Lexical Diversity (MTLD) (McCarthy & Jarvis 2010).
    Runs forward and backward passes and averages factor counts.
    Returns None if token count is less than 10.
    """
    cleaned_tokens = [
        t.lower().strip(".,!?") for t in tokens if t.strip(".,!?")
    ]
    if len(cleaned_tokens) < 10:
        return None

    def _mtld_one_direction(token_list: Sequence[str]) -> float:
        factor_count = 0.0
        types: set[str] = set()
        token_count_in_factor = 0

        for token in token_list:
            types.add(token)
            token_count_in_factor += 1
            ttr = len(types) / token_count_in_factor
            if ttr <= ttr_threshold:
                factor_count += 1.0
                types = set()
                token_count_in_factor = 0

        if token_count_in_factor > 0:
            remaining_ttr = len(types) / token_count_in_factor
            partial_factor = (
                (1.0 - remaining_ttr) / (1.0 - ttr_threshold)
                if remaining_ttr < 1.0
                else 0.0
            )
            factor_count += partial_factor

        if factor_count > 0:
            return len(token_list) / factor_count
        return float(len(token_list))

    forward = _mtld_one_direction(cleaned_tokens)
    backward = _mtld_one_direction(list(reversed(cleaned_tokens)))
    return (forward + backward) / 2.0


def interpolate_band(
    value: float,
    anchors: Sequence[Sequence[float] | tuple[float, float]],
    inverse: bool = False,
) -> float:
    """
    Interpolate band level given piecewise linear anchors: [(band, metric_value), ...].
    If inverse=True, metric_value is expected to decrease as band increases (e.g. pause_ratio, filler_density).
    """
    if not anchors:
        return 5.5

    # Standardize to list of (band, metric) tuples
    typed_anchors = [(float(a[0]), float(a[1])) for a in anchors]

    # Sort by metric value
    points = sorted(typed_anchors, key=lambda x: x[1], reverse=inverse)
    bands = [p[0] for p in points]
    metrics = [p[1] for p in points]

    if inverse:
        metrics, bands = metrics[::-1], bands[::-1]

    if value <= metrics[0]:
        return bands[0]
    if value >= metrics[-1]:
        return bands[-1]

    for i in range(len(metrics) - 1):
        if metrics[i] <= value <= metrics[i + 1]:
            denom = metrics[i + 1] - metrics[i]
            if denom == 0:
                return bands[i]
            ratio = (value - metrics[i]) / denom
            return bands[i] + ratio * (bands[i + 1] - bands[i])

    return bands[-1]
