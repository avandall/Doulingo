"""
app/services/feedback_service.py
=================================
Service for logging AI response ratings and updating Dialogue Bank (TASK-007).
Handles:
1. Validating rating inputs (hollow, out_of_context, good).
2. Appending rating logs into app/data/feedback_log.json.
3. Updating quality_score and blacklisting in app/data/sample_dialogue_bank.json.
4. Auto-incorporating highly-rated new responses into sample_dialogue_bank.json.
"""

import datetime
import json
import os
import uuid
from pathlib import Path
from typing import Any


class FeedbackService:
    """Service to handle user feedback on AI responses and adjust continuous dataset."""

    VALID_RATINGS = {"hollow", "out_of_context", "good"}

    def __init__(
        self,
        feedback_log_path: str | None = None,
        dialogue_bank_path: str | None = None,
    ) -> None:
        env_log = os.getenv("FEEDBACK_LOG_PATH")
        env_bank = os.getenv("DIALOGUE_BANK_PATH")
        log_path: str = feedback_log_path or env_log or "app/data/feedback_log.json"
        bank_path: str = dialogue_bank_path or env_bank or "app/data/sample_dialogue_bank.json"
        self.feedback_log_path = Path(log_path)
        self.dialogue_bank_path = Path(bank_path)

    def _resolve_path(self, p: Path) -> Path:
        """Resolves path relative to CWD if not absolute."""
        if not p.is_absolute() and not p.exists():
            resolved = Path(os.getcwd()) / p
            if resolved.exists() or resolved.parent.exists():
                return resolved
        return p

    def rate_response(
        self,
        response_text: str,
        rating: str,
        dialogue_id: str | None = None,
        context: dict[str, Any] | None = None,
        user_id: str | None = None,
        comments: str | None = None,
    ) -> dict[str, Any]:
        """
        Processes feedback rating for an AI response.

        Args:
            response_text: Text of the AI response being evaluated.
            rating: Rating grade ('hollow', 'out_of_context', 'good').
            dialogue_id: Optional ID of the matched exemplar.
            context: Optional dict containing metadata (level, persona, topic, etc.).
            user_id: Optional ID of the user submitting feedback.
            comments: Optional text comments/feedback.

        Returns:
            Dict summary of feedback recording and dialogue bank updates.

        Raises:
            ValueError: If response_text is empty or rating is invalid.
        """
        clean_text = (response_text or "").strip()
        if not clean_text:
            raise ValueError("response_text cannot be empty")

        normalized_rating = (rating or "").strip().lower()
        if normalized_rating not in self.VALID_RATINGS:
            valid_list = ", ".join(sorted(self.VALID_RATINGS))
            raise ValueError(f"Invalid rating '{rating}'. Must be one of: {valid_list}")

        # 1. Save entry to feedback_log.json
        feedback_entry = self._log_feedback(
            response_text=clean_text,
            rating=normalized_rating,
            dialogue_id=dialogue_id,
            context=context,
            user_id=user_id,
            comments=comments,
        )

        # 2. Update dialogue bank accordingly
        bank_result = self._update_dialogue_bank(
            response_text=clean_text,
            rating=normalized_rating,
            dialogue_id=dialogue_id,
            context=context,
        )

        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "feedback_id": feedback_entry["id"],
            "rating": normalized_rating,
            "bank_action": bank_result.get("action"),
            "dialogue_id": bank_result.get("dialogue_id"),
            "new_quality_score": bank_result.get("new_quality_score"),
            "is_blacklisted": bank_result.get("is_blacklisted", False),
        }

    def _log_feedback(
        self,
        response_text: str,
        rating: str,
        dialogue_id: str | None,
        context: dict[str, Any] | None,
        user_id: str | None,
        comments: str | None,
    ) -> dict[str, Any]:
        """Appends a new feedback log entry into feedback_log.json."""
        target_path = self._resolve_path(self.feedback_log_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        logs: list[dict[str, Any]] = []
        if target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        logs = content
            except Exception:
                logs = []

        entry_id = f"fb_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        entry = {
            "id": entry_id,
            "timestamp": timestamp,
            "response_text": response_text,
            "rating": rating,
            "dialogue_id": dialogue_id,
            "user_id": user_id,
            "context": context or {},
            "comments": comments,
        }

        logs.append(entry)

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        return entry

    def _update_dialogue_bank(
        self,
        response_text: str,
        rating: str,
        dialogue_id: str | None,
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Updates quality_score or adds new exemplars in sample_dialogue_bank.json."""
        target_path = self._resolve_path(self.dialogue_bank_path)
        if not target_path.exists():
            return {"action": "skipped_no_bank_file", "dialogue_id": None}

        bank: list[dict[str, Any]] = []
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    bank = content
        except Exception:
            return {"action": "skipped_invalid_bank_file", "dialogue_id": None}

        matched_item: dict[str, Any] | None = None

        # Search by dialogue_id or matching text
        if dialogue_id:
            for item in bank:
                if str(item.get("id")) == str(dialogue_id):
                    matched_item = item
                    break

        if matched_item is None:
            norm_target = response_text.strip().lower()
            for item in bank:
                ex_text = str(item.get("text", item.get("ai_response", ""))).strip().lower()
                if ex_text and ex_text == norm_target:
                    matched_item = item
                    break

        result_info: dict[str, Any] = {}

        if rating in ("hollow", "out_of_context"):
            if matched_item is not None:
                current_score = float(matched_item.get("quality_score", 4.0))
                # Penalize quality_score
                new_score = max(0.0, round(current_score - 1.5, 2))
                matched_item["quality_score"] = new_score
                # Blacklist if quality score drops to 2.0 or lower
                if new_score <= 2.0:
                    matched_item["is_blacklisted"] = True
                else:
                    matched_item["is_blacklisted"] = matched_item.get("is_blacklisted", False)

                result_info = {
                    "action": "penalized",
                    "dialogue_id": matched_item["id"],
                    "new_quality_score": new_score,
                    "is_blacklisted": matched_item.get("is_blacklisted", False),
                }
            else:
                result_info = {
                    "action": "penalized_no_match",
                    "dialogue_id": None,
                    "new_quality_score": None,
                }

        elif rating == "good":
            if matched_item is not None:
                current_score = float(matched_item.get("quality_score", 4.0))
                new_score = min(5.0, round(current_score + 0.5, 2))
                matched_item["quality_score"] = new_score
                matched_item["is_blacklisted"] = False

                result_info = {
                    "action": "boosted",
                    "dialogue_id": matched_item["id"],
                    "new_quality_score": new_score,
                    "is_blacklisted": False,
                }
            else:
                # Automatically create and add new high-scoring exemplar entry
                ctx = context or {}
                new_id = f"ex_auto_{uuid.uuid4().hex[:6]}"
                new_exemplar = {
                    "id": new_id,
                    "level": str(ctx.get("level", "A1")).upper(),
                    "persona": str(ctx.get("persona", "Lily")),
                    "persona_trait": str(ctx.get("persona_trait", "friendly, warm")),
                    "topic": str(ctx.get("topic", "general")),
                    "dialogue_act": str(ctx.get("dialogue_act", "statement")),
                    "user_input_context": str(ctx.get("user_input_context", "")),
                    "ai_response": response_text,
                    "text": response_text,
                    "word_count": len(response_text.split()),
                    "reviewed_by": "user_feedback_good",
                    "quality_score": 4.8,
                    "is_blacklisted": False,
                }
                bank.append(new_exemplar)

                result_info = {
                    "action": "added_new",
                    "dialogue_id": new_id,
                    "new_quality_score": 4.8,
                    "is_blacklisted": False,
                }

        # Save updated bank
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(bank, f, indent=2, ensure_ascii=False)

        return result_info
