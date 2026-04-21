# report_generator.py — creates a Google Doc matching the Emplicit Amazon Account Health Report format.
# Replicates the layout from the example PDF (info/walk_the_store_example_output.pdf):
#   Header → Executive Summary → Key Findings → Key Metrics table → Detailed Findings → Footer
# Saves the doc to the brand's Drive folder defined in AccountConfig.drive_folder_id,
# sets sharing to Emplicit domain, and returns the shareable Drive URL.

import logging
from datetime import date, datetime
from typing import Optional

import anthropic
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


# #note: Finds an existing date-named subfolder inside parent_folder_id, or creates one if absent.
# Folder name format is MMDDYYYY. Returns the subfolder's Drive folder ID.
def _get_or_create_date_folder(drive_service, parent_folder_id: str, date_str: str) -> str:
    query = (
        f"'{parent_folder_id}' in parents "
        f"and name = '{date_str}' "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    try:
        results = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        existing = results.get("files", [])
        if existing:
            logger.info(f"Date folder '{date_str}' already exists in {parent_folder_id}: {existing[0]['id']}")
            return existing[0]["id"]
    except Exception as e:
        logger.warning(f"Could not search for date folder '{date_str}': {e}")

    try:
        folder_meta = {
            "name": date_str,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }
        folder = drive_service.files().create(
            body=folder_meta,
            fields="id",
            supportsAllDrives=True,
        ).execute()
        folder_id: str = folder["id"]
        logger.info(f"Date folder '{date_str}' created in {parent_folder_id}: {folder_id}")
        return folder_id
    except Exception as e:
        logger.error(f"Could not create date folder '{date_str}' in {parent_folder_id}: {e}")
        raise


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


# #note: Calls Sonnet (executor) with Opus as advisor to write the Executive Summary and Key Findings
# narrative prose. Sonnet handles routine reports; Opus is consulted (up to 3 times) when Sonnet
# escalates on complex or multi-issue situations. Returns None on any failure so the caller can fall
# back to the deterministic template — the report always ships even if the LLM call fails.
def _generate_narrative(report: HealthReport, account: AccountConfig) -> Optional[str]:
    _SYSTEM_PROMPT = (
        "You are an Amazon account health analyst writing internal reports for an e-commerce agency. "
        "You will be given structured metric data and severity findings for a client brand. "
        "Write two sections only:\n\n"
        "1. Executive Summary — 2-4 sentences. State the overall status, identify the most urgent issue, "
        "and explain what it means for the account in plain language. Do not list every finding — focus on the story.\n\n"
        "2. Key Findings — 1-2 sentences per critical or warning finding. Explain what each metric means, "
        "why it matters, and what the likely next step is. Do not invent numbers — use only the values provided.\n\n"
        "Be direct and concise. Write for an ops manager who reads dozens of these. "
        "Use the severity emoji (🔴 🟡 🟢) at the start of each Key Finding line."
    )

    alert_findings = [f for f in report.findings if f.severity in (CRITICAL, WARNING)]
    findings_text = "\n".join(
        f"  {f.severity.upper()} — {f.check}: {f.message}" for f in alert_findings
    ) or "  No critical or warning findings."

    user_message = (
        f"Brand: {report.brand_name}\n"
        f"Report Date: {report.report_date}\n"
        f"Overall Status: {report.highest_severity.upper()}\n\n"
        f"Metric Values:\n"
        f"  Late Shipment Rate: {_fmt_pct(report.late_shipment_rate)}\n"
        f"  Valid Tracking Rate: {_fmt_pct(report.valid_tracking_rate)}\n"
        f"  Pre-fulfillment Cancel Rate: {_fmt_pct(report.pre_cancel_rate)}\n"
        f"  Order Defect Rate (ODR): {_fmt_pct(report.order_defect_rate)}\n"
        f"  Account Health Rating: {_fmt_val(report.account_health_rating)}\n"
        f"  Account Status: {_fmt_val(report.account_status)}\n"
        f"  Food/Product Safety Count: {_fmt_val(report.food_safety_count)}\n"
        f"  IP Complaint Count: {_fmt_val(report.ip_complaint_count)}\n\n"
        f"Classified Findings (critical and warning only):\n{findings_text}\n"
    )

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=settings.ANTHROPIC_EXECUTOR_MODEL,
            max_tokens=1024,
            extra_headers={"anthropic-beta": "advisor-tool-2026-03-01"},
            tools=[
                {
                    "type": "advisor_20260301",
                    "name": "advisor",
                    "model": settings.ANTHROPIC_ADVISOR_MODEL,
                    "max_uses": 3,
                }
            ],
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        # Extract the text content block from the response
        narrative = "\n".join(
            block.text for block in response.content if hasattr(block, "text") and block.text is not None
        ).strip()
        logger.info(
            f"[{report.brand_name}] Narrative generated via advisor strategy "
            f"(executor_tokens={response.usage.input_tokens}, "
            f"output_tokens={response.usage.output_tokens})"
        )
        return narrative if narrative else None
    except Exception as e:
        logger.warning(
            f"[{report.brand_name}] _generate_narrative failed — falling back to template: {e}"
        )
        return None


# #note: Builds the full plain-text body for the Google Doc, matching the example PDF layout exactly
def _build_doc_text(report: HealthReport, account: AccountConfig) -> str:
    critical_count, warning_count = _count_severities(report)
    severity_label = _SEVERITY_LABEL.get(report.highest_severity, "⚪ UNKNOWN")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # Attempt LLM-generated narrative (Sonnet executor + Opus advisor); fall back to template on failure
    llm_narrative = _generate_narrative(report, account)

    lines: list[str] = [
        "EMPLICIT — Amazon Account Health Report",
        f"Account: {report.brand_name}          Report Date: {report.report_date}",
        "─" * 60,
        "",
    ]

    if llm_narrative:
        lines.append(llm_narrative)
        lines.append("")
    else:
        lines += [
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
        lines.append("")

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

    # #note: Suppressed Listings section — shows all current suppressions with new ones flagged.
    # New suppressions include classification category and suggested action for the ops team.
    if report.suppressed_listings or report.new_suppressions:
        lines += ["", "Suppressed Listings"]
        new_asins = {s.get("asin") for s in report.new_suppressions}
        for s in report.suppressed_listings:
            asin = s.get("asin", "Unknown")
            sku = s.get("sku", "")
            date_changed = s.get("status_change_date", "")
            issue = s.get("issue_description", "No description available.")
            prefix = "NEW — " if asin in new_asins else ""
            sku_str = f" | SKU: {sku}" if sku else ""
            lines.append(f"  {prefix}ASIN: {asin}{sku_str} | Status change: {date_changed}")
            lines.append(f"    Issue: {issue}")
            if asin in new_asins:
                action = next(
                    (ns.get("suggested_action", "") for ns in report.new_suppressions if ns.get("asin") == asin),
                    "",
                )
                category = next(
                    (ns.get("category", "") for ns in report.new_suppressions if ns.get("asin") == asin),
                    "",
                )
                if category:
                    lines.append(f"    Category: {category}")
                if action:
                    lines.append(f"    Suggested Action: {action}")

    lines += [
        "",
        "─" * 60,
        f"This report was automatically generated by Emplicit Walk the Store on {timestamp}.",
        "Data sourced directly from Emplicit's PostgreSQL database (synced via Intentwise).",
        "For questions or issues, contact Steven Polino on Slack.",
        "For feedback on this solution, please fill out this form: https://docs.google.com/forms/d/e/1FAIpQLSfUyEi82zHU5HEv4Xi0rhRPCVBiJbLSAAzDKrhQTrBsIXS-BA/viewform",
    ]

    return "\n".join(lines)


# #note: Main entry point — creates the Google Doc, moves to Drive folder, sets sharing, returns URL
def create_report(report: HealthReport, account: AccountConfig) -> str:
    creds = _get_credentials()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    date_str = report.report_date.strftime("%B %d %Y")
    doc_title = f"{report.brand_name} - {date_str} - Amazon Health Report"
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

    # Step 3: Move doc into a MMDDYYYY date subfolder inside the brand's Drive folder.
    # supportsAllDrives=True is required for Shared Drive (Google Workspace Shared Drive) folders.
    # Without it the Drive API ignores Shared Drive content and returns 404 on the folder.
    if account.drive_folder_id:
        try:
            target_folder_id = _get_or_create_date_folder(
                drive_service, account.drive_folder_id, date_str
            )
            file_meta = drive_service.files().get(
                fileId=doc_id,
                fields="parents",
                supportsAllDrives=True,
            ).execute()
            current_parents = ",".join(file_meta.get("parents", []))
            drive_service.files().update(
                fileId=doc_id,
                addParents=target_folder_id,
                removeParents=current_parents,
                fields="id, parents",
                supportsAllDrives=True,
            ).execute()
            logger.info(
                f"[{report.brand_name}] Doc moved to date folder {target_folder_id} "
                f"({date_str}) inside {account.drive_folder_id}"
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

    date_str = report_date.strftime("%B %d %Y")
    doc_title = f"Walk the Store - {date_str} - Daily Ops Summary"

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

    # Move to a MMDDYYYY date subfolder inside the ops Drive folder — supportsAllDrives=True required for Shared Drive folders
    try:
        ops_date_folder_id = _get_or_create_date_folder(
            drive_service, settings.DRIVE_OPS_FOLDER_ID, date_str
        )
        file_meta = drive_service.files().get(
            fileId=doc_id,
            fields="parents",
            supportsAllDrives=True,
        ).execute()
        current_parents = ",".join(file_meta.get("parents", []))
        drive_service.files().update(
            fileId=doc_id,
            addParents=ops_date_folder_id,
            removeParents=current_parents,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()
        logger.info(
            f"Ops summary doc moved to date folder {ops_date_folder_id} "
            f"({date_str}) inside {settings.DRIVE_OPS_FOLDER_ID}"
        )
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
