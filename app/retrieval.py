"""
app/retrieval.py
================
RAG Retrieval Layer v1 (TASK-005 & TASK-015).

Retrieves sample dialogues matching user topic, target IELTS band window,
and excludes dialogues seen by the user in the past 30 days (exposure history).
Supports 4-stage fallback cascade when strict results are insufficient (< 2 items).
Automatically logs exposure records to `user_content_exposure`.
"""

import logging
import math
import struct
import uuid
from dataclasses import dataclass
from typing import Any

from app.db import get_db_connection

log = logging.getLogger(__name__)


@dataclass
class RetrievedDialogue:
    id: str
    content_unit_id: str
    band_level: float
    turn_type: str | None
    function_tag: str | None
    ai_line: str
    user_model_answer: str
    score: float = 0.0


def compute_band_window(base_band: float, difficulty_signal: str) -> tuple[float, float]:
    """
    Computes (band_min, band_max) window based on base_band and difficulty_signal (TASK-015 / SPEC 2 section 2.4).
    - increase: (base_band, base_band + 1.5)
    - decrease: (base_band - 1.5, base_band)
    - hold / default: (base_band - 0.5, base_band + 1.0)
    """
    sig = (difficulty_signal or "").lower()
    if sig == "increase":
        return (base_band, base_band + 1.5)
    if sig == "decrease":
        return (base_band - 1.5, base_band)
    return (base_band - 0.5, base_band + 1.0)


def blob_to_floats(blob: bytes) -> list[float]:
    """Unpacks little-endian float32 bytes array into list of floats."""
    if not blob or len(blob) % 4 != 0:
        return []
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob))


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def log_exposure(user_id: str, dialogue_ids: list[str], conn: Any = None) -> list[str]:
    """
    Logs records in user_content_exposure for user_id and dialogue_ids.
    Returns list of generated exposure UUIDs.
    """
    if not user_id or not dialogue_ids:
        return []

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    created_ids = []
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO user_profile (user_id) VALUES (?)", (user_id,))
        for sd_id in dialogue_ids:
            exp_id = f"exp_{uuid.uuid4().hex[:12]}"
            cursor.execute(
                """
                INSERT INTO user_content_exposure (id, user_id, sample_dialogue_id, exposed_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (exp_id, user_id, sd_id),
            )
            created_ids.append(exp_id)
        conn.commit()
    except Exception as e:
        log.error("Failed to log user content exposure: %s", e)
    finally:
        if close_conn:
            conn.close()

    return created_ids


def retrieve_dialogues(
    user_id: str,
    topic_tags: list[str] | str,
    band_min: float,
    band_max: float,
    query_embedding: list[float] | None = None,
    limit: int = 4,
    auto_log_exposure: bool = True,
    conn: Any = None,
) -> list[RetrievedDialogue]:
    """
    Retrieves sample_dialogues matching criteria with a 4-stage fallback cascade:
      Stage 0: exposure_days=30, band_pad=0.0, use_topic=True
      Stage 1: exposure_days=7,  band_pad=0.0, use_topic=True
      Stage 2: exposure_days=7,  band_pad=0.5, use_topic=True
      Stage 3: exposure_days=0,  band_pad=0.5, use_topic=False

    Logs warning on each fallback stage (stage > 0).
    Logs error if fallback is exhausted (< 2 items).
    Automatically records retrieved dialogue exposure in user_content_exposure if auto_log_exposure=True.
    """
    # Normalize topic_tags
    if isinstance(topic_tags, str):
        parsed_tags = [t.strip() for t in topic_tags.split(",") if t.strip()]
    else:
        parsed_tags = [t.strip() for t in topic_tags if t and t.strip()]

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    stages = [
        {"exposure_days": 30, "band_pad": 0.0, "use_topic": True},
        {"exposure_days": 7, "band_pad": 0.0, "use_topic": True},
        {"exposure_days": 7, "band_pad": 0.5, "use_topic": True},
        {"exposure_days": 0, "band_pad": 0.5, "use_topic": False},
    ]

    selected_results: list[RetrievedDialogue] = []

    try:
        cursor = conn.cursor()

        for stage_idx, stage in enumerate(stages):
            cur_band_min = band_min - stage["band_pad"]
            cur_band_max = band_max + stage["band_pad"]
            use_topic = stage["use_topic"] and len(parsed_tags) > 0
            exposure_days = stage["exposure_days"]

            params: list[Any] = []
            where_clauses = ["sd.band_level BETWEEN ? AND ?"]
            params.extend([cur_band_min, cur_band_max])

            if use_topic:
                topic_conditions = []
                for tag in parsed_tags:
                    topic_conditions.append("cu.topic_tags LIKE ?")
                    params.append(f'%"{"".join(tag.split())}"%')
                    # Also support unquoted match for simple string tags
                    topic_conditions.append("cu.topic_tags LIKE ?")
                    params.append(f"%{tag}%")

                where_clauses.append(f"({' OR '.join(topic_conditions)})")

            if exposure_days > 0 and user_id:
                sub_query = f"sd.id NOT IN (SELECT sample_dialogue_id FROM user_content_exposure WHERE user_id = ? AND exposed_at > datetime('now', '-{int(exposure_days)} days'))"  # nosec B608
                where_clauses.append(sub_query)
                params.append(user_id)

            where_str = " AND ".join(where_clauses)
            query = f"SELECT sd.id, sd.content_unit_id, sd.band_level, sd.turn_type, sd.function_tag, sd.ai_line, sd.user_model_answer, sd.embedding FROM sample_dialogues sd JOIN content_units cu ON sd.content_unit_id = cu.id WHERE {where_str}"  # nosec B608

            cursor.execute(query, params)
            rows = cursor.fetchall()

            candidates: list[RetrievedDialogue] = []
            for r in rows:
                if isinstance(r, dict):
                    row_dict = r
                elif hasattr(r, "keys"):
                    row_dict = dict(r)
                else:
                    row_dict = {
                        "id": r[0],
                        "content_unit_id": r[1],
                        "band_level": r[2],
                        "turn_type": r[3],
                        "function_tag": r[4],
                        "ai_line": r[5],
                        "user_model_answer": r[6],
                        "embedding": r[7],
                    }

                score = 0.0
                if query_embedding is not None and row_dict.get("embedding"):
                    raw_emb = row_dict["embedding"]
                    if isinstance(raw_emb, bytes):
                        vec = blob_to_floats(raw_emb)
                        score = cosine_similarity(query_embedding, vec)

                candidates.append(
                    RetrievedDialogue(
                        id=row_dict["id"],
                        content_unit_id=row_dict["content_unit_id"],
                        band_level=float(row_dict["band_level"]),
                        turn_type=row_dict.get("turn_type"),
                        function_tag=row_dict.get("function_tag"),
                        ai_line=row_dict["ai_line"],
                        user_model_answer=row_dict["user_model_answer"],
                        score=score,
                    )
                )

            # Sort candidates: if query_embedding given, sort by score descending, else sort by band_level
            if query_embedding is not None:
                candidates.sort(key=lambda x: x.score, reverse=True)
            else:
                candidates.sort(key=lambda x: x.band_level)

            if len(candidates) >= 2 or stage_idx == len(stages) - 1:
                selected_results = candidates[:limit]

                if stage_idx > 0:
                    log.warning(
                        "Retrieval fallback stage %d triggered — content thin for topic=%s, band=%s-%s.",
                        stage_idx,
                        parsed_tags,
                        band_min,
                        band_max,
                    )
                break

        if len(selected_results) < 2:
            log.error(
                "Retrieval fallback exhausted — returning %d items for user=%s, topic=%s",
                len(selected_results),
                user_id,
                parsed_tags,
            )

        if selected_results and auto_log_exposure and user_id:
            log_exposure(user_id, [d.id for d in selected_results], conn=conn)

        return selected_results

    finally:
        if close_conn:
            conn.close()


def retrieve_adaptive_dialogues(
    user_id: str,
    topic_tags: list[str] | str,
    base_band: float,
    difficulty_signal: str,
    query_embedding: list[float] | None = None,
    limit: int = 4,
    auto_log_exposure: bool = True,
    conn: Any = None,
) -> list[RetrievedDialogue]:
    """
    Retrieves sample dialogues adaptively based on user base band estimate and difficulty signal.
    Computes (band_min, band_max) window using compute_band_window() and delegates to retrieve_dialogues().
    """
    band_min, band_max = compute_band_window(base_band, difficulty_signal)
    return retrieve_dialogues(
        user_id=user_id,
        topic_tags=topic_tags,
        band_min=band_min,
        band_max=band_max,
        query_embedding=query_embedding,
        limit=limit,
        auto_log_exposure=auto_log_exposure,
        conn=conn,
    )

