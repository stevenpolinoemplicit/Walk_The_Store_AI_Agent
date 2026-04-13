# report_generator.py — creates a Google Doc matching the Emplicit Amazon Account Health Report format.
# Replicates the layout from the example PDF (info/walk_the_store_example_output.pdf):
#   Header → Executive Summary → Key Findings → Key Metrics table → Detailed Findings → Footer
# Saves the doc to the brand's Drive folder defined in AccountConfig.drive_folder_id,
# sets sharing to Emplicit domain, and returns the shareable Drive URL.

import logging
from datetime import datetime
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import settings
from config.thresholds import CRITICAL, WARNING, HEALTHY, UNKNOWN
from models.account import AccountConfig
from models.report import HealthReport

logger = logging.getLogger(__name__)

# Both scopes required: Docs API to create/write the document, Drive API to move + share it
_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

_SEVERITY_LABEL = {
    CRITICAL: "🔴 CRITICAL",
    WARNING: "🟡 WARNING",
    HEALTHY: "🟢 HEALTHY",
    UNKNOWN: "⚪ UNKNOWN",
}

_SEVERITY_EMOJI = {
    CRITICAL: "🔴",
    WARNING: "🟡",
    HEALTHY: "🟢",
    UNKNOWN: "⚪",
}

# Metric check names grouped into report sections (matches Finding.check values from classifier.py)
_INVENTORY_CHECKS = {"stranded_inventory", "unfulfillable_inventory", "aged_inventory"}
_SHIPPING_CHECKS = {"late_shipment_rate", "valid_tracking_rate", "pre_cancel_rate"}
_ACCOUNT_CHECKS = {"account_health_rating", "account_status", "food_safety", "ip_complaints"}
_CUSTOMER_CHECKS = {"order_defect_rate"}


# #note: Loads service account credentials from the JSON file path defined in settings.py
def _get_credentials() -> service_account.Credentials:
    # april13 waiting on confirmation - is GOOGLE_SERVICE_ACCOUNT_JSON a file path (e.g. /secrets/sa.json)
    # or the raw JSON content as a string? Adjust from_service_account_file vs from_service_account_info.
    sa_json_path = settings.GOOGLE_SERVICE_ACCOUNT_JSON
    creds = service_account.Credentials.from_service_account_file(
        sa_json_path, scopes=_SCOPES
    )
    return creds


# #note: Counts findings at critical and warning level for the executive summary line
def _count_severities(report: HealthReport) -> tuple[int, int]:
    critical = sum(1 for f in report.findings if f.severity == CRITICAL)
    warning = sum(1 for f in report.findings if f.severity == WARNING)
    return critical, warning


# #note: Formats a float as a percentage string; returns "N/A" if None
def _fmt_pct(val: Optional[float]) -> str:
    return f"{val:.2%}" if val is not None else "N/A"


# #note: Formats any value as a string; returns "N/A" if None
def _fmt_val(val: object) -> str:
    return str(val) if val is not None else "N/A"


# #note: Looks up the severity for a given check name from the findings list
def _check_severity(report: HealthReport, check_name: str) -> str:
    for f in report.findings:
        if f.check == check_name:
            return f.severity
    return UNKNOWN


# #note: Builds the full plain-text body for the Google Doc, matching the example PDF layout exactly
def _build_doc_text(report: HealthReport, account: AccountConfig) -> str:
    critical_count, warning_count = _count_severities(report)
    severity_label = _SEVERITY_LABEL.get(report.highest_severity, "⚪ UNKNOWN")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        "EMPLICIT — Amazon Account Health Report",
        f"Account: {report.brand_name}          Report Date: {report.report_date}",
        "─" * 60,
        "",
        "Executive Summary",
        f"Overall Status: {severity_label}",
        f"🔴 {critical_count} Critical Issues   🟡 {warning_count} Warning(s)",
        "",
        "Key Findings",
    ]

    for finding in report.findings:
        if finding.severity in (CRITICAL, WARNING):
            emoji = _SEVERITY_EMOJI.get(finding.severity, "⚪")
            lines.append(f"  - {emoji} {finding.message}")

    lines += [
        "",
        "Key Metrics",
        f"  {'Metric':<35} {'Value':<20} Status",
        "  " + "-" * 65,
    ]

    # Metric rows — each maps to a field on HealthReport and a check name in findings
    metric_rows: list[tuple[str, str, str]] = [
        ("Late Shipment Rate", _fmt_pct(report.late_shipment_rate), "late_shipment_rate"),
        ("Valid Tracking Rate", _fmt_pct(report.valid_tracking_rate), "valid_tracking_rate"),
        ("Pre-fulfillment Cancel Rate", _fmt_pct(report.pre_cancel_rate), "pre_cancel_rate"),
        ("Order Defect Rate (ODR)", _fmt_pct(report.order_defect_rate), "order_defect_rate"),
        ("Account Health Rating", _fmt_val(report.account_health_rating), "account_health_rating"),
        ("Account Status", _fmt_val(report.account_status), "account_status"),
        ("Food/Product Safety", _fmt_val(report.food_safety_count), "food_safety"),
        ("IP Complaints", _fmt_val(report.ip_complaint_count), "ip_complaints"),
    ]

    for metric_name, metric_val, check_name in metric_rows:
        sev = _check_severity(report, check_name)
        status = _SEVERITY_LABEL.get(sev, "🟢 OK")
        lines.append(f"  {metric_name:<35} {metric_val:<20} {status}")

    lines += ["", "Detailed Findings"]

    # Group findings into sections by check name
    shipping_findings = [f for f in report.findings if f.check in _SHIPPING_CHECKS]
    account_findings = [f for f in report.findings if f.check in _ACCOUNT_CHECKS]
    customer_findings = [f for f in report.findings if f.check in _CUSTOMER_CHECKS]
    other_findings = [
        f for f in report.findings
        if f.check not in _SHIPPING_CHECKS | _ACCOUNT_CHECKS | _CUSTOMER_CHECKS
    ]

    sections = [
        ("Shipping Performance", shipping_findings),
        ("Account Health", account_findings),
        ("Customer Service", customer_findings),
    ]
    if other_findings:
        sections.append(("Other", other_findings))

    for section_name, section_findings in sections:
        if section_findings:
            lines.append(f"  {section_name}")
            for f in section_findings:
                emoji = _SEVERITY_EMOJI.get(f.severity, "⚪")
                lines.append(f"    - {emoji} {f.check.upper()}: {f.message}")

    if report.data_gaps:
        lines += ["", "  Data Gaps (check source tables)"]
        for gap in report.data_gaps:
            lines.append(f"    ⚠️ {gap}")

    lines += [
        "",
        "─" * 60,
        f"This report was automatically generated by Emplicit Walk the Store on {timestamp}.",
        "Data sourced from Amazon Seller Central via Intentwise.",
        "For questions, contact your Emplicit account manager.",
    ]

    return "\n".join(lines)


# #note: Main entry point — creates the Google Doc, moves to Drive folder, sets sharing, returns URL
def create_report(report: HealthReport, account: AccountConfig) -> str:
    creds = _get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    doc_title = f"{report.brand_name} — Amazon Health Report — {report.report_date}"
    doc_body = _build_doc_text(report, account)

    # Step 1: Create the document shell
    try:
        doc = docs_service.documents().create(body={"title": doc_title}).execute()
        doc_id: str = doc["documentId"]
        logger.info(f"[{report.brand_name}] Google Doc created: doc_id={doc_id}")
    except Exception as e:
        logger.error(f"[{report.brand_name}] Failed to create Google Doc: {e}")
        raise

    # Step 2: Insert the report text at index 1 (beginning of document body)
    try:
        requests = [{"insertText": {"location": {"index": 1}, "text": doc_body}}]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        logger.info(f"[{report.brand_name}] Google Doc content written")
    except Exception as e:
        logger.error(f"[{report.brand_name}] Failed to write Doc content: {e}")
        raise

    # Step 3: Move doc to the brand's Drive folder (if drive_folder_id is configured)
    # april13 waiting on confirmation - are drive_folder_ids populated in walk_the_store.account_config
    # for all active brands? If not, docs will land in the service account's root Drive.
    if account.drive_folder_id:
        try:
            file_meta = (
                drive_service.files().get(fileId=doc_id, fields="parents").execute()
            )
            current_parents = ",".join(file_meta.get("parents", []))
            drive_service.files().update(
                fileId=doc_id,
                addParents=account.drive_folder_id,
                removeParents=current_parents,
                fields="id, parents",
            ).execute()
            logger.info(
                f"[{report.brand_name}] Doc moved to Drive folder {account.drive_folder_id}"
            )
        except Exception as e:
            logger.warning(
                f"[{report.brand_name}] Could not move to Drive folder — doc accessible from root: {e}"
            )
    else:
        logger.warning(
            f"[{report.brand_name}] No drive_folder_id configured — doc saved to service account root"
        )

    # Step 4: Set sharing — anyone at the Emplicit domain can view with the link
    # CONFIRMED: Emplicit Google Workspace domain is emplicit.co
    try:
        drive_service.permissions().create(
            fileId=doc_id,
            body={
                "type": "domain",
                "role": "reader",
                "domain": "emplicit.co",
            },
        ).execute()
        logger.info(f"[{report.brand_name}] Drive sharing set to emplicit.co domain")
    except Exception as e:
        logger.warning(
            f"[{report.brand_name}] Could not set Drive sharing permission: {e}"
        )

    shareable_url = f"https://docs.google.com/document/d/{doc_id}"
    logger.info(f"[{report.brand_name}] Report ready: {shareable_url}")
    return shareable_url
