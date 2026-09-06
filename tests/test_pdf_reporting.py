"""
test_pdf_reporting.py — Integration and Unit Tests for PDF Reporting Engine
"""

import os
import re
from pathlib import Path

import pytest

from app.services.pdf_report_service import (
    generate_speaking_pdf,
    get_sample_report_data,
    render_report_html,
)


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
