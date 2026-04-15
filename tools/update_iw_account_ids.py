# update_iw_account_ids.py — One-off utility to populate iw_account_id (col S) and us_ca (col T)
# in the Brand Code Mapping Sheet using a pgAdmin export of account_id / account_name from Intentwise.
# Matches on brand_name (col O) case-insensitively after stripping " Seller US/CA/etc" suffixes.
# Run directly: python tools/update_iw_account_ids.py

import csv
import logging
import re
import sys
from pathlib import Path
from typing import Optional

# #note: Adds the project root to sys.path so config/tools imports work when run as a standalone script
sys.path.insert(0, str(Path(__file__).parent.parent))

import gspread

from config import settings
from tools.google_auth import get_service_account_credentials

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Read + write scope required to update the sheet
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Path to the pgAdmin export file
_DATA_FILE = Path(__file__).parent.parent / "info" / "account_id_and_account_name"

# Pattern to detect and extract marketplace suffix from account_name
_SUFFIX_RE = re.compile(
    r"\s+Seller\s+(US|CA|AU|UK|DE|FR|IT|ES|MX|JP)\s*$", re.IGNORECASE
)


# #note: Reads the pgAdmin export file and returns a cleaned lookup dict.
# Key is lowercased brand name with marketplace suffix stripped.
# Value is (account_id, marketplace). If a brand has both US and CA entries,
# US is preferred and a warning is logged.
def _load_data_file() -> dict[str, tuple[int, Optional[str]]]:
    raw: dict[str, list[tuple[int, Optional[str]]]] = {}

    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header row
        for row in reader:
            if len(row) < 2:
                continue
            raw_id = row[0].strip().strip('"')
            raw_name = row[1].strip().strip('"')
            try:
                account_id = int(raw_id)
            except ValueError:
                logger.warning(f"Skipping non-integer account_id: '{raw_id}'")
                continue

            match = _SUFFIX_RE.search(raw_name)
            marketplace: Optional[str] = match.group(1).upper() if match else None
            cleaned = _SUFFIX_RE.sub("", raw_name).strip().lower()

            raw.setdefault(cleaned, []).append((account_id, marketplace))

    resolved: dict[str, tuple[int, Optional[str]]] = {}
    for name, entries in raw.items():
        if len(entries) == 1:
            resolved[name] = entries[0]
        else:
            us = next((e for e in entries if e[1] == "US"), None)
            ca = next((e for e in entries if e[1] == "CA"), None)
            chosen = us or ca or entries[0]
            resolved[name] = chosen
            logger.warning(
                f"Multiple entries for '{name}': {entries} — using {chosen}"
            )

    logger.info(f"Loaded {len(resolved)} entries from data file")
    return resolved


# #note: Converts a 1-based column number to its spreadsheet letter (e.g. 20 -> T).
def _col_letter(col: int) -> str:
    result = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        result = chr(65 + remainder) + result
    return result


# #note: Main entry point. Loads the data file, opens the Brand Code Mapping Sheet,
# finds the brand_name / iw_account_id / us_ca columns by header name,
# then writes account_id and marketplace for every matched row in a single batch update.
def update_sheet() -> None:
    lookup = _load_data_file()

    creds = get_service_account_credentials(_SCOPES)
    client = gspread.Client(auth=creds)

    sheet = client.open_by_key(settings.BRAND_SHEET_ID)
    worksheet = sheet.sheet1
    all_values = worksheet.get_all_values()

    if not all_values:
        logger.error("Sheet appears to be empty — aborting")
        return

    headers = [h.strip().lower() for h in all_values[0]]

    try:
        brand_name_col = headers.index("brand_name") + 1
        iw_account_id_col = headers.index("iw_account_id") + 1
        us_ca_col = headers.index("us_ca") + 1
    except ValueError as e:
        logger.error(f"Required column not found in sheet header: {e}")
        return

    logger.info(
        f"Columns — brand_name: {_col_letter(brand_name_col)}, "
        f"iw_account_id: {_col_letter(iw_account_id_col)}, "
        f"us_ca: {_col_letter(us_ca_col)}"
    )

    cells_to_update: list[gspread.Cell] = []
    matched: list[str] = []
    unmatched: list[str] = []

    for row_idx, row in enumerate(all_values[1:], start=2):  # row 1 is header
        if len(row) < brand_name_col:
            continue
        brand_name = row[brand_name_col - 1].strip()
        if not brand_name:
            continue

        entry = lookup.get(brand_name.lower())
        if entry:
            account_id, marketplace = entry
            cells_to_update.append(
                gspread.Cell(row=row_idx, col=iw_account_id_col, value=str(account_id))
            )
            if marketplace in ("US", "CA"):
                cells_to_update.append(
                    gspread.Cell(row=row_idx, col=us_ca_col, value=marketplace)
                )
            matched.append(f"  {brand_name} -> {account_id} ({marketplace})")
        else:
            unmatched.append(f"  {brand_name}")

    if cells_to_update:
        worksheet.update_cells(cells_to_update)
        logger.info(f"Wrote {len(cells_to_update)} cells to sheet")

    logger.info(f"\nMatched ({len(matched)}):\n" + "\n".join(matched))
    if unmatched:
        logger.warning(f"\nUnmatched — manual entry needed ({len(unmatched)}):\n" + "\n".join(unmatched))
    logger.info("Done")


if __name__ == "__main__":
    update_sheet()
