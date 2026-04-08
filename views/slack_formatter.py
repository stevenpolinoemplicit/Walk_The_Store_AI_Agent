# slack_formatter.py — formats a HealthReport into Slack Block Kit message blocks.
# Returns (fallback_text, blocks) so the caller can pass both to the Slack API.
# Emojis and structure follow the severity level of the report.

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
    recent = tasks[:5]  # show up to 5 most recent
    lines = ["*Recent Teamwork completions:*"]
    for t in recent:
        date_str = t.get("completed_on", "")
        lines.append(f"  ✅ {t.get('name', 'Unnamed task')} — {date_str}")
    return "\n".join(lines)


# #note: Builds the full Slack Block Kit message for one brand report; returns (text, blocks) tuple
def format_brand_report(report: HealthReport) -> tuple[str, list]:
    emoji = _emoji(report.highest_severity)
    title = f"{emoji} *{report.brand_name}* — {report.report_date}"
    fallback_text = f"{emoji} {report.brand_name}: {report.highest_severity.upper()} ({report.report_date})"

    blocks = [
        # Header
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {report.brand_name} — {report.highest_severity.upper()}",
            },
        },
        {"type": "divider"},
        # Findings section
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Account Health Findings:*\n"
                + "\n".join(_format_finding(f) for f in report.findings),
            },
        },
    ]

    # Data gaps notice
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

    # Teamwork section
    teamwork_text = _format_teamwork_section(report.teamwork_completed_tasks)
    if teamwork_text:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": teamwork_text},
            }
        )

    # Brand context (NotebookLM) if available
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
