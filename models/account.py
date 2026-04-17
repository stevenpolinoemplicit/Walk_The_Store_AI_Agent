# account.py — Pydantic model for a single brand/account loaded from Google Sheets.
# Replaces the previous Postgres-backed AccountConfig. Fields map directly to the
# Brand Code Mapping Sheet columns, with ops manager Slack ID resolved from the People Lookup Sheet.

from typing import Optional
from pydantic import BaseModel

# #note: Shared Drive folder where all POC reports are saved — one folder for all brands
POC_DRIVE_FOLDER_ID = "1jsEyn48SYDGxhvAu2-VQve9LP22UNXdp"


# #note: Represents one active brand — loaded from Google Sheets at agent startup
class AccountConfig(BaseModel):
    brand_code: str                             # sheet: brand_code — unique identifier
    brand_name: str                             # sheet: brand_name — display name for reports
    mws_seller_id: str                          # sheet: seller_id — bare MWS string (e.g. A2M0WKTGB6GQB6)
    account_ids: dict[str, int] = {}            # sheet cols S/T/U: iw_account_id_us/ca/mx — country_code -> Intentwise account_id
    slack_channel_id: str                       # sheet: internal_brand_slack_id
    ops_slack_id: Optional[str] = None          # People Lookup sheet: slack_user_id for this brand's ops manager (col I: ops_brands)
    drive_folder_id: str = POC_DRIVE_FOLDER_ID  # shared POC Drive folder for all reports
    tw_task_lists: dict[str, Optional[str]] = {}  # all 12 tw_*_task_list IDs, keyed by dept name
    fbm: bool = False                            # sheet col V: FBM — brand fulfills its own orders (MFN)
    fba: bool = False                            # sheet col W: FBA — brand uses Amazon fulfillment (AFN)
