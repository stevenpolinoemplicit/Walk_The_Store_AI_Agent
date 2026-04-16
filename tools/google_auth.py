# google_auth.py — shared Google service account credential helper.
# Handles both local (file path) and Cloud Run (JSON string from Secret Manager) environments.
# When GOOGLE_IMPERSONATION_EMAIL is set, activates DWD so the service account acts on behalf
# of that Workspace user — required for emplicit.co Google Workspace domain access.
# Used by sheets_reader.py and report_generator.py — do not call from_service_account_file() directly.

import json
import logging
import os
from typing import List

from google.oauth2.service_account import Credentials

from config import settings

logger = logging.getLogger(__name__)


# #note: Returns Google service account credentials scoped to the requested APIs.
# Locally, GOOGLE_SERVICE_ACCOUNT_JSON is a file path — uses from_service_account_file().
# On Cloud Run, the env var contains the raw JSON string from Secret Manager — uses from_service_account_info().
# If GOOGLE_IMPERSONATION_EMAIL is set, activates Domain-Wide Delegation so the service account
# impersonates that Workspace user — necessary for Google Workspace-restricted APIs (Docs, Drive).
def get_service_account_credentials(scopes: List[str]) -> Credentials:
    value = settings.GOOGLE_SERVICE_ACCOUNT_JSON
    if os.path.exists(value):
        logger.debug("Google auth: loading credentials from file path")
        creds = Credentials.from_service_account_file(value, scopes=scopes)
    else:
        logger.debug("Google auth: loading credentials from JSON string (Cloud Run)")
        info = json.loads(value)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
    if settings.GOOGLE_IMPERSONATION_EMAIL:
        logger.debug(f"Google auth: activating DWD as {settings.GOOGLE_IMPERSONATION_EMAIL}")
        creds = creds.with_subject(settings.GOOGLE_IMPERSONATION_EMAIL)
    return creds
