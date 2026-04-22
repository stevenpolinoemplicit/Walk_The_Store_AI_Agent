# suppression_classifier.py — classifies suppressed listing issue descriptions into actionable categories.
# Called by report_builder.py for each suppression. Returns category, severity, suggested action,
# enforcement_action, reason_bucket, and (when applicable) the parent_asin extracted from the
# issue text. Keyword matching is case-insensitive against issue_description.

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Severity constants matching the rest of the project
CRITICAL = "critical"
WARNING = "warning"

# #note: The only enforcement action represented in sellercentral_suppressedlistings_report is
# Amazon's "Search Suppressed" state — the detail page remains live and buyable via direct link.
# This label is attached to every classification so downstream readers don't confuse
# "suppressed" with "unbuyable".
ENFORCEMENT_ACTION = "Search Suppressed — detail page still buyable via direct link"

# #note: Regex to extract a parent ASIN from issue_description text.
# Matches phrases like "its parent ASIN B0CSKT2W9W" — ASINs are always 10 chars: B + 9 alphanumerics.
_PARENT_ASIN_RE = re.compile(r"parent\s+ASIN\s+(B[0-9A-Z]{9})", re.IGNORECASE)

# #note: Ordered list of classification rules — first match wins.
# Each rule is (keywords_any_of, category, severity, suggested_action).
# Order matters: more specific / higher-severity rules come first.
# PARENT_ASIN_ISSUE is handled separately (regex-based) before this list runs.
_RULES: list[tuple[list[str], str, str, str]] = [
    (
        ["policy violation", "policy compliance", "restricted", "prohibited"],
        "POLICY_VIOLATION",
        CRITICAL,
        "Review listing for policy compliance before submitting an appeal.",
    ),
    (
        ["not as described", "condition complaint", "condition issue", "product condition",
         "customer complaint", "buyer complaint"],
        "CONDITION_COMPLAINT",
        CRITICAL,
        "Investigate product quality. Provide inventory images with UPC and submit an appeal.",
    ),
    (
        ["authenticity", "counterfeit", "intellectual property", "trademark", "copyright"],
        "AUTHENTICITY",
        CRITICAL,
        "Provide proof of authenticity (invoices, LOA). Contact brand owner if needed.",
    ),
    (
        ["safety", "hazmat", "dangerous", "recall"],
        "SAFETY",
        CRITICAL,
        "Do not relist until safety concern is fully resolved. Contact Steven immediately.",
    ),
    (
        ["main image", "missing image", "image does not meet", "image requirement",
         "white background", "no image"],
        "MISSING_IMAGE",
        WARNING,
        "Submit a compliant main image: white background, product only, no text or watermarks.",
    ),
    (
        ["duplicate", "merged", "already exists"],
        "DUPLICATE",
        WARNING,
        "Merge or remove the duplicate listing via Seller Central.",
    ),
    (
        ["missing", "required attribute", "incomplete", "detail page", "bullet point",
         "description", "title"],
        "MISSING_INFO",
        WARNING,
        "Update the listing: add all missing required attributes on the detail page.",
    ),
]

_UNKNOWN_ACTION = "Review suppression reason in Seller Central and take appropriate action."


# #note: Classifies a suppression row into category, severity, suggested action, enforcement action,
# reason_bucket pass-through, and (if present) parent_asin.
# Parent-ASIN inheritance is detected first via regex — those rows don't need per-listing fixes,
# they're waiting on the parent ASIN to be fixed.
# If no rule matches, returns UNKNOWN category. Never raises.
def classify_suppression(
    issue_description: Optional[str],
    reason: Optional[str] = None,
) -> dict:
    base = {
        "enforcement_action": ENFORCEMENT_ACTION,
        "reason_bucket": reason,
        "parent_asin": None,
    }

    if not issue_description:
        return {
            **base,
            "category": "UNKNOWN",
            "severity": WARNING,
            "suggested_action": _UNKNOWN_ACTION,
        }

    # #note: Parent-ASIN inheritance takes priority — the child ASIN can't be fixed directly.
    parent_match = _PARENT_ASIN_RE.search(issue_description)
    if parent_match:
        parent_asin = parent_match.group(1).upper()
        logger.debug(f"Suppression classified as PARENT_ASIN_ISSUE (parent={parent_asin})")
        return {
            **base,
            "category": "PARENT_ASIN_ISSUE",
            "severity": WARNING,
            "suggested_action": (
                f"This ASIN is suppressed because its parent ASIN {parent_asin} has issues. "
                f"Fix the parent ASIN to lift the suppression on this one."
            ),
            "parent_asin": parent_asin,
        }

    text = issue_description.lower()

    for keywords, category, severity, action in _RULES:
        if any(kw in text for kw in keywords):
            logger.debug(f"Suppression classified as {category}: matched in '{text[:80]}'")
            return {
                **base,
                "category": category,
                "severity": severity,
                "suggested_action": action,
            }

    logger.debug(f"Suppression unclassified (UNKNOWN): '{text[:80]}'")
    return {
        **base,
        "category": "UNKNOWN",
        "severity": WARNING,
        "suggested_action": _UNKNOWN_ACTION,
    }
