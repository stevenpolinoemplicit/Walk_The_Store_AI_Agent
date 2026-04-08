# notebooklm.py — NotebookLM brand context client (STUB).
# Returns brand-specific context from the NotebookLM Enterprise API.
# API access is pending upgrade — this module is a stub until credentials are available.
# When the API is live: replace the stub body with real HTTP calls using NOTEBOOKLM_API_KEY.

import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


# #note: Returns brand context string from NotebookLM; returns None stub until API access is confirmed
def get_brand_context(brand_name: str) -> Optional[str]:
    if not settings.NOTEBOOKLM_API_KEY:
        logger.warning(
            f"NotebookLM API key not set — skipping brand context for {brand_name}"
        )
        return None

    # TODO: implement real NotebookLM Enterprise API call once access is granted
    # Expected: query the notebook associated with brand_name, return a context summary string
    logger.warning(
        f"NotebookLM integration not yet implemented — returning None for {brand_name}"
    )
    return None
