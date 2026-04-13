# intentwise_mcp.py — DEPRECATED
# Direct Intentwise MCP integration has been removed.
# Data is now read directly from the Emplicit Postgres database after Intentwise syncs it there.
# Use tools/postgres.py — get_account_health_metrics() for all account health data.
# This file is preserved per project no-delete policy.

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# #note: Deprecated — returns None unconditionally. Use postgres.get_account_health_metrics() instead.
def get_access_token() -> Optional[str]:
    return None


# #note: Deprecated — returns None unconditionally. Use postgres.get_account_health_metrics() instead.
def get_seller_performance(seller_id: str, marketplace: str) -> Optional[dict]:
    return None


# #note: Deprecated — returns None unconditionally. Use postgres.get_account_health_metrics() instead.
def get_shipping_performance(seller_id: str, marketplace: str) -> Optional[dict]:
    return None


# #note: Deprecated — returns None unconditionally. Use postgres.get_account_health_metrics() instead.
def get_customer_service_performance(seller_id: str, marketplace: str) -> Optional[dict]:
    return None


# #note: Deprecated — returns None unconditionally. Use postgres.get_account_health_metrics() instead.
def get_policy_compliance(seller_id: str, marketplace: str) -> Optional[dict]:
    return None


# #note: Deprecated — returns None unconditionally. Use postgres.get_account_health_metrics() instead.
def get_account_status(seller_id: str, marketplace: str) -> Optional[dict]:
    return None
