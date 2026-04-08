# report.py — Pydantic model for the complete daily health report for one brand.
# Built by report_builder.py, saved to Postgres, and formatted by slack_formatter.py.

from datetime import date
from typing import Optional, List
from pydantic import BaseModel

from models.findings import Finding


# #note: Full daily health snapshot for one account — all metric values, findings, and metadata
class HealthReport(BaseModel):
    account_config_id: int
    brand_name: str
    report_date: date
    highest_severity: str               # rolled-up worst severity across all findings

    # Individual metric values (None = data not available)
    late_shipment_rate: Optional[float] = None
    valid_tracking_rate: Optional[float] = None
    pre_cancel_rate: Optional[float] = None
    order_defect_rate: Optional[float] = None
    account_health_rating: Optional[int] = None
    account_status: Optional[str] = None
    food_safety_count: Optional[int] = None
    ip_complaint_count: Optional[int] = None

    # Classified findings list — one entry per metric checked
    findings: List[Finding] = []

    # Teamwork completed tasks for this brand (read-only)
    teamwork_completed_tasks: List[dict] = []

    # Brand context from NotebookLM (populated when API available)
    brand_context: Optional[str] = None

    # Tracks which metrics had no data so the report notes gaps instead of crashing
    data_gaps: List[str] = []
