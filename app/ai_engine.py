"""
AI Engine for Duolingo Speak
Features Smart Failover & Automatic Key/Model Rotation:
- Rotates between Groq, Gemini (2.5 Flash, 3.6 Flash, 2.5 Flash-Lite, 1.5 Flash), OpenAI, Anthropic, and Ollama.
- Supports multiple comma-separated keys in .env (e.g., GEMINI_API_KEY=key1,key2).
- Catches 429 Rate Limits automatically and switches to the next available provider/key seamlessly.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from app.scenarios import get_scenario
from app.characters import get_character

load_dotenv()

class AIEngine:
    def __init__(self):
        self.reload_keys()

    def reload_keys(self):
        load_dotenv(override=True)
        # Parse comma-separated keys
        self.gemini_keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
        self.groq_keys = [k.strip() for k in os.getenv("GROQ_API_KEY", "").split(",") if k.strip()]
        self.openai_keys = [k.strip() for k in os.getenv("OPENAI_API_KEY", "").split(",") if k.strip()]
        self.anthropic_keys = [k.strip() for k in os.getenv("ANTHROPIC_API_KEY", "").split(",") if k.strip()]
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3").strip()

        # Models prioritized by rate limit optimization (Exact user provided list)
        self.gemini_models = [
            "gemini-2.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemma-4-26b",
            "gemma-4-31b",
            "gemini-2.5-flash",
            "gemini-3.6-flash",
        ]
        self.groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768"
        ]

    def process_turn(
        self,
        scenario_id: str,
        character_id: Optional[str],
        user_transcript: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process user spoken turn with smart rate-limit failover across Groq & Gemini keys/models.
        """
        self.reload_keys()

        scenario = get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        default_char = scenario.get("default_character", "rajesh")
        char_key = character_id if character_id else default_char
        character = get_character(char_key)

        turn_count = len(conversation_history) // 2 + 1
        target_turns = scenario["target_turns"]

        prompt = self._build_token_efficient_prompt(
            scenario=scenario,
            character=character,
            user_transcript=user_transcript,
            history=conversation_history,
            turn_count=turn_count,
            target_turns=target_turns
        )

        # 1. Primary: Try Groq Keys & Models (Highest Quota: 30 RPM)
        for key in self.groq_keys:
            for model in self.groq_models:
                try:
                    res = self._call_groq(prompt, key, model)
                    if res:
                        return res
                except Exception as e:
                    print(f"[AI Engine] Groq ({model}) Rate Limit / Error: {e}. Trying next...")

        # 2. Secondary: Try Gemini Keys & Models (Rate limit failover across 2.5 Flash, 3.6 Flash, 2.5 Flash-Lite, 1.5 Flash)
        for key in self.gemini_keys:
            for model in self.gemini_models:
                try:
                    res = self._call_gemini(prompt, key, model)
                    if res:
                        return res
                except Exception as e:
                    print(f"[AI Engine] Gemini ({model}) Rate Limit / Error: {e}. Trying next...")

        # 3. Tertiary: Try OpenAI Keys
        for key in self.openai_keys:
            try:
                res = self._call_openai(prompt, key)
                if res:
                    return res
            except Exception as e:
                print(f"[AI Engine] OpenAI Rate Limit / Error: {e}. Trying next...")

        # 4. Quaternary: Try Anthropic Keys
        for key in self.anthropic_keys:
            try:
                res = self._call_anthropic(prompt, key)
                if res:
                    return res
            except Exception as e:
                print(f"[AI Engine] Anthropic Rate Limit / Error: {e}. Trying next...")

        # 5. Quinary: Try Ollama (Local)
        if self.ollama_base_url:
            try:
                res = self._call_ollama(prompt)
                if res:
                    return res
            except Exception:
                pass

        # If all keys and models hit rate limits or failed
        raise RuntimeError(
            "Tất cả lượt gọi API (Groq & Gemini) hiện tại đang bị Rate Limit hoặc chưa cấu hình API Key trong file .env. "
            "Vui lòng kiểm tra lại GEMINI_API_KEY hoặc GROQ_API_KEY trong file .env!"
        )

    def _build_token_efficient_prompt(
        self,
        scenario: Dict[str, Any],
        character: Dict[str, Any],
        user_transcript: str,
        history: List[Dict[str, str]],
        turn_count: int,
        target_turns: int
    ) -> str:
        recent_history = history[-4:] if history else []
        hist_str = ""
        for h in recent_history:
            role = "U" if h.get("role") == "user" else "A"
            hist_str += f"{role}:{h.get('content')} | "

        return f"""Role: {character['name']} ({character['country']}, {character['role']}). Style: {character['speech_style']}.
Topic: {scenario['title']}. Turn: {turn_count}/{target_turns}.
Hist: {hist_str}
User: "{user_transcript}"

Task: Reply in 1-4 concise sentences in character (<100 words). Evaluate English fluency.
Output JSON ONLY:
{{
  "ai_response": "1-4 sentence response",
  "ai_response_vi": "Vietnamese translation",
  "fluency_score": 75-100,
  "grammar_status": "Clean & Clear" or brief fix,
  "corrected_text": "Corrected sentence or same",
  "native_phrasing": "Native way to express user idea",
  "duo_reaction": "celebrate"|"happy"|"encouraging",
  "is_completed": false
}}"""

    def _call_gemini(self, prompt: str, api_key: str, model_name: str) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 400,
                "temperature": 0.7,
                "responseMimeType": "application/json"
            }
        }
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_groq(self, prompt: str, api_key: str, model_name: str) -> Optional[Dict[str, Any]]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_openai(self, prompt: str, api_key: str) -> Optional[Dict[str, Any]]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_anthropic(self, prompt: str, api_key: str) -> Optional[Dict[str, Any]]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}]
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["content"][0]["text"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"num_predict": 400}
        }
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["response"]
            return self._parse_json_response(text)
        return None

    def _parse_json_response(self, raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]

        data = json.loads(text)
        return {
            "ai_response": data.get("ai_response", "That's a very interesting point! Tell me more."),
            "ai_response_vi": data.get("ai_response_vi", "Đó là một điểm rất thú vị! Hãy kể cho tôi nghe thêm."),
            "user_feedback": {
                "fluency_score": data.get("fluency_score", 90),
                "word_count": len(data.get("corrected_text", "").split()),
                "grammar_status": data.get("grammar_status", "Clean & Clear"),
                "corrected_text": data.get("corrected_text", ""),
                "native_phrasing": data.get("native_phrasing", ""),
                "duo_reaction": data.get("duo_reaction", "happy"),
                "xp_earned": 10
            },
            "turn_index": 1,
            "is_completed": data.get("is_completed", False)
        }

ai_engine = AIEngine()
