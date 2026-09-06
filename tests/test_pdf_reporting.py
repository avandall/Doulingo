"""
test_pdf_reporting.py — Integration and Unit Tests for PDF Reporting Engine & API Endpoints
"""

import os
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_report_service import (
    generate_speaking_pdf,
    get_sample_report_data,
    render_report_html,
)

client = TestClient(app)


def get_pdf_page_count(pdf_path: str) -> int:
    """Parse total page count from raw PDF binary data."""
    with open(pdf_path, "rb") as f:
        content = f.read()
    match = re.search(rb"/Count\s+(\d+)", content)
    if match:
        return int(match.group(1))
    # Fallback count method
    return content.count(b"/Type /Page") + content.count(b"/Type/Page")


def test_render_report_html():
    """Verify that Jinja2 renders HTML with expected components."""
    data = get_sample_report_data()
    html = render_report_html(data)

    assert "<!DOCTYPE html>" in html
    assert data["candidate_name"] in html
    assert data["overall_score"] in html
    assert data["cefr_level"] in html
    assert "Fluency & Coherence" in html
    assert "Pronunciation" in html
    assert "Grammatical Range" in html
    assert "Lexical Resource" in html
    assert "break-inside: avoid" in html
    assert "@page {" in html


def test_render_pdf(tmp_path):
    """Verify that generate_speaking_pdf creates a valid A4 PDF with >= 2 pages."""
    data = get_sample_report_data()
    output_path = str(tmp_path / "test_speaking_report.pdf")

    result_path = generate_speaking_pdf(data, output_path)

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 5000  # Non-trivial PDF size

    pages = get_pdf_page_count(result_path)
    assert pages >= 2, f"Expected PDF to have at least 2 pages, got {pages}"


def test_generate_sample_report_file():
    """Generate reports/sample_report.pdf as requested by Task Acceptance Criteria."""
    data = get_sample_report_data()
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = str(out_dir / "sample_report.pdf")

    result_path = generate_speaking_pdf(data, target)

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0
    pages = get_pdf_page_count(result_path)
    assert pages >= 2


def test_reports_api_generate_and_idempotency():
    """Verify POST /api/reports/speaking/{session_id}/generate idempotency & force option."""
    import uuid
    session_id = f"test-session-idempotency-{uuid.uuid4().hex[:8]}"

    # 1. First time generation -> 201 Created
    res1 = client.post(f"/api/reports/speaking/{session_id}/generate", json={"force": False})
    assert res1.status_code == 201, f"Expected 201 Created, got {res1.status_code}: {res1.text}"
    body1 = res1.json()
    assert "report_id" in body1
    assert body1["session_id"] == session_id
    assert body1["cached"] is False
    assert "/api/reports/speaking/" in body1["download_url"]
    first_report_id = body1["report_id"]

    # 2. Second call same day -> 200 OK with old report_id (Idempotent Cache)
    res2 = client.post(f"/api/reports/speaking/{session_id}/generate", json={"force": False})
    assert res2.status_code == 200, f"Expected 200 OK for cached call, got {res2.status_code}: {res2.text}"
    body2 = res2.json()
    assert body2["report_id"] == first_report_id
    assert body2["cached"] is True

    # 3. Third call with force=True -> 201 Created with new report_id
    res3 = client.post(f"/api/reports/speaking/{session_id}/generate", json={"force": True})
    assert res3.status_code == 201, f"Expected 201 Created for forced call, got {res3.status_code}: {res3.text}"
    body3 = res3.json()
    assert body3["report_id"] != first_report_id
    assert body3["cached"] is False


def test_reports_api_get_file_and_metadata():
    """Verify GET /api/reports/speaking/{report_id}/file & GET /api/reports/speaking/{report_id}."""
    import uuid
    session_id = f"test-session-file-fetch-{uuid.uuid4().hex[:8]}"

    # Generate a report first
    gen_res = client.post(f"/api/reports/speaking/{session_id}/generate", json={"force": True})
    assert gen_res.status_code == 201
    report_id = gen_res.json()["report_id"]

    # 1. Fetch metadata
    meta_res = client.get(f"/api/reports/speaking/{report_id}")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert meta["report_id"] == report_id
    assert meta["session_id"] == session_id
    assert meta["file_exists"] is True
    assert meta["file_size"] > 0

    # 2. Download binary PDF file
    file_res = client.get(f"/api/reports/speaking/{report_id}/file")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"] == "application/pdf"
    assert len(file_res.content) > 1000

    # 3. Non-existent report ID returns 404
    bad_meta = client.get("/api/reports/speaking/non-existent-report-id-9999")
    assert bad_meta.status_code == 404

    bad_file = client.get("/api/reports/speaking/non-existent-report-id-9999/file")
    assert bad_file.status_code == 404
