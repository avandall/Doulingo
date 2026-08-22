"""
Main FastAPI App for Duolingo Speak
Features:
- LLM-quality Natural Vietnamese Translations (via ai_engine, NO Google Translate scraping).
- Mobile PWA Speech Recognition Fix (Full transcript capture).
- Saved Vocabulary Book Endpoint (/api/saved_words).
- Permanent SQLite Word Dictionary Storage & RAM Cache (0ms Instant Word Lookup).
- Expressive Neural Voice TTS (/api/tts).
- Granular 20-Level Difficulty System with per-level hard constraints.
"""

import base64
import json
import logging
import os
import unicodedata
import uuid
from typing import Any
from urllib.parse import quote

import requests
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.ai_engine import ai_engine
from app.asr_processor import ASRChunkResult, StreamingSessionState
from app.characters import get_character, list_characters
from app.conversational_agent import ConversationalAgent
from app.db import (
    add_custom_scenario,
    add_user_xp,
    get_all_saved_words,
    get_custom_scenarios,
    get_db_connection,
    get_translated_word,
    get_user_stats,
    save_translated_word,
)
from app.prompt_constructor import PromptContext
from app.reporting import generate_weekly_report
from app.retrieval import compute_band_window, retrieve_dialogues
from app.scenarios import get_scenario, list_scenarios
from app.tts_service import generate_tts_mp3, get_character_filler_path
from app.tts_streamer import TTSStreamer

logger = logging.getLogger("duolingo_speak.api")

app = FastAPI(title="Duolingo Speak - Unlimited AI Roleplays")

# Global In-Memory Caches for Instant 0ms Word Lookup
TRANSLATION_CACHE: dict[str, str] = {}
IPA_CACHE: dict[str, str] = {}

class TurnRequest(BaseModel):
    scenario_id: str
    character_id: str | None = None
    user_transcript: str
    conversation_history: list[dict[str, str]] = []
    level: int | None = 1

class ChatRequest(BaseModel):
    user_transcript: str | None = None
    text: str | None = None
    scenario_id: str | None = "everyday_chat"
    character_id: str | None = None
    conversation_history: list[dict[str, str]] = []
    level: int | None = 1

class StartScenarioRequest(BaseModel):
    scenario_id: str
    character_id: str | None = None
    level: int | None = 1

class CustomScenarioRequest(BaseModel):
    title: str
    category: str | None = "Everyday Life ☕"
    icon: str | None = "💬"
    color: str | None = "#1CB0F6"
    level: str | None = "Beginner"
    level_code: str | None = "A2"
    default_character: str | None = "rajesh"
    description: str | None = "Custom everyday life topic"
    objective: str | None = "Express your thoughts freely."
    suggested_vocabulary: list[str] | None = ["Everyday conversation", "Free chat"]
    mode: str | None = "roleplay"

class ScenarioImportRequest(BaseModel):
    scenarios: list[CustomScenarioRequest]

class SentenceTranslateRequest(BaseModel):
    text: str
    target_lang: str | None = "vi"
    character_name: str | None = ""
    scenario_title: str | None = ""
    context_history: list[str] | None = []

class DetSpeechEvalRequest(BaseModel):
    scenario_id: str
    user_speech: str
    duration_seconds: int | None = 120
    mode: str | None = "read_then_speak"
    wpm: int | None = None
    pause_count: int | None = None
    filler_count: int | None = None


class VoiceTurnRequest(BaseModel):
    user_id: str = "user_demo"
    topic: str = "general_conversation"
    band_level: float = 5.5
    level: int | None = None
    conversation_history: list[dict[str, str]] = []
    character_id: str | None = "lily"
    text_only_mode: bool = False
    user_transcript: str | None = None
    audio_base64: str | None = None


async def _execute_voice_turn_pipeline(
    user_id: str,
    topic: str,
    band_level: float,
    conversation_history: list[dict[str, str]],
    character_id: str,
    text_only_mode: bool,
    user_transcript: str | None,
    audio_bytes: bytes | None,
    level: int | None = None,
) -> dict[str, Any]:
    # 1. ASR Ingestion & Chunk Processor
    final_transcript = (user_transcript or "").strip()
    if audio_bytes and len(audio_bytes) > 0:
        session = StreamingSessionState()
        chunk_res = ASRChunkResult(transcript="", words=[])
        session.process_chunk(audio_bytes, chunk_res)
        asr_text = session.get_transcript().strip()
        if asr_text:
            final_transcript = (
                asr_text if not final_transcript else f"{final_transcript} {asr_text}".strip()
            )

    if not final_transcript:
        final_transcript = "Hello! Let's practice English."

    if level is not None:
        effective_level = max(1, min(20, int(level)))
        effective_band = round(4.0 + (effective_level - 1) * (5.0 / 19.0), 1)
    else:
        effective_band = float(band_level)
        effective_level = max(1, min(20, round(1.0 + (effective_band - 4.0) * (19.0 / 5.0))))

    # 2. RAG Retrieval Layer
    band_min, band_max = compute_band_window(effective_band, "hold")
    retrieved = retrieve_dialogues(
        user_id=user_id,
        topic_tags=topic,
        band_min=band_min,
        band_max=band_max,
        limit=4,
        auto_log_exposure=True,
    )

    # 3. Prompt Construction
    context = PromptContext(
        user_id=user_id,
        band_estimate=effective_band,
        level=effective_level,
        topic_tag=topic,
        retrieved_dialogues=retrieved,
        character_name=character_id or "Lily",
        difficulty_adjustment="hold",
    )

    # 4. Conversational Agent Execution
    agent = ConversationalAgent()
    agent_response = agent.generate_response(
        context=context,
        history=conversation_history,
        user_utterance=final_transcript,
    )

    # 5. TTS Audio Synthesis
    tts_streamer = TTSStreamer(default_char_id=character_id or "lily")
    tts_result = tts_streamer.generate_audio(
        text=agent_response.ai_utterance,
        char_id=character_id or "lily",
        text_only_mode=text_only_mode,
    )

    audio_b64 = None
    if tts_result.audio_bytes:
        audio_b64 = base64.b64encode(tts_result.audio_bytes).decode("utf-8")

    return {
        "user_transcript": final_transcript,
        "ai_utterance": agent_response.ai_utterance,
        "internal_band_signal": agent_response.internal_band_signal,
        "topic_tag": agent_response.topic_tag,
        "difficulty_adjustment": agent_response.difficulty_adjustment,
        "audio_base64": audio_b64,
        "text_only_mode": tts_result.text_only_mode,
        "retrieved_dialogues_count": len(retrieved),
        "is_fallback": agent_response.is_fallback,
    }


@app.get("/api/topics")
def api_get_topics():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, template_type, topic_tags, target_band_min, target_band_max FROM content_units"
        )
        rows = cursor.fetchall()
        topics_set = set()
        units = []
        for r in rows:
            if isinstance(r, dict):
                row_dict = r
            elif hasattr(r, "keys"):
                row_dict = dict(r)
            else:
                row_dict = {
                    "id": r[0],
                    "title": r[1],
                    "template_type": r[2],
                    "topic_tags": r[3],
                    "target_band_min": r[4],
                    "target_band_max": r[5],
                }
            units.append(row_dict)
            raw_tags = row_dict.get("topic_tags", "[]")
            try:
                tags = json.loads(raw_tags) if isinstance(raw_tags, str) else raw_tags
                if isinstance(tags, list):
                    for t in tags:
                        if t and isinstance(t, str):
                            topics_set.add(t.strip())
            except Exception:
                pass
        return {
            "topics": sorted(topics_set),
            "content_units_count": len(units),
            "content_units": units,
        }
    finally:
        conn.close()


@app.post("/api/voice/process_turn")
async def api_voice_process_turn(payload: VoiceTurnRequest):
    """
    MVP 5-step Pipeline Endpoint:
    [1] ASR Ingestion -> [2] RAG Retrieval -> [3] Prompt Constructor -> [4] Conversational Agent -> [5] TTS Output.
    """
    audio_bytes = None
    if payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
        except Exception:
            audio_bytes = None

    result = await _execute_voice_turn_pipeline(
        user_id=payload.user_id,
        topic=payload.topic,
        band_level=payload.band_level,
        level=payload.level,
        conversation_history=payload.conversation_history,
        character_id=payload.character_id or "lily",
        text_only_mode=payload.text_only_mode,
        user_transcript=payload.user_transcript,
        audio_bytes=audio_bytes,
    )
    return result


@app.post("/api/voice/process_turn_multipart")
async def api_voice_process_turn_multipart(
    file: UploadFile | None = File(None),
    user_id: str = Form("user_demo"),
    topic: str = Form("general_conversation"),
    band_level: float = Form(5.5),
    level: int | None = Form(None),
    conversation_history: str = Form("[]"),
    character_id: str = Form("lily"),
    text_only_mode: bool = Form(False),
    user_transcript: str = Form(""),
):
    """
    Multipart File/Form Upload Variant of the MVP 5-step Pipeline Endpoint.
    """
    audio_bytes = None
    if file:
        audio_bytes = await file.read()

    history_list: list[dict[str, str]] = []
    if conversation_history:
        try:
            parsed = json.loads(conversation_history)
            if isinstance(parsed, list):
                history_list = parsed
        except Exception:
            pass

    result = await _execute_voice_turn_pipeline(
        user_id=user_id,
        topic=topic,
        band_level=band_level,
        level=level,
        conversation_history=history_list,
        character_id=character_id,
        text_only_mode=text_only_mode,
        user_transcript=user_transcript,
        audio_bytes=audio_bytes,
    )
    return result


# NOTE: Google Translate gtx scraping (client=gtx) has been REMOVED.
# Translation fallback is now handled inside ai_engine._fallback_llm_translate()
# which uses Groq/Gemini LLM for high-quality natural Vietnamese output.

@app.get("/api/scenarios")
def api_list_scenarios():
    return {"scenarios": list_scenarios()}

@app.get("/api/scenarios/{scenario_id}")
def api_get_scenario(scenario_id: str):
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@app.post("/api/custom_scenarios")
def api_create_custom_scenario(payload: CustomScenarioRequest):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    prefix = "det_custom_" if payload.mode == "ielts_exam" else "custom_"
    sc_id = f"{prefix}{uuid.uuid4().hex[:8]}"
    sc_data = {
        "id": sc_id,
        "title": payload.title,
        "category": payload.category,
        "icon": payload.icon or "💬",
        "color": payload.color or "#1CB0F6",
        "level": payload.level or "Beginner",
        "level_code": payload.level_code or "A2",
        "default_character": payload.default_character or "rajesh",
        "description": payload.description or "Everyday life topic",
        "objective": payload.objective or "Express thoughts freely.",
        "suggested_vocabulary": payload.suggested_vocabulary or ["Everyday chat"],
        "mode": payload.mode or "roleplay"
    }
    saved = add_custom_scenario(sc_data)
    return {"status": "success", "scenario": saved}

@app.get("/api/custom_scenarios/export/{scenario_id}")
def api_export_custom_scenario(scenario_id: str):
    """
    Export custom scenario by ID or 'all' for sharing between learners.
    """
    logger.info(f"Exporting scenario: {scenario_id}")
    if scenario_id == "all":
        custom_scenarios = get_custom_scenarios()
        return {"scenarios": custom_scenarios, "count": len(custom_scenarios)}

    scenario = get_scenario(scenario_id)
    if not scenario:
        logger.error(f"Scenario not found for export: {scenario_id}")
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"scenario": scenario}

@app.post("/api/custom_scenarios/import")
def api_import_custom_scenarios(payload: ScenarioImportRequest):
    """
    Import custom scenarios from JSON list for sharing between learners.
    """
    if not payload.scenarios:
        raise HTTPException(status_code=400, detail="Scenarios list cannot be empty")

    logger.info(f"Importing {len(payload.scenarios)} custom scenario(s)")
    imported = []
    for item in payload.scenarios:
        if not item.title.strip():
            continue
        prefix = "det_custom_" if item.mode == "ielts_exam" else "custom_"
        sc_id = f"{prefix}{uuid.uuid4().hex[:8]}"
        sc_data = {
            "id": sc_id,
            "title": item.title.strip(),
            "category": item.category or "Custom Topic",
            "icon": item.icon or "💬",
            "color": item.color or "#1CB0F6",
            "level": item.level or "Beginner",
            "level_code": item.level_code or "A2",
            "default_character": item.default_character or "rajesh",
            "description": item.description or "Imported topic",
            "objective": item.objective or "Express thoughts freely.",
            "suggested_vocabulary": item.suggested_vocabulary or ["Imported chat"],
            "mode": item.mode or "roleplay"
        }
        saved = add_custom_scenario(sc_data)
        imported.append(saved)

    return {"status": "success", "imported_count": len(imported), "scenarios": imported}

@app.get("/api/characters")
def api_list_characters():
    return {"characters": list_characters()}

@app.get("/api/characters/{character_id}")
def api_get_character(character_id: str):
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@app.post("/api/start_scenario")
def api_start_scenario(payload: StartScenarioRequest):
    try:
        greeting = ai_engine.start_roleplay_greeting(
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            level=payload.level or 1
        )
        # ai_response_vi is generated by AI in the same call.
        # If missing, frontend will fetch on-demand via /api/translate_sentence when user clicks Translate.
        return greeting
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process_turn")
def api_process_turn(payload: TurnRequest):
    if not payload.user_transcript.strip():
        raise HTTPException(status_code=400, detail="User transcript cannot be empty")
    try:
        result = ai_engine.process_turn(
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            user_transcript=payload.user_transcript,
            conversation_history=payload.conversation_history,
            level=payload.level or 1
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def api_chat(payload: ChatRequest):
    input_text = (payload.user_transcript or payload.text or "").strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="User transcript cannot be empty")

    sc_id = payload.scenario_id or "everyday_chat"
    try:
        result = ai_engine.process_turn(
            scenario_id=sc_id,
            character_id=payload.character_id,
            user_transcript=input_text,
            conversation_history=payload.conversation_history,
            level=payload.level or 1
        )
        ai_resp = result.get("ai_response", "")
        audio_url = f"/api/tts?text={quote(ai_resp[:200])}&character_id={payload.character_id or 'lily'}"
        fb = result.get("user_feedback", {})

        return {
            "response": ai_resp,
            "audio_url": audio_url,
            "fluency_score": fb.get("fluency_score", 90),
            "native_suggestion": fb.get("native_phrasing", ""),
            "is_completed": result.get("is_completed", False),
            "xp_gained": result.get("xp_gained", 10),
            "ai_response_vi": result.get("ai_response_vi", ""),
            "user_feedback": fb
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe_audio")
async def api_transcribe_audio(
    file: UploadFile | None = File(None),
    fallback_text: str = Form("")
):
    """
    Transcribes recorded microphone audio using Groq Whisper / Gemini Audio ASR.
    Falls back to browser Web Speech API text if audio is empty or API unavailable.
    """
    audio_bytes = b""
    filename = "speech.webm"
    if file:
        audio_bytes = await file.read()
        filename = file.filename or "speech.webm"

    if not audio_bytes and not fallback_text.strip():
        raise HTTPException(status_code=400, detail="No audio or fallback text provided")

    result = await ai_engine.transcribe_audio(audio_bytes, filename=filename, fallback_text=fallback_text)
    return result

# In-Memory cache for on-demand sentence translations
SENTENCE_TRANSLATION_CACHE: dict[str, str] = {}

@app.post("/api/translate_sentence")
def api_translate_sentence(payload: SentenceTranslateRequest):
    """
    On-demand sentence translation endpoint.
    Called LAZILY only when user explicitly clicks the Translate button.
    Caches results in RAM - same sentence translated only ONCE per session.
    Uses the same LLM pool as the main AI engine (Groq -> Gemini fallback).
    ZERO extra API calls unless user actively requests translation.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    target_lang = payload.target_lang or "vi"
    cache_key = f"{target_lang}::{text}"

    # Check RAM cache first - avoids repeat LLM calls for same sentence
    if cache_key in SENTENCE_TRANSLATION_CACHE:
        return {"translation": SENTENCE_TRANSLATION_CACHE[cache_key], "cached": True}

    translation = ai_engine._professional_vietnamese_localization(
        text,
        character_name=payload.character_name or "",
        scenario_title=payload.scenario_title or "",
        context_history=payload.context_history or []
    )
    if not translation:
        translation = ai_engine._fallback_llm_translate(text)
    if not translation:
        translation = text  # Show original if all LLMs fail

    SENTENCE_TRANSLATION_CACHE[cache_key] = translation
    return {"translation": translation, "cached": False}

@app.post("/api/det/evaluate_speech")
async def api_det_evaluate_speech(payload: DetSpeechEvalRequest):
    """
    Evaluates DET Speaking tasks (Read, Then Speak & Interactive Speaking).
    Returns official 10-160 DET score, CEFR band, examiner critique, C1/C2 upgrades, and band-160 sample speech.
    """
    scenario = get_scenario(payload.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="DET Scenario not found")
    
    result = await ai_engine.evaluate_det_speech(
        scenario=scenario,
        user_speech=payload.user_speech.strip(),
        duration_seconds=payload.duration_seconds or 120,
        mode=payload.mode or "read_then_speak",
        wpm=payload.wpm,
        pause_count=payload.pause_count,
        filler_count=payload.filler_count
    )
    return result

@app.get("/api/saved_words")
def api_get_saved_words(target_lang: str | None = Query(None, description="Optional target language filter")):
    words = get_all_saved_words(target_lang)
    return {"count": len(words), "words": words}

@app.get("/api/user_stats")
def api_get_user_stats():
    return get_user_stats()

@app.post("/api/user_stats/add_xp")
def api_add_user_xp(xp: int = Query(10, description="XP amount to add")):
    return add_user_xp(xp)

@app.get("/api/reports/weekly")
@app.get("/api/reporting/weekly")
def api_get_weekly_report(
    user_id: str = Query("user_demo", description="User ID for weekly report"),
    days: int = Query(7, description="Number of days for weekly reporting period"),
):
    """
    Weekly Performance Reporting Endpoint (TASK-018).
    Aggregates 4-axis performance metrics (Fluency, Lexical, Grammar, Pronunciation)
    over the reporting period without exposing real-time per-sentence scores on main UI.
    """
    return generate_weekly_report(user_id=user_id, days=days)

@app.get("/api/health/quota")
@app.get("/api/trace")
def api_get_trace_quota():
    return ai_engine.get_trace_quota_health()

@app.get("/api/translate_word")
def api_translate_word(
    word: str = Query(..., description="Word to look up"),
    target_lang: str = Query("vi", description="Target translation language code (vi, en-def, es, fr)")
):
    """
    High-Quality Natural Dictionary Lookup Endpoint.
    Uses dt=bd parameter to fetch natural, accurate dictionary meanings.
    """
    clean_word = word.strip().strip(".,!?;:\"'()[]{}")
    if not clean_word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")

    cache_key = f"{clean_word.lower()}_{target_lang}"
    lang_labels = {
        "vi": "Tiếng Việt",
        "en-def": "English Definition",
        "es": "Spanish",
        "fr": "French"
    }

    # 1. Check RAM Cache (0ms response)
    if cache_key in TRANSLATION_CACHE:
        return {
            "word": clean_word,
            "target_lang": target_lang,
            "target_label": lang_labels.get(target_lang, "Translation"),
            "translation": TRANSLATION_CACHE[cache_key],
            "phonetic": IPA_CACHE.get(clean_word.lower(), f"/{clean_word.lower()}/")
        }

    # 2. Check Permanent SQLite Database
    db_word = get_translated_word(clean_word, target_lang)
    if db_word:
        TRANSLATION_CACHE[cache_key] = db_word["translation"]
        IPA_CACHE[clean_word.lower()] = db_word["phonetic"]
        return db_word

    # 3. High-Quality Dictionary API Lookup (dt=t & dt=bd for natural everyday terms)
    tl_code = target_lang if target_lang != "en-def" else "en"
    real_translation = f"Definition of '{clean_word}'"
    try:
        gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={tl_code}&dt=t&dt=bd&q={quote(clean_word)}"
        gt_res = requests.get(gt_url, timeout=4)
        if gt_res.status_code == 200:
            gt_data = gt_res.json()
            terms = []
            
            # Extract rich dictionary meanings if available (dt=bd)
            if len(gt_data) > 1 and gt_data[1]:
                for dict_entry in gt_data[1]:
                    if len(dict_entry) > 1 and dict_entry[1]:
                        terms.extend(dict_entry[1][:3])
            
            # Fallback to main translation
            if not terms and gt_data[0] and gt_data[0][0]:
                terms.append(gt_data[0][0][0])
                
            if terms:
                unique_terms = list(dict.fromkeys(terms))[:3]
                raw_str = ", ".join(unique_terms)
                real_translation = unicodedata.normalize('NFC', raw_str).capitalize()
    except Exception as e:
        logger.warning(f"[Translate Word] Google Translate error: {e}")

    # Fetch Real IPA Phonetics
    real_ipa = f"/{clean_word.lower()}/"
    try:
        dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(clean_word.lower())}"
        dict_res = requests.get(dict_url, timeout=3)
        if dict_res.status_code == 200:
            dict_data = dict_res.json()
            if isinstance(dict_data, list) and dict_data[0].get("phonetics"):
                for p in dict_data[0]["phonetics"]:
                    if p.get("text"):
                        real_ipa = p["text"]
                        break
    except Exception as e:
        logger.warning(f"[Translate Word] Dictionary API error: {e}")

    # Save permanently into SQLite DB & RAM Cache
    save_translated_word(
        word=clean_word,
        target_lang=target_lang,
        target_label=lang_labels.get(target_lang, "Translation"),
        translation=real_translation,
        phonetic=real_ipa
    )
    TRANSLATION_CACHE[cache_key] = real_translation
    IPA_CACHE[clean_word.lower()] = real_ipa

    return {
        "word": clean_word,
        "target_lang": target_lang,
        "target_label": lang_labels.get(target_lang, "Translation"),
        "translation": real_translation,
        "phonetic": real_ipa
    }

@app.get("/api/tts")
async def api_tts(
    text: str = Query(..., description="Text to synthesize"),
    character_id: str | None = Query(None, description="Character ID"),
    char_id: str | None = Query(None, description="Character ID alias"),
    tld: str = Query("com", description="Top level domain fallback for accent")
):
    selected_char = character_id or char_id or "rajesh"
    try:
        mp3_stream = generate_tts_mp3(text=text, char_id=selected_char, tld=tld)
        headers = {
            "Content-Disposition": "inline; filename=speech.mp3",
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=86400"
        }
        return StreamingResponse(mp3_stream, media_type="audio/mpeg", headers=headers)
    except Exception as e:
        logger.error(f"TTS Generation failed for char_id='{char_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS Generation failed: {e}")

@app.get("/api/fillers/{character_id}")
@app.get("/api/fillers")
async def api_filler(character_id: str = "lily"):
    try:
        rel_path = get_character_filler_path(character_id)
        abs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), rel_path)
        if os.path.exists(abs_path):
            return FileResponse(abs_path, media_type="audio/mpeg")
        # If file not found, generate on the fly
        mp3_stream = generate_tts_mp3("Hmm...", char_id=character_id)
        return StreamingResponse(mp3_stream, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Filler retrieval failed for char_id='{character_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Filler retrieval failed: {e}")

# Static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"message": "Duolingo Speak API Server Running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)  # nosec B104
