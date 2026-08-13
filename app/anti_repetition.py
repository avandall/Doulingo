"""
app/anti_repetition.py
=======================
Embedding Anti-Repetition Engine (TASK-016)

Compares newly generated AI utterances (output of TASK-007) against N past utterances
spoken to the user in the last 30 days / session history using cosine similarity of embeddings.
If similarity > threshold (default 0.85), flags the utterance as repetitive and generates a
re-generation directive for the LLM.
"""

import math
import re
import time
from dataclasses import dataclass
from typing import Any

# Optional sentence_transformers import with fallback
_MODEL = None


def _get_sentence_transformer():
    """Lazy load local SentenceTransformer model if available."""
    global _MODEL
    if _MODEL is False:
        return None
    if _MODEL is not None:
        return _MODEL
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        return _MODEL
    except Exception:
        _MODEL = False
        return None


def fallback_text_embedding(text: str, dim: int = 384) -> list[float]:
    """
    Fast, deterministic fallback embedding using character n-gram hashing trick.
    Guarantees sub-1ms execution time and 384 dimensions when model is unavailable.
    """
    words = re.findall(r"\w+", text.lower())
    if not words:
        return [0.0] * dim

    vec = [0.0] * dim
    # Hash 1-grams, 2-grams, 3-grams
    ngrams = []
    ngrams.extend(words)
    ngrams.extend([f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)])
    ngrams.extend([f"{words[i]}_{words[i+1]}_{words[i+2]}" for i in range(len(words) - 2)])

    for ngram in ngrams:
        idx = hash(ngram) % dim
        vec[idx] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def get_embedding(text: str) -> list[float]:
    """Generate vector embedding for text using sentence-transformers or fallback."""
    model = _get_sentence_transformer()
    if model is not None:
        try:
            vec = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
            return vec.tolist()
        except Exception:
            pass
    return fallback_text_embedding(text)


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vector embeddings."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 <= 1e-9 or norm2 <= 1e-9:
        return 0.0

    sim = dot / (norm1 * norm2)
    # Clamp due to floating point precision
    return max(0.0, min(1.0, float(sim)))


@dataclass
class RepetitionCheckResult:
    """Dataclass holding anti-repetition check result."""

    is_repetitive: bool
    max_similarity: float
    matched_utterance: str | None
    re_generation_directive: str | None
    execution_time_ms: float


def check_repetition(
    candidate_utterance: str,
    history_utterances: list[str] | None = None,
    similarity_threshold: float = 0.85,
    candidate_embedding: list[float] | None = None,
    history_embeddings: list[list[float]] | None = None,
) -> RepetitionCheckResult:
    """
    Check if candidate utterance is too similar to any utterance in history.

    Args:
        candidate_utterance: Newly generated AI response string.
        history_utterances: Optional list of past AI response strings.
        similarity_threshold: Threshold above which content is marked repetitive (default 0.85).
        candidate_embedding: Optional pre-computed embedding for candidate.
        history_embeddings: Optional pre-computed embeddings corresponding to history_utterances.

    Returns:
        RepetitionCheckResult object with detection details and LLM re-generation directive.
    """
    start_time = time.perf_counter()

    history_utterances = history_utterances or []
    if not history_utterances and not history_embeddings:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return RepetitionCheckResult(
            is_repetitive=False,
            max_similarity=0.0,
            matched_utterance=None,
            re_generation_directive=None,
            execution_time_ms=elapsed_ms,
        )

    # Calculate candidate embedding if missing
    if candidate_embedding is None:
        candidate_embedding = get_embedding(candidate_utterance)

    max_sim = 0.0
    matched_text: str | None = None

    # Case 1: Pre-computed history embeddings provided
    if history_embeddings:
        for idx, hist_vec in enumerate(history_embeddings):
            sim = cosine_similarity(candidate_embedding, hist_vec)
            if sim > max_sim:
                max_sim = sim
                matched_text = (
                    history_utterances[idx] if idx < len(history_utterances) else None
                )

    # Case 2: Pure history utterances provided
    elif history_utterances:
        for hist_text in history_utterances:
            hist_vec = get_embedding(hist_text)
            sim = cosine_similarity(candidate_embedding, hist_vec)
            if sim > max_sim:
                max_sim = sim
                matched_text = hist_text

    is_repetitive = max_sim >= similarity_threshold
    directive = None
    if is_repetitive:
        ref_clause = f": '{matched_text}'" if matched_text else ""
        directive = (
            f"Hội thoại vừa sinh bị trùng lặp motif ({max_sim:.2f} similarity{ref_clause}). "
            "Hãy diễn đạt khác đi, đổi góc nhìn hoặc cấu trúc câu và tránh lặp từ vựng/motif cũ."
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return RepetitionCheckResult(
        is_repetitive=is_repetitive,
        max_similarity=round(max_sim, 4),
        matched_utterance=matched_text,
        re_generation_directive=directive,
        execution_time_ms=round(elapsed_ms, 2),
    )


def fetch_user_history_utterances(
    user_id: str, conn: Any = None, limit: int = 30
) -> list[str]:
    """Fetch past AI lines exposed to user from database."""
    close_conn = False
    if conn is None:
        from app.db import get_db_connection

        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sd.ai_line
            FROM sample_dialogues sd
            JOIN user_content_exposure uce ON sd.id = uce.sample_dialogue_id
            WHERE uce.user_id = ?
            ORDER BY uce.exposed_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        past_lines = []
        for r in rows:
            if isinstance(r, (list, tuple)):
                past_lines.append(r[0])
            elif isinstance(r, dict):
                past_lines.append(r.get("ai_line", ""))
            elif hasattr(r, "keys"):
                past_lines.append(r["ai_line"])
        return [p for p in past_lines if p]
    except Exception:
        return []
    finally:
        if close_conn:
            conn.close()


def check_user_repetition(
    user_id: str,
    candidate_utterance: str,
    conn: Any = None,
    limit: int = 30,
    similarity_threshold: float = 0.85,
) -> RepetitionCheckResult:
    """Fetch user's past exposure history from DB and run anti-repetition check."""
    history = fetch_user_history_utterances(user_id, conn=conn, limit=limit)
    return check_repetition(
        candidate_utterance=candidate_utterance,
        history_utterances=history,
        similarity_threshold=similarity_threshold,
    )
