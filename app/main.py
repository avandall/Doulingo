"""
Main FastAPI App for Duolingo Speak
Features:
- Saved Vocabulary Book Endpoint (/api/saved_words).
- Permanent SQLite Word Dictionary Storage & RAM Cache (0ms Instant Word Lookup).
- Expressive Neural Voice TTS (/api/tts).
- Reliable Full Sentence Translation (/api/process_turn & /api/translate_word).
- Level 1-20 Difficulty Control & SQLite Custom Topics.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import requests

from app.scenarios import list_scenarios, get_scenario
from app.characters import list_characters, get_character
from app.db import add_custom_scenario, get_translated_word, save_translated_word, get_all_saved_words
from app.ai_engine import ai_engine
from app.tts_service import generate_tts_mp3

app = FastAPI(title="Duolingo Speak - Unlimited AI Roleplays")

# Global In-Memory Caches for Instant 0ms Word Lookup
TRANSLATION_CACHE: Dict[str, str] = {}
IPA_CACHE: Dict[str, str] = {}

class TurnRequest(BaseModel):
    scenario_id: str
    character_id: Optional[str] = None
    user_transcript: str
    conversation_history: List[Dict[str, str]] = []
    level: Optional[int] = 1

class StartScenarioRequest(BaseModel):
    scenario_id: str
    character_id: Optional[str] = None
    level: Optional[int] = 1

class CustomScenarioRequest(BaseModel):
    title: str
    category: Optional[str] = "Everyday Life ☕"
    icon: Optional[str] = "💬"
    color: Optional[str] = "#1CB0F6"
    level: Optional[str] = "Beginner"
    level_code: Optional[str] = "A2"
    default_character: Optional[str] = "rajesh"
    description: Optional[str] = "Custom everyday life topic"
    objective: Optional[str] = "Express your thoughts freely."
    suggested_vocabulary: Optional[List[str]] = ["Everyday conversation", "Free chat"]

def fetch_fallback_full_translation(text: str, target_lang: str = "vi") -> str:
    """Fetch full sentence translation if LLM omits it."""
    if not text:
        return ""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={requests.utils.quote(text)}"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data and data[0]:
                return "".join([part[0] for part in data[0] if part and part[0]])
    except Exception:
        pass
    return ""

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
    sc_id = f"custom_{uuid.uuid4().hex[:8]}"
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
        "suggested_vocabulary": payload.suggested_vocabulary or ["Everyday chat"]
    }
    saved = add_custom_scenario(sc_data)
    return {"status": "success", "scenario": saved}

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
        if not greeting.get("ai_response_vi"):
            greeting["ai_response_vi"] = fetch_fallback_full_translation(greeting.get("ai_response", ""))
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
        if not result.get("ai_response_vi"):
            result["ai_response_vi"] = fetch_fallback_full_translation(result.get("ai_response", ""))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/saved_words")
def api_get_saved_words(target_lang: Optional[str] = Query(None, description="Optional target language filter")):
    """
    Retrieve all saved vocabulary words from SQLite DB for user review & study.
    """
    words = get_all_saved_words(target_lang)
    return {"count": len(words), "words": words}

@app.get("/api/translate_word")
def api_translate_word(
    word: str = Query(..., description="Word to look up"),
    target_lang: str = Query("vi", description="Target translation language code (vi, en-def, es, fr)")
):
    """
    High-Performance Word Lookup Endpoint.
    Uses Permanent SQLite Storage + RAM Cache so all translated words are saved forever!
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

    # 3. Fetch from External APIs if not in DB yet
    tl_code = target_lang if target_lang != "en-def" else "en"
    real_translation = f"Definition of '{clean_word}'"
    try:
        gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={tl_code}&dt=t&q={requests.utils.quote(clean_word)}"
        gt_res = requests.get(gt_url, timeout=3)
        if gt_res.status_code == 200:
            gt_data = gt_res.json()
            if gt_data and gt_data[0] and gt_data[0][0]:
                real_translation = gt_data[0][0][0]
    except Exception as e:
        print(f"[Translate Word] Google Translate error: {e}")

    # Fetch Real IPA Phonetics
    real_ipa = f"/{clean_word.lower()}/"
    try:
        dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{requests.utils.quote(clean_word.lower())}"
        dict_res = requests.get(dict_url, timeout=3)
        if dict_res.status_code == 200:
            dict_data = dict_res.json()
            if isinstance(dict_data, list) and dict_data[0].get("phonetics"):
                for p in dict_data[0]["phonetics"]:
                    if p.get("text"):
                        real_ipa = p["text"]
                        break
    except Exception as e:
        print(f"[Translate Word] Dictionary API error: {e}")

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
def api_tts(
    text: str = Query(..., description="Text to synthesize"),
    char_id: str = Query("rajesh", description="Character ID for Neural Voice profile"),
    tld: str = Query("com", description="Top level domain fallback for accent")
):
    try:
        mp3_stream = generate_tts_mp3(text=text, char_id=char_id, tld=tld)
        return StreamingResponse(mp3_stream, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Generation failed: {e}")

# Static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Duolingo Speak API Server Running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
