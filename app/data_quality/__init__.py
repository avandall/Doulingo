"""
app/data_quality package — Modules for Data Flywheel, PII scrubbing, and quality control.
"""

from app.data_quality.pii_scrubber import check_pii

__all__ = ["check_pii"]
