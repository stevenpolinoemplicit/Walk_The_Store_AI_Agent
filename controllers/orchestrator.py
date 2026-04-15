# orchestrator.py — main agent loop. Gets all active accounts from Postgres, then for each one: builds the report, creates the Google Doc, routes Slack alerts, 
# saves the report to Postgres. After all accounts: posts the ops summary. 
# If one account fails entirely, it skips it and continues with the rest. Drive failure doesn't block Slack. 
# Postgres save failure doesn't block Slack.
#--- 
# Gets all active accounts from Postgres, builds a report for each one,
# generates a Google Doc report saved to Drive, routes Slack alerts by severity,
# saves reports to Postgres, and posts a cross-brand ops summary.
# Called by main.py in one-shot mode or by pg_listener.py on Postgres NOTIFY.

import logging
from typing import List, Optional

from controllers.report_builder import build_brand_report, build_ops_summary
from config import settings
from models.account import AccountConfig
from models.report import HealthReport
from tools import postgres, slack_alerts
from tools import sheets_reader
from views.slack_formatter import format_notification

logger = logging.getLogger(__name__)


# #note: Routes a single brand report to Slack — posts notification with Drive link on critical/warning,
#        DMs the brand's ops manager directly on critical. Healthy accounts are silent.
def _route_alerts(
    report: HealthReport,
    account: AccountConfig,
    drive_url: Optional[str],
) -> None:
    if report.highest_severity in ("critical", "warning"):
        try:
            text, blocks = format_notification(report, drive_url)
            slack_alerts.post_to_channel(account.slack_channel_id, text, blocks, drive_url)
            logger.info(
                f"[{report.brand_name}] Slack alert posted to channel {account.slack_channel_id}"
            )
        except Exception as e:
            logger.error(f"[{report.brand_name}] Failed to post channel alert: {e}")

        # #note: DM always-notify users on every warning or critical brand alert
        for user_id in settings.NOTIFY_ALWAYS_IDS:
            try:
                text, blocks = format_notification(report, drive_url)
                slack_alerts.send_dm(user_id, text, blocks)
            except Exception as e:
                logger.error(f"[{report.brand_name}] Failed to DM always-notify user {user_id}: {e}")

    if report.highest_severity == "critical":
        try:
            text, blocks = format_notification(report, drive_url)
            slack_alerts.send_dm(account.ops_slack_id, text, blocks)
        except Exception as e:
            logger.error(f"[{report.brand_name}] Failed to send DM to ops manager: {e}")


# #note: Main agent run — called by main.py or pg_listener; processes every active account end-to-end
def run_agent() -> None:
    logger.info("Orchestrator starting")

    # --- Fetch active accounts from Google Sheets ---
    try:
        accounts: List[AccountConfig] = sheets_reader.get_active_accounts()
        logger.info(f"Found {len(accounts)} active accounts")
    except Exception as e:
        logger.error(f"Failed to fetch accounts — aborting run: {e}")
        return

    completed_reports: List[HealthReport] = []

    # --- Per-account loop ---
    for account in accounts:
        logger.info(f"Processing account: {account.brand_name}")

        # Build the health report from Postgres + Teamwork data
        try:
            report = build_brand_report(account)
        except Exception as e:
            logger.error(f"[{account.brand_name}] Report build failed — skipping: {e}")
            continue

        # Generate the Google Doc and save it to Drive
        drive_url: Optional[str] = None
        try:
            from tools.report_generator import create_report
            drive_url = create_report(report, account)
            logger.info(f"[{account.brand_name}] Drive report created: {drive_url}")
        except Exception as e:
            logger.error(
                f"[{account.brand_name}] Drive report generation failed — "
                f"Slack alert will still send without link: {e}"
            )

        # Route Slack alerts (failure here does not stop Postgres save)
        _route_alerts(report, account, drive_url)

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

        # #note: DM always-notify users the full ops summary after every run
        for user_id in settings.NOTIFY_ALWAYS_IDS:
            try:
                slack_alerts.send_dm(user_id, summary)
            except Exception as e:
                logger.error(f"Failed to DM ops summary to always-notify user {user_id}: {e}")
    else:
        logger.warning("No reports completed — ops summary skipped")

    logger.info("Orchestrator run complete")
