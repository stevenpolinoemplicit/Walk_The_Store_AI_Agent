# sheets_reader.py — Loads active brand accounts from Google Sheets.
# Replaces postgres.get_active_accounts(). Reads the Brand Code Mapping Sheet for brand config
# and the People Lookup Sheet to find each brand's AM Slack ID.
# account_id is read directly from the iw_account_id column (column S) in the Brand Code Mapping Sheet.

import logging
from typing import List, Optional

import gspread

from config import settings
from models.account import AccountConfig
from tools.google_auth import get_service_account_credentials
from tools.slack_alerts import notify_error

logger = logging.getLogger(__name__)

# Scopes needed to read Google Sheets
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


# #note: Authenticates with Google using the shared credential helper — works locally (file path) and on Cloud Run (JSON string)
def _get_gspread_client() -> gspread.Client:
    creds = get_service_account_credentials(_SCOPES)
    return gspread.Client(auth=creds)


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
# as AccountConfig objects. Skips brands where iw_account_id is missing or invalid.
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

        # #note: iw_account_id (column S) is the numeric Intentwise account_id — read directly from sheet
        raw_account_id = row.get("iw_account_id", "")
        try:
            account_id = int(raw_account_id)
        except (ValueError, TypeError):
            logger.warning(
                f"[{brand_code}] iw_account_id '{raw_account_id}' is missing or invalid — skipping"
            )
            notify_error(
                source="sheets_reader / Brand Code Mapping Sheet",
                message=(
                    f"Brand `{brand_code}` was skipped — `iw_account_id` is missing or invalid in column S.\n"
                    f"Add the numeric Intentwise account_id for this brand to resume processing."
                ),
            )
            continue

        # #note: Strip tw_ prefix and _task_list suffix to get clean dept keys (e.g. "marketing")
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
        logger.info(f"Loaded account: {brand_code} (account_id={account_id})")

    logger.info(f"sheets_reader loaded {len(accounts)} active accounts")
    return accounts
