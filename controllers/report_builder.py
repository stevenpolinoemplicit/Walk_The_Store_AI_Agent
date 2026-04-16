# report_builder.py — assembles per-brand HealthReport objects and builds the cross-brand summary.
# Coordinates data from Postgres (Intentwise-synced tables), Teamwork, and the classifier.
# Coordinates the data gathering for one brand. Calls postgres.get_account_health_metrics(), calls teamwork.get_completed_tasks(), feeds the raw numbers into
# classifier.classify_account(), and assembles the final HealthReport object. If Postgres or Teamwork fails, it logs the gap and continues rather than crashing.

import logging
from datetime import date
from typing import List, Optional

from controllers.classifier import classify_account
from config.thresholds import CRITICAL, WARNING, HEALTHY, UNKNOWN
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


# #note: Builds one HealthReport per marketplace (country_code) for a brand.
# Teamwork data is fetched once and shared across all country reports for the brand.
# Returns a list — most brands will have one entry (US), multi-marketplace brands get one per country.
def build_brand_reports(account: AccountConfig) -> List[HealthReport]:
    brand = account.brand_name

    # Fetch metrics for all countries from Postgres
    metrics_by_country: dict[str, dict] = {}
    if account.account_id is None:
        logger.warning(f"[{brand}] account_id not resolved — skipping health metrics")
    else:
        try:
            metrics_by_country = postgres.get_account_health_metrics(
                account.account_id, fbm=account.fbm, fba=account.fba
            )
        except Exception:
            logger.warning(f"[{brand}] Health metrics unavailable — logged as gap")

    # Teamwork: fetched once per brand, attached to all country reports
    completed_tasks: list[dict] = []
    open_tasks: list[dict] = []
    teamwork_gap = False
    for dept, list_id in account.tw_task_lists.items():
        if not list_id:
            continue
        try:
            completed_tasks.extend(teamwork.get_completed_tasks_by_list(list_id))
        except Exception:
            logger.warning(f"[{brand}] Teamwork completed tasks for list '{dept}' unavailable — skipping")
            teamwork_gap = True
        try:
            open_tasks.extend(teamwork.get_open_tasks_by_list(list_id))
        except Exception:
            logger.warning(f"[{brand}] Teamwork open tasks for list '{dept}' unavailable — skipping")

    # No metrics at all — return a single unknown report so the brand appears in the summary
    if not metrics_by_country:
        findings, highest_severity = classify_account(
            {}, check_shipping=account.fbm, check_vtr=account.fbm
        )
        return [HealthReport(
            brand_code=account.brand_code,
            brand_name=brand,
            report_date=date.today(),
            highest_severity=highest_severity,
            findings=findings,
            teamwork_completed_tasks=completed_tasks,
            teamwork_open_tasks=open_tasks,
            data_gaps=["account_health_metrics"] + (["teamwork"] if teamwork_gap else []),
        )]

    # One HealthReport per country — brand_name and brand_code include country suffix
    reports: List[HealthReport] = []
    for cc, metrics_raw in metrics_by_country.items():
        data_gaps: list[str] = []
        if teamwork_gap:
            data_gaps.append("teamwork")

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

        findings, highest_severity = classify_account(
            metrics, check_shipping=account.fbm, check_vtr=account.fbm
        )

        reports.append(HealthReport(
            brand_code=f"{account.brand_code}_{cc}",
            brand_name=f"{brand} {cc}",
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
            teamwork_open_tasks=open_tasks,
            brand_context=None,
            data_gaps=data_gaps,
        ))

    return reports


# #note: Generates a plain-text cross-brand summary from a list of completed reports.
# Critical accounts listed first with top 4 findings; warning accounts with top 3 findings;
# healthy accounts collapsed into a single comma-separated line.
def build_ops_summary(reports: List[HealthReport]) -> str:
    critical = [r for r in reports if r.highest_severity == CRITICAL]
    warning = [r for r in reports if r.highest_severity == WARNING]
    # UNKNOWN means all metrics returned None (no data) — treat as no issues for summary grouping
    healthy = [r for r in reports if r.highest_severity in (HEALTHY, UNKNOWN)]

    lines = [
        f"*Walk the Store — Daily Summary ({date.today()})*",
        f"Accounts checked: {len(reports)}",
        f"🔴 Critical: {len(critical)}   🟡 Warning: {len(warning)}   🟢 Healthy: {len(healthy)}",
        "",
    ]

    if critical:
        lines.append("*Critical accounts:*")
        for r in critical:
            label = f"<{r.drive_url}|{r.brand_name}>" if r.drive_url else r.brand_name
            lines.append(f"  • {label}")
            alert_findings = [f for f in r.findings if f.severity in (CRITICAL, WARNING)][:4]
            for f in alert_findings:
                emoji = "🔴" if f.severity == CRITICAL else "🟡"
                lines.append(f"      {emoji} {f.message}")

    if warning:
        lines.append("*Warning accounts:*")
        for r in warning:
            label = f"<{r.drive_url}|{r.brand_name}>" if r.drive_url else r.brand_name
            lines.append(f"  • {label}")
            alert_findings = [f for f in r.findings if f.severity in (CRITICAL, WARNING)][:3]
            for f in alert_findings:
                emoji = "🔴" if f.severity == CRITICAL else "🟡"
                lines.append(f"      {emoji} {f.message}")

    if healthy:
        healthy_names = ", ".join(r.brand_name for r in healthy)
        lines.append(f"*Healthy accounts:* {healthy_names}")

    return "\n".join(lines)
