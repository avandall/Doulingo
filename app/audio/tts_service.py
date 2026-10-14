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

from app.core.ai_engine import (
    is_key_exhausted,
    log_api_trace,
    mark_key_exhausted,
    mask_api_key,
)

load_dotenv()
logger = logging.getLogger("duolingo_speak.tts")

# ElevenLabs & Azure Neural Voice Character Mappings
# All voice IDs are CONFIRMED FREE PREMADE voices from the ElevenLabs API.
CHARACTER_VOICE_MAP: dict[str, dict[str, Any]] = {
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

async def stream_elevenlabs_tts_ws(text: str, char_id: str, api_key: str, is_cancelled: Any = None):
    """
    WebSocket Streaming for ElevenLabs Text-to-Speech API.
    Uses wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input
    Provides zero-handshake overhead for successive chunks and unified contextual prosody.
    """
    import base64
    import json
    import websockets

    profile = CHARACTER_VOICE_MAP.get(char_id, CHARACTER_VOICE_MAP["lily"])
    voice_id = profile["eleven_voice_id"]
    settings = profile.get("eleven_settings", {"stability": 0.5, "similarity_boost": 0.75, "style": 0.5})

    ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_turbo_v2_5"

    headers = {
        "xi-api-key": api_key,
    }

    clean_text = sanitize_text_for_tts(text)

    async with websockets.connect(ws_url, additional_headers=headers, close_timeout=2.0) as ws:
        # Step 1: Send Initial Configuration (BOS - Beginning of Stream)
        bos_payload = {
            "text": " ",
            "voice_settings": {
                "stability": settings["stability"],
                "similarity_boost": settings["similarity_boost"],
                "style": settings["style"],
                "use_speaker_boost": True
            },
            "generation_config": {
                "chunk_length_schedule": [50, 100, 150, 200]
            }
        }
        await ws.send(json.dumps(bos_payload))

        # Step 2: Send text payload with flush trigger
        text_payload = {
            "text": f"{clean_text} ",
            "try_trigger_generation": True
        }
        await ws.send(json.dumps(text_payload))

        # Step 3: Send EOS (End of Stream)
        eos_payload = {"text": ""}
        await ws.send(json.dumps(eos_payload))

        # Step 4: Receive audio chunks as they arrive
        while True:
            if is_cancelled and await _check_cancelled(is_cancelled):
                logger.info("[ElevenLabs WS] Client cancelled stream. Closing socket.")
                await ws.close()
                return

            try:
                msg_str = await asyncio.wait_for(ws.recv(), timeout=6.0)
            except asyncio.TimeoutError:
                break

            data = json.loads(msg_str)
            audio_b64 = data.get("audio")
            if audio_b64:
                raw_chunk = base64.b64decode(audio_b64)
                if raw_chunk:
                    yield raw_chunk

            if data.get("isFinal"):
                break


async def stream_elevenlabs_tts_single(text: str, char_id: str, api_key: str, is_cancelled: Any = None):
    """Yields streaming chunks from ElevenLabs API. Tries WebSocket first; falls back to HTTP stream."""
    import httpx

    # Try WebSocket first for ultra-low latency & rate-limit safety
    try:
        ws_yielded = False
        async for chunk in stream_elevenlabs_tts_ws(text, char_id, api_key, is_cancelled=is_cancelled):
            ws_yielded = True
            yield chunk
        if ws_yielded:
            return
    except Exception as ws_err:
        logger.warning(f"[ElevenLabs WS] WebSocket connection failed ({ws_err}), falling back to HTTP Async Stream...")

    # Fallback to HTTP Async Stream if WebSocket fails
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

    async with httpx.AsyncClient(timeout=8.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as res:
            if res.status_code == 200:
                async for chunk in res.aiter_bytes(chunk_size=1024):
                    if is_cancelled and await _check_cancelled(is_cancelled):
                        logger.info("[ElevenLabs HTTP] Streaming cancelled by client.")
                        return
                    if chunk:
                        yield chunk
                return
            elif res.status_code in [400, 422]:
                # Fallback to multilingual v2 if turbo_v2_5 is not supported on a custom voice
                payload["model_id"] = "eleven_multilingual_v2"
                async with client.stream("POST", url, headers=headers, json=payload) as res_fb:
                    if res_fb.status_code == 200:
                        async for chunk in res_fb.aiter_bytes(chunk_size=1024):
                            if is_cancelled and await _check_cancelled(is_cancelled):
                                logger.info("[ElevenLabs HTTP] Streaming cancelled by client.")
                                return
                            if chunk:
                                yield chunk
                        return

            error_text = await res.aread()
            raise Exception(f"HTTP {res.status_code}: {error_text.decode('utf-8', errors='ignore')[:100]}")

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

async def _check_cancelled(is_cancelled: Any) -> bool:
    """Helper to check cancellation callback (sync or async callable, or boolean)."""
    if is_cancelled is None:
        return False
    if callable(is_cancelled):
        res = is_cancelled()
        if asyncio.iscoroutine(res):
            return await res
        return bool(res)
    return bool(is_cancelled)


async def stream_tts_mp3_chunks(text: str, char_id: str = "lily", tld: str = "com", is_cancelled: Any = None):
    """
    Asynchronously yields audio MP3 chunks for real-time low-latency streaming (<300ms initial chunk).
    Prioritizes ElevenLabs streaming, then Edge-TTS streaming async generator, then gTTS fallback.
    Supports early cancellation check to avoid wasting credits/compute when client disconnects.
    """
    logger.info(f"Starting chunked TTS audio stream for char_id='{char_id}', text_len={len(text)}")
    load_dotenv(override=True)
    raw_keys = os.getenv("ELEVENLABS_API_KEY", "").strip()
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

    # Early check before making remote calls
    if is_cancelled and await _check_cancelled(is_cancelled):
        logger.info("[TTS Service] Cancelled before synthesizing chunk.")
        return

    # 1. Try ElevenLabs Multi-Key Pool streaming if keys are present
    if keys:
        for idx, key in enumerate(keys):
            if is_key_exhausted(key):
                continue
            try:
                chunk_found = False
                async for chunk in stream_elevenlabs_tts_single(text, char_id, key, is_cancelled=is_cancelled):
                    chunk_found = True
                    yield chunk
                    if is_cancelled and await _check_cancelled(is_cancelled):
                        logger.info("[ElevenLabs] Streaming stopped mid-chunk due to client cancellation.")
                        return
                if chunk_found:
                    return
            except Exception as e:
                mark_key_exhausted(key)
                logger.warning(f"[ElevenLabs Stream Pool] Key #{idx+1} failed ({e}). Auto-rotating...")

    # 2. Try Edge-TTS async stream (<300ms initial chunk)
    try:
        chunk_count = 0
        async for chunk in stream_edge_tts(text, char_id):
            if is_cancelled and await _check_cancelled(is_cancelled):
                logger.info("[Edge-TTS] Stream cancelled by client disconnect.")
                return
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
            if is_cancelled and await _check_cancelled(is_cancelled):
                return
            yield chunk
        logger.info("Successfully streamed audio chunks via gTTS fallback")
    except Exception as e:
        logger.error(f"[TTS Service] All TTS providers failed: {e}", exc_info=True)
        raise


# List of common English abbreviations that end with a dot but should NOT cause sentence split
COMMON_ABBREVIATIONS = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "vs.", "etc.", "e.g.", "i.e.", "st.", "ave.", "approx."
}


def heuristic_split_sentences(text: str, max_clause_words: int = 14) -> list[str]:
    """
    Heuristic Chunking Buffer:
    1. Protects common abbreviations (Mr., Dr., etc.) from premature splitting.
    2. Splits primarily on strong sentence boundaries (. ! ? \n).
    3. If a sentence is long (> max_clause_words), splits at natural clause boundaries (, ; : —)
       so Time-To-First-Audio (TTFA) drops to ~300-500ms without breaking prosody.
    """
    if not text or not text.strip():
        return []

    clean_text = text.strip()

    # Step 1: Split by strong sentence boundaries (. ! ? \n)
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', clean_text)

    # Protect abbreviations by merging if previous token was an abbreviation
    refined_sentences: list[str] = []
    for s in raw_sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if refined_sentences:
            last_word = refined_sentences[-1].split()[-1].lower() if refined_sentences[-1].split() else ""
            if last_word in COMMON_ABBREVIATIONS:
                # Merge back
                refined_sentences[-1] = f"{refined_sentences[-1]} {s_clean}"
                continue
        refined_sentences.append(s_clean)

    # Step 2: Clause-level sub-chunking for long sentences
    final_chunks: list[str] = []
    for sentence in refined_sentences:
        words = sentence.split()
        if len(words) > max_clause_words and any(punct in sentence for punct in [",", ";", ":", "—", " - "]):
            # Split by comma or semicolon while preserving punctuation on the chunk
            sub_clauses = re.split(r'(?<=[,;:])\s+|(?<=\s—\s)|(?<=\s-\s)', sentence)
            acc_chunk = ""
            for clause in sub_clauses:
                clause = clause.strip()
                if not clause:
                    continue
                if not acc_chunk:
                    acc_chunk = clause
                else:
                    # If accumulating is still short, combine; otherwise emit
                    if len(acc_chunk.split()) + len(clause.split()) <= max_clause_words:
                        acc_chunk = f"{acc_chunk} {clause}"
                    else:
                        final_chunks.append(acc_chunk)
                        acc_chunk = clause
            if acc_chunk:
                final_chunks.append(acc_chunk)
        else:
            final_chunks.append(sentence)

    return final_chunks if final_chunks else [clean_text]


def split_sentences(text: str) -> list[str]:
    """Backward compatible wrapper using heuristic_split_sentences."""
    return heuristic_split_sentences(text)


async def stream_sentence_level_tts(text: str, char_id: str = "lily", tld: str = "com", is_cancelled: Any = None):
    """
    Sentence-level async generator for ultra-low latency TTS streaming (<1.0s TTFA).
    Splits the full utterance into sentence chunks, synthesizes and yields audio MP3 chunks
    for sentence 1 immediately, then streams sentence 2, sentence 3, etc. seamlessly.
    Checks cancellation state between sentences and within chunks to immediately stop resource consumption upon barge-in.
    """
    sentences = split_sentences(text)
    if not sentences:
        return

    logger.info(f"Starting sentence-level TTS stream ({len(sentences)} sentences) for char_id='{char_id}'")
    for idx, sentence in enumerate(sentences):
        if is_cancelled and await _check_cancelled(is_cancelled):
            logger.info(f"[SentenceTTS] Client barge-in / disconnected. Aborting sentence #{idx+1}/{len(sentences)}.")
            break

        t0 = time.time()
        chunk_count = 0
        async for chunk in stream_tts_mp3_chunks(sentence, char_id=char_id, tld=tld, is_cancelled=is_cancelled):
            chunk_count += 1
            yield chunk
            if is_cancelled and await _check_cancelled(is_cancelled):
                logger.info(f"[SentenceTTS] Barge-in during sentence #{idx+1}. Halting audio output.")
                return

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

