"""Analytics, Weekly Reports & User Stats API Router."""
import logging

from fastapi import APIRouter, Header, HTTPException, Query

from app.analytics import generate_weekly_report
from app.api.routers.auth import get_current_user_from_header
from app.api.schemas.chat import DetSpeechEvalRequest
from app.core import ai_engine
from app.scenarios import get_scenario
from app.storage import add_user_xp, get_user_stats

logger = logging.getLogger("duolingo_speak.api.analytics")
router = APIRouter(tags=["Analytics & User Stats"])


@router.get("/api/user_stats")
def api_get_user_stats():
    return get_user_stats()


@router.post("/api/user_stats/add_xp")
def api_add_user_xp(xp: int = Query(10, description="XP amount to add")):
    return add_user_xp(xp)


@router.get("/api/reports/weekly")
@router.get("/api/reporting/weekly")
def api_get_weekly_report(
    user_id: str = Query("user_demo", description="User ID for weekly report"),
    days: int = Query(7, description="Number of days for weekly reporting period"),
):
    return generate_weekly_report(user_id=user_id, days=days)


@router.get("/api/health/quota")
@router.get("/api/trace")
def api_get_trace_quota():
    return ai_engine.get_trace_quota_health()


@router.post("/api/det/evaluate_speech")
async def api_det_evaluate_speech(
    payload: DetSpeechEvalRequest,
    authorization: str | None = Header(None),
):
    scenario = get_scenario(payload.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="DET Scenario not found")

    user = get_current_user_from_header(authorization)
    mother_tongue = (payload.mother_tongue if payload.mother_tongue and payload.mother_tongue != "en" else None) or (user.get("mother_tongue") if user else "en") or "en"
    custom_keys = payload.custom_api_keys or (user.get("custom_api_keys") if user else {}) or {}

    result = await ai_engine.evaluate_det_speech(
        scenario=scenario,
        user_speech=payload.user_speech.strip(),
        duration_seconds=payload.duration_seconds or 120,
        mode=payload.mode or "read_then_speak",
        wpm=payload.wpm,
        pause_count=payload.pause_count,
        filler_count=payload.filler_count,
        conversation_history=payload.conversation_history,
        character_id=payload.character_id,
        mother_tongue=mother_tongue,
        custom_keys=custom_keys,
    )

    # Automatically record grammar/expression upgrades into user's personal Error Journal
    if user and isinstance(user, dict) and user.get("id"):
        user_id = user["id"]
        upgrades = result.get("sentence_upgrades", [])
        if isinstance(upgrades, list):
            for up in upgrades:
                if isinstance(up, dict):
                    orig = str(up.get("original", "")).strip()
                    upgraded = str(up.get("upgraded", "")).strip()
                    expl = str(up.get("explanation", "")).strip()
                    if orig and upgraded and orig.lower() != upgraded.lower():
                        try:
                            from app.analytics.error_journal import record_error
                            detail_str = f"Original: \"{orig}\" → Upgraded: \"{upgraded}\""
                            if expl:
                                detail_str += f" ({expl})"
                            record_error(
                                user_id=user_id,
                                error_type="grammar",
                                error_detail=detail_str,
                                context=scenario.get("title", "Speech Evaluation"),
                            )
                        except Exception as e:
                            logger.warning(f"[Analytics] Error recording to ErrorJournal: {e}")

    return result

