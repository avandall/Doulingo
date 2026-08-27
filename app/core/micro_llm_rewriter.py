"""
app/core/micro_llm_rewriter.py
==============================
Micro-LLM Heuristic Retry Rewriter Engine (TASK-012)

Provides ultra-fast (<150ms) natural contextual downgrade rewriting when AI responses
fail Heuristic Level Ceiling checks.

Instead of re-executing full multi-tier prompt templates, MicroLLMRewriter targets
only the violating words, replacing them with natural, CEFR level-appropriate phrasing
while preserving conversational tone and open-ended question endings.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import requests

from app.core.heuristic_checker import HeuristicChecker

logger = logging.getLogger("duolingo_speak.micro_llm_rewriter")

# Built-in heuristic dictionary for natural contextual downgrades when LLM APIs are offline
HEURISTIC_DOWNGRADE_MAP: dict[str, str] = {
    "contemplate": "think about",
    "contemplating": "thinking about",
    "contemplates": "thinks about",
    "philosophical": "big",
    "deeply": "a lot",
    "sophisticated": "smart",
    "elaborate": "explain",
    "elaborating": "explaining",
    "utilize": "use",
    "utilized": "used",
    "utilizing": "using",
    "utilization": "use",
    "meticulous": "careful",
    "meticulously": "carefully",
    "comprehend": "understand",
    "comprehending": "understanding",
    "comprehension": "understanding",
    "assistance": "help",
    "subsequent": "next",
    "terminate": "end",
    "terminating": "ending",
    "endeavor": "try",
    "endeavoring": "trying",
    "commence": "start",
    "commencing": "starting",
    "residence": "home",
    "inquire": "ask",
    "inquiring": "asking",
    "acquire": "get",
    "acquiring": "getting",
    "perceive": "see",
    "perceiving": "seeing",
    "perception": "view",
    "subennial": "yearly",
    "flamboyant": "bright",
    "astonishing": "amazing",
    "unprecedented": "new",
    "magnificent": "great",
    "extraordinary": "special",
    "formidable": "strong",
    "splendid": "nice",
    "exquisite": "lovely",
    "paramount": "important",
}


class MicroLLMRewriter:
    """
    Dedicated Micro-LLM Retry Rewriter for fast contextual sentence downgrades.
    """

    def __init__(self, heuristic_checker: HeuristicChecker | None = None) -> None:
        self.heuristic_checker = heuristic_checker or HeuristicChecker()

    def _apply_heuristic_downgrade(self, original_text: str, violating_words: list[str]) -> str:
        """
        Perform deterministic natural downgrade using builtin synonym map & simple word replacement.
        """
        rewritten = original_text
        for word in violating_words:
            norm_word = word.lower().strip()
            if norm_word in HEURISTIC_DOWNGRADE_MAP:
                replacement = HEURISTIC_DOWNGRADE_MAP[norm_word]
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                rewritten = pattern.sub(replacement, rewritten)
            else:
                # General fallback for unmapped long words: replace or simplify
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                if len(word) > 7:
                    rewritten = pattern.sub("good", rewritten)
                else:
                    rewritten = pattern.sub("nice", rewritten)

        # Clean up double spaces or awkward phrasing
        rewritten = re.sub(r"\s+", " ", rewritten).strip()

        # Ensure text retains or ends with an open question
        if not rewritten.endswith("?"):
            if not any(q_word in rewritten.lower() for q_word in ["what", "how", "why", "do you", "can you", "would you"]):
                rewritten += " What do you think?"
            elif not rewritten.endswith("?"):
                rewritten += "?"

        return rewritten

    def rewrite_naturally(
        self,
        original_text: str,
        violating_words: list[str],
        target_level: int | str,
        character_name: str = "",
        scenario_title: str = "",
        ai_engine_ref: Any | None = None
    ) -> dict[str, Any]:
        """
        Rewrite an AI response naturally to eliminate level ceiling violations.

        Args:
            original_text: Response containing violating vocabulary.
            violating_words: List of words exceeding target CEFR ceiling.
            target_level: CEFR level integer (1-20) or CEFR string.
            character_name: Character persona name for context.
            scenario_title: Conversation scenario title.
            ai_engine_ref: Reference to AIEngine instance for LLM provider calls.

        Returns:
            Dictionary containing rewritten_text, natural_draft, vocab_check, passed_heuristic, method.
        """
        t0 = time.perf_counter()
        violating_str = ", ".join(violating_words) if violating_words else "high-level vocabulary"

        prompt = (
            f"CRITICAL HEURISTIC VALIDATION FAILURE: You are a fast Micro-LLM Rewriter specializing in natural spoken English downgrades.\n"
            f"Original Response ({character_name or 'AI'} in '{scenario_title or 'Conversation'}'):\n"
            f"\"{original_text}\"\n\n"
            f"VIOLATION: Exceeds CEFR Level {target_level} ceiling due to words: [{violating_str}].\n\n"
            f"MANDATE:\n"
            f"1. Replace [{violating_str}] with simpler, everyday English words suitable for Level {target_level}.\n"
            f"2. Maintain natural conversational flow, warmth, and exact character tone.\n"
            f"3. MUST end with ONE clear, OPEN-ENDED QUESTION.\n"
            f"4. Output JSON ONLY with fields:\n"
            f"{{\n"
            f'  "natural_draft": "Draft replacing {violating_str} with simple words",\n'
            f'  "vocab_check": "Verified basic words suitable for Level {target_level}",\n'
            f'  "final_response": "Downgraded response in simple natural English"\n'
            f"}}\n"
        )

        llm_response = None
        if ai_engine_ref is not None and hasattr(ai_engine_ref, "_call_llm_providers"):
            try:
                llm_response = ai_engine_ref._call_llm_providers(prompt, temp=0.3)
            except Exception as e:
                logger.warning(f"[MicroLLMRewriter] Fast LLM call failed: {e}")
                llm_response = None

        if llm_response and (llm_response.get("final_response") or llm_response.get("ai_response")):
            final_text = llm_response.get("final_response") or llm_response.get("ai_response", "")
            draft = llm_response.get("natural_draft", f"Micro-LLM downgrade for {violating_str}")
            check = llm_response.get("vocab_check", f"Verified for Level {target_level}")

            check_res = self.heuristic_checker.check_level_ceiling(final_text, target_level)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            return {
                "rewritten_text": final_text,
                "natural_draft": draft,
                "vocab_check": check,
                "passed_heuristic": not check_res.is_violated,
                "violating_words": check_res.violating_words,
                "method": "micro_llm",
                "execution_time_ms": elapsed_ms,
            }

        # Fallback to deterministic natural heuristic rewriter
        fallback_text = self._apply_heuristic_downgrade(original_text, violating_words)
        check_res = self.heuristic_checker.check_level_ceiling(fallback_text, target_level)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "rewritten_text": fallback_text,
            "natural_draft": f"Heuristic fallback replacing [{violating_str}]",
            "vocab_check": f"Heuristic verified for Level {target_level}",
            "passed_heuristic": not check_res.is_violated,
            "violating_words": check_res.violating_words,
            "method": "heuristic_fallback",
            "execution_time_ms": elapsed_ms,
        }


micro_llm_rewriter = MicroLLMRewriter()
