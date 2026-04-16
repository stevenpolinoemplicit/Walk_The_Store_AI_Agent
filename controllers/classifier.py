# classifier.py — severity classification logic.
# Takes raw metric values, compares them to thresholds from config/thresholds.py,
# and returns a list of Finding objects plus the rolled-up highest severity for the account.

import logging
from typing import Optional

from config.thresholds import (
    CRITICAL,
    WARNING,
    HEALTHY,
    UNKNOWN,
    LATE_SHIPMENT_CRITICAL,
    LATE_SHIPMENT_WARNING,
    VALID_TRACKING_CRITICAL,
    VALID_TRACKING_WARNING,
    PRE_CANCEL_CRITICAL,
    PRE_CANCEL_WARNING,
    ODR_CRITICAL,
    ODR_WARNING,
    AHR_CRITICAL_STATUSES,
    AHR_WARNING_STATUSES,
    CRITICAL_ACCOUNT_STATUSES,
)
from models.findings import Finding

logger = logging.getLogger(__name__)

# Severity rank used to roll up the worst finding — higher number = worse
_SEVERITY_RANK = {HEALTHY: 0, UNKNOWN: 1, WARNING: 2, CRITICAL: 3}


# #note: Returns the worst severity string from a list of Finding objects
def _roll_up_severity(findings: list[Finding]) -> str:
    if not findings:
        return HEALTHY
    return max(findings, key=lambda f: _SEVERITY_RANK.get(f.severity, 0)).severity


# #note: Classifies late shipment rate — critical >= 4%, warning 2–4%, healthy < 2%
def classify_late_shipment_rate(value: Optional[float]) -> Finding:
    if value is None:
        return Finding(
            check="late_shipment_rate",
            severity=UNKNOWN,
            message="Late shipment rate: data not available",
        )
    if value >= LATE_SHIPMENT_CRITICAL:
        sev = CRITICAL
    elif value >= LATE_SHIPMENT_WARNING:
        sev = WARNING
    else:
        sev = HEALTHY
    return Finding(
        check="late_shipment_rate",
        metric_value=value,
        severity=sev,
        message=f"Late shipment rate: {value:.2f}%",
    )


# #note: Classifies valid tracking rate — critical < 95%, warning 95–98%, healthy > 98%
def classify_valid_tracking_rate(value: Optional[float]) -> Finding:
    if value is None:
        return Finding(
            check="valid_tracking_rate",
            severity=UNKNOWN,
            message="Valid tracking rate: data not available",
        )
    if value < VALID_TRACKING_CRITICAL:
        sev = CRITICAL
    elif value < VALID_TRACKING_WARNING:
        sev = WARNING
    else:
        sev = HEALTHY
    return Finding(
        check="valid_tracking_rate",
        metric_value=value,
        severity=sev,
        message=f"Valid tracking rate: {value:.2f}%",
    )


# #note: Classifies pre-fulfillment cancel rate — critical >= 2.5%, warning 1–2.5%, healthy < 1%
def classify_pre_cancel_rate(value: Optional[float]) -> Finding:
    if value is None:
        return Finding(
            check="pre_cancel_rate",
            severity=UNKNOWN,
            message="Pre-fulfillment cancel rate: data not available",
        )
    if value >= PRE_CANCEL_CRITICAL:
        sev = CRITICAL
    elif value >= PRE_CANCEL_WARNING:
        sev = WARNING
    else:
        sev = HEALTHY
    return Finding(
        check="pre_cancel_rate",
        metric_value=value,
        severity=sev,
        message=f"Pre-fulfillment cancel rate: {value:.2f}%",
    )


# #note: Classifies order defect rate — critical >= 1%, warning 0.5–1%, healthy < 0.5%
def classify_order_defect_rate(value: Optional[float]) -> Finding:
    if value is None:
        return Finding(
            check="order_defect_rate",
            severity=UNKNOWN,
            message="Order defect rate: data not available",
        )
    if value >= ODR_CRITICAL:
        sev = CRITICAL
    elif value >= ODR_WARNING:
        sev = WARNING
    else:
        sev = HEALTHY
    return Finding(
        check="order_defect_rate",
        metric_value=value,
        severity=sev,
        message=f"Order defect rate (ODR): {value:.2f}%",
    )


# #note: Classifies account health rating — Amazon returns a string status ('Great', 'Good', 'Fair', 'At Risk', 'Critical')
def classify_account_health_rating(value: Optional[str]) -> Finding:
    if value is None:
        return Finding(
            check="account_health_rating",
            severity=UNKNOWN,
            message="Account health rating: data not available",
        )
    if value in AHR_CRITICAL_STATUSES:
        sev = CRITICAL
    elif value in AHR_WARNING_STATUSES:
        sev = WARNING
    else:
        sev = HEALTHY
    return Finding(
        check="account_health_rating",
        severity=sev,
        message=f"Account health rating (AHR): {value}",
    )


# #note: Classifies food/product safety violation count — any count > 0 is critical
def classify_food_safety(count: Optional[int]) -> Finding:
    if count is None:
        return Finding(
            check="food_safety",
            severity=UNKNOWN,
            message="Food/product safety: data not available",
        )
    sev = CRITICAL if count > 0 else HEALTHY
    return Finding(
        check="food_safety",
        metric_value=float(count),
        severity=sev,
        message=f"Food/product safety violations: {count}",
    )


# #note: Classifies IP complaint count — any count > 0 is critical
def classify_ip_complaints(count: Optional[int]) -> Finding:
    if count is None:
        return Finding(
            check="ip_complaints",
            severity=UNKNOWN,
            message="IP complaints: data not available",
        )
    sev = CRITICAL if count > 0 else HEALTHY
    return Finding(
        check="ip_complaints",
        metric_value=float(count),
        severity=sev,
        message=f"IP complaints: {count}",
    )


# #note: Classifies account status string — AT_RISK/SUSPENDED/DEACTIVATED = critical, else healthy
def classify_account_status(status: Optional[str]) -> Finding:
    if status is None:
        return Finding(
            check="account_status",
            severity=UNKNOWN,
            message="Account status: data not available",
        )
    sev = CRITICAL if status.upper() in CRITICAL_ACCOUNT_STATUSES else HEALTHY
    return Finding(
        check="account_status",
        severity=sev,
        message=f"Account status: {status}",
    )


# #note: Runs all classifiers against a dict of raw metric values and returns (findings, highest_severity).
# check_shipping=False suppresses LSR, VTR, and pre-cancel for FBA-only brands (Amazon handles their shipping).
# check_vtr=False suppresses VTR alone for brands that do FBA but not FBM.
def classify_account(metrics: dict, check_shipping: bool = True, check_vtr: bool = True) -> tuple[list[Finding], str]:
    if check_shipping:
        lsr_finding = classify_late_shipment_rate(metrics.get("late_shipment_rate"))
        vtr_finding = classify_valid_tracking_rate(metrics.get("valid_tracking_rate")) if check_vtr else Finding(
            check="valid_tracking_rate",
            severity=HEALTHY,
            message="Valid tracking rate: not monitored for this brand",
        )
        pcr_finding = classify_pre_cancel_rate(metrics.get("pre_cancel_rate"))
    else:
        lsr_finding = Finding(check="late_shipment_rate", severity=HEALTHY, message="Late shipment rate: not monitored for this brand")
        vtr_finding = Finding(check="valid_tracking_rate", severity=HEALTHY, message="Valid tracking rate: not monitored for this brand")
        pcr_finding = Finding(check="pre_cancel_rate", severity=HEALTHY, message="Pre-fulfillment cancel rate: not monitored for this brand")

    findings = [
        lsr_finding,
        vtr_finding,
        pcr_finding,
        classify_order_defect_rate(metrics.get("order_defect_rate")),
        classify_account_health_rating(metrics.get("account_health_rating")),
        classify_food_safety(metrics.get("food_safety_count")),
        classify_ip_complaints(metrics.get("ip_complaint_count")),
        classify_account_status(metrics.get("account_status")),
    ]
    highest = _roll_up_severity(findings)
    logger.info(f"Classification complete — highest severity: {highest}")
    return findings, highest
