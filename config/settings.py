# settings.py — loads all environment variables from .env and exposes them as typed constants.
# Any module that needs a config value imports it from here — never reads os.environ directly.

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# --- Anthropic ---
# #note: Anthropic API key for authenticating Claude SDK calls
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

# --- Emplicit Postgres ---
# #note: Connection parameters for the Emplicit PostgreSQL database (used by psycopg2 and asyncpg)
EMPLICIT_PG_HOST: str = os.environ["EMPLICIT_PG_HOST"]
EMPLICIT_PG_PORT: int = int(os.environ.get("EMPLICIT_PG_PORT", "5432"))
EMPLICIT_PG_DB: str = os.environ["EMPLICIT_PG_DB"]
EMPLICIT_PG_USER: str = os.environ["EMPLICIT_PG_USER"]
EMPLICIT_PG_PASSWORD: str = os.environ["EMPLICIT_PG_PASSWORD"]

# --- Slack ---
# #note: Slack bot token and the ops channel ID for cross-brand daily summary posts
SLACK_BOT_TOKEN: str = os.environ["SLACK_BOT_TOKEN"]
SLACK_OPS_CHANNEL: str = os.environ["SLACK_OPS_CHANNEL"]

# --- Teamwork ---
# #note: Teamwork subdomain and API token for read-only task queries
TEAMWORK_DOMAIN: str = os.environ["TEAMWORK_DOMAIN"]
TEAMWORK_API_TOKEN: str = os.environ["TEAMWORK_API_TOKEN"]

# --- Google ---
# #note: Path to the Google service account JSON file — needs Drive + Docs + Sheets scopes
# CONFIRMED: value is a file path (e.g. "walk the store service account key.json") — from_service_account_file() is correct
GOOGLE_SERVICE_ACCOUNT_JSON: str = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# #note: Workspace user email the service account impersonates via DWD — required for Google Workspace domains
GOOGLE_IMPERSONATION_EMAIL: str = os.environ.get("GOOGLE_IMPERSONATION_EMAIL", "")

# --- Google Sheets ---
# #note: Sheet IDs for brand config and people lookup — used by sheets_reader.py at agent startup
BRAND_SHEET_ID: str = os.environ["BRAND_SHEET_ID"]
PEOPLE_SHEET_ID: str = os.environ["PEOPLE_SHEET_ID"]

# --- Google Drive ---
# #note: Folder ID for the daily ops summary Google Doc — separate from per-brand report folders
DRIVE_OPS_FOLDER_ID: str = os.environ.get("DRIVE_OPS_FOLDER_ID", "")

# --- Always-Notify Users ---
# #note: Slack user IDs that always receive the full ops summary DM (Steven + Adam + Emily)
NOTIFY_ALWAYS_IDS: list[str] = ["U0AJYBWU03X", "U5H5GLJLV", "UEKN0TY2D"]

# --- Weekend On-Call Coverage ---
# #note: On Saturday and Sunday, ops manager DMs are replaced by these on-call users:
#        Axel (U0339BL8PSN), Kay (U01J7UBBX3K), Milagros (U02GXHL9Q9M), Albenis (U01JLUZ534Y)
WEEKEND_ONCALL_IDS: list[str] = ["U0339BL8PSN", "U01J7UBBX3K", "U02GXHL9Q9M", "U01JLUZ534Y"]
