# findings.py — Pydantic models for individual metric findings and their severity classification.
# A Finding is one data point (e.g. late shipment rate) with its severity label and human message.

from typing import Optional
from pydantic import BaseModel


# #note: Represents a single classified metric check — one Finding per metric per account per run
class Finding(BaseModel):
    check: str                          # metric name, e.g. "late_shipment_rate"
    metric_value: Optional[float] = None  # raw numeric value if available
    severity: str                       # "critical", "warning", "healthy", or "unknown"
    message: str                        # human-readable description for Slack report
