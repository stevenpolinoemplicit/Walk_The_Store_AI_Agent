# settings.py — loads all environment variables from .env and exposes them as typed constants.
# Any module that needs a config value imports it from here — never reads os.environ directly.

import os
import logging
from dotenv import load_dotenv

# Load .env file into the process environment at import time
load_dotenv()

logger = logging.getLogger(__name__)


# --- Anthropic ---
# #note: Anthropic API key for authenticating Claude SDK calls
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

# --- Intentwise MCP ---
# #note: OAuth credentials and MCP server URL for Intentwise Amazon data queries
INTENTWISE_CLIENT_ID: str = os.environ["INTENTWISE_CLIENT_ID"]
INTENTWISE_CLIENT_SECRET: str = os.environ["INTENTWISE_CLIENT_SECRET"]
INTENTWISE_MCP_URL: str = os.environ.get(
    "INTENTWISE_MCP_URL", "https://mcp.intentwise.com/mcp"
)

# --- Emplicit Postgres ---
# #note: Connection parameters for the Emplicit PostgreSQL database
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

# --- NotebookLM (TBD — stub until API access is confirmed) ---
# #note: NotebookLM Enterprise API key — optional until access is granted
NOTEBOOKLM_API_KEY: str = os.environ.get("NOTEBOOKLM_API_KEY", "")
