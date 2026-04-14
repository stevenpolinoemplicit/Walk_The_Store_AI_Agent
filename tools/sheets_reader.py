# sheets_reader.py — Loads active brand accounts from Google Sheets.
# Replaces postgres.get_active_accounts(). Reads the Brand Code Mapping Sheet for brand config
# and the People Lookup Sheet to find each brand's AM Slack ID. Resolves each MWS seller ID
# to the numeric Intentwise account_id via a one-time Postgres lookup at startup.

import logging
from typing import List, Optional

import gspread
from google.oauth2.service_account import Credentials

from config import settings
from models.account import AccountConfig
from tools.postgres import get_connection

logger = logging.getLogger(__name__)

# Scopes needed to read both Google Sheets and (if needed) Drive file metadata
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# All 12 Teamwork task list column names in the Brand Code Mapping Sheet
_TW_COLUMNS = [
    "tw_reconciliation_task_list",
    "tw_marketing_task_list",
    "tw_finance_task_list",
    "tw_inventory_task_list",
    "tw_content_task_list",
    "tw_customer_service_task_list",
    "tw_case_management_task_list",
    "tw_catalog_task_list",
    "tw_account_coordinator_task_list",
    "tw_business_development_task_list",
    "tw_account_manager_task_list",
    "tw_project_coordinator_task_list",
    "tw_inbox_task_list",
]

# GID of the correct tab in the People Lookup Sheet
_PEOPLE_SHEET_GID = 2056938022


# #note: Authenticates with Google using the service account file path from settings
def _get_gspread_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=_SCOPES
    )
    return gspread.Client(auth=creds)


# #note: Queries Postgres to resolve a bare MWS seller ID to the numeric Intentwise account_id.
# The DB stores seller IDs with a _com suffix (e.g. A2M0WKTGB6GQB6_com), so we append it here.
def _resolve_account_id(mws_seller_id: str) -> Optional[int]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT account_id
                    FROM amazon_source_data.sellercentral_account_status_changed_report
                    WHERE mws_seller_id = %s
                    LIMIT 1
                    """,
                    (f"{mws_seller_id}_com",),
                )
                row = cur.fetchone()
                return int(row[0]) if row else None
    except Exception as e:
        logger.warning(f"account_id lookup failed for {mws_seller_id}: {e}")
        return None


# #note: Reads the People Lookup Sheet and returns a dict mapping brand_code -> AM slack_user_id.
# Each AM row has an am_brands column with comma-separated brand codes they manage.
def _build_am_lookup(client: gspread.Client) -> dict[str, str]:
    am_map: dict[str, str] = {}
    try:
        sheet = client.open_by_key(settings.PEOPLE_SHEET_ID)
        worksheet = sheet.get_worksheet_by_id(_PEOPLE_SHEET_GID)
        records = worksheet.get_all_records()
        for row in records:
            am_brands_raw = str(row.get("am_brands", "")).strip()
            slack_id = str(row.get("slack_user_id", "")).strip()
            if not am_brands_raw or not slack_id:
                continue
            for brand_code in [b.strip() for b in am_brands_raw.split(",")]:
                if brand_code:
                    am_map[brand_code] = slack_id
    except Exception as e:
        logger.warning(f"Failed to load People Lookup sheet — AM DMs will be skipped: {e}")
    return am_map


# #note: Main entry point — reads the Brand Code Mapping Sheet and returns all active brands
# as AccountConfig objects. Skips brands where account_id cannot be resolved from Postgres.
def get_active_accounts() -> List[AccountConfig]:
    client = _get_gspread_client()
    am_lookup = _build_am_lookup(client)

    try:
        sheet = client.open_by_key(settings.BRAND_SHEET_ID)
        worksheet = sheet.sheet1
        records = worksheet.get_all_records()
    except Exception as e:
        logger.error(f"Failed to load Brand Code Mapping sheet: {e}")
        raise

    accounts: List[AccountConfig] = []
    for row in records:
        if not row.get("reconciliation_in_scope"):
            continue

        brand_code = str(row.get("brand_code", "")).strip()
        mws_seller_id = str(row.get("seller_id", "")).strip()

        if not brand_code or not mws_seller_id:
            logger.warning(f"Skipping row with missing brand_code or seller_id: {row}")
            continue

        account_id = _resolve_account_id(mws_seller_id)
        if account_id is None:
            logger.warning(
                f"[{brand_code}] Could not resolve account_id for {mws_seller_id} — skipping"
            )
            continue

        # #note: Strip tw_prefix and _task_list suffix to get clean dept keys (e.g. "marketing")
        tw_task_lists: dict[str, Optional[str]] = {
            col.replace("tw_", "").replace("_task_list", ""): str(row.get(col, "")).strip() or None
            for col in _TW_COLUMNS
        }

        accounts.append(
            AccountConfig(
                brand_code=brand_code,
                brand_name=str(row.get("brand_name", brand_code)).strip(),
                mws_seller_id=mws_seller_id,
                account_id=account_id,
                slack_channel_id=str(row.get("internal_brand_slack_id", "")).strip(),
                am_slack_id=am_lookup.get(brand_code),
                tw_task_lists=tw_task_lists,
            )
        )
        logger.info(
            f"Loaded account: {brand_code} ({mws_seller_id} → account_id={account_id})"
        )

    logger.info(f"sheets_reader loaded {len(accounts)} active accounts")
    return accounts
