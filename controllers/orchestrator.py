# orchestrator.py — main agent loop.
# Gets all active accounts from Postgres, builds a report for each one,
# routes Slack alerts by severity, saves reports to Postgres, and posts a cross-brand ops summary.
# This is the file wired into main.py as the daily entry point.

import logging
from typing import List

from controllers.report_builder import build_brand_report, build_ops_summary
from models.account import AccountConfig
from models.report import HealthReport
from tools import postgres, slack_alerts
from views.slack_formatter import format_brand_report

logger = logging.getLogger(__name__)


# #note: Routes a single brand report to Slack — DMs AM on critical, posts to channel on critical/warning
def _route_alerts(report: HealthReport, account: AccountConfig) -> None:
    if report.highest_severity in ("critical", "warning"):
        try:
            text, blocks = format_brand_report(report)
            slack_alerts.post_to_channel(account.slack_channel_id, text, blocks)
            logger.info(
                f"[{report.brand_name}] Slack alert posted to channel {account.slack_channel_id}"
            )
        except Exception as e:
            logger.error(
                f"[{report.brand_name}] Failed to post channel alert: {e}"
            )

    if report.highest_severity == "critical":
        try:
            dm_text = (
                f"🔴 *CRITICAL* — {report.brand_name} has account health issues. "
                f"Please review today's report immediately."
            )
            slack_alerts.send_dm(account.account_manager_slack_id, dm_text)
        except Exception as e:
            logger.error(
                f"[{report.brand_name}] Failed to send DM to AM: {e}"
            )


# #note: Main agent run — called by main.py; processes every active account end-to-end
def run_agent() -> None:
    logger.info("Orchestrator starting")

    # --- Fetch active accounts ---
    try:
        accounts: List[AccountConfig] = postgres.get_active_accounts()
        logger.info(f"Found {len(accounts)} active accounts")
    except Exception as e:
        logger.error(f"Failed to fetch accounts — aborting run: {e}")
        return

    completed_reports: List[HealthReport] = []

    # --- Per-account loop ---
    for account in accounts:
        logger.info(f"Processing account: {account.brand_name}")
        try:
            report = build_brand_report(account)
        except Exception as e:
            logger.error(
                f"[{account.brand_name}] Report build failed — skipping: {e}"
            )
            continue

        # Route Slack alerts (failure here does not stop Postgres save)
        _route_alerts(report, account)

        # Save to Postgres (failure here does not crash the run)
        try:
            postgres.save_report(report)
        except Exception as e:
            logger.error(
                f"[{account.brand_name}] Postgres save failed — alert was still sent: {e}"
            )

        completed_reports.append(report)

    # --- Cross-brand ops summary ---
    if completed_reports:
        try:
            summary = build_ops_summary(completed_reports)
            slack_alerts.post_ops_summary(summary)
            logger.info("Ops summary posted to Slack")
        except Exception as e:
            logger.error(f"Failed to post ops summary: {e}")
    else:
        logger.warning("No reports completed — ops summary skipped")

    logger.info("Orchestrator run complete")
