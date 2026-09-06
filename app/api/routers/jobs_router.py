"""
Jobs & Async Evaluation APIRouter
Provides async background evaluation triggers (202 Accepted) and status polling endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.services.background_job_service import (
    get_job_status,
    trigger_async_evaluation,
)

router = APIRouter(tags=["jobs"])


@router.post(
    "/api/exams/{session_id}/evaluate-async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Async Exam Evaluation",
)
async def evaluate_exam_async(session_id: str, background_tasks: BackgroundTasks):
    """Trigger background AI evaluation job for exam session and respond in <1s with 202 Accepted."""
    result = await trigger_async_evaluation(
        session_id, background_tasks=background_tasks
    )
    return result


@router.get(
    "/api/jobs/{job_id}/status",
    summary="Get Background Job Status",
)
def get_evaluation_job_status(job_id: str):
    """Retrieve status polling info for background evaluation job."""
    job_info = get_job_status(job_id)
    if not job_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return job_info
