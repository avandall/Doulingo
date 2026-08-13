"""
Deep Scoring Agent — Tier 2 Scorer & Grammar Check (`app/scoring/tier2_deep.py`).
Evaluates deep language features across 4 IELTS axes:
- Fluency & Coherence (FC)
- Lexical Resource (LR)
- Grammatical Range & Accuracy (GRA)
- Pronunciation (PRON)

Uses spaCy parser with graceful fallback for grammar structure analysis,
reads anchor points from `config_loader` (no magic numbers), and produces
the authoritative `raw_score` used by `user_profile_engine`.
"""

import re
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.scoring.config_loader import get_anchor_points, load_active_anchors
from app.scoring.features import (
    WordTimestamp,
    compute_filler_density,
    compute_mtld,
    compute_pause_ratio,
    compute_wpm,
    interpolate_band,
)

# Attempt importing spacy safely
try:
    import spacy
    from spacy.language import Language

    try:
        NLP_MODEL: Language | None = spacy.load("en_core_web_sm")
    except Exception:
        NLP_MODEL = None
except ImportError:
    spacy = None  # type: ignore[assignment]
    NLP_MODEL = None


# Basic grammar error patterns for rule-based fallback check
COMMON_GRAMMAR_ERRORS = [
    (r"\b(he|she|it)\s+(go|do|have|want|like|need|say|think)\b", "Subject-verb agreement error"),
    (r"\b(i|they|we|you)\s+(is|was)\b", "Subject-verb agreement error"),
    (r"\b(can|could|should|would|must|may|might)\s+(can|could|should|would|must)\b", "Double modal verb"),
    (r"\ba\s+[aeiouAEIOU]\w+", "Indefinite article error (a before vowel)"),
    (r"\ban\s+[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]\w+", "Indefinite article error (an before consonant)"),
]

SUBORDINATE_CONJUNCTIONS = {
    "because",
    "although",
    "even though",
    "while",
    "whereas",
    "if",
    "unless",
    "since",
    "so that",
    "which",
    "that",
    "who",
    "whom",
    "whose",
    "where",
    "when",
}


@dataclass
class Tier2ScoreResult:
    """Result returned by Tier 2 Deep Scorer."""

    fluency_score: float
    lexical_score: float
    grammar_score: float
    pronunciation_score: float
    raw_score: float
    estimated_band: float
    latency_ms: float
    grammar_analysis: dict[str, Any] = field(default_factory=dict)
    metrics_detail: dict[str, Any] = field(default_factory=dict)


def analyze_grammar_spacy(text: str) -> dict[str, Any]:
    """
    Analyze grammatical complexity and errors using spaCy (or fallback rules).

    Returns details on:
    - total_sentences
    - subordinate_clause_count
    - clause_ratio (subordinate clauses per sentence)
    - error_count
    - detected_errors
    """
    if not text.strip():
        return {
            "total_sentences": 0,
            "subordinate_clause_count": 0,
            "clause_ratio": 0.0,
            "error_count": 0,
            "detected_errors": [],
            "used_spacy": False,
        }

    text_clean = text.strip()

    if NLP_MODEL is not None:
        doc = NLP_MODEL(text_clean)
        sentences = list(doc.sents)
        total_sentences = max(1, len(sentences))

        sub_clause_deps = {"advcl", "relcl", "ccomp", "xcomp", "acl"}
        subordinate_count = sum(
            1 for token in doc if token.dep_ in sub_clause_deps
        )

        detected_errors: list[str] = []
        # Rule-based error detection overlay
        for pattern, desc in COMMON_GRAMMAR_ERRORS:
            matches = re.findall(pattern, text_clean, flags=re.IGNORECASE)
            if matches:
                detected_errors.append(f"{desc}: {len(matches)} instance(s)")

        error_count = len(detected_errors)
        clause_ratio = subordinate_count / total_sentences

        return {
            "total_sentences": total_sentences,
            "subordinate_clause_count": subordinate_count,
            "clause_ratio": round(clause_ratio, 2),
            "error_count": error_count,
            "detected_errors": detected_errors,
            "used_spacy": True,
        }

    # Fallback when spaCy model is not available
    raw_sentences = [s for s in re.split(r"[.!?]+", text_clean) if s.strip()]
    total_sentences = max(1, len(raw_sentences))

    tokens_lower = text_clean.lower().split()
    subordinate_count = sum(
        1 for word in tokens_lower if word in SUBORDINATE_CONJUNCTIONS
    )

    detected_errors = []
    for pattern, desc in COMMON_GRAMMAR_ERRORS:
        matches = re.findall(pattern, text_clean, flags=re.IGNORECASE)
        if matches:
            detected_errors.append(f"{desc}: {len(matches)} instance(s)")

    error_count = len(detected_errors)
    clause_ratio = subordinate_count / total_sentences

    return {
        "total_sentences": total_sentences,
        "subordinate_clause_count": subordinate_count,
        "clause_ratio": round(clause_ratio, 2),
        "error_count": error_count,
        "detected_errors": detected_errors,
        "used_spacy": False,
    }


def compute_pronunciation_score(
    words: Sequence[WordTimestamp], fallback_confidence: float = 1.0
) -> float:
    """
    Calculate Pronunciation score (0-9) from ASR word-level confidence scores.
    Confidence maps linearly to band scale [4.0, 9.0].
    """
    if not words:
        avg_confidence = max(0.0, min(1.0, fallback_confidence))
    else:
        confidences = [w.confidence for w in words if hasattr(w, "confidence")]
        avg_confidence = (
            sum(confidences) / len(confidences) if confidences else fallback_confidence
        )

    avg_confidence = max(0.0, min(1.0, avg_confidence))
    # Map [0.5, 1.0] -> [4.0, 9.0]
    score = 4.0 + (avg_confidence * 5.0)
    return max(4.0, min(9.0, round(score, 2)))


def evaluate_tier2(
    words: Sequence[WordTimestamp],
    transcript: str,
    target_band: float = 6.0,
    config: dict[str, Any] | None = None,
) -> Tier2ScoreResult:
    """
    Evaluate Tier 2 deep speech & grammar metrics.

    Calculates sub-scores across 4 axes:
    - Fluency (FC): WPM, pause ratio, filler density
    - Lexical Resource (LR): MTLD & vocabulary diversity
    - Grammatical Range & Accuracy (GRA): Clause complexity & error density
    - Pronunciation (PRON): ASR confidence / GOP score

    Produces `raw_score = 0.3*FC + 0.25*LR + 0.25*GRA + 0.2*PRON`.
    """
    start_time = time.perf_counter()

    if config is None:
        config = load_active_anchors()

    tokens = [t for t in transcript.split() if t.strip(".,!?")]
    word_count = max(len(words), len(tokens))

    # 1. Fluency & Coherence (FC)
    wpm = compute_wpm(words)
    pause_ratio = compute_pause_ratio(words)
    filler_density = compute_filler_density(words)

    wpm_anchors = get_anchor_points(config, "wpm")
    pause_anchors = get_anchor_points(config, "pause_ratio")
    filler_anchors = get_anchor_points(config, "filler_density")

    band_wpm = interpolate_band(wpm, wpm_anchors, inverse=False)
    band_pause = interpolate_band(pause_ratio, pause_anchors, inverse=True)
    band_filler = interpolate_band(filler_density, filler_anchors, inverse=True)

    fc_score = round((band_wpm + band_pause + band_filler) / 3.0, 2)
    fc_score = max(4.0, min(9.0, fc_score))

    # 2. Lexical Resource (LR)
    mtld = compute_mtld(tokens)
    mtld_anchors = get_anchor_points(config, "mtld")

    if mtld is not None and mtld_anchors:
        lr_score = interpolate_band(mtld, mtld_anchors, inverse=False)
    else:
        # Fallback estimation based on unique token ratio
        unique_ratio = len(set(tokens)) / max(1, len(tokens))
        lr_score = 4.0 + (unique_ratio * 4.5)

    lr_score = max(4.0, min(9.0, round(lr_score, 2)))

    # 3. Grammatical Range & Accuracy (GRA)
    grammar_info = analyze_grammar_spacy(transcript)
    clause_ratio = float(grammar_info.get("clause_ratio", 0.0))
    error_count = int(grammar_info.get("error_count", 0))

    # Error density per 100 words
    error_density = (error_count / max(1, word_count)) * 100.0

    # Base grammar band: higher clause ratio -> higher band, higher error density -> lower band
    gra_base = 6.0 + (clause_ratio * 1.5) - (error_density * 0.5)
    gra_score = max(4.0, min(9.0, round(gra_base, 2)))

    # 4. Pronunciation (PRON)
    pron_score = compute_pronunciation_score(words)

    # Calculate overall weighted raw_score (0.3*FC + 0.25*LR + 0.25*GRA + 0.2*PRON)
    raw_score = round(
        (0.30 * fc_score)
        + (0.25 * lr_score)
        + (0.25 * gra_score)
        + (0.20 * pron_score),
        2,
    )
    estimated_band = max(4.0, min(9.0, raw_score))

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    metrics_detail = {
        "word_count": word_count,
        "wpm": round(wpm, 2),
        "pause_ratio": round(pause_ratio, 4),
        "filler_density": round(filler_density, 2),
        "mtld": round(mtld, 2) if mtld is not None else None,
        "clause_ratio": clause_ratio,
        "error_count": error_count,
    }

    return Tier2ScoreResult(
        fluency_score=fc_score,
        lexical_score=lr_score,
        grammar_score=gra_score,
        pronunciation_score=pron_score,
        raw_score=raw_score,
        estimated_band=estimated_band,
        latency_ms=round(elapsed_ms, 3),
        grammar_analysis=grammar_info,
        metrics_detail=metrics_detail,
    )
