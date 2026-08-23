"""Analytics, Weekly Reports & User Stats API Router."""
import logging
from fastapi import APIRouter, HTTPException, Query

from app.analytics import generate_weekly_report
from app.core import ai_engine
from app.scenarios import get_scenario
from app.storage import add_user_xp, get_user_stats
from app.api.schemas.chat import DetSpeechEvalRequest

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
async def api_det_evaluate_speech(payload: DetSpeechEvalRequest):
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
        filler_count=payload.filler_count,
    )
    return result
