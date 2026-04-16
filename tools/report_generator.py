# report_generator.py — creates a Google Doc matching the Emplicit Amazon Account Health Report format.
# Replicates the layout from the example PDF (info/walk_the_store_example_output.pdf):
#   Header → Executive Summary → Key Findings → Key Metrics table → Detailed Findings → Footer
# Saves the doc to the brand's Drive folder defined in AccountConfig.drive_folder_id,
# sets sharing to Emplicit domain, and returns the shareable Drive URL.

import logging
from datetime import date, datetime
from typing import Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings
from config.thresholds import CRITICAL, WARNING, HEALTHY, UNKNOWN
from tools.google_auth import get_service_account_credentials
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


# #note: Loads service account credentials via shared helper — works locally (file path) and on Cloud Run (JSON string)
def _get_credentials() -> Credentials:
    return get_service_account_credentials(_SCOPES)


# #note: Counts findings at critical and warning level for the executive summary line
def _count_severities(report: HealthReport) -> tuple[int, int]:
    critical = sum(1 for f in report.findings if f.severity == CRITICAL)
    warning = sum(1 for f in report.findings if f.severity == WARNING)
    return critical, warning


# #note: Formats a float as a percentage string; returns "N/A" if None
def _fmt_pct(val: Optional[float]) -> str:
    return f"{val:.2f}%" if val is not None else "N/A"


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

    # Teamwork Activity section — open tasks and recent completions
    has_open = bool(report.teamwork_open_tasks)
    has_completed = bool(report.teamwork_completed_tasks)
    if has_open or has_completed:
        lines += ["", "Teamwork Activity"]
        if has_open:
            lines.append("  Open / In Progress")
            for t in report.teamwork_open_tasks[:10]:
                assignee = t.get("assignee") or "Unassigned"
                due = t.get("due_date") or ""
                due_str = f" — due: {due}" if due else ""
                lines.append(f"    - {t.get('name', 'Unnamed task')} ({assignee}){due_str}")
        if has_completed:
            lines.append("  Recently Completed")
            for t in report.teamwork_completed_tasks[:5]:
                assignee = t.get("assignee") or "Unassigned"
                completed_on = t.get("completed_on", "")
                lines.append(f"    - ✅ {t.get('name', 'Unnamed task')} ({assignee}) — {completed_on}")

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
    except HttpError as e:
        logger.error(
            f"[{report.brand_name}] Failed to create Google Doc — "
            f"HTTP {e.status_code} {e.reason}: {e.error_details}"
        )
        raise
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
    except HttpError as e:
        logger.error(
            f"[{report.brand_name}] Failed to write Doc content — "
            f"HTTP {e.status_code} {e.reason}: {e.error_details}"
        )
        raise
    except Exception as e:
        logger.error(f"[{report.brand_name}] Failed to write Doc content: {e}")
        raise

    # Step 3: Move doc to the brand's Drive folder (if drive_folder_id is configured)
    # supportsAllDrives=True is required for Shared Drive (Google Workspace Shared Drive) folders.
    # Without it the Drive API ignores Shared Drive content and returns 404 on the folder.
    if account.drive_folder_id:
        try:
            file_meta = drive_service.files().get(
                fileId=doc_id,
                fields="parents",
                supportsAllDrives=True,
            ).execute()
            current_parents = ",".join(file_meta.get("parents", []))
            drive_service.files().update(
                fileId=doc_id,
                addParents=account.drive_folder_id,
                removeParents=current_parents,
                fields="id, parents",
                supportsAllDrives=True,
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
            supportsAllDrives=True,
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


# #note: Creates a Google Doc for the daily cross-brand ops summary and saves it to DRIVE_OPS_FOLDER_ID.
# Returns a shareable URL. Skipped if DRIVE_OPS_FOLDER_ID is not configured.
def create_ops_summary_doc(summary_text: str, report_date: date) -> str:
    if not settings.DRIVE_OPS_FOLDER_ID:
        raise ValueError("DRIVE_OPS_FOLDER_ID is not configured — cannot create ops summary doc")

    creds = _get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    doc_title = f"Walk the Store — Daily Ops Summary — {report_date}"

    try:
        doc = docs_service.documents().create(body={"title": doc_title}).execute()
        doc_id: str = doc["documentId"]
        logger.info(f"Ops summary doc created: doc_id={doc_id}")
    except HttpError as e:
        logger.error(
            f"Failed to create ops summary doc — HTTP {e.status_code} {e.reason}: {e.error_details}"
        )
        raise
    except Exception as e:
        logger.error(f"Failed to create ops summary doc: {e}")
        raise

    try:
        requests = [{"insertText": {"location": {"index": 1}, "text": summary_text}}]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        logger.info("Ops summary doc content written")
    except HttpError as e:
        logger.error(
            f"Failed to write ops summary doc content — HTTP {e.status_code} {e.reason}: {e.error_details}"
        )
        raise
    except Exception as e:
        logger.error(f"Failed to write ops summary doc content: {e}")
        raise

    # Move to ops summary Drive folder — supportsAllDrives=True required for Shared Drive folders
    try:
        file_meta = drive_service.files().get(
            fileId=doc_id,
            fields="parents",
            supportsAllDrives=True,
        ).execute()
        current_parents = ",".join(file_meta.get("parents", []))
        drive_service.files().update(
            fileId=doc_id,
            addParents=settings.DRIVE_OPS_FOLDER_ID,
            removeParents=current_parents,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()
        logger.info(f"Ops summary doc moved to Drive folder {settings.DRIVE_OPS_FOLDER_ID}")
    except Exception as e:
        logger.warning(f"Could not move ops summary doc to Drive folder — accessible from root: {e}")

    # Set domain sharing
    try:
        drive_service.permissions().create(
            fileId=doc_id,
            supportsAllDrives=True,
            body={"type": "domain", "role": "reader", "domain": "emplicit.co"},
        ).execute()
        logger.info("Ops summary doc sharing set to emplicit.co domain")
    except Exception as e:
        logger.warning(f"Could not set ops summary doc sharing permission: {e}")

    shareable_url = f"https://docs.google.com/document/d/{doc_id}"
    logger.info(f"Ops summary doc ready: {shareable_url}")
    return shareable_url
