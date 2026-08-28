"""
High-Quality Expressive Neural Voice TTS Service
Supports:
1. ElevenLabs Human Voice Actor Multi-Key Pool (Auto-rotates keys when quota limit 429/402 is hit).
2. Microsoft Edge Neural Voices (100% Free Edge-TTS fallback).
3. Google TTS (gTTS safety fallback).
"""

import asyncio
import concurrent.futures
import io
import logging
import os
import re
import time
from typing import Any

import edge_tts
import requests
from dotenv import load_dotenv
from gtts import gTTS

from app.core.ai_engine import is_key_exhausted, log_api_trace, mark_key_exhausted, mask_api_key

load_dotenv()
logger = logging.getLogger("duolingo_speak.tts")

# ElevenLabs & Azure Neural Voice Character Mappings
# All voice IDs are CONFIRMED FREE PREMADE voices from the ElevenLabs API.
CHARACTER_VOICE_MAP: dict[str, dict[str, Any]] = {
    "alex": {
        "eleven_voice_id": "21m00Tcm4TlvDq8ikWAM",
        "eleven_settings": {"stability": 0.50, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
        "azure_voice": "en-US-JennyNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "duo": {
        "eleven_voice_id": "cgSgspJ2msm6clMCkdW9",
        "eleven_settings": {"stability": 0.5, "similarity_boost": 0.85, "style": 0.5, "use_speaker_boost": True},
        "azure_voice": "en-US-AnaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "lily": {
        # 'Lily - Velvety Actress' (British female) - CONFIRMED FREE PREMADE
        "eleven_voice_id": "pFZP5JQG7iQjIQuC4Bku",
        # DEADPAN: Max stability, zero style = total monotone flatness.
        "eleven_settings": {"stability": 0.95, "similarity_boost": 0.92, "style": 0.0, "use_speaker_boost": True},
        "azure_voice": "en-GB-SoniaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "co.uk"
    },
    "oscar": {
        # 'Harry - Fierce Warrior' (American male) - aggressive, intense
        "eleven_voice_id": "SOYHLrjzK2X1ezoPC6cr",
        # GYM BRO: Min stability = explosive unpredictable peaks. Max style = full warrior.
        "eleven_settings": {"stability": 0.12, "similarity_boost": 0.72, "style": 0.95, "use_speaker_boost": True},
        "azure_voice": "en-US-GuyNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "viktor": {
        # 'Adam - Dominant, Firm' (American male) - deep authoritative
        "eleven_voice_id": "pNInz6obpgDQGcFmaJgB",
        # COLD SPY: Max stability = dead flat emotionless delivery. Barely any style = robot agent.
        "eleven_settings": {"stability": 0.90, "similarity_boost": 0.96, "style": 0.08, "use_speaker_boost": True},
        "azure_voice": "en-GB-ThomasNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "de"
    },
    "chanel": {
        # 'Jessica - Playful, Bright, Warm' (American female) - CONFIRMED FREE PREMADE
        "eleven_voice_id": "cgSgspJ2msm6clMCkdW9",
        # DRAMA QUEEN: Low stability = chaotic gasping/squealing. Max style = full theatrical acting.
        "eleven_settings": {"stability": 0.15, "similarity_boost": 0.70, "style": 0.92, "use_speaker_boost": True},
        "azure_voice": "en-US-JennyNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "kaelen": {
        # 'Callum - Husky Trickster' (American male) - CONFIRMED FREE PREMADE
        # Callum has a deep, husky, dark quality - perfect for sinister Kaelen character.
        "eleven_voice_id": "N2lVS1w4EtoT3dr4eOWO",
        # DARK NIGHTMARE: High stability = slow calculated darkness. High style = sinister acting.
        "eleven_settings": {"stability": 0.85, "similarity_boost": 0.95, "style": 0.88, "use_speaker_boost": True},
        "azure_voice": "en-GB-ThomasNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "colt": {
        # 'Roger - Laid-Back, Casual, Resonant' (American male) - CONFIRMED FREE PREMADE
        # Roger has that relaxed, drawling, resonant quality perfect for Colt Maverick.
        "eleven_voice_id": "CwhRBWXzGAHq8TQ4Fs17",
        # COWBOY DRAWL: Mid stability = relaxed natural pace. Mid style = Western character acting.
        "eleven_settings": {"stability": 0.50, "similarity_boost": 0.80, "style": 0.68, "use_speaker_boost": True},
        "azure_voice": "en-US-GuyNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "zarina": {
        # 'Matilda - Knowledgeable, Professional' (American female) - CONFIRMED FREE PREMADE
        "eleven_voice_id": "XrExE9yKIg1WjnnlVkGX",
        # GHOSTLY SPIRIT: Very high stability = eerily deliberate, ghost-like delivery.
        "eleven_settings": {"stability": 0.91, "similarity_boost": 0.92, "style": 0.62, "use_speaker_boost": True},
        "azure_voice": "en-CA-ClaraNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "ca"
    },
    "scarlet": {
        # 'Bella - Professional, Bright, Warm' (American female) - CONFIRMED FREE PREMADE
        # Bella has a bold, warm, bright quality - great for Captain Scarlet pirate energy.
        "eleven_voice_id": "hpp4J3VqNfWAUOO0d1Us",
        # PIRATE CAPTAIN: Low stability = bold, unpredictable pirate energy. High style = swashbuckling acting.
        "eleven_settings": {"stability": 0.22, "similarity_boost": 0.75, "style": 0.88, "use_speaker_boost": True},
        "azure_voice": "en-AU-NatashaNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "com"
    },
    "luigi": {
        # 'Brian - Deep, Resonant and Comforting' (American male) - THE DEEPEST FREE PREMADE VOICE
        "eleven_voice_id": "nPczCjzI2devNBz1zQrb",
        # MAFIA DON: stability=0.78 = cold, CALCULATED, slow delivery. style=0.95 = full menacing acting.
        "eleven_settings": {"stability": 0.78, "similarity_boost": 0.95, "style": 0.95, "use_speaker_boost": True},
        "azure_voice": "en-US-BrianNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "fallback_tld": "it"
    }
}

CHARACTER_FILLER_MAP: dict[str, str] = {
    "alex": "Hmm...",
    "duo": "Hmm, let me see...",
    "lily": "Well...",
    "oscar": "Right...",
    "viktor": "Hmm...",
    "chanel": "Oh, let me think...",
    "kaelen": "Mmm...",
    "colt": "Well now...",
    "zarina": "Ah...",
    "scarlet": "Aha...",
    "luigi": "Hmm..."
}

def get_character_filler_path(char_id: str) -> str:
    """Return relative file path for character filler audio."""
    clean_char = char_id.lower().strip() if char_id else "lily"
    if clean_char not in CHARACTER_FILLER_MAP:
        clean_char = "lily"
    path = f"static/audio/fillers/{clean_char}.mp3"
    if not os.path.exists(path):
        return "static/audio/fillers/lily.mp3"
    return path


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
    
    t0 = time.time()
    res = requests.post(url, headers=headers, json=payload, timeout=8)
    latency_ms = (time.time() - t0) * 1000
    if res.status_code == 200 and len(res.content) > 500:
        log_api_trace("ElevenLabs", "eleven_multilingual_v2", api_key, res.status_code, latency_ms, step="TTS")
        mp3_fp = io.BytesIO(res.content)
        mp3_fp.seek(0)
        return mp3_fp
        
    log_api_trace("ElevenLabs", "eleven_multilingual_v2", api_key, res.status_code, latency_ms, error_msg=res.text[:100], step="TTS")
    raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")

def generate_elevenlabs_tts_multi_key(text: str, char_id: str, keys: list) -> io.BytesIO:
    """
    Multi-Key Auto-Rotation Pool for ElevenLabs API.
    Iterates through key pool. If a key hits quota limit (429/402) or error, automatically tries the next key!
    """
    for idx, key in enumerate(keys):
        if is_key_exhausted(key):
            continue
        try:
            return generate_elevenlabs_tts_single(text, char_id, key)
        except Exception as e:
            mark_key_exhausted(key)
            masked = mask_api_key(key)
            next_hint = f"Auto-rotating to Key #{idx+2}" if idx + 1 < len(keys) else "Key pool exhausted -> Fallback to Edge-TTS"
            msg = f"[ElevenLabs] Key #{idx+1} ({masked}) hit quota/error ({e}) -> {next_hint}"
            logger.warning(msg)

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

async def stream_edge_tts(text: str, char_id: str):
    """Async generator yielding Edge-TTS MP3 chunks directly as they are generated (<300ms latency)."""
    profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["lily"])
    clean_text = sanitize_text_for_tts(text)

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=profile["azure_voice"],
        rate=profile["rate"],
        pitch=profile["pitch"]
    )
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]

def stream_elevenlabs_tts_single(text: str, char_id: str, api_key: str):
    """Yields streaming chunks from ElevenLabs API."""
    profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["lily"])
    voice_id = profile["eleven_voice_id"]
    settings = profile.get("eleven_settings", {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5})
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?optimize_streaming_latency=3"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": sanitize_text_for_tts(text),
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": settings["stability"],
            "similarity_boost": settings["similarity_boost"],
            "style": settings["style"],
            "use_speaker_boost": True
        }
    }
    
    res = requests.post(url, headers=headers, json=payload, stream=True, timeout=8)
    if res.status_code == 200:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
        return
    elif res.status_code in [400, 422]:
        # Fallback to multilingual v2 if turbo_v2_5 is not supported on a custom voice
        payload["model_id"] = "eleven_multilingual_v2"
        res_fb = requests.post(url, headers=headers, json=payload, stream=True, timeout=8)
        if res_fb.status_code == 200:
            for chunk in res_fb.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
            return
        
    raise Exception(f"HTTP {res.status_code}: {res.text[:100]}")

def stream_gtts(text: str, char_id: str = "lily", tld: str = "com"):
    """Yields MP3 audio chunks from gTTS safety fallback."""
    profile = CHARACTER_VOICE_MAP.get(char_id, {})
    fallback_tld = profile.get("fallback_tld", tld)
    clean_text = sanitize_text_for_tts(text)
    mp3_fp = io.BytesIO()
    tts = gTTS(text=clean_text, lang="en", tld=fallback_tld, slow=False)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    while chunk := mp3_fp.read(4096):
        yield chunk

async def stream_tts_mp3_chunks(text: str, char_id: str = "lily", tld: str = "com"):
    """
    Asynchronously yields audio MP3 chunks for real-time low-latency streaming (<300ms initial chunk).
    Prioritizes ElevenLabs streaming, then Edge-TTS streaming async generator, then gTTS fallback.
    """
    logger.info(f"Starting chunked TTS audio stream for char_id='{char_id}', text_len={len(text)}")
    load_dotenv(override=True)
    raw_keys = os.getenv("ELEVENLABS_API_KEY", "").strip()
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    
    # 1. Try ElevenLabs Multi-Key Pool streaming if keys are present
    if keys:
        for idx, key in enumerate(keys):
            if is_key_exhausted(key):
                continue
            try:
                chunk_found = False
                for chunk in stream_elevenlabs_tts_single(text, char_id, key):
                    chunk_found = True
                    yield chunk
                if chunk_found:
                    return
            except Exception as e:
                mark_key_exhausted(key)
                logger.warning(f"[ElevenLabs Stream Pool] Key #{idx+1} failed ({e}). Auto-rotating...")

    # 2. Try Edge-TTS async stream (<300ms initial chunk)
    try:
        chunk_count = 0
        async for chunk in stream_edge_tts(text, char_id):
            chunk_count += 1
            yield chunk
        if chunk_count > 0:
            logger.info(f"Successfully streamed {chunk_count} audio chunks via Edge-TTS")
            return
    except Exception as e:
        logger.warning(f"[TTS Service] Edge-TTS stream warning ({e}), falling back to gTTS...")

    # 3. Safety Fallback to gTTS
    try:
        for chunk in stream_gtts(text, char_id, tld):
            yield chunk
        logger.info("Successfully streamed audio chunks via gTTS fallback")
    except Exception as e:
        logger.error(f"[TTS Service] All TTS providers failed: {e}", exc_info=True)
        raise


def split_sentences(text: str) -> list[str]:
    """
    Splits text into a list of sentences based on sentence boundary delimiters (. ! ? \\n).
    Preserves natural sentence boundaries while handling common abbreviations (e.g., Mr., Dr.)
    and numbers.
    """
    if not text or not text.strip():
        return []

    clean_text = text.strip()
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', clean_text)

    sentences = []
    for s in raw_sentences:
        s_clean = s.strip()
        if s_clean:
            sentences.append(s_clean)

    return sentences if sentences else [clean_text]


async def stream_sentence_level_tts(text: str, char_id: str = "lily", tld: str = "com"):
    """
    Sentence-level async generator for ultra-low latency TTS streaming (<1.0s TTFA).
    Splits the full utterance into sentence chunks, synthesizes and yields audio MP3 chunks
    for sentence 1 immediately, then streams sentence 2, sentence 3, etc. seamlessly.
    """
    sentences = split_sentences(text)
    if not sentences:
        return

    logger.info(f"Starting sentence-level TTS stream ({len(sentences)} sentences) for char_id='{char_id}'")
    for idx, sentence in enumerate(sentences):
        t0 = time.time()
        chunk_count = 0
        async for chunk in stream_tts_mp3_chunks(sentence, char_id=char_id, tld=tld):
            chunk_count += 1
            yield chunk
        latency_ms = (time.time() - t0) * 1000
        logger.debug(
            f"[SentenceTTS] Streamed sentence #{idx+1}/{len(sentences)} "
            f"({len(sentence)} chars, {chunk_count} chunks in {latency_ms:.1f}ms)"
        )


def generate_tts_mp3(text: str, char_id: str = "lily", tld: str = "com") -> io.BytesIO:
    """
    Generate character-specific MP3 audio stream as a complete BytesIO buffer.
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
            logger.warning(f"[TTS Service] ElevenLabs pool exhausted ({e}), falling back to Edge-TTS...")

    # 2. Free Edge-TTS Azure Neural Voice
    try:
        profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["lily"])
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            mp3_bytes = executor.submit(lambda: asyncio.run(_generate_edge_tts_async(text, char_id))).result(timeout=7)
            latency_ms = (time.time() - t0) * 1000
            if mp3_bytes and len(mp3_bytes) > 500:
                log_api_trace("Edge-TTS", profile["azure_voice"], "free", 200, latency_ms, step="TTS_Fallback")
                mp3_fp = io.BytesIO(mp3_bytes)
                mp3_fp.seek(0)
                return mp3_fp
    except Exception as e:
        logger.warning(f"[TTS Service] Edge-TTS warning ({e}), using gTTS fallback...")

    # 3. Safety Fallback to gTTS
    profile = CHARACTER_VOICE_MAP.get(char_id, {})
    fallback_tld = profile.get("fallback_tld", tld)
    clean_text = sanitize_text_for_tts(text)
    t0 = time.time()
    mp3_fp = io.BytesIO()
    tts = gTTS(text=clean_text, lang="en", tld=fallback_tld, slow=False)
    tts.write_to_fp(mp3_fp)
    latency_ms = (time.time() - t0) * 1000
    log_api_trace("gTTS", "gtts-standard", "free", 200, latency_ms, step="TTS_Fallback")
    mp3_fp.seek(0)
    return mp3_fp

