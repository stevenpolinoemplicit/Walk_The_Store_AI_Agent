# slack_formatter.py — formats HealthReport objects into Slack Block Kit messages.
# format_brand_report: full detailed report (legacy, kept for backward compat)
# format_notification: brief summary with Drive link — used by the POC notification flow

import logging
from typing import Optional

from config.thresholds import CRITICAL, WARNING, HEALTHY, UNKNOWN
from models.report import HealthReport

logger = logging.getLogger(__name__)

# #note: Maps severity string to the matching emoji for Slack display
_SEVERITY_EMOJI = {
    CRITICAL: "🔴",
    WARNING: "🟡",
    HEALTHY: "🟢",
    UNKNOWN: "⚪",
}


# #note: Returns a single emoji string for the given severity level
def _emoji(severity: str) -> str:
    return _SEVERITY_EMOJI.get(severity, "⚪")


# #note: Formats a single Finding line as a Slack mrkdwn string
def _format_finding(finding) -> str:
    return f"{_emoji(finding.severity)} {finding.message}"


# #note: Builds the Teamwork task section text; returns None if no completed tasks to show
def _format_teamwork_section(tasks: list[dict]) -> Optional[str]:
    if not tasks:
        return None
    recent = tasks[:5]
    lines = ["*Recent Teamwork completions:*"]
    for t in recent:
        date_str = t.get("completed_on", "")
        lines.append(f"  ✅ {t.get('name', 'Unnamed task')} — {date_str}")
    return "\n".join(lines)


# #note: Builds a brief Slack Block Kit notification for one brand — summary + Drive link.
#        Used by the POC flow: orchestrator calls this after creating the Drive report.
#        Returns (fallback_text, blocks) — healthy accounts return (None, None) to suppress posting.
def format_notification(
    report: HealthReport, drive_url: Optional[str]
) -> tuple[Optional[str], Optional[list]]:
    if report.highest_severity == HEALTHY:
        return None, None

    emoji = _emoji(report.highest_severity)
    severity_upper = report.highest_severity.upper()
    fallback_text = f"{emoji} {report.brand_name} — {severity_upper} | {report.report_date}"

    # Count critical and warning findings for the summary line
    critical_count = sum(1 for f in report.findings if f.severity == CRITICAL)
    warning_count = sum(1 for f in report.findings if f.severity == WARNING)
    counts_text = f"{critical_count} critical · {warning_count} warning"

    # Show top findings (critical first, then warning)
    top_findings = [f for f in report.findings if f.severity in (CRITICAL, WARNING)][:4]
    findings_text = "\n".join(f"• {_format_finding(f)}" for f in top_findings)

    # Build the Drive link line — gracefully handles None if Drive failed
    if drive_url:
        link_text = f"📄 <{drive_url}|View Full Report>"
    else:
        link_text = "_(Drive report unavailable — check logs)_"

    body_text = f"{counts_text}\n{findings_text}\n{link_text}"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {report.brand_name} — {severity_upper}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": body_text},
        },
        {"type": "divider"},
    ]

    return fallback_text, blocks


# #note: Builds the full detailed Slack Block Kit message for one brand report; returns (text, blocks) tuple.
#        Kept for backward compatibility and manual review use cases.
def format_brand_report(report: HealthReport) -> tuple[str, list]:
    emoji = _emoji(report.highest_severity)
    fallback_text = (
        f"{emoji} {report.brand_name}: {report.highest_severity.upper()} ({report.report_date})"
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {report.brand_name} — {report.highest_severity.upper()}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Account Health Findings:*\n"
                + "\n".join(_format_finding(f) for f in report.findings),
            },
        },
    ]

    if report.data_gaps:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *Data gaps (check sources):* {', '.join(report.data_gaps)}",
                },
            }
        )

    teamwork_text = _format_teamwork_section(report.teamwork_completed_tasks)
    if teamwork_text:
        blocks.append({"type": "divider"})
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": teamwork_text}}
        )

    if report.brand_context:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Brand Context:*\n{report.brand_context}",
                },
            }
        )

    blocks.append({"type": "divider"})
    return fallback_text, blocks
