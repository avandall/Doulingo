"""
Main FastAPI App for Duolingo Speak
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from app.scenarios import list_scenarios, get_scenario
from app.characters import list_characters, get_character
from app.ai_engine import ai_engine
from app.tts_service import generate_tts_mp3

app = FastAPI(title="Duolingo Speak - Long Context Speaking App")

class TurnRequest(BaseModel):
    scenario_id: str
    character_id: Optional[str] = None
    user_transcript: str
    conversation_history: List[Dict[str, str]] = []

@app.get("/api/scenarios")
def api_list_scenarios():
    return {"scenarios": list_scenarios()}

@app.get("/api/scenarios/{scenario_id}")
def api_get_scenario(scenario_id: str):
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@app.get("/api/characters")
def api_list_characters():
    return {"characters": list_characters()}

@app.get("/api/characters/{character_id}")
def api_get_character(character_id: str):
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@app.post("/api/process_turn")
def api_process_turn(payload: TurnRequest):
    if not payload.user_transcript.strip():
        raise HTTPException(status_code=400, detail="User transcript cannot be empty")
    try:
        result = ai_engine.process_turn(
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            user_transcript=payload.user_transcript,
            conversation_history=payload.conversation_history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tts")
def api_tts(
    text: str = Query(..., description="Text to synthesize"),
    tld: str = Query("com", description="Top level domain for accent (e.g. co.in for Indian English)")
):
    try:
        mp3_stream = generate_tts_mp3(text=text, lang="en", tld=tld)
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
