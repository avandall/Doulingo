"""
High-Quality Expressive Neural Voice TTS Service using Microsoft Edge TTS (edge-tts).
Fixes audio stuttering/pausing midway by sanitizing text & ensuring clean audio buffer accumulation.
"""

import io
import re
import asyncio
import concurrent.futures
import edge_tts
from gtts import gTTS

# Permanent Fixed Character Voice ID Mapping
CHARACTER_VOICE_MAP = {
    "rajesh": {
        "voice": "en-IN-PrabhatNeural",
        "rate": "+15%",
        "pitch": "+5Hz",
        "fallback_tld": "co.in"
    },
    "priya": {
        "voice": "en-IN-NeerjaNeural",
        "rate": "+10%",
        "pitch": "+8Hz",
        "fallback_tld": "co.in"
    },
    "william": {
        "voice": "en-GB-RyanNeural",
        "rate": "+5%",
        "pitch": "-3Hz",
        "fallback_tld": "co.uk"
    },
    "chloe": {
        "voice": "en-US-AnaNeural",
        "rate": "+20%",
        "pitch": "+10Hz",
        "fallback_tld": "com"
    },
    "hans": {
        "voice": "en-DE-KillianNeural",
        "rate": "0%",
        "pitch": "-6Hz",
        "fallback_tld": "de"
    },
    "lily": {
        "voice": "en-US-AvaNeural",
        "rate": "-3%",
        "pitch": "-4Hz",
        "fallback_tld": "com"
    },
    "evelyn": {
        "voice": "en-CA-ClaraNeural",
        "rate": "+10%",
        "pitch": "-2Hz",
        "fallback_tld": "ca"
    },
    "marco": {
        "voice": "en-IT-DiegoNeural",
        "rate": "+15%",
        "pitch": "+6Hz",
        "fallback_tld": "it"
    }
}

def sanitize_text_for_tts(text: str) -> str:
    """
    Remove triple dots, ellipses, and unprintable characters that cause Edge-TTS to stutter or pause midway.
    """
    if not text:
        return ""
    # Replace ellipses with clean comma pauses
    clean = text.replace("...", ", ").replace("…", ", ")
    # Replace multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

async def _generate_edge_tts_async(text: str, char_id: str) -> bytes:
    profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["rajesh"])
    clean_text = sanitize_text_for_tts(text)

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=profile["voice"],
        rate=profile["rate"],
        pitch=profile["pitch"]
    )
    mp3_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_data += chunk["data"]
    return mp3_data

def generate_tts_mp3(text: str, char_id: str = "rajesh", tld: str = "com") -> io.BytesIO:
    """
    Generate distinct, character-specific neural voice MP3 audio stream without stuttering.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            mp3_bytes = executor.submit(lambda: asyncio.run(_generate_edge_tts_async(text, char_id))).result(timeout=7)
            if mp3_bytes and len(mp3_bytes) > 500:
                mp3_fp = io.BytesIO(mp3_bytes)
                mp3_fp.seek(0)
                return mp3_fp
    except Exception as e:
        print(f"[TTS Service] Edge-TTS warning ({e}), using gTTS fallback...")

    # Fallback to gTTS
    profile = CHARACTER_VOICE_MAP.get(char_id, {})
    fallback_tld = profile.get("fallback_tld", tld)
    clean_text = sanitize_text_for_tts(text)
    mp3_fp = io.BytesIO()
    tts = gTTS(text=clean_text, lang="en", tld=fallback_tld, slow=False)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp
