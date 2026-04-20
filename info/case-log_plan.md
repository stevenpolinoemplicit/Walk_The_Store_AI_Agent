# Plan: Case Log Visibility — Extend Walk the Store (All 3 Phases)

## Context

Amazon Seller Central case log emails go to client inboxes (not Emplicit), SP-API has no case log
endpoint, and email is not viable at scale. However, Intentwise already syncs two tables into
`amazon_source_data` on Postgres that contain equivalent or better data:

1. `sellercentral_suppressedlistings_report` — current suppressed listings with human-readable
   remediation text and status change dates. Captures listing-level issues (missing image, policy
   violations, "not as described" complaints, etc.) — the same events that generate the case log emails.

2. `sellercentral_sellerperformance_policycompliance_report` — already queried by Walk the Store,
   but we currently read only 3 of ~20+ columns. Unexpanded columns cover 8 policy categories with
   `defects_count`, `status`, `target_value`, and `target_condition`.

**Everything is built into the existing Walk the Store agent. Same 7am run. Same orchestrator.**

---

## Architecture Decisions

| Decision | Choice |
|---|---|
| Integration | Extend existing Walk the Store (not a new service) |
| State tracking | New `agent_state.suppression_alerts` Postgres table (Steven creates manually) |
| Brand matching | `account_id` in suppression table = same Intentwise account IDs in `AccountConfig.account_ids` ✓ |
| Schedule | Daily 7am Cloud Run — unchanged |
| Schema ownership | `agent_state.*` (agent-owned); `amazon_source_data.*` never written to |

---

## Manual Step Required Before Phase 1 (Steven)

Create `info/agent_state_schema.sql` and run it in pgAdmin:

```sql
CREATE SCHEMA IF NOT EXISTS agent_state;

CREATE TABLE agent_state.suppression_alerts (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER     NOT NULL,
    asin                VARCHAR(20) NOT NULL,
    sku                 VARCHAR(200),
    status_change_date  DATE,
    issue_description   TEXT,
    alerted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    report_date         DATE        NOT NULL,
    UNIQUE (account_id, asin, status_change_date)
);
```

---

## Phase 1 — Suppression Watcher (MVP)

### New: `tools/postgres.py` — 3 new functions

**`get_suppressed_listings(account_id, country_code)`**
- Queries `sellercentral_suppressedlistings_report` filtered by `account_id`
- Returns `list[dict]` of all current suppressed listings for that account
- Note to verify: whether this table has a `country_code` column — if not, filter by `account_id` only

**`get_alerted_suppression_keys(account_id)`**
- Queries `agent_state.suppression_alerts` for `(asin, status_change_date)` tuples already alerted
- Returns `set[tuple[str, date]]` for fast deduplication

**`save_suppression_alerts(alerts)`**
- Inserts new alerts into `agent_state.suppression_alerts`
- ON CONFLICT DO NOTHING (UNIQUE on account_id + asin + status_change_date)

### New: `controllers/suppression_classifier.py`

**`classify_suppression(issue_description: str) -> dict`**
- Maps `issue_description` text to a category + suggested remediation:
  - `MISSING_IMAGE` → "Submit a compliant main image (white background, product only)"
  - `MISSING_INFO` → "Update listing: add missing required attributes"
  - `POLICY_VIOLATION` → "Review listing for policy compliance before appeal"
  - `CONDITION_COMPLAINT` → "Investigate product quality, provide images + appeal"
  - `DUPLICATE` → "Merge or remove duplicate listing"
  - `UNKNOWN` → "Review in Seller Central"
- Returns `{category, severity, suggested_action}`

### Modified: `models/report.py`

Add two new fields to `HealthReport`:
```python
suppressed_listings: List[dict] = []   # all current suppressions for this brand
new_suppressions: List[dict] = []      # newly detected since last run (for urgent alert)
```

### Modified: `controllers/report_builder.py`

After Teamwork block, before building HealthReport:
1. Call `get_suppressed_listings(account_id, cc)` per country
2. Call `get_alerted_suppression_keys(account_id)` once per brand
3. Diff: new = suppressions not in alerted keys
4. Call `classify_suppression()` on each new suppression's `issue_description`
5. Attach `suppressed_listings` and `new_suppressions` to HealthReport
6. After HealthReport built: call `save_suppression_alerts(new_suppressions)` to persist state

**Severity elevation rule:** If `new_suppressions` is non-empty, `highest_severity` is raised to at
least WARNING (if currently HEALTHY). A suppression with category POLICY_VIOLATION or
CONDITION_COMPLAINT elevates to CRITICAL.

### Modified: `views/slack_formatter.py`

Add `_format_suppression_section(report)` helper:
- If `new_suppressions`: shows as urgent block — "🔴 NEW: X suppressed listing(s) require action"
  with ASIN, issue category, and suggested action per item
- If `suppressed_listings` but no `new_suppressions`: shows as informational — "📋 X listing(s)
  currently suppressed (previously alerted)"
- Max 5 items shown; "+N more in Drive report" for overflow

### Modified: `tools/report_generator.py`

In `_build_doc_text()`, after Teamwork section, add "Suppressed Listings" section:
- Lists all `suppressed_listings` with ASIN, SKU, issue_description, status_change_date
- Highlights new suppressions with "NEW —" prefix

---

## Phase 2 — Expanded Policy Compliance

### Modified: `tools/postgres.py` — expand existing query

The current `get_account_health_metrics()` reads only 3 columns from policycompliance.
Expand to fetch all 8+ categories. New columns to add:

```
listing_policy_violations_defects_count
listing_policy_violations_status
product_authenticity_cust_complaints_defects_count
product_authenticity_cust_complaints_status
product_condition_cust_complaints_defects_count   ← maps to "not as described" cases
product_condition_cust_complaints_status
product_safety_cust_complaints_defects_count
product_safety_cust_complaints_status
suspected_intellectual_property_violations_defects_count
suspected_intellectual_property_violations_status
restricted_product_policy_violations_defects_count
restricted_product_policy_violations_status
customer_product_reviews_policy_violations_defects_count
customer_product_reviews_policy_violations_status
other_policy_violations_defects_count
other_policy_violations_status
```

Returns all values in the existing `metrics` dict — no function signature change.

### Modified: `models/report.py`

Add new optional fields for each expanded category:
```python
product_condition_complaints: Optional[int] = None
product_condition_status: Optional[str] = None
product_authenticity_complaints: Optional[int] = None
product_authenticity_status: Optional[str] = None
listing_policy_violations: Optional[int] = None
listing_policy_status: Optional[str] = None
product_safety_complaints: Optional[int] = None
product_safety_status: Optional[str] = None
suspected_ip_violations: Optional[int] = None
suspected_ip_status: Optional[str] = None
restricted_product_violations: Optional[int] = None
restricted_product_status: Optional[str] = None
review_policy_violations: Optional[int] = None
review_policy_status: Optional[str] = None
other_policy_violations: Optional[int] = None
other_policy_status: Optional[str] = None
```

### Modified: `controllers/classifier.py`

Add classification rules for all new categories:
- `product_condition_complaints > 0` → WARNING/CRITICAL based on count vs. target
- `product_authenticity_complaints > 0` → CRITICAL (higher severity than condition)
- `listing_policy_violations > 0` → WARNING
- Each category's `status` field (At Risk, Elevated, etc.) also feeds classification

### Modified: `views/slack_formatter.py` and `tools/report_generator.py`

Surface new categories in both Slack notifications and Google Docs alongside existing metrics.

---

## Phase 3 — Claude Triage Layer

### New: `tools/case_triage.py`

For each NEW suppression or NEW policy compliance event, calls Claude to generate:
1. Severity + urgency assessment
2. Step-by-step action plan specific to the issue type
3. Draft appeal/response template for cases requiring a seller reply

**`generate_triage(suppression: dict, brand_name: str) -> dict`**
- Uses `ANTHROPIC_EXECUTOR_MODEL` (claude-sonnet-4-6) — already in settings
- Prompt includes: ASIN, SKU, issue_description, category, brand context
- Returns `{severity, action_plan, response_draft}`
- Wrapped in try/except — triage failure does not block alerting

### Integration point

Called from `controllers/report_builder.py` for `new_suppressions` only (not historical suppressions,
to control API cost). Triage result stored on the suppression dict before attaching to HealthReport.

### Modified: `views/slack_formatter.py`

If triage result present on a new suppression: include `action_plan` in the Slack block and note
"📝 Draft response available in Drive report."

### Modified: `tools/report_generator.py`

In Google Doc: include full `action_plan` and `response_draft` under each new suppression entry.

---

## Full File Change Summary

| File | Action | Phase |
|---|---|---|
| `info/agent_state_schema.sql` | **Create** (Steven runs manually) | Pre-work |
| `tools/postgres.py` | **Modify** — add 3 functions + expand policycompliance query | 1 + 2 |
| `controllers/suppression_classifier.py` | **Create** | 1 |
| `models/report.py` | **Modify** — add suppression + expanded compliance fields | 1 + 2 |
| `controllers/report_builder.py` | **Modify** — suppression fetch, dedup, classify, save | 1 |
| `controllers/classifier.py` | **Modify** — add rules for 8 new compliance categories | 2 |
| `views/slack_formatter.py` | **Modify** — suppression section + triage summary | 1 + 3 |
| `tools/report_generator.py` | **Modify** — suppression + triage sections in Doc | 1 + 3 |
| `tools/case_triage.py` | **Create** | 3 |

**No files deleted. All changes are additive.**

---

## Data Flow After Integration

```
orchestrator.run_agent()
  → postgres.check_connection()
  → sheets_reader.get_active_accounts()
  → FOR EACH account:
      build_brand_reports(account)
        → postgres.get_account_health_metrics()     (expanded — Phase 2)
        → postgres.get_suppressed_listings()         NEW Phase 1
        → postgres.get_alerted_suppression_keys()    NEW Phase 1
        → diff → new_suppressions
        → suppression_classifier.classify_suppression() NEW Phase 1
        → case_triage.generate_triage()              NEW Phase 3 (new suppressions only)
        → postgres.save_suppression_alerts()         NEW Phase 1
        → HealthReport(..., suppressed_listings, new_suppressions, expanded compliance fields)
      report_generator.create_report()   ← suppression + triage in Doc
      slack_alerts.send_dm()             ← suppression + triage in Slack
      postgres.save_report()
  → build_ops_summary() / post_ops_summary()
```

---

## Open Assumptions (verify at session start)

1. **`country_code` on suppression table**: Brief lists columns without `country_code`. If absent,
   query by `account_id` only. Confirm with:
   ```sql
   SELECT column_name FROM information_schema.columns
   WHERE table_schema = 'amazon_source_data'
     AND table_name = 'sellercentral_suppressedlistings_report'
   ORDER BY ordinal_position;
   ```

2. **Deduplication key stability**: `asin + status_change_date` is the unique key. Confirm that if
   a listing is re-suppressed after being fixed, `status_change_date` changes (triggering a new alert).

3. **policycompliance column names**: Exact column names must be verified before writing the expanded
   query. Run:
   ```sql
   SELECT column_name FROM information_schema.columns
   WHERE table_schema = 'amazon_source_data'
     AND table_name = 'sellercentral_sellerperformance_policycompliance_report'
   ORDER BY ordinal_position;
   ```

---

## No New Python Dependencies

`psycopg2` (installed), `anthropic` (installed), `pydantic` (installed).
Phase 3 uses the existing Claude API client pattern already in `tools/report_generator.py`.

---

## Verification Steps

1. Steven runs `info/agent_state_schema.sql` in pgAdmin
2. Set `LOG_LEVEL=DEBUG` in `.env`
3. Run `python main.py`
4. Check logs: "Suppressed listings found for [brand]" and "New suppressions: N"
5. Check Slack: new suppression block appears in at least one brand notification
6. Check `agent_state.suppression_alerts` in pgAdmin — rows should be present
7. Second run: same suppressions should NOT re-alert (dedup working)
8. Check Google Doc: "Suppressed Listings" section present with triage content
