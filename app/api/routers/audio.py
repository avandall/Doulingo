"""Audio Services API Router (TTS & ASR)."""
import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.audio import generate_tts_mp3, get_character_filler_path
from app.core import ai_engine

logger = logging.getLogger("duolingo_speak.api.audio")
router = APIRouter(tags=["Audio & Voice Synthesis"])


@router.get("/api/tts")
async def api_tts(
    text: str = Query(..., description="Text to synthesize"),
    character_id: str | None = Query(None, description="Character ID"),
    char_id: str | None = Query(None, description="Character ID alias"),
    tld: str = Query("com", description="Top level domain fallback for accent"),
):
    selected_char = character_id or char_id or "rajesh"
    try:
        mp3_stream = generate_tts_mp3(text=text, char_id=selected_char, tld=tld)
        headers = {
            "Content-Disposition": "inline; filename=speech.mp3",
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=86400",
        }
        return StreamingResponse(mp3_stream, media_type="audio/mpeg", headers=headers)
    except Exception as e:
        logger.error(f"TTS Generation failed for char_id='{selected_char}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS Generation failed: {e}")


@router.get("/api/fillers/{character_id}")
@router.get("/api/fillers")
async def api_filler(character_id: str = "lily"):
    try:
        rel_path = get_character_filler_path(character_id)
        abs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), rel_path)
        if os.path.exists(abs_path):
            return FileResponse(abs_path, media_type="audio/mpeg")
        mp3_stream = generate_tts_mp3("Hmm...", char_id=character_id)
        return StreamingResponse(mp3_stream, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Filler retrieval failed for char_id='{character_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Filler retrieval failed: {e}")


@router.post("/api/transcribe_audio")
async def api_transcribe_audio(
    file: UploadFile | None = File(None),
    fallback_text: str = Form(""),
):
    audio_bytes = b""
    filename = "speech.webm"
    if file:
        audio_bytes = await file.read()
        filename = file.filename or "speech.webm"

    if not audio_bytes and not fallback_text.strip():
        raise HTTPException(status_code=400, detail="No audio or fallback text provided")

    result = await ai_engine.transcribe_audio(audio_bytes, filename=filename, fallback_text=fallback_text)
    return result
