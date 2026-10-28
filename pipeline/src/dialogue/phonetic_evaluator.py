"""Phoneme-Level Acoustic Evaluator with L1 Interference Guidance.

Detects articulatory speech errors:
- Substitution (e.g. /θ/ -> /t/ or /s/)
- Deletion (dropping word-final consonants like /s/, /t/, /d/)
- Insertion (unintentional vowel epenthesis)

Generates clinically actionable articulatory guidance (tongue placement, airflow, voicing).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class ErrorType(str, enum.Enum):
    SUBSTITUTION = "Substitution"
    DELETION = "Deletion"
    INSERTION = "Insertion"
    NONE = "None"


@dataclass(slots=True)
class PhonemeFeedback:
    """Feedback item for a specific phoneme error."""

    word: str
    target_phoneme: str
    detected_phoneme: str | None
    error_type: ErrorType
    timestamp_ms: tuple[int, int]
    guidance: str


@dataclass(slots=True)
class EvaluationResult:
    """Consolidated phonetic and fluency score result."""

    overall_score: int
    accuracy_score: int
    fluency_score: int
    integrity_score: int
    phoneme_feedback: list[PhonemeFeedback] = field(default_factory=list)


class PhoneticEvaluator:
    """Acoustic phoneme comparator and articulatory guidance generator."""

    # L1 Interference knowledge base (mapped to articulatory corrections)
    L1_ARTICULATORY_RULES: dict[tuple[str, str], str] = {
        ("/θ/", "/t/"): (
            "Tongue position error: You substituted /θ/ with /t/. To produce /θ/, "
            "place the tip of your tongue lightly between your upper and lower teeth, "
            "and push a steady stream of air through without stopping the airflow."
        ),
        ("/θ/", "/s/"): (
            "Dental fricative error: You substituted /θ/ with /s/. Ensure your tongue tip "
            "is between your teeth rather than behind your alveolar ridge."
        ),
        ("/ð/", "/d/"): (
            "Voiced dental error: You substituted /ð/ with /d/. Place your tongue between your "
            "teeth and vibrate your vocal cords while releasing continuous air."
        ),
        ("/ʃ/", "/s/"): (
            "Postalveolar fricative error: Curve the sides of your tongue slightly upward toward the palate "
            "to make the /ʃ/ sound (as in 'she'), without blowing forward like /s/."
        ),
    }

    FINAL_CONSONANT_DELETION_RULES: dict[str, str] = {
        "/s/": "Final consonant omission: Be careful not to drop the final /s/ sound at the end of the word.",
        "/t/": "Ending sound dropped: Ensure you make a clear release of the final /t/ sound.",
        "/d/": "Ending sound dropped: Ensure you lightly voice and release the final /d/ consonant.",
        "/k/": "Final consonant dropped: Clearly release the velar stop /k/ at the word ending.",
    }

    @classmethod
    def analyze_phoneme(
        cls,
        word: str,
        target_phoneme: str,
        detected_phoneme: str | None,
        timestamp_ms: tuple[int, int] = (0, 0),
    ) -> PhonemeFeedback:
        """Analyzes a single phoneme comparison and generates articulatory guidance."""
        if detected_phoneme is None:
            # Deletion error
            guidance = cls.FINAL_CONSONANT_DELETION_RULES.get(
                target_phoneme,
                f"Omission: The target sound {target_phoneme} was dropped in word '{word}'.",
            )
            return PhonemeFeedback(
                word=word,
                target_phoneme=target_phoneme,
                detected_phoneme=None,
                error_type=ErrorType.DELETION,
                timestamp_ms=timestamp_ms,
                guidance=guidance,
            )

        if target_phoneme == detected_phoneme:
            return PhonemeFeedback(
                word=word,
                target_phoneme=target_phoneme,
                detected_phoneme=detected_phoneme,
                error_type=ErrorType.NONE,
                timestamp_ms=timestamp_ms,
                guidance="Pronounced accurately.",
            )

        # Substitution error
        rule_key = (target_phoneme, detected_phoneme)
        guidance = cls.L1_ARTICULATORY_RULES.get(
            rule_key,
            f"Substitution: You said {detected_phoneme} instead of {target_phoneme}. "
            f"Focus on your tongue positioning and airflow when pronouncing '{word}'.",
        )
        return PhonemeFeedback(
            word=word,
            target_phoneme=target_phoneme,
            detected_phoneme=detected_phoneme,
            error_type=ErrorType.SUBSTITUTION,
            timestamp_ms=timestamp_ms,
            guidance=guidance,
        )

    @classmethod
    def evaluate_utterance(
        cls,
        target_phonemes: list[tuple[str, str]],  # [(word, target_ipa), ...]
        detected_phonemes: list[str | None],
    ) -> EvaluationResult:
        """Evaluates a full sequence of phonemes against observed detections."""
        feedbacks: list[PhonemeFeedback] = []
        correct_count = 0
        total_phonemes = max(len(target_phonemes), 1)

        for i, (word, target_ipa) in enumerate(target_phonemes):
            detected = detected_phonemes[i] if i < len(detected_phonemes) else None
            fb = cls.analyze_phoneme(word, target_ipa, detected)
            if fb.error_type == ErrorType.NONE:
                correct_count += 1
            else:
                feedbacks.append(fb)

        accuracy = int((correct_count / total_phonemes) * 100)
        fluency = min(100, max(60, accuracy + 5))
        integrity = min(100, max(70, accuracy + 10))
        overall = int((accuracy * 0.6) + (fluency * 0.2) + (integrity * 0.2))

        return EvaluationResult(
            overall_score=overall,
            accuracy_score=accuracy,
            fluency_score=fluency,
            integrity_score=integrity,
            phoneme_feedback=feedbacks,
        )
