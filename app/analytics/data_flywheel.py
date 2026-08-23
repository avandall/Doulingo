"""
app/data_flywheel.py — High-Band User Answer Harvest Pipeline (TASK-023)

Harvests high-band user answers (Tier 2 score >= 7.5 overall, min axis >= 7.0, ASR confidence >= 0.85).
Enforces a 3-layer safety filter:
  Layer 1: PII Scrubbing via app.data_quality.pii_scrubber.check_pii (REJECT-FIRST)
  Rate Cap: Maximum 10 auto-harvested items per topic per week
  Layer 2: Quality & ASR confidence verification
  Layer 3: Vector Deduplication against sample_dialogues (similarity threshold 0.92)
  Staging: Insert into `harvest_review_queue` table with review_status='pending'

TUYỆT ĐỐI không insert trực tiếp vào sample_dialogues.
"""

from __future__ import annotations

import json
import logging
import math
import struct
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.anti_repetition import get_embedding
from app.data_quality.pii_scrubber import check_pii
from app.storage.db import get_db_connection

log = logging.getLogger(__name__)

MIN_AXIS_SCORE: float = 7.0
MIN_AVERAGE_SCORE: float = 7.5
MIN_ASR_CONFIDENCE: float = 0.85
MAX_AUTO_HARVEST_PER_TOPIC_PER_WEEK: int = 10

DUPLICATE_THRESHOLD: float = 0.92
SIMILAR_VARIANT_THRESHOLD: float = 0.75


@dataclass
class TurnData:
    """Dataclass encapsulating candidate user answer turn data for harvesting."""

    user_transcript: str
    ai_line: str
    source_user_id: str
    source_turn_id: str
    topic_tag: str = ""
    tier2_scores: dict[str, float] = field(default_factory=dict)
    avg_asr_confidence: float = 1.0
    embedding: list[float] | None = None


def blob_to_floats(blob: bytes | Any) -> list[float]:
    """Unpacks float32 bytes array or converts JSON/list to list of floats."""
    if isinstance(blob, bytes):
        if not blob or len(blob) % 4 != 0:
            return []
        n = len(blob) // 4
        return list(struct.unpack(f"<{n}f", blob))
    if isinstance(blob, str):
        try:
            parsed = json.loads(blob)
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        except Exception:
            return []
    if isinstance(blob, list):
        return [float(x) for x in blob]
    return []


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 <= 1e-9 or norm2 <= 1e-9:
        return 0.0
    sim = dot / (norm1 * norm2)
    return max(0.0, min(1.0, float(sim)))


def check_quality(tier2_scores: dict[str, float], avg_asr_confidence: float) -> bool:
    """
    Layer 2: Verify high-band quality criteria.
    - ASR confidence >= 0.85
    - All 4 axes (fluency, lexical, grammar, pronunciation) >= 7.0
    - Overall average across 4 axes >= 7.5
    """
    if avg_asr_confidence < MIN_ASR_CONFIDENCE:
        return False

    axes = ["fluency", "lexical", "grammar", "pronunciation"]
    scores = [tier2_scores.get(axis, 0.0) for axis in axes]

    if not scores or min(scores) < MIN_AXIS_SCORE:
        return False

    avg_score = sum(scores) / len(scores)
    if avg_score < MIN_AVERAGE_SCORE:
        return False

    return True


def check_rate_cap(topic_tag: str, conn: Any = None) -> bool:
    """
    Check rate cap: maximum 10 auto-harvested items per topic per week.
    Returns True if under cap, False if cap exceeded.
    """
    if not topic_tag:
        return True

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM harvest_review_queue
            WHERE topic_tag = ? AND created_at >= datetime('now', '-7 days')
            """,
            (topic_tag,),
        )
        row = cursor.fetchone()
        count = row[0] if row else 0
        return count < MAX_AUTO_HARVEST_PER_TOPIC_PER_WEEK
    except Exception as e:
        log.warning("Rate cap check query error: %s", e)
        return True
    finally:
        if close_conn:
            conn.close()


def check_dedup(
    candidate_embedding: list[float] | None,
    candidate_answer: str,
    conn: Any = None,
) -> tuple[str, float]:
    """
    Layer 3: Vector Deduplication against sample_dialogues.
    Returns (dedup_status, max_similarity):
        - "duplicate_rejected" if max_sim >= 0.92
        - "similar_variant" if max_sim >= 0.75
        - "unique" otherwise
    """
    if not candidate_embedding:
        candidate_embedding = get_embedding(candidate_answer)

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    max_sim = 0.0
    cand_clean = candidate_answer.strip().lower()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_model_answer, embedding FROM sample_dialogues")
        rows = cursor.fetchall()
        for row in rows:
            model_ans = (
                row["user_model_answer"]
                if isinstance(row, dict) or hasattr(row, "__getitem__")
                else row[0]
            )
            emb_blob = (
                row["embedding"]
                if isinstance(row, dict) or hasattr(row, "__getitem__")
                else row[1]
            )

            # Direct string match shortcut
            if model_ans and model_ans.strip().lower() == cand_clean:
                max_sim = 1.0
                break

            if emb_blob:
                emb_floats = blob_to_floats(emb_blob)
                if emb_floats and len(emb_floats) == len(candidate_embedding):
                    sim = cosine_similarity(candidate_embedding, emb_floats)
                    max_sim = max(max_sim, sim)
    except Exception as e:
        log.warning("Deduplication vector search warning: %s", e)
    finally:
        if close_conn:
            conn.close()

    if max_sim >= DUPLICATE_THRESHOLD:
        return "duplicate_rejected", max_sim
    if max_sim >= SIMILAR_VARIANT_THRESHOLD:
        return "similar_variant", max_sim
    return "unique", max_sim


def harvest_candidate(turn_data: TurnData, conn: Any = None) -> str:
    """
    Main Data Flywheel pipeline. Strictly executes safety layers in order:
      1. Layer 1: PII Scrubbing (REJECT-FIRST)
      2. Rate Cap check (max 10 items/topic/week)
      3. Layer 2: Quality verification
      4. Layer 3: Vector Deduplication
      5. Staging: Insert into `harvest_review_queue` table

    Returns status string:
      - "rejected_pii"
      - "rejected_rate_cap"
      - "rejected_quality"
      - "rejected_duplicate"
      - "queued_for_review"
    """
    # Layer 1: PII Scrubbing (Must be first to prevent PII leakage down pipeline)
    pii_passed, pii_entities = check_pii(turn_data.user_transcript)
    if not pii_passed:
        log.info(
            "Candidate rejected by PII scrubber: user_id=%s, entities=%s",
            turn_data.source_user_id,
            pii_entities,
        )
        return "rejected_pii"

    # Rate Cap check
    if not check_rate_cap(turn_data.topic_tag, conn=conn):
        log.info(
            "Candidate rejected by topic rate cap: topic=%s", turn_data.topic_tag
        )
        return "rejected_rate_cap"

    # Layer 2: Quality & ASR confidence check
    if not check_quality(turn_data.tier2_scores, turn_data.avg_asr_confidence):
        log.info("Candidate rejected by quality filter")
        return "rejected_quality"

    # Layer 3: Vector Deduplication
    dedup_status, max_sim = check_dedup(
        turn_data.embedding, turn_data.user_transcript, conn=conn
    )
    if dedup_status == "duplicate_rejected":
        log.info("Candidate rejected by vector dedup: max_sim=%.3f", max_sim)
        return "rejected_duplicate"

    # Staging: Save candidate into harvest_review_queue table
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    queue_id = f"hrq_{uuid.uuid4().hex[:12]}"
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO harvest_review_queue (
                id,
                candidate_ai_line,
                candidate_user_answer,
                source_user_id,
                source_turn_id,
                topic_tag,
                tier2_scores,
                pii_check_passed,
                pii_entities_found,
                dedup_max_similarity,
                dedup_status,
                review_status,
                reviewed_by,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, datetime('now'))
            """,
            (
                queue_id,
                turn_data.ai_line,
                turn_data.user_transcript,
                turn_data.source_user_id,
                turn_data.source_turn_id,
                turn_data.topic_tag,
                json.dumps(turn_data.tier2_scores),
                1 if pii_passed else 0,
                json.dumps(pii_entities),
                max_sim,
                dedup_status,
            ),
        )
        conn.commit()
        log.info("Candidate queued for review: queue_id=%s", queue_id)
        return "queued_for_review"
    except Exception as e:
        log.error("Failed to insert candidate into harvest_review_queue: %s", e)
        return "rejected_quality"
    finally:
        if close_conn:
            conn.close()
