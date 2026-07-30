"""
High-Quality Expressive Neural Voice TTS Service
Supports:
1. ElevenLabs Human Voice Actor Multi-Key Pool (Auto-rotates keys when quota limit 429/402 is hit).
2. Microsoft Edge Neural Voices (100% Free Edge-TTS fallback).
3. Google TTS (gTTS safety fallback).
"""

import os
import io
import re
import asyncio
import concurrent.futures
import requests
import edge_tts
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

# ElevenLabs & Azure Neural Voice Character Mappings
# All voice IDs are CONFIRMED FREE PREMADE voices from the ElevenLabs API.
CHARACTER_VOICE_MAP = {
    "lily": {
        # 'Lily - Velvety Actress' (British female) - CONFIRMED FREE PREMADE
        "eleven_voice_id": "pFZP5JQG7iQjIQuC4Bku",
        # DEADPAN: Max stability, zero style = total monotone flatness.
        "eleven_settings": {"stability": 0.95, "similarity_boost": 0.92, "style": 0.0, "use_speaker_boost": True},
        "azure_voice": "en-US-AvaNeural",
        "rate": "-12%",
        "pitch": "-14Hz",
        "fallback_tld": "com"
    },
    "oscar": {
        # 'Harry - Fierce Warrior' (American male) - aggressive, intense
        "eleven_voice_id": "SOYHLrjzK2X1ezoPC6cr",
        # GYM BRO: Min stability = explosive unpredictable peaks. Max style = full warrior.
        "eleven_settings": {"stability": 0.12, "similarity_boost": 0.72, "style": 0.95, "use_speaker_boost": True},
        "azure_voice": "en-US-GuyNeural",
        "rate": "+20%",
        "pitch": "+5Hz",
        "fallback_tld": "com"
    },
    "viktor": {
        # 'Adam - Dominant, Firm' (American male) - deep authoritative
        "eleven_voice_id": "pNInz6obpgDQGcFmaJgB",
        # COLD SPY: Max stability = dead flat emotionless delivery. Barely any style = robot agent.
        "eleven_settings": {"stability": 0.90, "similarity_boost": 0.96, "style": 0.08, "use_speaker_boost": True},
        "azure_voice": "en-GB-ThomasNeural",
        "rate": "-12%",
        "pitch": "-10Hz",
        "fallback_tld": "de"
    },
    "chanel": {
        # 'Jessica - Playful, Bright, Warm' (American female) - CONFIRMED FREE PREMADE
        "eleven_voice_id": "cgSgspJ2msm6clMCkdW9",
        # DRAMA QUEEN: Low stability = chaotic gasping/squealing. Max style = full theatrical acting.
        "eleven_settings": {"stability": 0.15, "similarity_boost": 0.70, "style": 0.92, "use_speaker_boost": True},
        "azure_voice": "en-US-JennyNeural",
        "rate": "+8%",
        "pitch": "+2Hz",
        "fallback_tld": "com"
    },
    "kaelen": {
        # 'Callum - Husky Trickster' (American male) - CONFIRMED FREE PREMADE
        # Callum has a deep, husky, dark quality - perfect for sinister Kaelen character.
        "eleven_voice_id": "N2lVS1w4EtoT3dr4eOWO",
        # DARK NIGHTMARE: High stability = slow calculated darkness. High style = sinister acting.
        "eleven_settings": {"stability": 0.85, "similarity_boost": 0.95, "style": 0.88, "use_speaker_boost": True},
        "azure_voice": "en-GB-ThomasNeural",
        "rate": "-18%",
        "pitch": "-12Hz",
        "fallback_tld": "com"
    },
    "colt": {
        # 'Roger - Laid-Back, Casual, Resonant' (American male) - CONFIRMED FREE PREMADE
        # Roger has that relaxed, drawling, resonant quality perfect for Colt Maverick.
        "eleven_voice_id": "CwhRBWXzGAHq8TQ4Fs17",
        # COWBOY DRAWL: Mid stability = relaxed natural pace. Mid style = Western character acting.
        "eleven_settings": {"stability": 0.50, "similarity_boost": 0.80, "style": 0.68, "use_speaker_boost": True},
        "azure_voice": "en-US-GuyNeural",
        "rate": "-8%",
        "pitch": "-6Hz",
        "fallback_tld": "com"
    },
    "zarina": {
        # 'Matilda - Knowledgeable, Professional' (American female) - CONFIRMED FREE PREMADE
        "eleven_voice_id": "XrExE9yKIg1WjnnlVkGX",
        # GHOSTLY SPIRIT: Very high stability = eerily deliberate, ghost-like delivery.
        "eleven_settings": {"stability": 0.91, "similarity_boost": 0.92, "style": 0.62, "use_speaker_boost": True},
        "azure_voice": "en-CA-ClaraNeural",
        "rate": "-25%",
        "pitch": "-12Hz",
        "fallback_tld": "ca"
    },
    "scarlet": {
        # 'Bella - Professional, Bright, Warm' (American female) - CONFIRMED FREE PREMADE
        # Bella has a bold, warm, bright quality - great for Captain Scarlet pirate energy.
        "eleven_voice_id": "hpp4J3VqNfWAUOO0d1Us",
        # PIRATE CAPTAIN: Low stability = bold, unpredictable pirate energy. High style = swashbuckling acting.
        "eleven_settings": {"stability": 0.22, "similarity_boost": 0.75, "style": 0.88, "use_speaker_boost": True},
        "azure_voice": "en-AU-NatashaNeural",
        "rate": "+5%",
        "pitch": "+3Hz",
        "fallback_tld": "com"
    },
    "luigi": {
        # 'Brian - Deep, Resonant and Comforting' (American male) - THE DEEPEST FREE PREMADE VOICE
        "eleven_voice_id": "nPczCjzI2devNBz1zQrb",
        # MAFIA DON: stability=0.78 = cold, CALCULATED, slow delivery. style=0.95 = full menacing acting.
        "eleven_settings": {"stability": 0.78, "similarity_boost": 0.95, "style": 0.95, "use_speaker_boost": True},
        "azure_voice": "en-US-BrianNeural",
        "rate": "-12%",
        "pitch": "-8Hz",
        "fallback_tld": "it"
    }
}

def sanitize_text_for_tts(text: str) -> str:
    """Remove triple dots and ellipses that cause TTS stuttering."""
    if not text:
        return ""
    clean = text.replace("...", ", ").replace("…", ", ")
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def generate_elevenlabs_tts_single(text: str, char_id: str, api_key: str) -> io.BytesIO:
    """Single key call to ElevenLabs API."""
    profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["lily"])
    voice_id = profile["eleven_voice_id"]
    settings = profile.get("eleven_settings", {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5})
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": sanitize_text_for_tts(text),
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": settings["stability"],
            "similarity_boost": settings["similarity_boost"],
            "style": settings["style"],
            "use_speaker_boost": True
        }
    }
    
    res = requests.post(url, headers=headers, json=payload, timeout=8)
    if res.status_code == 200 and len(res.content) > 500:
        mp3_fp = io.BytesIO(res.content)
        mp3_fp.seek(0)
        return mp3_fp
        
    raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")

def generate_elevenlabs_tts_multi_key(text: str, char_id: str, keys: list) -> io.BytesIO:
    """
    Multi-Key Auto-Rotation Pool for ElevenLabs API.
    Iterates through key pool. If a key hits quota limit (429/402) or error, automatically tries the next key!
    """
    for idx, key in enumerate(keys):
        try:
            return generate_elevenlabs_tts_single(text, char_id, key)
        except Exception as e:
            print(f"[ElevenLabs Pool] Key #{idx+1} warning ({e}). Auto-rotating to next key in pool...")

    raise Exception("All ElevenLabs API keys in pool have exhausted their quota or failed.")

async def _generate_edge_tts_async(text: str, char_id: str) -> bytes:
    profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["lily"])
    clean_text = sanitize_text_for_tts(text)

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=profile["azure_voice"],
        rate=profile["rate"],
        pitch=profile["pitch"]
    )
    mp3_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_data += chunk["data"]
    return mp3_data

def generate_tts_mp3(text: str, char_id: str = "lily", tld: str = "com") -> io.BytesIO:
    """
    Generate character-specific MP3 audio stream.
    Prioritizes ElevenLabs API with Multi-Key Pool,
    falls back to Microsoft Edge Neural Voice (100% Free) or gTTS.
    """
    load_dotenv(override=True)
    raw_keys = os.getenv("ELEVENLABS_API_KEY", "").strip()
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    
    # 1. Try ElevenLabs Multi-Key Pool if keys are present
    if keys:
        try:
            return generate_elevenlabs_tts_multi_key(text, char_id, keys)
        except Exception as e:
            print(f"[TTS Service] ElevenLabs pool exhausted ({e}), falling back to Edge-TTS...")

    # 2. Free Edge-TTS Azure Neural Voice
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            mp3_bytes = executor.submit(lambda: asyncio.run(_generate_edge_tts_async(text, char_id))).result(timeout=7)
            if mp3_bytes and len(mp3_bytes) > 500:
                mp3_fp = io.BytesIO(mp3_bytes)
                mp3_fp.seek(0)
                return mp3_fp
    except Exception as e:
        print(f"[TTS Service] Edge-TTS warning ({e}), using gTTS fallback...")

    # 3. Safety Fallback to gTTS
    profile = CHARACTER_VOICE_MAP.get(char_id, {})
    fallback_tld = profile.get("fallback_tld", tld)
    clean_text = sanitize_text_for_tts(text)
    mp3_fp = io.BytesIO()
    tts = gTTS(text=clean_text, lang="en", tld=fallback_tld, slow=False)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
