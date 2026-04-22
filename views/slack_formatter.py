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


# #note: Builds the Teamwork task section text showing open and completed tasks.
# Returns None if both lists are empty. Shows up to 5 open tasks and 5 recent completions.
def _format_teamwork_section(
    open_tasks: list[dict], completed_tasks: list[dict]
) -> Optional[str]:
    if not open_tasks and not completed_tasks:
        return None
    lines = ["*Teamwork Activity:*"]
    if open_tasks:
        lines.append("  _Open / In Progress:_")
        for t in open_tasks[:5]:
            assignee = t.get("assignee") or "Unassigned"
            due = t.get("due_date") or ""
            due_str = f" — due: {due}" if due else ""
            lines.append(f"    🔲 {t.get('name', 'Unnamed task')} ({assignee}){due_str}")
    if completed_tasks:
        lines.append("  _Recently Completed:_")
        for t in completed_tasks[:5]:
            assignee = t.get("assignee") or "Unassigned"
            date_str = t.get("completed_on", "")
            lines.append(f"    ✅ {t.get('name', 'Unnamed task')} ({assignee}) — {date_str}")
    return "\n".join(lines)


# #note: Builds the one-line per-listing detail shown under each NEW suppression.
# Includes marketplace (country_code), enforcement action, reason bucket, and a ⏳ lag tag
# when the row may not reflect Amazon's current state.
def _format_new_suppression_lines(s: dict) -> list[str]:
    asin = s.get("asin", "Unknown ASIN")
    sku = s.get("sku", "")
    category = s.get("category", "UNKNOWN")
    action = s.get("suggested_action", "Review in Seller Central.")
    country = s.get("country_code") or "—"
    enforcement = s.get("enforcement_action") or "Search Suppressed"
    reason_bucket = s.get("reason_bucket") or "—"
    sku_str = f" | SKU: {sku}" if sku else ""
    lag_tag = "  ⏳ report lag possible" if s.get("lag_risk") else ""

    out = [
        f"  📬 *ASIN: {asin}*{sku_str}  `{country}`{lag_tag}",
        f"     Enforcement: {enforcement}",
        f"     Reason bucket: {reason_bucket}  |  Category: {category}",
        f"     Action: {action}",
    ]
    return out


# #note: Formats suppressed listings into a Slack mrkdwn block.
# New suppressions (not previously alerted) appear with urgent 🔴 NEW prefix + full detail.
# Previously alerted suppressions are summarized by count with a country breakdown line.
# A clarifying note explains the ⏳ lag tag and the "search suppressed" enforcement state.
# Returns None if there are no suppressions at all.
def _format_suppression_section(report: HealthReport) -> Optional[str]:
    if not report.suppressed_listings and not report.new_suppressions:
        return None

    lines: list[str] = []

    if report.new_suppressions:
        lines.append(f"*🔴 NEW: {len(report.new_suppressions)} suppressed listing(s) require action*")
        for s in report.new_suppressions[:5]:
            lines.extend(_format_new_suppression_lines(s))
        if len(report.new_suppressions) > 5:
            lines.append(f"  _(+{len(report.new_suppressions) - 5} more — see Drive report)_")

    already_alerted = [
        s for s in report.suppressed_listings
        if s not in report.new_suppressions
    ]
    if already_alerted:
        # Country breakdown for already-alerted so ops can see marketplace spread at a glance
        country_counts: dict[str, int] = {}
        for s in already_alerted:
            cc = s.get("country_code") or "—"
            country_counts[cc] = country_counts.get(cc, 0) + 1
        breakdown = ", ".join(f"{cc}: {n}" for cc, n in sorted(country_counts.items()))
        lines.append(
            f"📋 {len(already_alerted)} listing(s) suppressed (previously alerted — {breakdown}) — see Drive report"
        )

    # #note: Clarifying footer — explains the enforcement state and the ⏳ lag tag.
    # Keeps ops from confusing "Search Suppressed" with "unbuyable" and signals when a row
    # might no longer reflect Amazon's live state.
    if lines:
        lines.append(
            "_Note: `Search Suppressed` = hidden from Amazon search but the product detail "
            "page is still live and buyable via direct link. ⏳ flags rows where the suppression "
            "state may already have changed on Amazon's side (download 2+ days stale OR status "
            "changed today)._"
        )

    return "\n".join(lines) if lines else None


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

    # #note: Append suppression block when listings exist — new ones shown urgently, old ones as info
    suppression_text = _format_suppression_section(report)
    if suppression_text:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": suppression_text}})
        blocks.append({"type": "divider"})

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

    teamwork_text = _format_teamwork_section(report.teamwork_open_tasks, report.teamwork_completed_tasks)
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
