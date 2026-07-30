"""
AI Engine for Duolingo Speak
Features:
- Meaning-Preserving Grammatical Correction (LLM preserves user's exact opinion/intent in corrected_text).
- Cleaned Punctuation & Contraction-Aware Deterministic Scoring.
- High Conversational Creativity (temperature = 0.85 + Dynamic Scenario Angle Randomizer).
- Single API Call Execution.
"""

import os
import re
import json
import random
import difflib
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from app.scenarios import get_scenario
from app.characters import get_character

load_dotenv()

# Dynamic Scenario Angle Presets for Endless Variety
SCENARIO_ANGLES = [
    "Focus on budget travel, hidden local spots, and street food recommendations.",
    "Focus on flight bookings, luggage packing essentials, and airport navigation.",
    "Focus on outdoor adventures, beach activities, and scenic nature spots.",
    "Focus on hotel reservations, room upgrades, and local transportation tips.",
    "Focus on cultural festivals, evening entertainment, and meeting friendly locals.",
    "Focus on coffee tasting, cozy neighborhood cafes, and relaxing afternoon vibes.",
    "Focus on shopping deals, market bargaining, and finding unique souvenirs."
]

class AIEngine:
    def __init__(self):
        self.reload_keys()

    def reload_keys(self):
        load_dotenv(override=True)
        self.gemini_keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
        self.groq_keys = [k.strip() for k in os.getenv("GROQ_API_KEY", "").split(",") if k.strip()]
        self.openai_keys = [k.strip() for k in os.getenv("OPENAI_API_KEY", "").split(",") if k.strip()]
        self.anthropic_keys = [k.strip() for k in os.getenv("ANTHROPIC_API_KEY", "").split(",") if k.strip()]
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3").strip()

        self.gemini_models = [
            "gemini-2.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemma-4-26b",
            "gemma-4-31b",
            "gemini-2.5-flash",
            "gemini-3.6-flash"
        ]
        self.groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768"
        ]

    def _normalize_text_for_comparison(self, text: str) -> str:
        """
        Normalize text by stripping punctuation, standardizing contractions, and case.
        """
        if not text:
            return ""
        t = text.lower()
        # Common contractions
        t = t.replace("can't", "cannot").replace("won't", "will not").replace("n't", " not")
        t = t.replace("'m", " am").replace("'re", " are").replace("'s", " is").replace("'ve", " have")
        # Remove punctuation
        t = re.sub(r'[^\w\s]', '', t)
        # Normalize spaces
        return re.sub(r'\s+', ' ', t).strip()

    def _compute_deterministic_score(self, user_transcript: str, corrected_text: str) -> Dict[str, int]:
        """
        Deterministic Mathematical Scoring algorithm based on Normalized Edit Distance.
        Preserves user intent and ignores punctuation/contraction differences.
        """
        u_clean = self._normalize_text_for_comparison(user_transcript)
        c_clean = self._normalize_text_for_comparison(corrected_text)

        if not u_clean:
            return {"fluency": 50, "grammar": 50, "overall": 50}

        if u_clean == c_clean:
            return {"fluency": 96, "grammar": 98, "overall": 97}

        ratio = difflib.SequenceMatcher(None, u_clean, c_clean).ratio()
        grammar = int(70 + ratio * 28)
        fluency = int(72 + ratio * 26)
        overall = int((grammar + fluency) / 2)

        return {
            "fluency": max(50, min(100, fluency)),
            "grammar": max(50, min(100, grammar)),
            "overall": max(50, min(100, overall))
        }

    def start_roleplay_greeting(
        self,
        scenario_id: str,
        character_id: Optional[str],
        level: int = 1
    ) -> Dict[str, Any]:
        self.reload_keys()
        scenario = get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        default_char = scenario.get("default_character", "rajesh")
        char_key = character_id if character_id else default_char
        character = get_character(char_key)

        level_desc = self._get_level_description(level)
        trait = character.get("trait", "Friendly")
        style = character.get("speech_style", "Conversational")
        
        angle = random.choice(SCENARIO_ANGLES)

        prompt = f"""CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
DO NOT USE ANY FOREIGN GREETINGS OR LOCAL WORDS.
DO NOT INTRODUCE YOURSELF (DO NOT SAY 'Hello I am {character['name']}' OR 'My name is'). JUMP DIRECTLY INTO THE TOPIC!

DYNAMIC SESSION ANGLE: {angle}
You are playing the role of {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
SCENARIO TOPIC: "{scenario['title']}" - {scenario.get('description', '')}.
OBJECTIVE: {scenario.get('objective', '')}.
DIFFICULTY LEVEL: {level}/20 ({level_desc}).

Task: Proactively START the roleplay conversation in a fresh, creative way! Jump DIRECTLY into an engaging, direct question or statement about "{scenario['title']}" focusing on the dynamic angle ({angle}).

Output JSON ONLY:
{{
  "ai_response": "Direct topic question or opening statement in 100% STANDARD ENGLISH",
  "ai_response_vi": "Vietnamese translation of your English opening question"
}}"""

        for key in self.groq_keys:
            for model in self.groq_models:
                try:
                    res = self._call_groq(prompt, key, model, temp=0.85)
                    if res and "ai_response" in res:
                        return res
                except Exception:
                    pass

        for key in self.gemini_keys:
            for model in self.gemini_models:
                try:
                    res = self._call_gemini(prompt, key, model, temp=0.85)
                    if res and "ai_response" in res:
                        return res
                except Exception:
                    pass

        return {
            "ai_response": f"What is your favorite item on the menu for '{scenario['title']}'?",
            "ai_response_vi": f"Món ăn yêu thích của bạn trong menu này là gì?"
        }

    def process_turn(
        self,
        scenario_id: str,
        character_id: Optional[str],
        user_transcript: str,
        conversation_history: List[Dict[str, str]],
        level: int = 1
    ) -> Dict[str, Any]:
        self.reload_keys()

        scenario = get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        default_char = scenario.get("default_character", "rajesh")
        char_key = character_id if character_id else default_char
        character = get_character(char_key)

        turn_count = len(conversation_history) // 2 + 1

        prompt = self._build_token_efficient_prompt(
            scenario=scenario,
            character=character,
            user_transcript=user_transcript,
            history=conversation_history,
            turn_count=turn_count,
            level=level
        )

        raw_res = None
        for key in self.groq_keys:
            for model in self.groq_models:
                try:
                    raw_res = self._call_groq(prompt, key, model, temp=0.85)
                    if raw_res:
                        break
                except Exception:
                    pass
            if raw_res:
                break

        if not raw_res:
            for key in self.gemini_keys:
                for model in self.gemini_models:
                    try:
                        raw_res = self._call_gemini(prompt, key, model, temp=0.85)
                        if raw_res:
                            break
                    except Exception:
                        pass
                if raw_res:
                    break

        if not raw_res:
            for key in self.openai_keys:
                try:
                    raw_res = self._call_openai(prompt, key, temp=0.85)
                    if raw_res:
                        break
                except Exception:
                    pass

        if not raw_res and self.ollama_base_url:
            try:
                raw_res = self._call_ollama(prompt, temp=0.85)
            except Exception:
                pass

        if not raw_res:
            raise RuntimeError("API Rate Limit hoặc chưa cấu hình API Key trong .env.")

        # Post-process: Compute 100% Deterministic Scores mathematically
        fb = raw_res.get("user_feedback", {})
        corrected = fb.get("corrected_text", user_transcript)
        det_scores = self._compute_deterministic_score(user_transcript, corrected)

        fb["fluency_score"] = det_scores["fluency"]
        fb["grammar_score"] = det_scores["grammar"]
        fb["overall_score"] = det_scores["overall"]
        raw_res["user_feedback"] = fb

        return raw_res

    def _get_level_description(self, level: int) -> str:
        if level <= 4:
            return "ELEMENTARY (Level 1-4): Basic A1 words (<8 words per sentence), simple binary choices."
        elif level <= 9:
            return "INTERMEDIATE (Level 5-9): Everyday B1 words (12-18 words per sentence), natural follow-ups."
        elif level <= 15:
            return "ADVANCED (Level 10-15): B2/C1 idiomatic English, rich adjectives, complex sentences."
        else:
            return "NATIVE EXPERT (Level 16-20): C2 Native vocabulary, fast pace, sophisticated arguments!"

    def _build_token_efficient_prompt(
        self,
        scenario: Dict[str, Any],
        character: Dict[str, Any],
        user_transcript: str,
        history: List[Dict[str, str]],
        turn_count: int,
        level: int
    ) -> str:
        recent_history = history[-10:] if history else []
        hist_str = ""
        for h in recent_history:
            role = "User" if h.get("role") == "user" else f"{character['name']}"
            hist_str += f"{role}: \"{h.get('content')}\"\n"

        level_desc = self._get_level_description(level)
        trait = character.get("trait", "Friendly")
        style = character.get("speech_style", "Conversational")

        return f"""CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
DO NOT USE ANY FOREIGN GREETINGS OR LOCAL WORDS.
DO NOT INTRODUCE YOURSELF IN CONVERSATION.

CRITICAL RULE FOR corrected_text:
"corrected_text" MUST BE THE DIRECT GRAMMATICAL FIX OF THE USER'S EXACT SPOKEN SENTENCE ("{user_transcript}").
PRESERVE THE USER'S EXACT MEANING, OPINION, AND DECISION 100%!
- If the user says "No I cannot drink it", corrected_text MUST BE "No, I cannot drink it."
- NEVER change "No" to "Yes" or alter what the user literally intended to say.

SMART CONVERSATION DIRECTIVES:
1. DYNAMIC & CREATIVE DIALOGUE: Advance the conversation in a fresh, creative, and engaging way! Never repeat questions or loop in circles.
2. BE PROACTIVE: If the user asks for suggestions or choices (e.g. "Can you suggest?", "What do you recommend?"), IMMEDIATELY PROVIDE SPECIFIC, INTERESTING SUGGESTIONS WITH REASONS!
3. STRICT LEVEL DIFFERENTIATION: Enforce Difficulty Level {level}/20 parameters strictly: {level_desc}.

PERMANENT ROLE: You are {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
PERMANENT TOPIC: "{scenario['title']}" - {scenario.get('description', '')}.
DIFFICULTY LEVEL: {level}/20 ({level_desc}).
TURN NUMBER: {turn_count}.

CONVERSATION HISTORY SO FAR:
{hist_str}
USER JUST SAID: "{user_transcript}"

TASK:
1. Reply in 100% STANDARD NATURAL ENGLISH strictly on topic, adapted strictly to Level {level}/20.
2. REWRITE USER SENTENCE ACCURATELY: In "corrected_text", fix ONLY the grammar/spelling of the user's sentence ("{user_transcript}") while preserving their exact meaning 100%. In "native_phrasing", provide how a native English speaker would express that exact same thought.

Output JSON ONLY:
{{
  "ai_response": "Response in 100% STANDARD NATURAL ENGLISH strictly on topic",
  "ai_response_vi": "Vietnamese translation of your English response",
  "user_feedback": {{
    "grammar_status": "Clean & Clear" or brief fix,
    "corrected_text": "Grammatically corrected version of user's sentence preserving exact meaning",
    "native_phrasing": "Direct native speaker English rewrite of user's sentence",
    "duo_reaction": "celebrate"|"happy"|"encouraging"
  }}
}}"""

    def _call_gemini(self, prompt: str, api_key: str, model_name: str, temp: float = 0.85) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 1200,
                "temperature": temp,
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

    def _call_groq(self, prompt: str, api_key: str, model_name: str, temp: float = 0.85) -> Optional[Dict[str, Any]]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": temp,
            "response_format": {"type": "json_object"}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_openai(self, prompt: str, api_key: str, temp: float = 0.85) -> Optional[Dict[str, Any]]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": temp,
            "response_format": {"type": "json_object"}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_ollama(self, prompt: str, temp: float = 0.85) -> Optional[Dict[str, Any]]:
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"num_predict": 1200, "temperature": temp}
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
        ai_res = data.get("ai_response", "That's a very interesting point! Tell me more.")
        ai_res_vi = data.get("ai_response_vi", "Đó là một điểm rất thú vị!")
        
        fb = data.get("user_feedback", {})

        return {
            "ai_response": ai_res,
            "ai_response_vi": ai_res_vi,
            "user_feedback": {
                "fluency_score": fb.get("fluency_score", 90),
                "grammar_score": fb.get("grammar_score", 92),
                "overall_score": fb.get("overall_score", 91),
                "grammar_status": fb.get("grammar_status", "Clean & Clear"),
                "corrected_text": fb.get("corrected_text", ""),
                "native_phrasing": fb.get("native_phrasing", ""),
                "duo_reaction": fb.get("duo_reaction", "happy"),
                "xp_earned": 10
            }
        }

ai_engine = AIEngine()
