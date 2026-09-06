"""
reports_router.py — FastAPI Router for Speaking PDF Reports & Idempotent Caching
"""

import os
import uuid
from typing import Any

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.services.pdf_report_service import (
    generate_speaking_pdf,
    get_sample_report_data,
)
from app.storage.db import (
    get_cached_exam_report,
    get_exam_report_by_id,
    save_exam_report,
)

router = APIRouter(prefix="/api/reports", tags=["Speaking Reports"])


class GenerateReportRequest(BaseModel):
    """Payload for PDF report generation request."""
    force: bool = Field(default=False, description="Force re-generation bypassing cache")
    report_data: dict[str, Any] | None = Field(default=None, description="Optional custom report data")


@router.post(
    "/speaking/{session_id}/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Generate or return cached Speaking PDF report",
)
def generate_speaking_report(
    session_id: str,
    payload: GenerateReportRequest | None = Body(default=None),
) -> JSONResponse:
    """
    Generate or retrieve an idempotent Speaking PDF report for session_id.
    - If called repeatedly on the same day with force=False, returns HTTP 200 OK with cached report_id.
    - If force=True or first time generation, generates new PDF and returns HTTP 201 Created.
    """
    force = payload.force if payload else False
    custom_data = payload.report_data if (payload and payload.report_data) else None

    # 1. Idempotency Check (if not forced)
    if not force:
        cached = get_cached_exam_report(session_id)
        if cached:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "report_id": cached["id"],
                    "session_id": cached["session_id"],
                    "download_url": f"/api/reports/speaking/{cached['id']}/file",
                    "created_at": cached["created_at"],
                    "cached": True,
                },
            )

    # 2. Generate new PDF Report
    report_id = f"rpt_{session_id}_{uuid.uuid4().hex[:8]}"
    output_file_path = f"reports/{report_id}.pdf"

    if custom_data:
        data_to_render = dict(custom_data)
        data_to_render["session_id"] = session_id
    else:
        data_to_render = get_sample_report_data()
        data_to_render["session_id"] = session_id

    generate_speaking_pdf(data_to_render, output_file_path)

    # 3. Store record in database
    saved_record = save_exam_report(
        report_id=report_id,
        session_id=session_id,
        file_path=output_file_path,
        report_data=data_to_render,
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "report_id": report_id,
            "session_id": session_id,
            "download_url": f"/api/reports/speaking/{report_id}/file",
            "created_at": saved_record.get("created_at", ""),
            "cached": False,
        },
    )


@router.get(
    "/speaking/{report_id}/file",
    summary="Download binary Speaking PDF report file",
)
def get_speaking_report_file(report_id: str) -> FileResponse:
    """Return binary PDF file stream for given report_id."""
    record = get_exam_report_by_id(report_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found",
        )

    file_path = record["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file for report '{report_id}' not found on server disk",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"speaking_report_{report_id}.pdf",
    )


@router.get(
    "/speaking/{report_id}",
    summary="Get Speaking report metadata and download link",
)
def get_speaking_report_metadata(report_id: str) -> dict[str, Any]:
    """Return metadata and download URL for given report_id."""
    record = get_exam_report_by_id(report_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found",
        )

    file_exists = os.path.exists(record["file_path"])
    file_size = os.path.getsize(record["file_path"]) if file_exists else 0

    return {
        "report_id": record["id"],
        "session_id": record["session_id"],
        "download_url": f"/api/reports/speaking/{record['id']}/file",
        "created_at": record["created_at"],
        "file_exists": file_exists,
        "file_size": file_size,
    }
