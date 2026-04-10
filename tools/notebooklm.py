# notebooklm.py — Brand context tool.
# Brand memory / agentic context is NOT in scope for v1.
# This file is preserved per project deletion policy.
# To implement brand context in a future version, replace the body of get_brand_context().

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# #note: Returns None unconditionally — brand context is deferred to a future version
def get_brand_context(brand_name: str) -> Optional[str]:
    logger.debug(f"Brand context not implemented in v1 — returning None for {brand_name}")
    return None
