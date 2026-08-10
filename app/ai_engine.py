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
import time
import datetime
import random
import difflib
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from app.scenarios import get_scenario
from app.characters import get_character
from app.prompt_factory import get_prompt_factory

load_dotenv()

# Trace Logging & Masked Key Helpers
KEY_STATUS_CACHE: Dict[str, Dict[str, Any]] = {}

def mask_api_key(key: Optional[str]) -> str:
    """Safely mask API Key showing only 4 leading and 4 trailing characters (e.g. gsk_...9aB)."""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

# Tracks keys that are currently rate-limited (429/403) to skip on next call
KEY_EXHAUSTED_CACHE: Dict[str, float] = {}  # key -> epoch timestamp when it was exhausted
KEY_COOLDOWN_SECONDS = 60  # How long before retrying an exhausted key

def is_key_exhausted(api_key: str) -> bool:
    """Return True if this key has been rate-limited within the cooldown window."""
    exhausted_at = KEY_EXHAUSTED_CACHE.get(api_key)
    if exhausted_at is None:
        return False
    return (time.time() - exhausted_at) < KEY_COOLDOWN_SECONDS

def mark_key_exhausted(api_key: str):
    """Mark this key as rate-limited."""
    KEY_EXHAUSTED_CACHE[api_key] = time.time()

def log_api_trace(provider: str, model: str, api_key: str, status_code: int, latency_ms: float, error_msg: str = ""):
    """Log LLM API invocation trace to logs/api_trace.log and console."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "api_trace.log")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    masked = mask_api_key(api_key)
    
    if status_code in [429, 403]:
        mark_key_exhausted(api_key)

    KEY_STATUS_CACHE[masked] = {
        "provider": provider,
        "model": model,
        "status": "EXHAUSTED" if status_code in [429, 403] or error_msg else "ACTIVE",
        "status_code": status_code,
        "last_used": timestamp,
        "error": error_msg
    }

    err_suffix = f" | Error={error_msg}" if error_msg else ""
    log_line = f"[{timestamp}] [TRACE] Provider={provider} | Model={model} | Key={masked} | Status={status_code} | Latency={latency_ms:.1f}ms{err_suffix}\n"
    
    print(log_line.strip())
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"[TraceLogger] Failed to write to log file: {e}")

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
        "sentence_words": "8-15",
        "min_words": 35,
        "max_words": 70,
        "vocab_tier": "ONLY the 100 most common English words (yes, no, good, want, like, have, go, eat, drink, please, what, how)",
        "grammar_allowed": "Subject + Verb only. Present simple tense ONLY. Simple questions.",
        "response_style": "2-3 simple sentences. Greet friendly, answer clearly, and ask one basic everyday question (35-70 words). Example: 'Hello! I like coffee very much. Do you like coffee or tea?'",
        "example_response": "I like food. Food is good. Do you like food?",
    },
    2: {
        "cefr": "A1",
        "sentence_words": "8-15",
        "min_words": 35,
        "max_words": 70,
        "vocab_tier": "Top 200 most common English words. Concrete nouns (food, water, home, bus, shop, today).",
        "grammar_allowed": "Simple present tense. 'I am', 'You are', 'It is'. Basic everyday phrasing.",
        "response_style": "2-3 short, natural sentences. Include clear everyday details and ask a follow-up question (35-70 words).",
        "example_response": "I eat lunch at home every day. I like rice and vegetables. Do you eat at home or at a restaurant?",
    },
    3: {
        "cefr": "A1",
        "sentence_words": "9-15",
        "min_words": 35,
        "max_words": 70,
        "vocab_tier": "A1 basic vocabulary. Simple adjectives (big, small, hot, cold, good, bad, happy).",
        "grammar_allowed": "Present simple. Can/cannot. Have/don't have. Simple yes/no and what/where questions.",
        "response_style": "2-3 sentences with natural conversational flow. End with an engaging question (35-70 words).",
        "example_response": "I think this place is very big and nice. I can see many people here. Where do you usually go in your free time?",
    },
    4: {
        "cefr": "A1+",
        "sentence_words": "9-15",
        "min_words": 35,
        "max_words": 70,
        "vocab_tier": "A1-A2 vocabulary. Can use 'would like', 'want to', common verbs (eat, drink, go, take, give).",
        "grammar_allowed": "Present simple + 'would like' + simple imperatives. Basic time words (today, now, yesterday).",
        "response_style": "2-3 sentences. Express a basic preference or fact clearly, then ask about theirs (35-70 words).",
        "example_response": "I would like to try something new today. Yesterday I had coffee and it was really good. What would you like to eat or drink?",
    },
    5: {
        "cefr": "A2",
        "sentence_words": "10-16",
        "min_words": 35,
        "max_words": 70,
        "vocab_tier": "A2 everyday vocabulary. Common adjectives, basic adverbs (very, really, often, sometimes).",
        "grammar_allowed": "Present simple + past simple (regular verbs only). 'How much/many', basic questions.",
        "response_style": "2-3 sentences. Share an interesting observation and invite their thoughts (35-70 words).",
        "example_response": "I really enjoy spending time with friends on weekends. Last Saturday, we went to a small café near the park. How often do you usually meet up with your friends?",
    },
    6: {
        "cefr": "A2",
        "sentence_words": "10-16",
        "min_words": 45,
        "max_words": 85,
        "vocab_tier": "A2 vocabulary. Can use common collocations (have a meal, take a break, make a call).",
        "grammar_allowed": "Past simple (regular + irregular). Future with 'going to'. Questions with 'When, Where, Who'.",
        "response_style": "2-3 sentences. Connect past experiences or future plans with the topic (45-85 words).",
        "example_response": "I'm going to have lunch with my colleague today at the new place downtown. Last week we tried a noodle shop and it was pretty good - decent food and a really relaxed atmosphere. Have you made any plans for eating out this week?",
    },
    7: {
        "cefr": "A2+",
        "sentence_words": "10-17",
        "min_words": 45,
        "max_words": 85,
        "vocab_tier": "A2-B1 vocabulary. Basic phrasal verbs (look for, pick up, find out). Simple idioms avoided.",
        "grammar_allowed": "Past simple + continuous. Future with 'will'. Comparative adjectives (bigger, better, more).",
        "response_style": "3 sentences with smooth transitions. Ask a question that encourages elaboration (45-85 words).",
        "example_response": "I was looking for a good travel destination last week and found this amazing coastal town. The reviews were much better than the places I checked before, and the prices were more affordable too. Have you been travelling anywhere interesting recently, or are you still figuring out where to go?",
    },
    8: {
        "cefr": "B1-",
        "sentence_words": "11-17",
        "min_words": 45,
        "max_words": 85,
        "vocab_tier": "B1 vocabulary. Common idioms (a piece of cake, hit the road). Basic phrasal verbs freely.",
        "grammar_allowed": "Present perfect (have been, have done). Comparatives + superlatives. 'I think', 'I believe'.",
        "response_style": "3 sentences. Share an opinion with a reason, then ask for their viewpoint (45-85 words).",
        "example_response": "I think learning a new language is a piece of cake when you're surrounded by native speakers - immersion is by far the most effective approach I've tried. I've been studying Spanish for six months and I've already noticed a huge improvement in how confident I feel. What do you believe is the biggest obstacle to becoming fluent in another language?",
    },
    9: {
        "cefr": "B1",
        "sentence_words": "11-18",
        "min_words": 45,
        "max_words": 85,
        "vocab_tier": "B1 vocabulary. B1 idioms (on second thought, to be honest, as far as I know).",
        "grammar_allowed": "Past perfect. Conditionals (if...will). 'Used to'. Clause linking (because, although, while).",
        "response_style": "3 sentences. Use natural idiomatic expressions and conditional phrasing (45-85 words).",
        "example_response": "To be honest, I used to think social media was just a distraction, but on second thought it's actually helped me stay connected with people who matter. If I hadn't downloaded that app last year, I would have lost touch with a lot of old friends. How has technology changed the way you maintain your friendships, if at all?",
    },
    10: {
        "cefr": "B1",
        "sentence_words": "12-18",
        "min_words": 45,
        "max_words": 85,
        "vocab_tier": "B1-B2 vocabulary. Phrasal verbs freely. Common idioms used naturally in context.",
        "grammar_allowed": "Reported speech. Relative clauses (who, which, that). Second conditional (if...would).",
        "response_style": "3 sentences. Compare alternatives and present a thoughtful perspective (45-85 words).",
        "example_response": "There's this interesting debate about whether remote work, which has become the norm for so many people, actually improves productivity or quietly erodes teamwork. My colleague who switched to fully remote last year told me she gets more done, but she misses the spontaneous conversations that used to spark her best ideas. If you could design your ideal work setup, would you go fully remote, fully in-office, or something in between?",
    },
    11: {
        "cefr": "B1+",
        "sentence_words": "12-19",
        "min_words": 55,
        "max_words": 105,
        "vocab_tier": "B2 vocabulary. Abstract nouns. B2 collocations (raise awareness, make an impression).",
        "grammar_allowed": "All conditionals. Passive voice. Modals for deduction (must be, might have).",
        "response_style": "3-4 sentences. Provide structured conversational analysis with discourse markers (55-105 words).",
        "example_response": "It's worth raising awareness about how much our childhood experiences shape our adult relationships - something I've been reflecting on quite a bit lately. Growing up in a community where open communication was actively encouraged must have made a significant difference for those who had that privilege. Furthermore, the absence of such an environment might have led to communication barriers that can take years to unlearn. What aspects of your upbringing do you think have had the most lasting impression on how you interact with people today?",
    },
    12: {
        "cefr": "B2-",
        "sentence_words": "13-20",
        "min_words": 55,
        "max_words": 105,
        "vocab_tier": "B2 vocabulary. Formal and informal registers. Discourse markers (Furthermore, Nevertheless, In contrast).",
        "grammar_allowed": "Subjunctive (I wish, if only). Inversion for emphasis (Not only...but also). All tenses.",
        "response_style": "3-4 sentences. Explore pros and cons or challenge an idea politely (55-105 words).",
        "example_response": "Not only does urban living offer unparalleled access to career opportunities and cultural experiences, but it also comes with significant trade-offs in terms of space, noise, and cost of living. If only city planners prioritized affordable housing as much as they do commercial development, the quality of life would improve substantially for most residents. Nevertheless, I wish more people would challenge the assumption that city life is inherently superior to a quieter, more rural existence. In your view, what would the ideal balance between urban convenience and a more peaceful lifestyle look like?",
    },
    13: {
        "cefr": "B2",
        "sentence_words": "13-20",
        "min_words": 55,
        "max_words": 105,
        "vocab_tier": "B2 rich vocabulary. Sophisticated adjectives (meticulous, vibrant, compelling). Abstract concepts.",
        "grammar_allowed": "Complex sentences. Mixed conditionals. Cleft sentences (It was...that). Emphatic structures.",
        "response_style": "3-4 sentences. Employ abstract vocabulary and sophisticated reasoning naturally (55-105 words).",
        "example_response": "It was precisely the meticulous attention to cultural nuance that made that documentary so compelling - a rare quality in mainstream media. Had the director taken a more conventional approach, the vibrant complexity of those communities would have been flattened into a superficial stereotype. What I find particularly fascinating is how documentary filmmakers navigate the tension between telling a coherent narrative and preserving the messy, authentic reality of their subjects. Which aspects of storytelling do you think are most easily distorted when a story crosses cultural boundaries?",
    },
    14: {
        "cefr": "B2",
        "sentence_words": "14-21",
        "min_words": 55,
        "max_words": 105,
        "vocab_tier": "B2-C1 vocabulary. Native idioms freely. Academic and journalistic vocabulary.",
        "grammar_allowed": "All advanced structures. Ellipsis. Fronting (What I find interesting is...). Perfect modals.",
        "response_style": "3-4 sentences. Develop an engaging conversational point with idiomatic precision (55-105 words).",
        "example_response": "What I find genuinely intriguing is how the gig economy has quietly dismantled the very concept of job security - an idea that previous generations treated as a given rather than a privilege. Journalists have been documenting this shift for years, yet policymakers seem to have dragged their feet in responding to its implications. There's something to be said for the flexibility it offers, but one could argue that it largely benefits those who were already economically stable to begin with. To what extent do you think institutional responses to economic disruption tend to favour those who already hold the most power?",
    },
    15: {
        "cefr": "B2+",
        "sentence_words": "14-22",
        "min_words": 55,
        "max_words": 105,
        "vocab_tier": "C1 vocabulary. Nuanced language. Near-native collocations. Literary expressions.",
        "grammar_allowed": "Any native-level grammar. Hedging language (arguably, to a certain extent). Nominalizations.",
        "response_style": "3-4 sentences. Anticipate viewpoints and use nuanced hedging language (55-105 words).",
        "example_response": "Arguably, the proliferation of social media has fundamentally altered the dynamics of human connection - not so much by bringing people closer together, but by creating the illusion of closeness while arguably deepening a sense of isolation. To a certain extent, the curation of one's online persona has become a form of performative self-expression that prioritises external validation over genuine intimacy. The normalization of this behaviour raises fascinating questions about authenticity in contemporary relationships. To what degree do you think the boundaries between one's public and private self have eroded in the age of constant digital visibility?",
    },
    16: {
        "cefr": "C1",
        "sentence_words": "15-24",
        "min_words": 65,
        "max_words": 130,
        "vocab_tier": "C1 vocabulary. Idiomatic mastery. Academic and professional register.",
        "grammar_allowed": "Full native grammar range. Complex subordination. Implicit logical connectors.",
        "response_style": "3-4 sentences. Speak with near-native eloquence, humor, and subtle connotations (65-130 words).",
        "example_response": "There's an almost paradoxical quality to ambition - the very drive that compels people to pursue extraordinary goals tends to render the attainment of those goals strangely anticlimactic, as though the journey itself was the point all along. I've often wondered whether high achievers are genuinely motivated by the destination or whether they're, in some sense, addicted to the act of striving - a distinction that carries profound implications for how we structure our lives and measure fulfilment. What strikes you as the most honest answer when someone asks whether you're ultimately driven by a passion for the work itself or by the recognition and reward it might bring?",
    },
    17: {
        "cefr": "C1",
        "sentence_words": "15-24",
        "min_words": 65,
        "max_words": 130,
        "vocab_tier": "C1-C2 vocabulary. Philosophical terms. Rhetorical devices (rhetorical questions, anaphora).",
        "grammar_allowed": "Native-level full range. Parenthetical remarks. Appositive phrases. Absolute constructions.",
        "response_style": "3-4 sentences. Employ rhetorical devices, wit, or cultural references naturally (65-130 words).",
        "example_response": "Is it not curious - deeply, philosophically curious - that the societies most obsessed with measuring happiness tend to produce populations that report feeling least content? There's an aphorism lurking here: the more rigorously we attempt to quantify well-being, the more elusive it becomes, slipping through the fingers of our instruments like sand. Our metrics, precise as they are, capture the shadow of human flourishing while the substance stubbornly resists quantification - a limitation that should give any serious policymaker pause. What, in your estimation, lies beyond the reach of our current frameworks for understanding what it means to live well?",
    },
    18: {
        "cefr": "C1+",
        "sentence_words": "15-25",
        "min_words": 65,
        "max_words": 130,
        "vocab_tier": "C2 near-native vocabulary. Literary and cultural references. Nuanced connotations.",
        "grammar_allowed": "Any grammatical structure. Poetic license. Sophisticated register shifts.",
        "response_style": "3-4 sentences. Express deep abstract ideas with effortless syntactic variety (65-130 words).",
        "example_response": "Memory, as Proust understood, is less an archive than a creative act - each retrieval subtly reshapes the original, so that what we remember is always, in some sense, a fiction we have authored about our past. This insight carries uncomfortable implications: the sense of continuity that anchors our identity is built, at least in part, on stories we've told ourselves so many times they've hardened into apparent fact. There is something both liberating and vertiginous in that recognition - liberating because it suggests the past is more malleable than we imagined, vertiginous because it undermines the bedrock on which we've constructed our sense of self. In what ways do you find yourself curating or revising the narrative of your own life?",
    },
    19: {
        "cefr": "C2",
        "sentence_words": "16-25",
        "min_words": 65,
        "max_words": 130,
        "vocab_tier": "C2 eloquent vocabulary. Native-speaker precision. Rare but precise word choices.",
        "grammar_allowed": "Fully native syntax. Deliberate syntactic complexity for stylistic effect.",
        "response_style": "3-4 sentences. Speak as an articulate native speaker with rich conversational depth (65-130 words).",
        "example_response": "What separates the merely clever from the genuinely wise is, I suspect, not the breadth of knowledge but the quality of attention - an almost Simone Weil-ian capacity to be wholly present to what stands before you, unmediated by the noise of prior assumption. Wisdom, in this sense, has less to do with accumulating the right answers than with cultivating a certain tolerance for uncertainty, a willingness to sit with questions that resist resolution without collapsing into either nihilism or false comfort. It is a rarer disposition than intelligence, and arguably more necessary. What do you think our educational systems most fundamentally fail to cultivate in the people who pass through them?",
    },
    20: {
        "cefr": "C2+",
        "sentence_words": "16-25",
        "min_words": 65,
        "max_words": 130,
        "vocab_tier": "Native expert: slang, colloquialisms, domain jargon, cultural humor - all natural.",
        "grammar_allowed": "All native structures including deliberately broken grammar for rhetorical effect.",
        "response_style": "3-4 sentences. Speak exactly as an articulate, witty native virtuoso. Complete conversational freedom (65-130 words).",
        "example_response": "Look, I'll be straight with you - the older I get, the more I'm convinced that the things we spend our twenties absolutely certain about are precisely the things we spend our forties quietly dismantling. There's a kind of intellectual arrogance that's almost endearing in retrospect: all that ferocious certainty! And yet, I'm not sure the alternative - the studied, performative open-mindedness you see everywhere now - is meaningfully better; it just swaps one pose for another. What's something you held as an absolute conviction a decade ago that now strikes you as, well, frankly embarrassing?",
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

    def _build_smart_fallback_opener(self, scenario_id: str, scenario_title: str, level: int) -> str:
        """
        Build a smart, varied fallback opening when all LLM APIs are rate-limited.
        Uses a level-aware question bank keyed to the scenario title.
        Does NOT rely on DB*.md data (which may have parsing mix-ups).
        """
        t = scenario_title.lower()

        # Level-stratified opener pools
        if level <= 3:
            pool = [
                f"Do you like {t}?",
                f"What do you think about {t}?",
                f"Is {t} important to you?",
                f"Tell me one thing about {t}.",
            ]
        elif level <= 7:
            pool = [
                f"What is your favorite thing about {t}?",
                f"How often do you think about {t}?",
                f"Do you have any experience with {t}?",
                f"What do you usually do when it comes to {t}?",
            ]
        elif level <= 12:
            pool = [
                f"What has been your most memorable experience related to {t}?",
                f"How has your perspective on {t} changed over the years?",
                f"If you could change one thing about {t}, what would it be and why?",
                f"What do you think is the biggest challenge people face when it comes to {t}?",
                f"How do {t} affect people's daily lives, in your opinion?",
            ]
        else:
            pool = [
                f"To what extent do you think {t} shapes people's identities and worldviews?",
                f"What would you argue is the most underrated aspect of {t} that most people overlook?",
                f"If you were to challenge a common assumption about {t}, what would it be?",
                f"How do cultural differences influence the way people approach {t}?",
                f"In your view, what distinguishes genuine engagement with {t} from mere surface-level interest?",
            ]

        return random.choice(pool)


    def _build_level_constraint_block(self, level: int) -> str:
        """Build a hard-constraint text block to inject into the prompt."""
        cfg = self._get_level_config(level)
        return f"""
=== STRICT DIFFICULTY ENFORCEMENT: LEVEL {level}/20 ({cfg['cefr']}) ===
YOU MUST WRITE EXACTLY LIKE THE EXAMPLE BELOW. DO NOT DEVIATE.

EXAMPLE OF A PERFECT LEVEL {level} RESPONSE:
"{cfg['example_response']}"

RULES (same style as the example above):
- LENGTH: Between {cfg['min_words']} and {cfg['max_words']} words. COUNT YOUR WORDS.
- VOCABULARY: {cfg['vocab_tier']}
- GRAMMAR: {cfg['grammar_allowed']}
=== END LEVEL RULES ===
"""

    def start_roleplay_greeting(
        self,
        scenario_id: str,
        character_id: Optional[str],
        level: int = 1
    ) -> Dict[str, Any]:
        self.reload_keys()
        scenario = get_scenario(scenario_id)
        if not scenario:
            topic = get_prompt_factory()._get_bank().get_topic(scenario_id)
            if topic:
                scenario = {
                    "id": topic.topic_id,
                    "title": topic.topic_name,
                    "description": f"IELTS Speaking Topic: {topic.topic_name}",
                    "default_character": character_id or "lily",
                    "open_story_guide": f"Engage in an authentic IELTS speaking discussion about {topic.topic_name}."
                }
            else:
                raise ValueError(f"Unknown scenario: {scenario_id}")

        default_char = scenario.get("default_character", "rajesh")
        char_key = character_id if character_id else default_char
        character = get_character(char_key)

        prompt_factory = get_prompt_factory()
        mb_system_prompt = prompt_factory.build_system_prompt(
            topic_id=scenario_id,
            level=f"{level}",
            character_id=char_key
        )

        level_block = self._build_level_constraint_block(level)
        cfg = self._get_level_config(level)
        trait = character.get("trait", "Friendly")
        style = character.get("speech_style", "Conversational")
        
        story_guide = scenario.get("open_story_guide", "Improvise an exciting, unscripted roleplay with unexpected surprises and plot twists.")
        angle = random.choice(SCENARIO_ANGLES)

        prompt = f"""{mb_system_prompt}

CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
DO NOT USE ANY FOREIGN GREETINGS OR LOCAL WORDS.
DO NOT INTRODUCE YOURSELF (DO NOT SAY 'Hello I am {character['name']}' OR 'My name is'). JUMP DIRECTLY INTO THE TOPIC!

UNSCRIPTED OPEN CREATIVE STORYTELLING:
Story Guide: {story_guide}
Dynamic Session Angle: {angle}
Improvise an open, creative roleplay! Bring unexpected twists, humorous situations, and vivid character interactions. Never use repetitive templates.

You are playing the role of {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
SCENARIO TOPIC: "{scenario['title']}" - {scenario.get('description', '')}.
{level_block}

Task: Proactively START the roleplay conversation as {character['name']}.
1. Share a compelling thought, personal observation, or story setup (2-3 sentences) about "{scenario['title']}" matching your character persona and difficulty level.
2. End your turn with ONE engaging, OPEN-ENDED question that invites the user to elaborate.
3. CRITICAL LENGTH & LEVEL MANDATE: Your ENTIRE response MUST be between {cfg['min_words']} and {cfg['max_words']} words. Match the exact vocabulary complexity, sentence length, and structure of the Level {level} ({cfg['cefr']}) example provided above!

Output JSON ONLY:
{{
  "ai_response": "Opening in 100% STANDARD ENGLISH strictly obeying all level rules"
}}"""

        for key in self.groq_keys:
            if is_key_exhausted(key):
                continue  # Skip rate-limited keys, use next available
            for model in self.groq_models:
                try:
                    res = self._call_groq(prompt, key, model, temp=0.8)
                    if res and "ai_response" in res:
                        res["ai_response_vi"] = ""
                        return res
                except Exception:
                    continue

        for key in self.gemini_keys:
            if is_key_exhausted(key):
                continue  # Skip rate-limited keys, use next available
            for model in self.gemini_models:
                try:
                    res = self._call_gemini(prompt, key, model, temp=0.8)
                    if res and "ai_response" in res:
                        res["ai_response_vi"] = ""
                        return res
                except Exception:
                    continue

        # All providers exhausted - use smart level-aware fallback
        fallback_q = self._build_smart_fallback_opener(scenario_id, scenario['title'], level)
        return {"ai_response": fallback_q, "ai_response_vi": ""}

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
            topic = get_prompt_factory()._get_bank().get_topic(scenario_id)
            if topic:
                scenario = {
                    "id": topic.topic_id,
                    "title": topic.topic_name,
                    "description": f"IELTS Speaking Topic: {topic.topic_name}",
                    "default_character": character_id or "lily",
                    "open_story_guide": f"Engage in an authentic IELTS speaking discussion about {topic.topic_name}."
                }
            else:
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
            if is_key_exhausted(key):
                continue
            for model in self.groq_models:
                try:
                    raw_res = self._call_groq(prompt, key, model, temp=0.8)
                    if raw_res:
                        break
                except Exception:
                    continue
            if raw_res:
                break

        if not raw_res:
            for key in self.gemini_keys:
                if is_key_exhausted(key):
                    continue
                for model in self.gemini_models:
                    try:
                        raw_res = self._call_gemini(prompt, key, model, temp=0.8)
                        if raw_res:
                            break
                    except Exception:
                        continue
                if raw_res:
                    break

        if not raw_res:
            for key in self.openai_keys:
                if is_key_exhausted(key):
                    continue
                try:
                    raw_res = self._call_openai(prompt, key, temp=0.8)
                    if raw_res:
                        break
                except Exception:
                    continue

        if not raw_res and self.ollama_base_url:
            try:
                raw_res = self._call_ollama(prompt, temp=0.8)
            except Exception:
                pass

        if not raw_res:
            raw_res = self._get_mock_fallback_response(scenario, character, user_transcript)

        fb = raw_res.get("user_feedback", {})
        corrected = fb.get("corrected_text", user_transcript)
        det_scores = self._compute_deterministic_score(user_transcript, corrected)

        fb["fluency_score"] = det_scores["fluency"]
        fb["grammar_score"] = det_scores["grammar"]
        fb["overall_score"] = det_scores["overall"]
        raw_res["user_feedback"] = fb
        return raw_res

    def _get_mock_fallback_response(
        self,
        scenario: Dict[str, Any],
        character: Dict[str, Any],
        user_transcript: str
    ) -> Dict[str, Any]:
        """Generate a realistic mock fallback response when LLM APIs are unavailable/rate-limited."""
        title = scenario.get("title", "Everyday Practice")
        char_name = character.get("name", "AI Partner")
        
        fallback_responses = [
            f"That sounds wonderful! Could you tell me more about your thoughts on {title}?",
            f"I completely agree with you! How do you usually handle this when dealing with {title}?",
            f"That's a great point. What is the most important thing to remember about {title}?",
            "Interesting perspective! Have you ever experienced anything similar before?"
        ]
        chosen = random.choice(fallback_responses)
        vi_trans = self._professional_vietnamese_localization(chosen, char_name, title)
        
        det_scores = self._compute_deterministic_score(user_transcript, user_transcript)
        
        return {
            "ai_response": chosen,
            "ai_response_vi": vi_trans,
            "user_feedback": {
                "fluency_score": max(det_scores["fluency"], 85),
                "grammar_score": max(det_scores["grammar"], 88),
                "overall_score": max(det_scores["overall"], 86),
                "corrected_text": user_transcript,
                "native_phrasing": "Great expression! Try adding conversational connectors like 'In my opinion' or 'To be honest' when speaking."
            },
            "is_completed": False,
            "xp_gained": 10
        }

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
            f"1. Contextual & Spoken Flow: Translate into natural spoken Vietnamese that fits '{character_name}' in the scenario. Do NOT translate word-for-word.\n"
            f"2. Natural Roleplay Pronouns (Xưng hô ngữ cảnh): Choose warm, natural Vietnamese pronouns based on character persona and relationship (e.g., 'tớ - cậu', 'em - anh', 'mình - bạn'). NEVER use rigid robotic 'tôi - bạn' for every line.\n"
            f"3. Spoken Vietnamese Particles (Từ đệm cảm xúc): Naturally include conversational particles ('nhé', 'nha', 'đấy', 'đi', 'cơ mà', 'chứ', 'nè', 'vậy', 'cậu ạ') at sentence ends for authentic spoken warmth.\n"
            f"4. FEW-SHOT CONTRAST EXAMPLES (SO SÁNH DỞ vs. HAY):\n"
            f"   - Bad (Literal): \"Tôi muốn bạn làm điều này cho tôi ngay bây giờ.\" -> Good (Spoken): \"Cậu giúp tớ việc này luôn nhé!\"\n"
            f"   - Bad (Literal): \"Chúng ta có sự gia tăng giá thuê nhà.\" -> Good (Spoken): \"Đợt này tiền nhà lại tăng rồi cậu ạ.\"\n"
            f"   - Bad (Literal): \"Tôi nghe thấy bạn thích cà phê.\" -> Good (Spoken): \"Nghe nói cậu thích uống cà phê hả?\"\n"
            f"5. Output ONLY the translated Vietnamese dialogue line without quotes, markdown, or commentary."
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
                        "temperature": 0.35,
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
                        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.35}
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

    def _summarize_or_prune_history(
        self,
        history: List[Dict[str, str]],
        max_exchanges: int = 15
    ) -> tuple[List[Dict[str, str]], str]:
        """
        Multi-Turn Context Truncation Guard:
        If conversation history exceeds max_exchanges (default 15 exchanges = 30 messages),
        automatically prune older turns into a condensed summary block to prevent prompt
        overflow while preserving core conversational context.
        """
        max_messages = max_exchanges * 2
        if not history or len(history) <= max_messages:
            return history if history else [], ""

        # Retain last 10 messages (5 exchanges) for immediate rolling context
        recent_window = 10
        pruned_items = history[:-recent_window]
        recent_items = history[-recent_window:]

        # Create a structured summary of pruned history turns
        summary_lines = []
        for item in pruned_items:
            role_name = "User" if item.get("role") == "user" else "AI"
            content = item.get("content", "").strip()
            if content:
                short_text = content[:80] + "..." if len(content) > 80 else content
                summary_lines.append(f"{role_name}: {short_text}")

        concise_summary = " | ".join(summary_lines[-10:])
        summary_block = (
            f"[MULTI-TURN CONTEXT SUMMARY - PRUNED {len(pruned_items)} PREVIOUS MESSAGES ({len(pruned_items)//2} TURNS)]:\n"
            f"{concise_summary}\n"
        )
        return recent_items, summary_block

    def _build_token_efficient_prompt(
        self,
        scenario: Dict[str, Any],
        character: Dict[str, Any],
        user_transcript: str,
        history: List[Dict[str, str]],
        turn_count: int,
        level: int
    ) -> str:
        recent_history, summary_block = self._summarize_or_prune_history(history, max_exchanges=15)

        hist_str = ""
        if summary_block:
            hist_str += f"{summary_block}\n"

        for h in recent_history:
            role = "User" if h.get("role") == "user" else f"{character['name']}"
            hist_str += f"{role}: \"{h.get('content')}\"\n"

        prompt_factory = get_prompt_factory()
        scenario_key = scenario.get("id") or scenario.get("title", "")
        mb_system_prompt = prompt_factory.build_system_prompt(
            topic_id=scenario_key,
            level=f"{level}",
            character_id=character.get("id", "lily")
        )

        level_block = self._build_level_constraint_block(level)
        cfg = self._get_level_config(level)
        trait = character.get("trait", "Friendly")
        style = character.get("speech_style", "Conversational")

        story_guide = scenario.get("open_story_guide", "Improvise an exciting, unscripted roleplay with unexpected surprises and plot twists.")

        return f"""{mb_system_prompt}

CRITICAL MANDATE: YOU MUST SPEAK 100% STANDARD NATURAL ENGLISH ONLY.
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
5. AUTHENTIC DUOLINGO ASR PHONETIC CLARIFICATION ("did you mean X? Is that right?"):
   - The user's input "{user_transcript}" is transcribed from a microphone via Speech-to-Text (ASR).
   - Because of learner pronunciation errors or accents, the ASR may transcribe homophones or acoustically similar words (e.g., 'important' -> 'in portal', 'think' -> 'sink', 'beach' -> 'bitch', 'sheet' -> 'seat').
   - NEVER complain or say you don't understand an STT misrecognition!
   - Instead, naturally GUESS the user's intended word, politely CONFIRM it in character in your spoken reply (e.g., "Oh, did you mean 'important'? Is that right? Because I agree that..."), and seamlessly continue your response based on your guess!
   - In "user_feedback", praise their effort and give a gentle tip in Vietnamese on pronouncing that word clearer so ASR hears it accurately next time.
{level_block}

PERMANENT ROLE: You are {character['name']} ({character.get('country', '')}, {character.get('role', '')}). Traits: {trait}. Style: {style}.
PERMANENT TOPIC: "{scenario['title']}" - {scenario.get('description', '')}. Story Guide: {story_guide}.
TURN NUMBER: {turn_count}.

CONVERSATION HISTORY SO FAR:
{hist_str}
USER JUST SAID: "{user_transcript}"

TASK:
1. Reply in 100% STANDARD NATURAL ENGLISH as {character['name']}. Your response MUST be between {cfg['min_words']} and {cfg['max_words']} words total (strictly obeying Level {level} - {cfg['cefr']} length and vocabulary rules). Express a rich 2-3 sentence thought/reaction matching the Level {level} example above, and end with ONE FRESH OPEN-ENDED QUESTION.
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

    def _call_gemini(self, prompt: str, api_key: str, model_name: str, temp: float = 0.8) -> Optional[Dict[str, Any]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 1200,
                "temperature": temp,
                "presencePenalty": 0.6,
                "responseMimeType": "application/json"
            }
        }
        t0 = time.time()
        res = requests.post(url, json=payload, timeout=8)
        latency_ms = (time.time() - t0) * 1000
        log_api_trace("Gemini", model_name, api_key, res.status_code, latency_ms)
        if res.status_code == 200:
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_groq(self, prompt: str, api_key: str, model_name: str, temp: float = 0.8) -> Optional[Dict[str, Any]]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": temp,
            "presence_penalty": 0.6,
            "response_format": {"type": "json_object"}
        }
        t0 = time.time()
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        latency_ms = (time.time() - t0) * 1000
        log_api_trace("Groq", model_name, api_key, res.status_code, latency_ms)
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_openai(self, prompt: str, api_key: str, temp: float = 0.8) -> Optional[Dict[str, Any]]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": temp,
            "presence_penalty": 0.6,
            "response_format": {"type": "json_object"}
        }
        t0 = time.time()
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        latency_ms = (time.time() - t0) * 1000
        log_api_trace("OpenAI", "gpt-4o-mini", api_key, res.status_code, latency_ms)
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"]
            return self._parse_json_response(text)
        elif res.status_code in [429, 403, 400]:
            raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")
        return None

    def _call_ollama(self, prompt: str, temp: float = 0.8) -> Optional[Dict[str, Any]]:
        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"num_predict": 1200, "temperature": temp, "presence_penalty": 0.6}
        }
        t0 = time.time()
        res = requests.post(url, json=payload, timeout=8)
        latency_ms = (time.time() - t0) * 1000
        log_api_trace("Ollama", self.ollama_model, "localhost", res.status_code, latency_ms)
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

    def _compute_hybrid_acoustic_metrics(
        self,
        user_speech: str,
        duration_seconds: int,
        wpm: Optional[int] = None,
        pause_count: Optional[int] = None,
        filler_count: Optional[int] = None
    ) -> Dict[str, Any]:
        words = [w for w in user_speech.strip().split() if len(w) > 0]
        word_count = len(words)
        effective_wpm = wpm if (wpm is not None and wpm > 0) else int((word_count / max(1, duration_seconds)) * 60)

        import re
        filler_pattern = r'\b(uh|um|er|ah|like|you know|actually|basically|literally)\b'
        matches = re.findall(filler_pattern, user_speech.lower())
        detected_fillers = len(matches)
        effective_fillers = max(filler_count or 0, detected_fillers)

        effective_pauses = pause_count if pause_count is not None else (0 if effective_wpm >= 95 else 2)

        if effective_wpm < 80:
            pace_label = "Chậm / Ấp úng (Slow / Hesitant)"
        elif effective_wpm <= 105:
            pace_label = "Ổn định (Moderate Pace)"
        elif effective_wpm <= 155:
            pace_label = "Trôi chảy tự nhiên (Native-like Rhythm)"
        else:
            pace_label = "Nói quá nhanh (Rushed)"

        if effective_wpm < 75 or effective_pauses >= 5 or effective_fillers >= 4:
            rhythm_diagnosis = "Nhịp nói còn ngập ngừng, xuất hiện nhiều từ đệm hoặc khoảng lặng (High Hesitation)"
        elif 85 <= effective_wpm <= 155 and effective_fillers <= 2 and effective_pauses <= 2:
            rhythm_diagnosis = "Nhịp điệu trôi chảy, tự nhiên, liên tục và tự tin (Smooth & Continuous Rhythm)"
        else:
            rhythm_diagnosis = "Tốc độ nói khá tốt, cần duy trì nhịp điệu đều đặn hơn (Moderate Fluency)"

        return {
            "wpm": effective_wpm,
            "pace_label": pace_label,
            "pause_count": effective_pauses,
            "filler_count": effective_fillers,
            "filler_words_found": ", ".join(set(matches)) if matches else "None",
            "rhythm_diagnosis": rhythm_diagnosis
        }

    async def evaluate_det_speech(
        self,
        scenario: Dict[str, Any],
        user_speech: str,
        duration_seconds: int = 120,
        mode: str = "read_then_speak",
        wpm: Optional[int] = None,
        pause_count: Optional[int] = None,
        filler_count: Optional[int] = None
    ) -> Dict[str, Any]:
        question_card = scenario.get("question_card", {})
        prompt_text = question_card.get("prompt", scenario.get("description", ""))
        bullet_points = question_card.get("bullet_points", [])

        words = [w for w in user_speech.strip().split() if len(w) > 0]
        word_count = len(words)
        is_too_short = word_count < 15

        acoustic_metrics = self._compute_hybrid_acoustic_metrics(
            user_speech=user_speech,
            duration_seconds=duration_seconds,
            wpm=wpm,
            pause_count=pause_count,
            filler_count=filler_count
        )

        if is_too_short:
            est_score = min(35, max(10, 10 + int(word_count * 1.5)))
            cefr = "Pre-A1" if est_score < 25 else "A1 Elementary"
            critique_msg = f"Bài làm quá ngắn (chỉ có {word_count} từ), không đủ dữ liệu phát âm và từ vựng để đánh giá năng lực theo chuẩn Quốc Tế IELTS / CEFR. Thí sinh cần phát triển trọn vẹn dàn ý (tối thiểu 40 - 60 từ) trong thời gian 1 - 3 phút."
        elif word_count < 40:
            est_score = min(85, max(45, 40 + int((word_count - 15) * 1.2)))
            cefr = "A2 Elementary" if est_score < 65 else "B1 Intermediate"
            critique_msg = f"Thí sinh có cố gắng trả lời đề bài '{scenario.get('title')}' ({word_count} từ), tuy nhiên câu trả lời còn ngắn. Để đạt mốc B2/C1, bạn cần mở rộng thêm các ý chi tiết và ví dụ thực tế."
        elif word_count < 80:
            est_score = min(115, max(85, 80 + int((word_count - 40) * 0.7)))
            cefr = "B1 Intermediate" if est_score < 95 else "B2 Upper-Intermediate"
            critique_msg = f"Bài nói triển khai tốt ý tưởng ({word_count} từ, {duration_seconds}s). Ngữ pháp và từ vựng đạt mức khá. Để vươn lên band C1, hãy chú ý sử dụng thêm các cấu trúc câu đảo ngữ, liên từ học thuật và từ vựng chủ đề chuyên sâu."
        else:
            est_score = min(160, max(120, 115 + int((word_count - 80) * 0.5)))
            cefr = "C1 Advanced" if est_score >= 130 else "B2 Upper-Intermediate"
            critique_msg = f"Bài làm xuất sắc ({word_count} từ trong {duration_seconds} giây), lập luận chặt chẽ và từ vựng phong phú, thể hiện trình độ thành thạo ngôn ngữ tốt."

        eval_prompt = f"""You are an Official International English (IELTS / CEFR) Senior Speaking Examiner.
Evaluate the candidate's speech for a '{mode}' task.

CRITICAL IELTS / CEFR RUBRIC PENALTY RULES:
1. HYBRID FLUENCY SCORING MANDATE: You MUST evaluate "fluency_score" (0-100) based on BOTH text grammar AND the HYBRID ACOUSTIC METRICS below! If WPM < 75 or Long Pauses >= 5 or Fillers >= 4, penalize fluency_score (do not exceed 65) and comment on the hesitant pace in 'examiner_critique'. If WPM is 105-155 with <= 2 pauses, award 85-98 for fluency.
2. MINIMUM LENGTH PENALTY: If the candidate speech is under 20 words, or just 1-2 words like "hello" / "test", the maximum possible det_score is 10-35 (Pre-A1 / A1). NEVER assign B1, B2, or C1 to a response under 25 words!
3. RELEVANCE & MEANING PENALTY: If the speech is gibberish, off-topic, or meaningless, det_score MUST be between 10 and 25 (Pre-A1).
4. CRITIQUE REQUIREMENTS: If penalized for being too short or irrelevant, state clearly in 'examiner_critique' in Vietnamese: "Bài nói quá ngắn (dưới 20 từ) hoặc không trả lời đúng trọng tâm đề bài..."
5. ASR/STT PHONETIC RECONSTRUCTION & PRONUNCIATION ANALYSIS:
   - The candidate's speech "{user_speech}" is transcribed from a microphone via Speech-to-Text (ASR).
   - If there are homophone misrecognitions or phonetic substitutions (e.g., learner mispronounced a sound causing ASR to transcribe an acoustically similar word like 'in portal' instead of 'important'), RECONSTRUCT the candidate's intended vocabulary in context.
   - In 'pronunciation_score' and 'examiner_critique', explicitly point out which specific words the candidate mispronounced that caused the STT engine to hear them incorrectly (e.g. "Từ 'important' bạn phát âm chưa chuẩn âm cuối nên máy bắt thành 'in portal'...").

QUESTION PROMPT: "{prompt_text}"
KEY POINTS TO ADDRESS:
{chr(10).join(['- ' + bp for bp in bullet_points])}

CANDIDATE SPEECH ({duration_seconds} seconds, {word_count} words):
"{user_speech}"

[HYBRID ACOUSTIC & RHYTHM METRICS (Measured from audio stream)]
- Measured Speaking Rate (WPM): {acoustic_metrics['wpm']} words/min ({acoustic_metrics['pace_label']})
- Long Pauses / Hesitation Count: {acoustic_metrics['pause_count']} times
- Filler Words / Stutter Count: {acoustic_metrics['filler_count']} times (words found: {acoustic_metrics['filler_words_found']})
- Acoustic Rhythm Profile: {acoustic_metrics['rhythm_diagnosis']}

Return ONLY a valid JSON object with EXACTLY this schema:
{{
  "det_score": (integer from 10 to 160 based on IELTS/CEFR speaking rubric scale),
  "cefr_level": "(e.g., 'C1 Advanced', 'B2 Upper-Intermediate', 'B1 Intermediate', 'A1 Elementary', 'Pre-A1')",
  "fluency_score": (integer 0-100),
  "grammar_score": (integer 0-100),
  "vocabulary_score": (integer 0-100),
  "coherence_score": (integer 0-100),
  "examiner_critique": "(In Vietnamese 🇻🇳: Detailed examiner critique of strengths, structure, acoustic pace/pauses, and areas to improve)",
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
                data["acoustic_metrics"] = acoustic_metrics
                return data
            except Exception as e:
                print(f"DET json parse fallback: {e}")

        # Smart fallback if API unconfigured or JSON failed
        return {
            "det_score": est_score,
            "cefr_level": cefr,
            "fluency_score": min(95, max(15, est_score - 10)),
            "grammar_score": min(95, max(15, est_score - 5)),
            "vocabulary_score": min(95, max(15, est_score)),
            "coherence_score": min(95, max(15, est_score - 5)),
            "examiner_critique": critique_msg,
            "sentence_upgrades": [
                {
                    "original": user_speech[:80] + "..." if len(user_speech) > 80 else user_speech,
                    "upgraded": "In retrospect, that profound experience significantly shaped my personal philosophy and resilience.",
                    "explanation": "Sử dụng cụm từ 'In retrospect' và tính từ C1 'profound' để làm câu văn trang trọng và logic hơn."
                }
            ],
            "sample_native_response": f"Regarding the topic of {prompt_text}, I would like to highlight a truly defining moment in my life. It occurred several years ago and taught me resilience, adaptability, and the value of clear communication. Not only did it broaden my perspective, but it also reinforced the importance of continuous learning.",
            "acoustic_metrics": acoustic_metrics
        }

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "speech.webm", fallback_text: str = "") -> Dict[str, Any]:
        """
        Transcribes recorded microphone audio using Groq Whisper Large V3 (ultra-fast & accurate for ESL learners).
        Falls back to Gemini Audio or browser STT fallback text if API keys are unavailable.
        """
        if self.groq_keys:
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            for key in self.groq_keys:
                try:
                    headers = {"Authorization": f"Bearer {key}"}
                    files = {"file": (filename, audio_bytes, "audio/webm")}
                    data = {"model": "whisper-large-v3", "language": "en", "response_format": "json"}
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        text = result.get("text", "").strip()
                        if text:
                            return {"transcript": text, "source": "groq-whisper-large-v3"}
                except Exception as e:
                    print(f"[AIEngine] Groq Whisper error: {e}")
                    if "429" in str(e) or "403" in str(e):
                        pass # No inner loop here, continue outer loop
                    continue

        if self.gemini_keys:
            import base64
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            for key in self.gemini_keys:
                for model in self.gemini_models:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                        payload = {
                            "contents": [{
                                "parts": [
                                    {"inline_data": {"mime_type": "audio/webm", "data": b64_audio}},
                                    {"text": "Transcribe this English speech accurately into text. Output ONLY the exact transcribed text without any conversational filler or quotes."}
                                ]
                            }],
                            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
                        }
                        response = requests.post(url, json=payload, timeout=10)
                        if response.status_code == 200:
                            res_json = response.json()
                            candidates = res_json.get("candidates", [])
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                                if text:
                                    return {"transcript": text, "source": f"gemini-audio-{model}"}
                    except Exception as e:
                        if "429" in str(e) or "403" in str(e):
                            break
                        continue

        return {"transcript": fallback_text.strip(), "source": "browser-stt"}

    def get_trace_quota_health(self) -> Dict[str, Any]:
        """Return active key counts, key status cache, and recent 25 trace log entries."""
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        log_file = os.path.join(logs_dir, "api_trace.log")
        recent_logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_logs = [line.strip() for line in lines[-25:]]
            except Exception:
                pass

        return {
            "active_groq_keys_count": len(self.groq_keys),
            "active_gemini_keys_count": len(self.gemini_keys),
            "active_openai_keys_count": len(self.openai_keys),
            "key_statuses": KEY_STATUS_CACHE,
            "recent_trace_logs": recent_logs
        }

ai_engine = AIEngine()
