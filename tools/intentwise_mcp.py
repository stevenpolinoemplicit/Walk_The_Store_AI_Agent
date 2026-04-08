# intentwise_mcp.py — Intentwise MCP client.
# Handles OAuth client_credentials token exchange, then queries the MCP server for Amazon account health data.
# All credentials come from config/settings.py. Blocked until Intentwise delivers OAuth client ID + secret.

import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# OAuth token endpoint — standard Intentwise auth server (confirm exact URL with Intentwise)
INTENTWISE_TOKEN_URL = "https://auth.intentwise.com/oauth/token"

# In-memory token cache (replaced each run; no persistent storage needed for daily agent)
_access_token: Optional[str] = None


# #note: Exchanges client_id + client_secret for a bearer token via OAuth client_credentials grant
def get_access_token() -> str:
    global _access_token
    if _access_token:
        return _access_token
    try:
        response = httpx.post(
            INTENTWISE_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.INTENTWISE_CLIENT_ID,
                "client_secret": settings.INTENTWISE_CLIENT_SECRET,
            },
            timeout=30,
        )
        response.raise_for_status()
        _access_token = response.json()["access_token"]
        logger.info("Intentwise OAuth token acquired")
        return _access_token
    except httpx.HTTPError as e:
        logger.error(f"Intentwise OAuth token exchange failed: {e}")
        raise


# #note: Sends a single JSON-RPC call to the Intentwise MCP server and returns the result payload
def _mcp_call(method: str, params: dict) -> Any:
    token = get_access_token()
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    try:
        response = httpx.post(
            settings.INTENTWISE_MCP_URL,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise RuntimeError(f"MCP error: {result['error']}")
        return result.get("result")
    except httpx.HTTPError as e:
        logger.error(f"Intentwise MCP call failed ({method}): {e}")
        raise


# #note: Queries seller performance metrics for a given seller_id and marketplace
def get_seller_performance(seller_id: str, marketplace: str) -> dict:
    try:
        return _mcp_call(
            "tools/call",
            {
                "name": "query_table",
                "arguments": {
                    "table": "sellercentral_sellerperformance_report",
                    "seller_id": seller_id,
                    "marketplace": marketplace,
                },
            },
        )
    except Exception as e:
        logger.error(f"get_seller_performance failed for {seller_id}: {e}")
        raise


# #note: Queries shipping performance metrics (late shipment rate, valid tracking rate, cancel rate)
def get_shipping_performance(seller_id: str, marketplace: str) -> dict:
    try:
        return _mcp_call(
            "tools/call",
            {
                "name": "query_table",
                "arguments": {
                    "table": "sellercentral_sellerperformance_shippingperformance_report",
                    "seller_id": seller_id,
                    "marketplace": marketplace,
                },
            },
        )
    except Exception as e:
        logger.error(f"get_shipping_performance failed for {seller_id}: {e}")
        raise


# #note: Queries customer service performance metrics including ODR and A-to-Z claims
def get_customer_service_performance(seller_id: str, marketplace: str) -> dict:
    try:
        return _mcp_call(
            "tools/call",
            {
                "name": "query_table",
                "arguments": {
                    "table": "sellercentral_sellerperformance_customerserviceperformance_report",
                    "seller_id": seller_id,
                    "marketplace": marketplace,
                },
            },
        )
    except Exception as e:
        logger.error(f"get_customer_service_performance failed for {seller_id}: {e}")
        raise


# #note: Queries policy compliance metrics — food safety violations and IP complaints
def get_policy_compliance(seller_id: str, marketplace: str) -> dict:
    try:
        return _mcp_call(
            "tools/call",
            {
                "name": "query_table",
                "arguments": {
                    "table": "sellercentral_sellerperformance_policycompliance_report",
                    "seller_id": seller_id,
                    "marketplace": marketplace,
                },
            },
        )
    except Exception as e:
        logger.error(f"get_policy_compliance failed for {seller_id}: {e}")
        raise


# #note: Queries account status change alerts to detect AT_RISK or SUSPENDED states
def get_account_status(seller_id: str, marketplace: str) -> dict:
    try:
        return _mcp_call(
            "tools/call",
            {
                "name": "query_table",
                "arguments": {
                    "table": "sellercentral_account_status_changed_report",
                    "seller_id": seller_id,
                    "marketplace": marketplace,
                },
            },
        )
    except Exception as e:
        logger.error(f"get_account_status failed for {seller_id}: {e}")
        raise
