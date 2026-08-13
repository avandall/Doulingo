"""
app/error_journal.py
=====================
Personal Error Journal & Interleaved Practice Weaver (TASK-020).

Logs recurring grammar and vocabulary errors for each user into `user_profile.recurring_errors`,
retrieves error patterns repeated > 2 times (or configurable threshold), and generates interleaved
practice prompt directives to embed subtle targeted practice/traps into upcoming AI conversation turns.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from app.db import get_user_profile, save_user_profile

log = logging.getLogger(__name__)


class ErrorJournalManager:
    """Manager for recording user errors and weaving interleaved practice directives."""

    def record_error(
        self,
        user_id: str,
        error_type: str,
        error_detail: str,
        context: str = "",
        conn: Any = None,
    ) -> dict[str, Any]:
        """
        Record a grammar or vocabulary error for a user in `user_profile.recurring_errors`.

        If an error with matching `error_type` and `error_detail` already exists,
        its `count` is incremented and `last_seen` timestamp updated.
        Otherwise, a new error record is appended.
        """
        profile = get_user_profile(user_id)
        recurring_errors = profile.get("recurring_errors", [])
        if not isinstance(recurring_errors, list):
            recurring_errors = []

        now_iso = datetime.now(UTC).isoformat()
        updated_entry: dict[str, Any] | None = None

        found = False
        normalized_errors: list[dict[str, Any]] = []

        for item in recurring_errors:
            if isinstance(item, str):
                entry: dict[str, Any] = {
                    "error_type": "general",
                    "error_detail": item,
                    "count": 1,
                    "last_seen": now_iso,
                    "context": "",
                }
            elif isinstance(item, dict):
                entry = dict(item)
            else:
                continue

            if (
                not found
                and str(entry.get("error_type", "")).lower() == error_type.lower()
                and str(entry.get("error_detail", "")).strip().lower()
                == error_detail.strip().lower()
            ):
                entry["count"] = int(entry.get("count", 1)) + 1
                entry["last_seen"] = now_iso
                if context:
                    entry["context"] = context
                found = True
                updated_entry = entry

            normalized_errors.append(entry)

        if not found:
            updated_entry = {
                "error_type": error_type,
                "error_detail": error_detail,
                "count": 1,
                "last_seen": now_iso,
                "context": context,
            }
            normalized_errors.append(updated_entry)

        profile["recurring_errors"] = normalized_errors
        save_user_profile(user_id, profile)

        log.info(
            "Recorded error for user '%s': [%s] %s (count=%d)",
            user_id,
            error_type,
            error_detail,
            updated_entry.get("count", 1) if updated_entry else 1,
        )

        return updated_entry or {}

    def get_recurring_errors(
        self,
        user_id: str,
        threshold: int = 2,
        conn: Any = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve errors repeated >= `threshold` times for a specific user.
        """
        profile = get_user_profile(user_id)
        recurring_errors = profile.get("recurring_errors", [])
        if not isinstance(recurring_errors, list):
            return []

        results: list[dict[str, Any]] = []
        for item in recurring_errors:
            if isinstance(item, str):
                entry: dict[str, Any] = {
                    "error_type": "general",
                    "error_detail": item,
                    "count": 1,
                    "last_seen": "",
                    "context": "",
                }
            elif isinstance(item, dict):
                entry = dict(item)
            else:
                continue

            count = int(entry.get("count", 1))
            if count >= threshold:
                results.append(entry)

        return results

    def weave_interleaved_practice_directives(
        self,
        user_id: str,
        current_topic: str = "",
        conn: Any = None,
    ) -> dict[str, Any]:
        """
        Construct prompt directives to embed subtle grammar/vocabulary practice or traps
        into upcoming conversation turns based on recurring errors.
        """
        recurring = self.get_recurring_errors(user_id, threshold=2, conn=conn)
        if not recurring:
            recurring = self.get_recurring_errors(user_id, threshold=1, conn=conn)

        if not recurring:
            return {
                "has_directives": False,
                "directives_text": "",
                "targeted_errors": [],
            }

        lines: list[str] = [
            "### INTERLEAVED PRACTICE DIRECTIVES (Error Journal Traps)",
            (
                "The user has a history of recurring grammar/vocabulary errors. "
                "Seamlessly weave subtle conversational opportunities or traps into your turn to prompt correct usage:"
            ),
        ]

        for idx, err in enumerate(recurring[:5], 1):
            etype = str(err.get("error_type", "error")).upper()
            detail = str(err.get("error_detail", ""))
            count = int(err.get("count", 1))
            ctx = f" (e.g. \"{err['context']}\")" if err.get("context") else ""
            lines.append(
                f"{idx}. [{etype}] {detail}{ctx} — repeated {count} times. "
                "Prompt or model the correct pattern in your response."
            )

        lines.append(
            "Instruction: Do NOT explicitly mock or lecture the user. "
            "Gently guide or structure your question so the user is encouraged to practice the correct form."
        )

        directives_text = "\n".join(lines)

        return {
            "has_directives": True,
            "directives_text": directives_text,
            "targeted_errors": recurring,
        }


# Global default instance & convenience functions
_default_manager = ErrorJournalManager()


def record_error(
    user_id: str,
    error_type: str,
    error_detail: str,
    context: str = "",
    conn: Any = None,
) -> dict[str, Any]:
    """Module-level convenience function for ErrorJournalManager.record_error."""
    return _default_manager.record_error(
        user_id=user_id,
        error_type=error_type,
        error_detail=error_detail,
        context=context,
        conn=conn,
    )


def get_recurring_errors(
    user_id: str,
    threshold: int = 2,
    conn: Any = None,
) -> list[dict[str, Any]]:
    """Module-level convenience function for ErrorJournalManager.get_recurring_errors."""
    return _default_manager.get_recurring_errors(
        user_id=user_id,
        threshold=threshold,
        conn=conn,
    )


def weave_interleaved_practice_directives(
    user_id: str,
    current_topic: str = "",
    conn: Any = None,
) -> dict[str, Any]:
    """Module-level convenience function for ErrorJournalManager.weave_interleaved_practice_directives."""
    return _default_manager.weave_interleaved_practice_directives(
        user_id=user_id,
        current_topic=current_topic,
        conn=conn,
    )
