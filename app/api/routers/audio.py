"""Audio Services API Router (TTS & ASR)."""
import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.audio import (
    generate_tts_mp3,
    get_character_filler_path,
    stream_sentence_level_tts,
)
from app.core import ai_engine

logger = logging.getLogger("duolingo_speak.api.audio")
router = APIRouter(tags=["Audio & Voice Synthesis"])


@router.get("/api/tts/stream")
async def api_tts_stream(
    text: str = Query(..., description="Text to synthesize"),
    character_id: str | None = Query(None, description="Character ID"),
    char_id: str | None = Query(None, description="Character ID alias"),
    tld: str = Query("com", description="Top level domain fallback for accent"),
):
    """Sentence-level ultra-low latency audio streaming endpoint (<1.0s TTFA)."""
    selected_char = character_id or char_id or "lily"
    try:
        audio_generator = stream_sentence_level_tts(text=text, char_id=selected_char, tld=tld)
        headers = {
            "Content-Disposition": "inline; filename=speech_stream.mp3",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
        return StreamingResponse(audio_generator, media_type="audio/mpeg", headers=headers)
    except Exception as e:
        logger.error(f"TTS Sentence Stream failed for char_id='{selected_char}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS Sentence Stream failed: {e}")


@router.get("/api/tts")
async def api_tts(
    text: str = Query(..., description="Text to synthesize"),
    character_id: str | None = Query(None, description="Character ID"),
    char_id: str | None = Query(None, description="Character ID alias"),
    tld: str = Query("com", description="Top level domain fallback for accent"),
    stream: bool = Query(False, description="Enable sentence-level streaming"),
):
    selected_char = character_id or char_id or "rajesh"
    try:
        if stream:
            audio_generator = stream_sentence_level_tts(text=text, char_id=selected_char, tld=tld)
            headers = {
                "Content-Disposition": "inline; filename=speech_stream.mp3",
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
            return StreamingResponse(audio_generator, media_type="audio/mpeg", headers=headers)

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


@router.post("/api/audio/extract_acoustic_metrics")
async def api_extract_acoustic_metrics(
    file: UploadFile | None = File(None),
    transcript: str = Form(""),
):
    """
    Asynchronously extracts acoustic metrics (WPM, pauses, fluency tier, pronunciation score)
    from background recorded audio blob + transcript without blocking optimistic client STT.
    """
    audio_bytes = b""
    if file:
        audio_bytes = await file.read()

    clean_tx = (transcript or "").strip()
    metrics = ai_engine._compute_speech_acoustic_metrics(clean_tx, audio_bytes)
    return {
        "status": "success",
        "speech_metrics": metrics,
        "transcript": clean_tx,
    }

