"""
app/conversational_agent.py
============================
Conversational Agent & Structured JSON Parser (TASK-007).

Step [5] of the 5-step conversational pipeline:
1. Assembles payload using app.prompt_constructor (TASK-006).
2. Invokes LLM API (Groq / Gemini / custom LLM client).
3. Parses structured JSON response into ConversationalResponse dataclass.
4. Ensures internal scoring signals (internal_band_signal, difficulty_adjustment)
   are kept private and safe fallback responses are provided on error.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable

import requests

from app.prompt_constructor import PromptContext, construct_messages

log = logging.getLogger(__name__)

VALID_DIFFICULTY_ADJUSTMENTS = {"increase", "hold", "decrease"}


@dataclass
class ConversationalResponse:
    ai_utterance: str
    internal_band_signal: float | str
    topic_tag: str
    difficulty_adjustment: str  # "increase" | "hold" | "decrease"
    raw_json: dict[str, Any] | None = field(default=None)
    is_fallback: bool = False


def parse_conversational_response(
    raw_text: str,
    fallback_topic: str = "general_conversation",
    default_band: float = 6.0,
) -> ConversationalResponse:
    """
    Parses raw string output from LLM into a validated ConversationalResponse object.
    Strips markdown code blocks, handles malformed JSON, and provides graceful fallbacks.
    """
    if not raw_text or not raw_text.strip():
        return _make_fallback("Could you please tell me more about that?", fallback_topic, default_band)

    cleaned = raw_text.strip()

    # Strip markdown codeblocks like ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    parsed_dict: dict[str, Any] | None = None

    # Try direct JSON parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            parsed_dict = data
    except json.JSONDecodeError:
        pass

    # If direct parse failed, attempt regex extraction of JSON object {...}
    if parsed_dict is None:
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if isinstance(data, dict):
                    parsed_dict = data
            except json.JSONDecodeError:
                pass

    if parsed_dict is None:
        # If parsing completely failed, use cleaned text as ai_utterance if non-empty
        return _make_fallback(cleaned, fallback_topic, default_band)

    # Extract & validate fields
    ai_utterance = str(parsed_dict.get("ai_utterance", "")).strip()
    if not ai_utterance:
        ai_utterance = "That's an interesting point. What else can you share about it?"

    internal_band_signal = parsed_dict.get("internal_band_signal", default_band)
    if isinstance(internal_band_signal, (int, float)):
        internal_band_signal = float(internal_band_signal)
    elif isinstance(internal_band_signal, str):
        try:
            internal_band_signal = float(internal_band_signal)
        except ValueError:
            internal_band_signal = str(internal_band_signal)

    topic_tag = str(parsed_dict.get("topic_tag", fallback_topic)).strip() or fallback_topic

    diff_adj = str(parsed_dict.get("difficulty_adjustment", "hold")).strip().lower()
    if diff_adj not in VALID_DIFFICULTY_ADJUSTMENTS:
        diff_adj = "hold"

    return ConversationalResponse(
        ai_utterance=ai_utterance,
        internal_band_signal=internal_band_signal,
        topic_tag=topic_tag,
        difficulty_adjustment=diff_adj,
        raw_json=parsed_dict,
        is_fallback=False,
    )


def _make_fallback(
    text: str,
    topic: str,
    band: float,
) -> ConversationalResponse:
    """Helper to construct a safe fallback response."""
    safe_text = text.strip() or "That's interesting! Could you elaborate a bit more on that?"
    return ConversationalResponse(
        ai_utterance=safe_text,
        internal_band_signal=band,
        topic_tag=topic,
        difficulty_adjustment="hold",
        raw_json=None,
        is_fallback=True,
    )


class ConversationalAgent:
    """
    LLM-powered Conversational Agent for generating structured IELTS responses.
    """

    def __init__(
        self,
        llm_client: Callable[[list[dict[str, str]]], str] | Any | None = None,
        model: str = "groq/llama-3.3-70b-versatile",
    ):
        self.llm_client = llm_client
        self.model = model

    def generate_response(
        self,
        context: PromptContext,
        history: list[dict[str, str]] | None = None,
        user_utterance: str | None = None,
        llm_client_override: Callable[[list[dict[str, str]]], str] | Any | None = None,
    ) -> ConversationalResponse:
        """
        Executes Step [5] of the pipeline:
        1. Construct message payload with System Prompt & history.
        2. Invoke LLM client.
        3. Parse JSON response & return ConversationalResponse object.
        """
        messages = construct_messages(context, history=history, user_utterance=user_utterance)
        client = llm_client_override or self.llm_client

        raw_output: str | None = None

        if client is not None:
            try:
                if hasattr(client, "generate"):
                    raw_output = client.generate(messages)
                elif hasattr(client, "invoke"):
                    raw_output = client.invoke(messages)
                elif hasattr(client, "chat") and hasattr(client.chat, "completions"):
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                    )
                    raw_output = response.choices[0].message.content
                elif callable(client):
                    raw_output = client(messages)

                if raw_output is not None and not isinstance(raw_output, str):
                    raw_output = str(raw_output)
            except Exception as err:
                log.error("LLM client invocation failed: %s", err)
                return _make_fallback(
                    "That sounds interesting! Could you tell me a bit more about your thoughts on this topic?",
                    context.topic_tag,
                    context.band_estimate,
                )

        if raw_output is None:
            # Fallback to direct HTTP request if GROQ_API_KEY is available
            raw_output = _call_groq_api_direct(messages)

        if raw_output is None:
            log.warning("No LLM client or API key available, using safe fallback response.")
            return _make_fallback(
                "That's a fascinating topic! What else would you like to share about it?",
                context.topic_tag,
                context.band_estimate,
            )

        return parse_conversational_response(
            raw_text=raw_output,
            fallback_topic=context.topic_tag,
            default_band=context.band_estimate,
        )


def _call_groq_api_direct(messages: list[dict[str, str]]) -> str | None:
    """Helper to directly call Groq API if GROQ_API_KEY env variable is present."""
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data["choices"][0]["message"]["content"]
        else:
            log.error("Groq API returned error status %d: %s", res.status_code, res.text)
            return None
    except Exception as err:
        log.error("Groq direct API call failed: %s", err)
        return None
