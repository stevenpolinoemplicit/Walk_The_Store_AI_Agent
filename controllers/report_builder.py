# report_builder.py — assembles per-brand HealthReport objects and builds the cross-brand summary.
# Coordinates data from Intentwise, Teamwork, and the classifier into a single report.

import logging
from datetime import date
from typing import List, Optional

from controllers.classifier import classify_account
from models.account import AccountConfig
from models.report import HealthReport
from tools import intentwise_mcp, teamwork

logger = logging.getLogger(__name__)


# #note: Safely extracts a float metric from an Intentwise response dict; logs and returns None on failure
def _safe_float(data: dict, key: str, brand: str) -> Optional[float]:
    try:
        val = data.get(key)
        return float(val) if val is not None else None
    except (TypeError, ValueError) as e:
        logger.warning(f"[{brand}] Could not parse {key}: {e}")
        return None


# #note: Safely extracts an int metric from an Intentwise response dict; logs and returns None on failure
def _safe_int(data: dict, key: str, brand: str) -> Optional[int]:
    try:
        val = data.get(key)
        return int(val) if val is not None else None
    except (TypeError, ValueError) as e:
        logger.warning(f"[{brand}] Could not parse {key}: {e}")
        return None


# #note: Builds a complete HealthReport for one brand — fetches all data, handles per-source failures
def build_brand_report(account: AccountConfig) -> HealthReport:
    brand = account.brand_name
    data_gaps: list[str] = []

    # --- Intentwise: shipping metrics ---
    shipping: dict = {}
    try:
        shipping = intentwise_mcp.get_shipping_performance(
            account.seller_id, account.marketplace
        )
    except Exception:
        logger.warning(f"[{brand}] Shipping data unavailable — logged as gap")
        data_gaps.append("shipping_performance")

    # --- Intentwise: customer service / ODR ---
    cs: dict = {}
    try:
        cs = intentwise_mcp.get_customer_service_performance(
            account.seller_id, account.marketplace
        )
    except Exception:
        logger.warning(f"[{brand}] Customer service data unavailable — logged as gap")
        data_gaps.append("customer_service_performance")

    # --- Intentwise: policy compliance ---
    policy: dict = {}
    try:
        policy = intentwise_mcp.get_policy_compliance(
            account.seller_id, account.marketplace
        )
    except Exception:
        logger.warning(f"[{brand}] Policy compliance data unavailable — logged as gap")
        data_gaps.append("policy_compliance")

    # --- Intentwise: account status ---
    status_data: dict = {}
    try:
        status_data = intentwise_mcp.get_account_status(
            account.seller_id, account.marketplace
        )
    except Exception:
        logger.warning(f"[{brand}] Account status data unavailable — logged as gap")
        data_gaps.append("account_status")

    # --- Intentwise: seller performance (AHR) ---
    perf: dict = {}
    try:
        perf = intentwise_mcp.get_seller_performance(
            account.seller_id, account.marketplace
        )
    except Exception:
        logger.warning(f"[{brand}] Seller performance data unavailable — logged as gap")
        data_gaps.append("seller_performance")

    # --- Teamwork: completed tasks ---
    completed_tasks: list[dict] = []
    try:
        completed_tasks = teamwork.get_completed_tasks(account.teamwork_project_id)
    except Exception:
        logger.warning(f"[{brand}] Teamwork data unavailable — continuing without it")
        data_gaps.append("teamwork")

    # Brand context not implemented in v1
    brand_ctx: Optional[str] = None

    # --- Assemble raw metrics dict for classifier ---
    metrics = {
        "late_shipment_rate": _safe_float(shipping, "late_shipment_rate", brand),
        "valid_tracking_rate": _safe_float(shipping, "valid_tracking_rate", brand),
        "pre_cancel_rate": _safe_float(
            shipping, "pre_fulfillment_cancel_rate", brand
        ),
        "order_defect_rate": _safe_float(cs, "order_defect_rate", brand),
        "account_health_rating": _safe_int(
            perf, "account_health_rating_ahr_status", brand
        ),
        "food_safety_count": _safe_int(policy, "food_safety_count", brand),
        "ip_complaint_count": _safe_int(policy, "ip_complaint_count", brand),
        "account_status": status_data.get("account_status"),
    }

    # --- Classify ---
    findings, highest_severity = classify_account(metrics)

    return HealthReport(
        account_config_id=account.id,
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
