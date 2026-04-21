# suppression_classifier.py — classifies suppressed listing issue descriptions into actionable categories.
# Called by report_builder.py for each new suppression detected. Returns category, severity, and
# a suggested action for the ops team. Keyword matching is case-insensitive against issue_description.

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Severity constants matching the rest of the project
CRITICAL = "critical"
WARNING = "warning"

# #note: Ordered list of classification rules — first match wins.
# Each rule is (keywords_any_of, category, severity, suggested_action).
# Order matters: more specific / higher-severity rules come first.
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


# #note: Classifies a suppression issue_description string into a category, severity, and suggested action.
# Iterates the rule list in order — first keyword match wins.
# Returns a dict with keys: category, severity, suggested_action.
# Returns UNKNOWN category if no rule matches — never raises.
def classify_suppression(issue_description: Optional[str]) -> dict:
    if not issue_description:
        return {
            "category": "UNKNOWN",
            "severity": WARNING,
            "suggested_action": _UNKNOWN_ACTION,
        }

    text = issue_description.lower()

    for keywords, category, severity, action in _RULES:
        if any(kw in text for kw in keywords):
            logger.debug(f"Suppression classified as {category}: matched in '{text[:80]}'")
            return {
                "category": category,
                "severity": severity,
                "suggested_action": action,
            }

    logger.debug(f"Suppression unclassified (UNKNOWN): '{text[:80]}'")
    return {
        "category": "UNKNOWN",
        "severity": WARNING,
        "suggested_action": _UNKNOWN_ACTION,
    }
