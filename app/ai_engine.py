"""
AI Engine for Duolingo Speak
Features:
- Smart Fluent Conversational Vietnamese Translations (Natural, non-machine translation).
- Meaning-Preserving Grammatical Correction.
- Cleaned Punctuation & Contraction-Aware Deterministic Scoring.
- High Conversational Creativity (temperature = 0.85 + Dynamic Scenario Angle Randomizer).
- Granular 20-Level Difficulty System with per-level hard constraints.
- LLM-based fallback translation (replaces unreliable Google Translate scraping).
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

# ============================================================
# GRANULAR 20-LEVEL CONFIGURATION SYSTEM
# Each level has precise, machine-enforceable constraints:
#   sentence_words  : target word count range per sentence
#   max_words       : hard max words for AI's entire response
#   vocab_tier      : vocabulary complexity description
#   grammar_allowed : allowed grammar structures (whitelist)
#   response_style  : how AI should format/length its response
#   cefr            : CEFR reference level
# ============================================================
LEVEL_CONFIGS = {
    1: {
        "cefr": "Pre-A1",
        "sentence_words": "5-10",
        "min_words": 15,
        "max_words": 30,
        "vocab_tier": "ONLY the 100 most common English words (yes, no, good, want, like, have, go, eat, drink, please, what, how)",
        "grammar_allowed": "Subject + Verb only. Present simple tense ONLY. Simple questions.",
        "response_style": "1-2 short, simple sentences. Greet friendly and ask one basic everyday question (15-30 words). Example: 'Hello! Do you like coffee or tea?'",
    },
    2: {
        "cefr": "A1",
        "sentence_words": "6-11",
        "min_words": 20,
        "max_words": 35,
        "vocab_tier": "Top 200 most common English words. Concrete nouns (food, water, home, bus, shop, today).",
        "grammar_allowed": "Simple present tense. 'I am', 'You are', 'It is'. Basic everyday phrasing.",
        "response_style": "2 short sentences. Include one simple detail and ask a clear follow-up question (20-35 words).",
    },
    3: {
        "cefr": "A1",
        "sentence_words": "7-12",
        "min_words": 25,
        "max_words": 40,
        "vocab_tier": "A1 basic vocabulary. Simple adjectives (big, small, hot, cold, good, bad, happy).",
        "grammar_allowed": "Present simple. Can/cannot. Have/don't have. Simple yes/no and what/where questions.",
        "response_style": "2 sentences with natural conversational flow. End with an engaging question (25-40 words).",
    },
    4: {
        "cefr": "A1+",
        "sentence_words": "8-13",
        "min_words": 25,
        "max_words": 45,
        "vocab_tier": "A1-A2 vocabulary. Can use 'would like', 'want to', common verbs (eat, drink, go, take, give).",
        "grammar_allowed": "Present simple + 'would like' + simple imperatives. Basic time words (today, now, yesterday).",
        "response_style": "2-3 sentences. Express a basic preference or fact, then ask about theirs (25-45 words).",
    },
    5: {
        "cefr": "A2",
        "sentence_words": "8-14",
        "min_words": 30,
        "max_words": 50,
        "vocab_tier": "A2 everyday vocabulary. Common adjectives, basic adverbs (very, really, often, sometimes).",
        "grammar_allowed": "Present simple + past simple (regular verbs only). 'How much/many', basic questions.",
        "response_style": "2-3 sentences. Share an interesting observation and invite their thoughts (30-50 words).",
    },
    6: {
        "cefr": "A2",
        "sentence_words": "9-15",
        "min_words": 30,
        "max_words": 55,
        "vocab_tier": "A2 vocabulary. Can use common collocations (have a meal, take a break, make a call).",
        "grammar_allowed": "Past simple (regular + irregular). Future with 'going to'. Questions with 'When, Where, Who'.",
        "response_style": "2-3 sentences. Connect past experiences or future plans with the topic (30-55 words).",
    },
    7: {
        "cefr": "A2+",
        "sentence_words": "10-15",
        "min_words": 35,
        "max_words": 60,
        "vocab_tier": "A2-B1 vocabulary. Basic phrasal verbs (look for, pick up, find out). Simple idioms avoided.",
        "grammar_allowed": "Past simple + continuous. Future with 'will'. Comparative adjectives (bigger, better, more).",
        "response_style": "2-3 sentences with smooth transitions. Ask a question that encourages elaboration (35-60 words).",
    },
    8: {
        "cefr": "B1-",
        "sentence_words": "10-16",
        "min_words": 35,
        "max_words": 65,
        "vocab_tier": "B1 vocabulary. Common idioms (a piece of cake, hit the road). Basic phrasal verbs freely.",
        "grammar_allowed": "Present perfect (have been, have done). Comparatives + superlatives. 'I think', 'I believe'.",
        "response_style": "2-3 sentences. Share an opinion with a reason, then ask for their viewpoint (35-65 words).",
    },
    9: {
        "cefr": "B1",
        "sentence_words": "11-17",
        "min_words": 40,
        "max_words": 70,
        "vocab_tier": "B1 vocabulary. B1 idioms (on second thought, to be honest, as far as I know).",
        "grammar_allowed": "Past perfect. Conditionals (if...will). 'Used to'. Clause linking (because, although, while).",
        "response_style": "3 sentences. Use natural idiomatic expressions and conditional phrasing (40-70 words).",
    },
    10: {
        "cefr": "B1",
        "sentence_words": "11-18",
        "min_words": 40,
        "max_words": 75,
        "vocab_tier": "B1-B2 vocabulary. Phrasal verbs freely. Common idioms used naturally in context.",
        "grammar_allowed": "Reported speech. Relative clauses (who, which, that). Second conditional (if...would).",
        "response_style": "3 sentences. Compare alternatives and present a thoughtful perspective (40-75 words).",
    },
    11: {
        "cefr": "B1+",
        "sentence_words": "12-18",
        "min_words": 45,
        "max_words": 80,
        "vocab_tier": "B2 vocabulary. Abstract nouns. B2 collocations (raise awareness, make an impression).",
        "grammar_allowed": "All conditionals. Passive voice. Modals for deduction (must be, might have).",
        "response_style": "3 sentences. Provide structured conversational analysis with discourse markers (45-80 words).",
    },
    12: {
        "cefr": "B2-",
        "sentence_words": "12-19",
        "min_words": 45,
        "max_words": 85,
        "vocab_tier": "B2 vocabulary. Formal and informal registers. Discourse markers (Furthermore, Nevertheless, In contrast).",
        "grammar_allowed": "Subjunctive (I wish, if only). Inversion for emphasis (Not only...but also). All tenses.",
        "response_style": "3-4 sentences. Explore pros and cons or challenge an idea politely (45-85 words).",
    },
    13: {
        "cefr": "B2",
        "sentence_words": "13-20",
        "min_words": 50,
        "max_words": 90,
        "vocab_tier": "B2 rich vocabulary. Sophisticated adjectives (meticulous, vibrant, compelling). Abstract concepts.",
        "grammar_allowed": "Complex sentences. Mixed conditionals. Cleft sentences (It was...that). Emphatic structures.",
        "response_style": "3-4 sentences. Employ abstract vocabulary and sophisticated reasoning naturally (50-90 words).",
    },
    14: {
        "cefr": "B2",
        "sentence_words": "13-21",
        "min_words": 50,
        "max_words": 95,
        "vocab_tier": "B2-C1 vocabulary. Native idioms freely. Academic and journalistic vocabulary.",
        "grammar_allowed": "All advanced structures. Ellipsis. Fronting (What I find interesting is...). Perfect modals.",
        "response_style": "3-4 sentences. Develop an engaging conversational point with idiomatic precision (50-95 words).",
    },
    15: {
        "cefr": "B2+",
        "sentence_words": "14-22",
        "min_words": 55,
        "max_words": 100,
        "vocab_tier": "C1 vocabulary. Nuanced language. Near-native collocations. Literary expressions.",
        "grammar_allowed": "Any native-level grammar. Hedging language (arguably, to a certain extent). Nominalizations.",
        "response_style": "3-4 sentences. Anticipate viewpoints and use nuanced hedging language (55-100 words).",
    },
    16: {
        "cefr": "C1",
        "sentence_words": "14-23",
        "min_words": 55,
        "max_words": 105,
        "vocab_tier": "C1 vocabulary. Idiomatic mastery. Academic and professional register.",
        "grammar_allowed": "Full native grammar range. Complex subordination. Implicit logical connectors.",
        "response_style": "3-4 sentences. Speak with near-native eloquence, humor, and subtle connotations (55-105 words).",
    },
    17: {
        "cefr": "C1",
        "sentence_words": "15-23",
        "min_words": 60,
        "max_words": 110,
        "vocab_tier": "C1-C2 vocabulary. Philosophical terms. Rhetorical devices (rhetorical questions, anaphora).",
        "grammar_allowed": "Native-level full range. Parenthetical remarks. Appositive phrases. Absolute constructions.",
        "response_style": "3-4 sentences. Employ rhetorical devices, wit, or cultural references naturally (60-110 words).",
    },
    18: {
        "cefr": "C1+",
        "sentence_words": "15-24",
        "min_words": 60,
        "max_words": 115,
        "vocab_tier": "C2 near-native vocabulary. Literary and cultural references. Nuanced connotations.",
        "grammar_allowed": "Any grammatical structure. Poetic license. Sophisticated register shifts.",
        "response_style": "3-4 sentences. Express deep abstract ideas with effortless syntactic variety (60-115 words).",
    },
    19: {
        "cefr": "C2",
        "sentence_words": "16-24",
        "min_words": 65,
        "max_words": 120,
        "vocab_tier": "C2 eloquent vocabulary. Native-speaker precision. Rare but precise word choices.",
        "grammar_allowed": "Fully native syntax. Deliberate syntactic complexity for stylistic effect.",
        "response_style": "3-4 sentences. Speak as an articulate native speaker with rich conversational depth (65-120 words).",
    },
    20: {
        "cefr": "C2+",
        "sentence_words": "16-25",
        "min_words": 65,
        "max_words": 125,
        "vocab_tier": "Native expert: slang, colloquialisms, domain jargon, cultural humor — all natural.",
        "grammar_allowed": "All native structures including deliberately broken grammar for rhetorical effect.",
        "response_style": "3-4 sentences. Speak exactly as an articulate, witty native virtuoso. Complete conversational freedom (65-125 words).",
    },
}

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
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "llama-3.1-8b-instant"
        ]

    def _normalize_text_for_comparison(self, text: str) -> str:
        if not text:
            return ""
        t = text.lower()
        t = t.replace("can't", "cannot").replace("won't", "will not").replace("n't", " not")
        t = t.replace("'m", " am").replace("'re", " are").replace("'s", " is").replace("'ve", " have")
        t = re.sub(r'[^\w\s]', '', t)
        return re.sub(r'\s+', ' ', t).strip()

    def _compute_deterministic_score(self, user_transcript: str, corrected_text: str) -> Dict[str, int]:
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

    def _get_level_config(self, level: int) -> Dict[str, Any]:
        """Return the precise level configuration for levels 1-20."""
        lvl = max(1, min(20, level))
        return LEVEL_CONFIGS[lvl]

    def _build_level_constraint_block(self, level: int) -> str:
        """Build a hard-constraint text block to inject into the prompt."""
        cfg = self._get_level_config(level)
        return f"""
=== STRICT DIFFICULTY ENFORCEMENT: LEVEL {level}/20 ({cfg['cefr']}) ===
YOU MUST OBEY ALL RULES BELOW. VIOLATING ANY RULE = FAIL.

RULE 1 — NATURAL SPOKEN CONVERSATIONAL LENGTH: Your ENTIRE response MUST be between {cfg['min_words']} and {cfg['max_words']} words total. Speak like a natural human in a real dialogue — NEVER write a long essay, speech, or textbook paragraph. Each sentence should be around {cfg['sentence_words']} words within [{cfg['min_words']} - {cfg['max_words']} words].
RULE 2 — VOCABULARY: Use ONLY {cfg['vocab_tier']}. Do NOT use words outside this tier.
RULE 3 — GRAMMAR: {cfg['grammar_allowed']}. Do NOT use grammar structures beyond this level.
RULE 4 — RESPONSE FORMAT & MANDATORY QUESTION: {cfg['response_style']}. You SHOULD end your turn with a fresh, OPEN-ENDED question that NEVER repeats previous questions or loops back to topics already discussed in the conversation!

SELF-CHECK BEFORE RESPONDING: Count your words. Is your response a natural spoken dialogue between {cfg['min_words']} and {cfg['max_words']} words? Did you end with a FRESH OPEN-ENDED QUESTION that does NOT repeat previous topics? If not, rewrite.
=== END DIFFICULTY RULES ==="""

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

        level_block = self._build_level_constraint_block(level)
        trait = character.get("trait", "Friendly")
        style = character.get("speech_style", "Conversational")
        
        story_guide = scenario.get("open_story_guide", "Improvise an exciting, unscripted roleplay with unexpected surprises and plot twists.")
        angle = random.choice(SCENARIO_ANGLES)

        prompt = f"""CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
DO NOT USE ANY FOREIGN GREETINGS OR LOCAL WORDS.
DO NOT INTRODUCE YOURSELF (DO NOT SAY 'Hello I am {character['name']}' OR 'My name is'). JUMP DIRECTLY INTO THE TOPIC!

UNSCRIPTED OPEN CREATIVE STORYTELLING:
Story Guide: {story_guide}
Dynamic Session Angle: {angle}
Improvise an open, creative roleplay! Bring unexpected twists, humorous situations, and vivid character interactions. Never use repetitive templates.

You are playing the role of {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
SCENARIO TOPIC: "{scenario['title']}" - {scenario.get('description', '')}.
{level_block}

Task: Proactively START the roleplay conversation. Jump DIRECTLY into an engaging, OPEN-ENDED opening question about "{scenario['title']}" that inspires storytelling and rich dialogue — strictly obeying the level rules above. NEVER use closed yes/no questions unless Level 1.

Output JSON ONLY:
{{
  "ai_response": "Opening in 100% STANDARD ENGLISH strictly obeying all level rules"
}}"""

        for key in self.groq_keys:
            for model in self.groq_models:
                try:
                    res = self._call_groq(prompt, key, model, temp=0.85)
                    if res and "ai_response" in res:
                        res["ai_response_vi"] = ""
                        return res
                except Exception:
                    pass

        for key in self.gemini_keys:
            for model in self.gemini_models:
                try:
                    res = self._call_gemini(prompt, key, model, temp=0.85)
                    if res and "ai_response" in res:
                        res["ai_response_vi"] = ""
                        return res
                except Exception:
                    pass

        return {
            "ai_response": f"What is your favorite item on the menu for '{scenario['title']}'?",
            "ai_response_vi": ""
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

        fb = raw_res.get("user_feedback", {})
        corrected = fb.get("corrected_text", user_transcript)
        det_scores = self._compute_deterministic_score(user_transcript, corrected)

        fb["fluency_score"] = det_scores["fluency"]
        fb["grammar_score"] = det_scores["grammar"]
        fb["overall_score"] = det_scores["overall"]
        raw_res["user_feedback"] = fb

        raw_res["ai_response_vi"] = ""
        return raw_res

    def _professional_vietnamese_localization(self, english_text: str, character_name: str = "", scenario_title: str = "", context_history: Optional[List[str]] = None) -> str:
        """
        Dedicated Professional Vietnamese Localization Engine (Dịch thuật ngữ cảnh văn nói).
        Called LAZILY only when the user clicks the translate button.
        Decouples translation from creative roleplay generation to guarantee idiomatic, culturally accurate Vietnamese.
        Runs at low temperature (temp=0.15) on the largest 70B model with explicit speaker & context history rules.
        """
        if not english_text or not english_text.strip():
            return ""

        context_str = "\n".join([f"- {s}" for s in (context_history or [])[-3:]]) if context_history else "No previous turns"

        translate_prompt = (
            f"You are an expert film subtitle and dialogue translator specializing in spoken conversational Vietnamese (DỊCH THOÁT Ý TỰ NHIÊN THEO NGỮ CẢNH VĂN NÓI).\n"
            f"Speaker Persona: '{character_name}'\n"
            f"Scenario / Context: '{scenario_title}'\n"
            f"Recent Dialogue Context (last 1-3 turns):\n{context_str}\n\n"
            f"Target English Line to Translate: \"{english_text}\"\n\n"
            f"LOCALIZATION RULES (MANDATORY):\n"
            f"1. Contextual & Spoken Flow: Translate into natural spoken Vietnamese that fits '{character_name}' in the scenario and context above. Do NOT translate word-for-word.\n"
            f"2. Appropriate Vietnamese Pronouns (Xưng hô): Select appropriate natural Vietnamese pronouns based on '{character_name}' and context. NEVER add hallucinated extra words or third-person pronouns not present in the English line (e.g., never say 'với chàng trai anh ấy không').\n"
            f"3. Precise Business/Domain Terms: Accurately translate idioms and terminology based on context (e.g., 'rent increase' -> 'tăng giá thuê nhà / tăng tiền nhà' NOT 'thuế tăng'; 'do business with checks' -> 'làm ăn bằng séc / chuyển khoản minh bạch'; 'dirty cash' -> 'tiền bẩn / tiền mặt không rõ nguồn gốc').\n"
            f"4. Output ONLY the translated Vietnamese dialogue line without quotes, markdown, or commentary."
        )

        for key in self.groq_keys:
            for model in self.groq_models:
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": translate_prompt}],
                        "max_tokens": 200,
                        "temperature": 0.15,
                    }
                    res = requests.post(url, headers=headers, json=payload, timeout=6)
                    if res.status_code == 200:
                        text = res.json()["choices"][0]["message"]["content"].strip()
                        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                            text = text[1:-1].strip()
                        if text:
                            return text
                except Exception:
                    pass

        for key in self.gemini_keys:
            for model in self.gemini_models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    payload = {
                        "contents": [{"parts": [{"text": translate_prompt}]}],
                        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.15}
                    }
                    res = requests.post(url, json=payload, timeout=6)
                    if res.status_code == 200:
                        text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                            text = text[1:-1].strip()
                        if text:
                            return text
                except Exception:
                    pass

        return ""

    def _fallback_llm_translate(self, english_text: str) -> str:
        """
        LLM-based fallback translation when AI omits ai_response_vi.
        Now routes directly through _professional_vietnamese_localization.
        """
        return self._professional_vietnamese_localization(english_text)

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

        level_block = self._build_level_constraint_block(level)
        trait = character.get("trait", "Friendly")
        style = character.get("speech_style", "Conversational")

        story_guide = scenario.get("open_story_guide", "Improvise an exciting, unscripted roleplay with unexpected surprises and plot twists.")

        return f"""CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
DO NOT USE ANY FOREIGN GREETINGS OR LOCAL WORDS.
DO NOT INTRODUCE YOURSELF IN CONVERSATION.

CRITICAL RULE FOR corrected_text:
"corrected_text" MUST BE THE DIRECT GRAMMATICAL FIX OF THE USER'S EXACT SPOKEN SENTENCE ("{user_transcript}").
PRESERVE THE USER'S EXACT MEANING, OPINION, AND DECISION 100%!

SMART CONVERSATION DIRECTIVES & OPEN QUESTION MANDATE (MUST OBEY):
1. ALWAYS END YOUR TURN WITH AN OPEN-ENDED QUESTION:
   - NEVER end your turn with just an affirmative statement, agreement, or comment! If you do not ask a question, the conversation dies.
   - Every single response MUST conclude with a compelling, OPEN-ENDED question (asking 'why', 'how', 'what led to...', 'what would you do if...', etc.) that inspires the user to speak more and share stories/details.
2. STRICT ANTI-REPETITION (NEVER ASK PREVIOUSLY DISCUSSED TOPICS):
   - NEVER repeat a question or circle back to an idea that was already asked or answered in the CONVERSATION HISTORY! Re-asking the same question/topic in slightly different words ("hỏi tới hỏi lui 1 vấn đề") is a CRITICAL ERROR.
   - Actively drive the dialogue FORWARD to a brand-new angle, an unexpected plot twist, or a fresh sub-topic every single turn.
3. UNSCRIPTED OPEN STORYTELLING: Follow story guide: '{story_guide}'. Improvise dynamic plot twists, humorous surprises, and unscripted developments!
4. BE PROACTIVE WITH SUGGESTIONS: If the user asks for recommendations or choices, immediately provide specific, interesting suggestions with reasons, then ask an open-ended question about their preference.
{level_block}

PERMANENT ROLE: You are {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
PERMANENT TOPIC: "{scenario['title']}" - {scenario.get('description', '')}. Story Guide: {story_guide}.
TURN NUMBER: {turn_count}.

CONVERSATION HISTORY SO FAR:
{hist_str}
USER JUST SAID: "{user_transcript}"

TASK:
1. Reply in 100% STANDARD NATURAL ENGLISH strictly obeying all level rules above. Your reply MUST end with a FRESH, OPEN-ENDED QUESTION that drives the topic forward without repeating previous ideas.
2. REWRITE USER SENTENCE ACCURATELY: In "corrected_text", fix ONLY grammar/spelling of "{user_transcript}" while preserving their exact meaning 100%. In "native_phrasing", show how a native speaker would say that exact thought.

Output JSON ONLY:
{{
  "ai_response": "Response in 100% STANDARD NATURAL ENGLISH strictly obeying all level rules",
  "user_feedback": {{
    "grammar_status": "Clean & Clear" or brief fix note,
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
        ai_res_vi = data.get("ai_response_vi", "")
        
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

    async def evaluate_det_speech(
        self,
        scenario: Dict[str, Any],
        user_speech: str,
        duration_seconds: int = 120,
        mode: str = "read_then_speak"
    ) -> Dict[str, Any]:
        question_card = scenario.get("question_card", {})
        prompt_text = question_card.get("prompt", scenario.get("description", ""))
        bullet_points = question_card.get("bullet_points", [])

        word_count = len(user_speech.split())
        est_score = min(155, max(45, 60 + int(word_count * 0.7)))
        cefr = "C1 Advanced" if est_score >= 125 else ("B2 Upper-Intermediate" if est_score >= 95 else "B1 Intermediate")

        eval_prompt = f"""You are an Official Duolingo English Test (DET) Senior Speaking Examiner.
Evaluate the candidate's speech for a '{mode}' task.

QUESTION PROMPT: "{prompt_text}"
KEY POINTS TO ADDRESS:
{chr(10).join(['- ' + bp for bp in bullet_points])}

CANDIDATE SPEECH ({duration_seconds} seconds, {word_count} words):
"{user_speech}"

Return ONLY a valid JSON object with EXACTLY this schema:
{{
  "det_score": (integer from 10 to 160 based on DET speaking rubric),
  "cefr_level": "(e.g., 'C1 Advanced', 'B2 Upper-Intermediate', 'B1 Intermediate')",
  "fluency_score": (integer 0-100),
  "grammar_score": (integer 0-100),
  "vocabulary_score": (integer 0-100),
  "coherence_score": (integer 0-100),
  "examiner_critique": "(In Vietnamese 🇻🇳: Detailed examiner critique of strengths, structure, and areas to improve)",
  "sentence_upgrades": [
    {{
      "original": "(A sentence from candidate's speech)",
      "upgraded": "(A C1/C2 academic rewrite of that sentence)",
      "explanation": "(In Vietnamese 🇻🇳: Explain why the upgraded vocabulary/structure is higher level)"
    }}
  ],
  "sample_native_response": "(A full 150-200 word Band-160 sample answer to the prompt)"
}}
"""
        raw_res = None
        if self.gemini_keys:
            raw_res = self._call_gemini(eval_prompt, self.gemini_keys[0], self.gemini_models[0], temp=0.2)
        elif self.groq_keys:
            raw_res = self._call_groq(eval_prompt, self.groq_keys[0], self.groq_models[0], temp=0.2)
        elif self.openai_keys:
            raw_res = self._call_openai(eval_prompt, self.openai_keys[0], temp=0.2)

        if raw_res:
            try:
                text = raw_res.get("response", "").strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1:
                    text = text[start:end+1]
                data = json.loads(text)
                return data
            except Exception as e:
                print(f"DET json parse fallback: {e}")

        # Smart fallback if API unconfigured or JSON failed
        return {
            "det_score": est_score,
            "cefr_level": cefr,
            "fluency_score": min(95, max(60, est_score - 10)),
            "grammar_score": min(95, max(60, est_score - 5)),
            "vocabulary_score": min(95, max(60, est_score)),
            "coherence_score": min(95, max(65, est_score - 5)),
            "examiner_critique": f"Thí sinh đã phát triển ý khá tốt cho chủ đề '{scenario.get('title')}'. Bài nói đạt khoảng {word_count} từ trong {duration_seconds} giây. Để đạt band C1/C2, nên tập trung sử dụng thêm câu phức và liên từ học thuật.",
            "sentence_upgrades": [
                {
                    "original": user_speech[:80] + "..." if len(user_speech) > 80 else user_speech,
                    "upgraded": "In retrospect, that profound experience significantly shaped my personal philosophy and resilience.",
                    "explanation": "Sử dụng cụm từ 'In retrospect' và tính từ C1 'profound' để làm câu văn trang trọng và logic hơn."
                }
            ],
            "sample_native_response": f"Regarding the topic of {prompt_text}, I would like to highlight a truly defining moment in my life. It occurred several years ago and taught me resilience, adaptability, and the value of clear communication. Not only did it broaden my perspective, but it also reinforced the importance of continuous learning."
        }

ai_engine = AIEngine()
