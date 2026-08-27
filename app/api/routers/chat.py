"""Chat & Conversational Dialogue API Router."""
import base64
import json
import logging
import uuid
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.api.schemas.chat import (
    ChatRequest,
    FastTurnRequest,
    StartScenarioRequest,
    TurnRequest,
    VoiceTurnRequest,
)
from app.audio import ASRChunkResult, StreamingSessionState, TTSStreamer
from app.core import ConversationalAgent, ai_engine
from app.core.ai_engine import get_background_evaluation
from app.rag import PromptContext, compute_band_window, retrieve_dialogues
from app.storage import get_db_connection

logger = logging.getLogger("duolingo_speak.api.chat")
router = APIRouter(tags=["Chat & Dialogue Engine"])


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


@router.get("/api/topics")
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


@router.post("/api/voice/process_turn")
async def api_voice_process_turn(payload: VoiceTurnRequest):
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


@router.post("/api/voice/process_turn_multipart")
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


@router.post("/api/start_scenario")
def api_start_scenario(payload: StartScenarioRequest):
    try:
        greeting = ai_engine.start_roleplay_greeting(
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            level=payload.level or 1,
        )
        return greeting
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/process_turn")
def api_process_turn(payload: TurnRequest):
    if not payload.user_transcript.strip():
        raise HTTPException(status_code=400, detail="User transcript cannot be empty")
    try:
        result = ai_engine.process_turn(
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            user_transcript=payload.user_transcript,
            conversation_history=payload.conversation_history,
            level=payload.level or 1,
            speech_metrics=payload.speech_metrics,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat")
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
            level=payload.level or 1,
            speech_metrics=payload.speech_metrics,
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
            "user_feedback": fb,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/process_turn_fast")
def api_process_turn_fast(payload: FastTurnRequest, background_tasks: BackgroundTasks):
    if not payload.user_transcript.strip():
        raise HTTPException(status_code=400, detail="User transcript cannot be empty")
    turn_id = payload.turn_id or str(uuid.uuid4())
    try:
        fast_result = ai_engine.process_turn_fast(
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            user_transcript=payload.user_transcript,
            conversation_history=payload.conversation_history,
            level=payload.level or 1,
        )
        ai_response = fast_result.get("ai_response", "")
        background_tasks.add_task(
            ai_engine.evaluate_turn_background,
            turn_id=turn_id,
            scenario_id=payload.scenario_id,
            character_id=payload.character_id,
            user_transcript=payload.user_transcript,
            conversation_history=payload.conversation_history,
            ai_response=ai_response,
            level=payload.level or 1,
            speech_metrics=payload.speech_metrics,
        )
        return {
            "turn_id": turn_id,
            "ai_response": ai_response,
            "status": "processing_eval",
            "latency_mode": "fast_voice",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/turn_evaluation/{turn_id}")
def api_get_turn_evaluation(turn_id: str):
    eval_res = get_background_evaluation(turn_id)
    if not eval_res:
        return {"turn_id": turn_id, "status": "pending", "user_feedback": None}
    return eval_res

