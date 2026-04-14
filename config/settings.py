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

# --- Google Sheets ---
# #note: Sheet IDs for brand config and people lookup — used by sheets_reader.py at agent startup
BRAND_SHEET_ID: str = os.environ["BRAND_SHEET_ID"]
PEOPLE_SHEET_ID: str = os.environ["PEOPLE_SHEET_ID"]
