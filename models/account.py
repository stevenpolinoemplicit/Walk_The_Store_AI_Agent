# account.py — Pydantic model for a single brand/account row from walk_the_store.account_config.
# Used by postgres.py to deserialize DB rows, and by the orchestrator to iterate active accounts.

from typing import Optional
from pydantic import BaseModel


# #note: Mirrors the walk_the_store.account_config table schema; one instance per active brand
class AccountConfig(BaseModel):
    id: int
    brand_name: str
    seller_id: str
    marketplace: str
    slack_channel_id: str
    teamwork_project_id: str
    account_manager_slack_id: str
    drive_folder_id: Optional[str] = None
    is_active: bool = True
