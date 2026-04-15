# report_builder.py — assembles per-brand HealthReport objects and builds the cross-brand summary.
# Coordinates data from Postgres (Intentwise-synced tables), Teamwork, and the classifier.
# Coordinates the data gathering for one brand. Calls postgres.get_account_health_metrics(), calls teamwork.get_completed_tasks(), feeds the raw numbers into
# classifier.classify_account(), and assembles the final HealthReport object. If Postgres or Teamwork fails, it logs the gap and continues rather than crashing.

import logging
from datetime import date
from typing import List, Optional

from controllers.classifier import classify_account
from models.account import AccountConfig
from models.report import HealthReport
from tools import postgres, teamwork

logger = logging.getLogger(__name__)


# #note: Safely extracts a float metric from a dict; logs and returns None on failure
def _safe_float(data: dict, key: str, brand: str) -> Optional[float]:
    try:
        val = data.get(key)
        return float(val) if val is not None else None
    except (TypeError, ValueError) as e:
        logger.warning(f"[{brand}] Could not parse {key}: {e}")
        return None


# #note: Safely extracts an int metric from a dict; logs and returns None on failure
def _safe_int(data: dict, key: str, brand: str) -> Optional[int]:
    try:
        val = data.get(key)
        return int(val) if val is not None else None
    except (TypeError, ValueError) as e:
        logger.warning(f"[{brand}] Could not parse {key}: {e}")
        return None


# #note: Builds a complete HealthReport for one brand — reads metrics from Postgres, handles failures
def build_brand_report(account: AccountConfig) -> HealthReport:
    brand = account.brand_name
    data_gaps: list[str] = []

    # Fetch all health metrics from Intentwise-synced Postgres tables
    # Guard: account_id is resolved at startup — if None, the brand was skipped during load,
    # but guard here as a safety net in case AccountConfig is constructed elsewhere
    metrics_raw: dict = {}
    if account.account_id is None:
        logger.warning(f"[{brand}] account_id not resolved — skipping health metrics")
        data_gaps.append("account_health_metrics")
    else:
        try:
            metrics_raw = postgres.get_account_health_metrics(
                account.account_id, account.country_code
            )
        except Exception:
            logger.warning(f"[{brand}] Health metrics unavailable — logged as gap")
            data_gaps.append("account_health_metrics")

    # Teamwork: completed tasks — iterate all task lists for this brand and aggregate results
    completed_tasks: list[dict] = []
    for dept, list_id in account.tw_task_lists.items():
        if not list_id:
            continue
        try:
            tasks = teamwork.get_completed_tasks_by_list(list_id)
            completed_tasks.extend(tasks)
        except Exception:
            logger.warning(f"[{brand}] Teamwork list '{dept}' unavailable — skipping")
            if "teamwork" not in data_gaps:
                data_gaps.append("teamwork")

    # Brand context not implemented in v1
    brand_ctx: Optional[str] = None

    # Assemble raw metrics dict for classifier
    metrics = {
        "late_shipment_rate": _safe_float(metrics_raw, "late_shipment_rate", brand),
        "valid_tracking_rate": _safe_float(metrics_raw, "valid_tracking_rate", brand),
        "pre_cancel_rate": _safe_float(metrics_raw, "pre_cancel_rate", brand),
        "order_defect_rate": _safe_float(metrics_raw, "order_defect_rate", brand),
        "account_health_rating": metrics_raw.get("account_health_rating"),
        "food_safety_count": _safe_int(metrics_raw, "food_safety_count", brand),
        "ip_complaint_count": _safe_int(metrics_raw, "ip_complaint_count", brand),
        "account_status": metrics_raw.get("account_status"),
    }

    # Classify
    findings, highest_severity = classify_account(metrics)

    return HealthReport(
        brand_code=account.brand_code,
        brand_name=brand,
        report_date=date.today(),
        highest_severity=highest_severity,
        findings=findings,
        late_shipment_rate=metrics["late_shipment_rate"],
        valid_tracking_rate=metrics["valid_tracking_rate"],
        pre_cancel_rate=metrics["pre_cancel_rate"],
        order_defect_rate=metrics["order_defect_rate"],
        account_health_rating=metrics["account_health_rating"],
        account_status=metrics["account_status"],
        food_safety_count=metrics["food_safety_count"],
        ip_complaint_count=metrics["ip_complaint_count"],
        teamwork_completed_tasks=completed_tasks,
        brand_context=brand_ctx,
        data_gaps=data_gaps,
    )


# #note: Generates a plain-text cross-brand summary from a list of completed reports
def build_ops_summary(reports: List[HealthReport]) -> str:
    critical = [r for r in reports if r.highest_severity == "critical"]
    warning = [r for r in reports if r.highest_severity == "warning"]
    healthy = [r for r in reports if r.highest_severity == "healthy"]

    lines = [
        f"*Walk the Store — Daily Summary ({date.today()})*",
        f"Accounts checked: {len(reports)}",
        f"🔴 Critical: {len(critical)}   🟡 Warning: {len(warning)}   🟢 Healthy: {len(healthy)}",
        "",
    ]

    if critical:
        lines.append("*Critical accounts:*")
        for r in critical:
            lines.append(f"  • {r.brand_name}")

    if warning:
        lines.append("*Warning accounts:*")
        for r in warning:
            lines.append(f"  • {r.brand_name}")

    return "\n".join(lines)
