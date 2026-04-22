# settings.py — loads all environment variables from .env and exposes them as typed constants.
# Any module that needs a config value imports it from here — never reads os.environ directly.

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# --- Anthropic ---
# #note: Anthropic API key for authenticating Claude SDK calls
# .strip() on all string secrets — PowerShell echo adds \r\n when secrets were originally stored via CLI
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"].strip()

# #note: Executor model (Sonnet) drives the full report narrative; advisor model (Opus) is consulted
# only when Sonnet escalates — used by the advisor strategy in tools/report_generator.py
ANTHROPIC_EXECUTOR_MODEL: str = "claude-sonnet-4-6"
ANTHROPIC_ADVISOR_MODEL: str = "claude-opus-4-6"

# --- Emplicit Postgres ---
# #note: Connection parameters for the Emplicit PostgreSQL database (used by psycopg2 and asyncpg)
EMPLICIT_PG_HOST: str = os.environ["EMPLICIT_PG_HOST"].strip()
EMPLICIT_PG_PORT: int = int(os.environ.get("EMPLICIT_PG_PORT", "5432").strip())
EMPLICIT_PG_DB: str = os.environ["EMPLICIT_PG_DB"].strip()
EMPLICIT_PG_USER: str = os.environ["EMPLICIT_PG_USER"].strip()
EMPLICIT_PG_PASSWORD: str = os.environ["EMPLICIT_PG_PASSWORD"].strip()

# --- Slack ---
# #note: Slack bot token and the ops channel ID for cross-brand daily summary posts
SLACK_BOT_TOKEN: str = os.environ["SLACK_BOT_TOKEN"].strip()
SLACK_OPS_CHANNEL: str = os.environ["SLACK_OPS_CHANNEL"].strip()

# --- Teamwork ---
# #note: Teamwork subdomain and API token for read-only task queries
TEAMWORK_DOMAIN: str = os.environ["TEAMWORK_DOMAIN"].strip()
TEAMWORK_API_TOKEN: str = os.environ["TEAMWORK_API_TOKEN"].strip()

# --- Google ---
# #note: Path to the Google service account JSON file — needs Drive + Docs + Sheets scopes
# CONFIRMED: value is a file path (e.g. "walk the store service account key.json") — from_service_account_file() is correct
GOOGLE_SERVICE_ACCOUNT_JSON: str = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"].strip()

# #note: Workspace user email the service account impersonates via DWD — required for Google Workspace domains
# .strip() removes trailing \r\n that PowerShell/Secret Manager sometimes appends when storing the value
GOOGLE_IMPERSONATION_EMAIL: str = os.environ.get("GOOGLE_IMPERSONATION_EMAIL", "").strip()

# --- Google Sheets ---
# #note: Sheet IDs for brand config and people lookup — used by sheets_reader.py at agent startup
# .strip() guards against trailing \r\n from PowerShell when secrets were originally stored
BRAND_SHEET_ID: str = os.environ["BRAND_SHEET_ID"].strip()
PEOPLE_SHEET_ID: str = os.environ["PEOPLE_SHEET_ID"].strip()

# --- Google Drive ---
# #note: Folder ID for the daily ops summary Google Doc — separate from per-brand report folders
DRIVE_OPS_FOLDER_ID: str = os.environ.get("DRIVE_OPS_FOLDER_ID", "").strip()

# --- Always-Notify Users ---
# #note: Slack user IDs that always receive the full ops summary DM (Steven + Adam + Emily + Jessie (U022DEVDUHZ))
NOTIFY_ALWAYS_IDS: list[str] = ["U0AJYBWU03X", "U5H5GLJLV", "UEKN0TY2D", "U022DEVDUHZ"]

# --- Weekend On-Call Coverage ---
# #note: On Saturday and Sunday, ops manager DMs are replaced by these on-call users:
#        Axel (U0339BL8PSN), Kay (U01J7UBBX3K), Milagros (U02GXHL9Q9M)
WEEKEND_ONCALL_IDS: list[str] = ["U0339BL8PSN", "U01J7UBBX3K", "U02GXHL9Q9M"]
