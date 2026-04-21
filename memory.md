# memory.md — Walk the Store AI Agent
> Running log of decisions, changes, and context for this project.
> Updated by Claude and contributors as work progresses.
> Claude Code automatically loads CLAUDE.md — read this file at the start of every session.

---

## Project Overview

Autonomous AI agent triggered daily at 7:00 AM PDT via Cloud Scheduler + Cloud Run Jobs. Reads Amazon account health data from Intentwise-synced Postgres tables (amazon_source_data), classifies by severity (Critical/Warning/Healthy), generates a Google Doc report per brand saved to Drive, posts a Slack notification with the Drive link. Claude Enterprise (claude.ai) handles interactive chat via Drive connector — no custom bot.

POC/v1 scope: Account Health only. Brand memory, inventory health, Walmart out of scope.
Owner: Steven Polino | Approvers: Adam Weiler, Emily Lindahl

---

## Session Log

### Session 25 — Add model version requirement to CLAUDE.md
**Date:** 2026-04-21
**Participants:** Claude Code

#### Decisions Made
- **Always use latest/most powerful model** — Steven wants every Claude Code session to default to `claude-opus-4-6`; configured globally in `~/.claude/settings.json` with `"model": "claude-opus-4-6"`
- **Added CLAUDE.md Section 16** — codifies this as a project standard so contributors don't downgrade

#### Files Updated
- `CLAUDE.md` — added Section 16 (Model Version — Always Use Latest); updated "Last updated" date to 2026-04-21

#### Still To Do
- [ ] README still references "Sonnet + Opus advisor" in two places (lines 6 and 39) — should be updated to "Sonnet-only" to match Session 24 changes

---

### Session 24 — Run stabilization: timeout fix, narrative bug, Sonnet-only, skip healthy narratives
**Date:** 2026-04-21
**Participants:** Claude Code

#### Decisions Made
- **Task timeout was 600s (10 min) — too short for 50+ brands** — increased to 3600s; root cause was Claude advisor API calls (~50s/brand × 50 brands = ~40 min total)
- **Max retries set to 0** — retries cause duplicate Drive docs since each retry creates fresh docs without checking for existing ones
- **Removed Opus advisor** — advisor strategy added in Session 23 was the cause of today's timeout; removed Opus, now Sonnet-only; ~10-15s per call instead of ~50s
- **Skip narrative for healthy/unknown brands** — LLM call skipped entirely for brands with no findings; template used instead; reduces API calls by ~30-40%
- **Narrative bug fixed** — `block.text` can be `None` on advisor tool-use blocks even when `hasattr(block, "text")` is True; `"\n".join()` raised `TypeError`; fixed by adding `and block.text is not None` to filter
- **Teamwork 401 — expired token** — all brands failing on Teamwork; token updated in Secret Manager; takes effect on next execution
- **ASIN deactivations are a case log gap** — suppression table only captures hidden listings, not fully removed/deactivated ASINs; need to find Intentwise table for this

#### Files Updated
- `tools/report_generator.py` — removed Opus advisor tool, Sonnet-only; skip `_generate_narrative()` for healthy/unknown brands; fixed `block.text is not None` bug
- `CLAUDE.md` — added rule: never solicit API tokens or credentials from user

#### GCP Changes
- `walk-the-store` job task timeout: 600s → 3600s
- `walk-the-store` job max retries: 3 → 0
- `TEAMWORK_API_TOKEN` secret updated to new token

#### Today's Run (walk-the-store-v9vqs)
- Started 14:00 UTC, timed out after 3 retries (~41 min total)
- 54 reports saved to Postgres and Drive docs created (with duplicates due to retries)
- Ops summary + Slack DMs never sent (job killed before reaching that step)
- Suppression watcher confirmed working: UpWellness (2), Mokai Pets (1), Trtl (1), Organifi (13)

#### Still To Do
- [ ] Check Intentwise for ASIN deactivations table (e.g. `sellercentral_inactive_listings`) — main remaining case log gap
- [ ] Phase 2: expand `sellercentral_sellerperformance_policycompliance_report` query to all 8+ categories
- [ ] Phase 3: Claude triage — generate action plan + draft appeal template for new suppressions
- [ ] Verify Teamwork 401s resolve on tomorrow's run with new token
- [ ] Verify dedup working tomorrow — same suppressions should NOT re-alert

---

### Session 23 — Phase 1 suppression watcher built and deployed
**Date:** 2026-04-21
**Participants:** Claude Code

#### Decisions Made
- **Suppression table has no `country_code`** — confirmed via pgAdmin column query; filter by `account_id` only; for multi-marketplace brands (e.g. Trtl US + CA), loop over all `account_ids` and combine results
- **Deduplication key: `(account_id, asin, status_change_date)`** — stored in new `agent_state.suppression_alerts` table; ON CONFLICT DO NOTHING makes saves idempotent
- **Severity elevation** — new suppressions bump brand severity: HEALTHY → at least WARNING; WARNING → CRITICAL if classification is POLICY_VIOLATION, CONDITION_COMPLAINT, AUTHENTICITY, or SAFETY
- **7 classification categories** — keyword-matched against `issue_description`: MISSING_IMAGE, MISSING_INFO, POLICY_VIOLATION, CONDITION_COMPLAINT, AUTHENTICITY, SAFETY, DUPLICATE; UNKNOWN fallback
- **gcloud default project was wrong** — `gcloud` CLI defaulted to `emplicit-ai-automations-polino`; build/deploy commands for this project must always include `--project=polino-agentic-solutions` explicitly
- **agent_state schema created manually by Steven in pgAdmin** — Claude Code never executes DDL; DDL saved to `info/agent_state_schema.sql` for reference

#### Files Created
- `info/agent_state_schema.sql` — DDL for `agent_state` schema + `suppression_alerts` table (Steven ran manually in pgAdmin)
- `controllers/suppression_classifier.py` — classifies `issue_description` text into 7 categories with severity + suggested action

#### Files Updated
- `tools/postgres.py` — added `get_suppressed_listings()`, `get_alerted_suppression_keys()`, `save_suppression_alerts()`
- `models/report.py` — added `suppressed_listings: List[dict]` and `new_suppressions: List[dict]` fields to `HealthReport`
- `controllers/report_builder.py` — fetches suppressions across all account_ids, diffs against alerted keys, classifies new ones, elevates severity, saves alerts after build
- `views/slack_formatter.py` — added `_format_suppression_section()` + injected suppression block into `format_notification()`
- `tools/report_generator.py` — added "Suppressed Listings" section to `_build_doc_text()` with NEW prefix and suggested action for new suppressions

#### GCP
- Deployed to Cloud Run job `walk-the-store` — build `1aeec8d3` succeeded; job updated and will run at 7am today with new features

#### Still To Do
- [ ] Monitor today's 7am run — check logs for "Suppressed listings found" and "New suppressions" lines
- [ ] Verify `agent_state.suppression_alerts` has rows after the run
- [ ] Second run tomorrow — confirm same suppressions do NOT re-alert (dedup working)
- [ ] Phase 2: expand `sellercentral_sellerperformance_policycompliance_report` query to all 8+ categories
- [ ] Phase 3: Claude triage — generate action plan + draft appeal template for new suppressions

---

### Session 22 — Case log visibility planning (caselog_agent_planning)
**Date:** 2026-04-20
**Participants:** Claude Code

#### Decisions Made
- **SP-API has no case log endpoint** — confirmed via feature-integrator agent research; no `getCaseLog`, `listCases`, or equivalent exists in SP-API as of April 2026
- **Email ruled out entirely** — case log emails go to client inboxes (not Emplicit); no single shared inbox; email is not a viable integration path
- **Intentwise already has the data** — two tables in `amazon_source_data` cover the same events as case log emails:
  - `sellercentral_suppressedlistings_report` — suppressed listings with human-readable remediation text (`account_id`, `asin`, `sku`, `product_name`, `status`, `reason`, `issue_description`, `status_change_date`)
  - `sellercentral_sellerperformance_policycompliance_report` — already queried but only 3 of ~20+ columns used; has 8 policy categories including `product_condition_cust_complaints_*` (maps directly to "not as described" cases)
- **Build as Walk the Store extension** — same orchestrator, same 7am run; not a separate service
- **`account_id` in suppression table = same Intentwise IDs in `AccountConfig.account_ids`** — brand matching solved without extra lookup
- **State table approach** — new `agent_state.suppression_alerts` Postgres table for deduplication; Steven creates manually (Claude never writes DDL)
- **3-phase plan approved**: Phase 1 = suppression watcher MVP, Phase 2 = expanded policy compliance (all 8 categories), Phase 3 = Claude triage/appeal draft generation
- **Email content analysis** — real case log email (Nolan Interior, ASIN B0DT4YLVLJ, case 19898704701) contains ASIN + SKU but NOT MWS Seller ID; brand matching must use ASIN-to-account_id lookup, not seller ID — this was invalidated as concern because Intentwise suppression table already has `account_id`

#### Files Created
- `info/case-log_plan.md` — full 3-phase implementation plan: suppression watcher, expanded compliance, Claude triage; includes file change table, data flow diagram, pre-build verification queries, and agent_state schema DDL

#### Files Updated
- None — planning session only; no code written

#### Still To Do
- [ ] Verify `country_code` column exists on `sellercentral_suppressedlistings_report` (run column query in pgAdmin)
- [ ] Verify exact column names on `sellercentral_sellerperformance_policycompliance_report` (all 20+ columns)
- [ ] Confirm deduplication key: `asin + status_change_date` — verify status_change_date changes on re-suppression
- [ ] Steven runs `agent_state_schema.sql` DDL in pgAdmin before Phase 1 build
- [ ] Build Phase 1 (suppression watcher) in next session — start with `tools/postgres.py` new functions

---

### Session 21 — Drive folder structure, report renaming, advisor strategy (Sonnet + Opus)
**Date:** 2026-04-20
**Participants:** Claude Code

#### Decisions Made
- **Date subfolder created per daily run** — each run now creates a `Month DD YYYY` subfolder (e.g. `April 20 2026`) inside the brand's Drive folder and the ops folder before depositing reports; if the folder already exists it is reused; prevents docs from piling up flat in the parent folder
- **Report title format changed** — from `{brand} — Amazon Health Report — YYYY-MM-DD` to `{brand} - Month DD YYYY - Amazon Health Report`; ops summary follows same pattern: `Walk the Store - Month DD YYYY - Daily Ops Summary`; date is human-readable (month name, not numbers)
- **Advisor strategy introduced** — Sonnet (`claude-sonnet-4-6`) is the executor; Opus (`claude-opus-4-6`) is the advisor (max 3 calls per report); the advisor tool is declared via `advisor_20260301` with beta header `anthropic-beta: advisor-tool-2026-03-01`; Sonnet writes the Executive Summary and Key Findings prose, escalating to Opus on complex multi-issue reports
- **Hybrid LLM + deterministic design** — Key Metrics table, Detailed Findings, Teamwork Activity, and Footer remain fully templated; LLM only touches the narrative prose sections; if `_generate_narrative()` fails for any reason, `_build_doc_text()` silently falls back to the template — no crashes
- **Two rebuilds and redeployments this session** — image rebuilt and Cloud Run Job updated after each change set

#### Files Updated
- `tools/report_generator.py` — `_get_or_create_date_folder()` helper added; `doc_title` format updated to `Month DD YYYY`; date subfolder routing added to both `create_report()` and `create_ops_summary_doc()`; `import anthropic` added; `_generate_narrative()` added using advisor strategy; `_build_doc_text()` updated to call `_generate_narrative()` with template fallback
- `config/settings.py` — added `ANTHROPIC_EXECUTOR_MODEL = "claude-sonnet-4-6"` and `ANTHROPIC_ADVISOR_MODEL = "claude-opus-4-6"` constants

#### Still To Do
- [ ] Monitor next 7:00 AM run — check Cloud Run logs for `_generate_narrative` success/fallback messages
- [ ] Open a generated Google Doc to confirm Executive Summary reads as prose, not template strings
- [ ] Confirm Opus advisor tokens appear in usage logs on critical-severity brands

---

### Session 20 — Teamwork auth fix, repo cleanup, docs moved to info/
**Date:** 2026-04-17
**Participants:** Claude Code

#### Decisions Made
- **Teamwork auth password changed to `"x"`** — Teamwork v1 Basic auth convention is `(token, "x")`; empty string `""` may be rejected by some instances; `.strip()` was already applied in settings.py so trailing newline was not the root cause
- **Response body added to Teamwork error logs** — previously only status code was logged; `e.response.text[:500]` now appears so the next run will show the actual Teamwork error message (401/403/404 + reason)
- **`_route_alerts` function removed permanently** — function was dead code (`pass` only); per-brand alert routing is not part of the final design; call site and `format_notification` import removed alongside it
- **`gradio` and `huggingface_hub` removed from dependencies** — neither is used anywhere in the codebase; both bloat the Docker image; removed from `pyproject.toml`
- **`docs/` folder contents moved to `info/`** — user is deleting the `docs/` folder; all three files copied to `info/`; README and deploy-checklist references updated
- **`.env` security check passed** — `git log --oneline -- .env` returned empty; file was never committed to history
- **`.claude/settings.local.json` added to `.gitignore`** — file existed but wasn't ignored; machine-specific Claude local settings should not be committed

#### Files Created
- `info/CLOUD_RUN_DEPLOY.md` — copy of docs/ version; updated `echo -n` → `printf`, scheduler command updated to `America/Los_Angeles` + 7:00 AM, `printf` note added to secrets section
- `info/CLAUDE_ENTERPRISE_SETUP.md` — copy of docs/ version; time updated to LA timezone
- `info/walk_the_store_schema.sql` — copy of docs/ version; unchanged
- `info/RESOURCE.md` — copy of root RESOURCE.md; root copy pending manual delete by user

#### Files Updated
- `tools/teamwork.py` — auth `("", "")` → `(token, "x")` in all 3 functions; `e.response.text[:500]` added to all `HTTPStatusError` error logs
- `controllers/orchestrator.py` — removed `_route_alerts` function + call site + `format_notification` import; blank line formatting fix
- `pyproject.toml` — removed `gradio` and `huggingface_hub` from dependencies
- `PROJECT_SCOPE.md` — owner "Steven Chicken" → "Steven Polino"; run time "9:00 AM ET" → "7:00 AM Los Angeles time"; gradio row removed from tech stack table
- `.gitignore` — added `.claude/settings.local.json`
- `.claude/commands/deploy-checklist.md` — "Section 11" → "Section 12"; scheduler time corrected to "7:00 AM Los Angeles time"
- `README.md` — `docs/` → `info/` in project structure and deployment section

#### Still To Do
- [ ] Teamwork tasks — next run logs will reveal actual error (401/403/404); diagnose and fix based on those logs
- [ ] `DRIVE_OPS_FOLDER_ID` — user confirmed ops summary doc issue is already fixed; monitor next run to confirm
- [ ] Manual deletes: `docs/` folder, root `RESOURCE.md`, `info/1`, `info/account_id_and_account_name`, `info/recent_query`
- [ ] Redeploy required — `tools/teamwork.py` and `controllers/orchestrator.py` changed; rebuild image and update Cloud Run Job

---

### Session 19 — GCP deployment live, DWD fixed, trailing newline secrets fixed, scheduler set up
**Date:** 2026-04-17
**Participants:** Claude Code

#### Decisions Made
- **DWD `invalid_request` root cause: wrong client ID in Google Admin** — the service account client ID registered in Google Admin didn't match `polino-agentic-solutions-servi`; user added the correct SA to Google Admin with all scopes; also added `walk-the-store-sa` as a second entry for future consolidation
- **Trailing `\r\n` in Secret Manager secrets** — all secrets originally stored via PowerShell `echo` which appends `\r\n`; caused Postgres hostname DNS failure, gspread 404 on sheet IDs; fixed by re-storing secrets using `printf` (no newline) and adding `.strip()` to all string values in `settings.py` as defensive guard
- **Sheets 404 was not a permissions issue** — `steven.polino@emplicit.co` owns the sheets; the 404 was caused entirely by the `\r\n` in the `BRAND_SHEET_ID` and `PEOPLE_SHEET_ID` secrets
- **Postgres unreachable → false healthy report** — when Postgres is down, all brands return `unknown` severity which is bucketed with `healthy`; ops summary showed 0 critical/warning; added `postgres.check_connection()` call at orchestrator startup to abort and DM error to always-notify users instead
- **Cloud Scheduler uses `America/Los_Angeles` timezone** — `0 7 * * *` with LA timezone handles daylight saving automatically; next run: 2026-04-18 07:00 LA time
- **Scheduler test confirmed working** — `gcloud scheduler jobs run` triggered a real execution via HTTP/OAuth; execution was cancelled immediately after confirming it fired (user did not want a 4th report sent that day)
- **Never trigger live runs without permission** — each execution DMs the entire ops team; requires explicit user approval before any `gcloud run jobs execute` or `gcloud scheduler jobs run`
- **`SLACK_OPS_CHANNEL` left as-is** — user confirmed `C0AS4D84NET` (walk-the-store channel) is the only channel and it's already working; no change needed
- **Verified real data after Postgres fix** — execution `walk-the-store-68pcs` showed 2 critical brands in logs; confirmed account 2625280 US has LSR 5.1% (critical) from pgAdmin query

#### Files Updated
- `config/settings.py` — `.strip()` added to ALL string secret reads; `EMPLICIT_PG_PORT` strip added; `WEEKEND_ONCALL_IDS` already present
- `tools/postgres.py` — added `check_connection()` function; returns bool; used by orchestrator at startup
- `controllers/orchestrator.py` — added Postgres connectivity check at top of `run_agent()`; aborts and DMs error to `NOTIFY_ALWAYS_IDS` if unreachable
- `README.md` — updated status to live/deployed; added Emily to always-notify; added weekend on-call docs; updated scheduler time; added Secret Manager newline warning
- `info/SETUP.md` — Cloud Scheduler step marked complete

#### GCP Resources Created
- Cloud Scheduler job `walk-the-store-daily` — `0 7 * * *` America/Los_Angeles, HTTP target → Cloud Run Jobs API, OAuth via `walk-the-store-sa`
- Secret Manager version 2 for `GOOGLE_IMPERSONATION_EMAIL`, `BRAND_SHEET_ID`, `PEOPLE_SHEET_ID` — all re-stored without trailing newline

#### Still To Do
- [ ] Teamwork tasks — all task lists returning unavailable (separate investigation needed)
- [ ] `DRIVE_OPS_FOLDER_ID` — ops summary doc not moving to correct folder (angle brackets in secret or wrong folder ID)
- [ ] Verify pgAdmin `walk_the_store.daily_health_reports` has correct rows after clean run

---

### Session 18 — GCP deployment unblocked, per-country account IDs, weekend on-call routing
**Date:** 2026-04-17
**Participants:** Claude Code

#### Decisions Made
- **Artifact Registry permission root cause: wrong service account** — newer GCP projects use Compute Engine default SA (`140357370341-compute@developer.gserviceaccount.com`) as Cloud Build executor, not the legacy `@cloudbuild` SA; all prior grants were to the wrong identity; fixed by granting `roles/artifactregistry.writer` and `roles/storage.admin` to the Compute Engine default SA
- **Cloud Run job created via `update` not `create`** — job already existed from a prior failed attempt; used `gcloud run jobs update` instead
- **walk-the-store-sa service account created** — did not exist; created fresh; granted `roles/secretmanager.secretAccessor` at project level; granted `roles/iam.serviceAccountUser` to `steven.polino@emplicit.co`
- **Per-country Intentwise account IDs moved to sheet** — Brand Code Mapping Sheet now has 3 account ID columns: S=`iw_account_id_us`, T=`iw_account_id_ca`, U=`iw_account_id_mx`; FBM moved to col V, FBA to col W; only numeric values used — blanks and "no account id" text skip silently
- **AccountConfig.account_id replaced by account_ids dict** — `account_id: Optional[int]` removed; replaced with `account_ids: dict[str, int]` keyed by country_code (e.g. `{"US": 123, "CA": 456}`); brands with no valid numeric IDs are skipped entirely
- **Postgres queries now per-country** — `get_account_health_metrics(account_id, country_code, fbm, fba)` filters by both account_id AND country_code; returns flat dict for one country; report_builder iterates `account.account_ids.items()` and calls once per country
- **ODR table name confirmed truncated** — PostgreSQL 63-char limit truncates `sellercentral_sellerperformance_customerserviceperformance_report` to `sellercentral_sellerperformance_customerserviceperformance_repo`; fixed in postgres.py
- **accounts_by_code lookup strips country suffix** — `report.brand_code` is `TRT_CA` but AccountConfig is keyed by `TRT` (3-letter codes); `rsplit("_", 1)[0]` strips suffix for lookup only; display names still include country (e.g. "Trtl CA")
- **Weekend on-call routing added** — Saturday + Sunday: ops manager DMs replaced by DMs to Axel (U0339BL8PSN), Kay (U01J7UBBX3K), Milagros (U02GXHL9Q9M), Albenis (U01JLUZ534Y); weekdays unchanged; Steven + Adam + Emily always receive full summary regardless of day
- **CA/MX data confirmed** — only Trtl (2625620) and Woof Pet (3594300) have CA accounts; TrtlTravel (2625700) is AU (not supported); no MX accounts exist in DB yet; iw_account_id_ca populated for Trtl + Woof Pet; iw_account_id_mx has one entry

#### Files Updated
- `models/account.py` — `account_id: Optional[int]` → `account_ids: dict[str, int] = {}`; FBM/FBA column comments updated to V/W
- `tools/sheets_reader.py` — reads `iw_account_id_us/ca/mx`; builds per-country dict; skips non-numeric; FBM/FBA header names unchanged (gspread is header-based)
- `tools/postgres.py` — `get_account_health_metrics()` now takes `country_code` param; all 4 queries filter by `account_id AND country_code`; returns flat dict; ODR table name fixed to 63-char truncated form
- `controllers/report_builder.py` — iterates `account.account_ids.items()`; calls postgres per country
- `controllers/orchestrator.py` — `accounts_by_code` lookup strips `_CC` suffix; weekend on-call routing added with day-of-week check
- `config/settings.py` — added `WEEKEND_ONCALL_IDS` list with Axel, Kay, Milagros, Albenis Slack IDs

#### Still To Do
- [ ] Rebuild Docker image + redeploy Cloud Run job (image predates per-country account_ids changes)
- [ ] Confirm manual test run logs — check for errors after execution `walk-the-store-bfcxk`
- [ ] Set up Cloud Scheduler (7:00 AM PDT / 14:00 UTC daily)
- [ ] Update SETUP.md to reflect completed GCP steps
- [ ] Ops team to investigate 4 food/product safety violations on account 3619670 (AllGood / LVL10)
- [ ] Verify mfn_rate data for remaining FBM brands in pgAdmin

---

### Session 17 — FBM/FBA suppression, ODR fix, UNKNOWN severity fix, country investigation
**Date:** 2026-04-16
**Participants:** Claude Code

#### Decisions Made
- **FBM vs FBA columns added to Brand Code Mapping Sheet** — column U = FBM (merchant-fulfilled, controls own shipping), column V = FBA (Amazon-fulfilled); value of 1 = enrolled; both read into `AccountConfig.fbm` and `AccountConfig.fba`
- **Shipping metric suppression for FBA-only brands** — `classify_account()` now accepts `check_shipping: bool`; when False, LSR / VTR / pre-cancel all set to HEALTHY with "not monitored" message; FBM brands get full shipping checks; hybrid brands (both flags) get shipping checks
- **VTR suppression folded into check_shipping** — previously `check_vtr` was standalone; now when `check_shipping=False` all three shipping metrics are suppressed together; `check_vtr` still exists as a secondary gate for edge cases
- **ODR query fixed for fulfillment type** — now selects both `order_defect_rate_afn_rate` and `order_defect_rate_mfn_rate`; FBM-only → mfn_rate; FBA-only or unset → afn_rate; hybrid → `max()` of both; mfn_rate confirmed non-null for FBM brands via pgAdmin (Shop Indoor Golf: 0.0033 = 0.33%)
- **UNKNOWN severity brands included in healthy bucket** — `build_ops_summary()` previously dropped brands with `highest_severity = "unknown"` silently; now grouped with healthy; this was why daily summary only showed critical brands
- **Out-of-scope brands skip silently** — removed `notify_error()` call for missing `iw_account_id`; these brands don't pay for the service so missing ID is expected, not an error; now `logger.debug()` only
- **Shared account_id is expected and correct** — AllGood and LVL10 share account_id 3619670; multiple brands can legitimately share one Amazon seller account; agent processes each brand independently; account-level metrics (food safety, IP, AHR, status) apply to all brands under the account
- **Food safety violations on account 3619670 are real** — pgAdmin confirmed: 4 food/product safety violations, `status = 'BAD'`, `country_code = 'US'`, consistent since at least 2026-03-28; rolling 6-month window; ops manager for those brands needs to address
- **VTR warning threshold confirmed good** — keep critical < 95%, warning 95–98%; no change
- **Google Doc footer updated** — now reads: data sourced from Emplicit's PostgreSQL database; contact Steven Polino on Slack; feedback form link added
- **SETUP.md Part 4 marked complete** — local end-to-end test run confirmed successful; new env vars added to Part 3

#### Files Updated
- `models/account.py` — `fmb` renamed to `fbm`; `fba: bool = False` added
- `tools/sheets_reader.py` — reads `FBM` (col U) and `FBA` (col V); removed `notify_error()` for missing iw_account_id; removed unused `notify_error` import
- `tools/postgres.py` — `get_account_health_metrics()` now accepts `fbm` and `fba` params; ODR query selects both afn and mfn rates, picks correct one in Python
- `controllers/classifier.py` — `classify_account()` now accepts `check_shipping: bool = True`; suppresses LSR/VTR/pre-cancel for FBA-only brands
- `controllers/report_builder.py` — passes `fbm`/`fba` to metrics query; passes `check_shipping=account.fbm` to classifier; `UNKNOWN` added to imports; healthy bucket in `build_ops_summary()` now includes UNKNOWN severity
- `tools/report_generator.py` — footer text updated (data source, contact, feedback form)
- `info/SETUP.md` — Part 3 env vars updated; Part 4 fully checked off

#### Still To Do
- [ ] Restore Adam (U5H5GLJLV) + Emily (UEKN0TY2D) to `NOTIFY_ALWAYS_IDS` in `settings.py` before go-live
- [ ] Uncomment ops manager filtered DM loop in `orchestrator.py` before go-live
- [ ] GCP deployment (Parts 5–6 of SETUP.md)
- [ ] Ops team to investigate 4 food/product safety violations on account 3619670 (AllGood / LVL10 shared account)
- [ ] Verify mfn_rate data exists for all other FBM brands in pgAdmin (confirmed for Shop Indoor Golf only)

---

### Session 16 — Pre-deployment: summary format, Drive 403 fix, Teamwork open tasks, ops routing
**Date:** 2026-04-16
**Participants:** Claude Code

#### Decisions Made
- **Daily ops summary now posts to channel + per-ops-manager filtered DMs** — `post_ops_summary()` restored (was TEST MODE); orchestrator groups completed reports by `ops_slack_id` and DMs each ops manager only their brands; Steven (U0AJYBWU03X) + Adam (U5H5GLJLV) always receive the full summary via `NOTIFY_ALWAYS_IDS`; per-brand individual alerts remain commented out permanently — this is the final design
- **No individual brand notifications to anyone** — `_route_alerts()` body stays commented out; only the daily ops summary is sent
- **Daily ops summary saved as a Google Doc** — new `create_ops_summary_doc()` in `report_generator.py` creates a dated doc in `DRIVE_OPS_FOLDER_ID` and appends the link to Slack DMs; requires new env var `DRIVE_OPS_FOLDER_ID`
- **Drive 403 root cause: DWD not activated in code** — domain-wide delegation was confirmed configured in Google Admin but code never called `.with_subject()`; `google_auth.py` now calls `creds.with_subject(settings.GOOGLE_IMPERSONATION_EMAIL)` when the env var is set; requires new env var `GOOGLE_IMPERSONATION_EMAIL` (a real emplicit.co Workspace user email)
- **HttpError logging added to report_generator.py** — Doc creation and batchUpdate catches now log HTTP status code + reason + error_details specifically for `HttpError` before re-raising
- **Teamwork now fetches open/pending tasks in addition to completed** — new `get_open_tasks_by_list()` in `teamwork.py`; `report_builder.py` loops over all 12 task lists for both completed + open; open task failures are silent (don't add to data_gaps — supplementary data)
- **Teamwork section added to Google Doc** — `_build_doc_text()` now includes "Teamwork Activity" section with open tasks (top 10) and recent completions (top 5) after Detailed Findings
- **Teamwork section in Slack updated** — `_format_teamwork_section()` now accepts both `open_tasks` and `completed_tasks`, shows both with "`Open / In Progress`" and "`Recently Completed`" sub-labels
- **Daily summary format updated** — warning brands now show top 3 findings (was names-only); healthy brands collapsed to single comma-separated line; `HEALTHY` constant added to imports
- **Adam (U5H5GLJLV) added to NOTIFY_ALWAYS_IDS** — was commented out; both Steven + Adam now receive all reports

#### Files Updated
- `models/report.py` — added `teamwork_open_tasks: List[dict] = []` field
- `config/settings.py` — added `GOOGLE_IMPERSONATION_EMAIL`, `DRIVE_OPS_FOLDER_ID`; fixed `NOTIFY_ALWAYS_IDS` to include both U0AJYBWU03X and U5H5GLJLV
- `tools/google_auth.py` — added `.with_subject()` call when `GOOGLE_IMPERSONATION_EMAIL` is set
- `tools/teamwork.py` — added `get_open_tasks_by_list()`
- `tools/report_generator.py` — `HttpError` import + specific catches on Doc create/batchUpdate; Teamwork Activity section in `_build_doc_text()`; new `create_ops_summary_doc()` function; added `date` import
- `views/slack_formatter.py` — `_format_teamwork_section()` now accepts open + completed lists; shows both sections
- `controllers/report_builder.py` — `HEALTHY` import added; `build_brand_report()` collects open tasks; `build_ops_summary()` shows warning findings + healthy comma line
- `controllers/orchestrator.py` — restored `post_ops_summary()` channel post; added ops summary doc creation; added per-ops-manager filtered DM logic; added `date` import
- `.env.example` — added `GOOGLE_IMPERSONATION_EMAIL` and `DRIVE_OPS_FOLDER_ID` entries with comments

#### Still To Do
- [ ] Add `GOOGLE_IMPERSONATION_EMAIL=<user@emplicit.co>` to `.env` (use a real Workspace user who has Drive access)
- [ ] Add `DRIVE_OPS_FOLDER_ID=<folder_id>` to `.env` (Drive folder for daily ops summary docs)
- [ ] Full local end-to-end test: `python main.py`
- [ ] Verify Drive 403 is resolved (check logs for "Google Doc created" not "HTTP 403")
- [ ] VTR warning threshold decision — keep 97% buffer or collapse to single 95% critical
- [ ] Restore remaining TEST MODE items if any before go-live
- [ ] GCP deployment (Parts 5–6 of SETUP.md)
- [ ] ~26 brands still unmatched (no iw_account_id) — need investigation

---

### Session 15 — iw_account_id bulk population script built and run
**Date:** 2026-04-15
**Participants:** Claude Code

#### Decisions Made
- **iw_account_id lives in Google Sheets, not Postgres** — user couldn't find `account_config` table; confirmed it was removed in Session 9 and replaced by Google Sheets; Postgres has no brand config table
- **Bulk populate via pgAdmin export** — user ran `SELECT DISTINCT account_id, account_name` against Intentwise source tables; exported as TSV to `info/account_id_and_account_name`; script reads this file and writes to sheet
- **us_ca column (col T) added** — script also populates marketplace (US or CA) for each brand; AU/UK/etc. left blank
- **16 name mismatch mappings hardcoded** — sheet `brand_name` values differ from Intentwise `account_name` for 16 brands (e.g. "Organics Ocean" vs "organicsocean", "Goldpaw" vs "Gold Paw Series"); `_NAME_MAP` dict added to script to resolve these
- **Shared iw_account_id is safe** — confirmed no code changes needed; orchestrator loops over `AccountConfig` Python objects (not DB rows); both brands process independently and appear separately in daily summary; `save_report()` unique constraint is on `brand_code`, not `account_id`
- **Service account needed Editor access to sheet** — initial run got 403; fixed by sharing Brand Code Mapping Sheet with service account email as Editor

#### Files Created
- `tools/update_iw_account_ids.py` — one-off utility; reads pgAdmin TSV export, matches to sheet `brand_name` (col O), writes `account_id` → col S and `US/CA` → col T; includes `_NAME_MAP` for 16 known mismatches

#### Still To Do
- [ ] ~26 brands still unmatched (not in Intentwise data at all) — need investigation; includes ORG, SEL, ALG, MOK, PHT, AJK, NLN, CCB, NHR and others
- [ ] Restore TEST MODE comments in orchestrator.py before go-live
- [ ] Full local end-to-end test with `python main.py`
- [ ] VTR warning threshold decision
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 14 — Slack DM alerts suppressed for local test run
**Date:** 2026-04-15
**Participants:** Claude Code

#### Decisions Made
- **Per-brand Slack DMs suppressed for local testing** — `NOTIFY_ALWAYS_IDS` DM loop inside `_route_alerts` commented out so individual brand alert DMs do not fire during local runs
- **Ops summary channel post suppressed** — `slack_alerts.post_ops_summary(summary)` commented out; ops summary now logged to console via `logger.info` instead
- **Daily ops summary DM retained** — `NOTIFY_ALWAYS_IDS` DM loop for the end-of-run ops summary kept active so Steven still receives the daily summary in Slack
- **`pass` added to empty `if` block in `_route_alerts`** — all code inside the `if report.highest_severity in ("critical", "warning")` block was commented out, causing `IndentationError`; `pass` added to satisfy Python syntax

#### Files Updated
- `controllers/orchestrator.py` — per-brand DM loop commented out; ops summary channel post commented out + replaced with `logger.info`; `pass` added to empty `if` block

#### Still To Do
- [ ] Restore TEST MODE comments in orchestrator.py before go-live
- [ ] Full local end-to-end test with `python main.py`
- [ ] VTR warning threshold decision
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 13 — Rate units bug fixed, test mode, ops summary findings, VTR threshold question
**Date:** 2026-04-15
**Participants:** Claude Code

#### Decisions Made
- **Rate values multiplied by 100 in postgres.py** — DB stores all rates as decimals (1.00 = 100%); thresholds are in percentage points (95.0, 4.0, etc.); this caused every rate metric to classify incorrectly (valid tracking 100% was flagged Critical, bad late shipment rates passed as Healthy); fix is * 100 at read time in postgres.py
- **_fmt_pct fixed in report_generator.py** — was using `:.2%` (Python format that multiplies by 100 again); changed to `:.2f%` to avoid double-multiplication after the postgres.py fix
- **Test mode added to orchestrator.py** — brand channel posts and ops manager DMs commented out with `# TEST MODE` markers; NOTIFY_ALWAYS_IDS DMs and ops channel summary remain active; restore before go-live
- **Ops summary now includes critical findings** — previously only listed brand names; now shows critical/warning findings indented under each critical brand, matching notification format
- **GOOGLE_SERVICE_ACCOUNT_JSON changed to inline JSON** — was a file path to OneDrive (path with spaces causing os.path.exists issues on OneDrive sync); now raw JSON string in .env; google_auth.py already handled this case
- **VTR warning threshold unresolved** — Amazon documents only one hard floor (95%); code warns at < 97%; decision deferred to Steven; low-volume MFN brands can drop 3%+ overnight so buffer has merit

#### Files Updated
- `tools/postgres.py` — multiply all 4 rate metrics by 100 at read time (late shipment, valid tracking, pre-cancel, ODR)
- `tools/report_generator.py` — `_fmt_pct` changed from `:.2%` to `:.2f%`
- `controllers/orchestrator.py` — test mode comments on brand channel + ops manager DM sends; ops summary restored
- `controllers/report_builder.py` — `build_ops_summary` now appends critical/warning findings under each critical brand; added CRITICAL/WARNING imports
- `.claude/hooks/save_session.sh` — single file output, ET timestamp, dedup logic (session 12 work, logged now)
- `info/New_POC_Plan_April13.md` — VTR threshold decision added to Still Waiting On
- `info/SETUP.md` — ODR confirmed, various items updated (session 12 work, logged now)

#### Still To Do
- [ ] Resolve Google Docs API 403 — confirmed key/APIs/project/billing all correct; inline JSON in .env is latest attempt; re-run `python main.py` to verify
- [ ] `python main.py` — full local end-to-end test
- [ ] VTR warning threshold decision — keep 97% buffer or collapse to single 95% critical
- [ ] Restore TEST MODE comments in orchestrator.py before go-live
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 12 — ODR unblocked, save_session.sh cleanup
**Date:** 2026-04-15
**Participants:** Claude Code

#### Decisions Made
- **ODR table confirmed via pgAdmin** — user uploaded pgAdmin export of `sellercentral_sellerperformance_customerserviceperformance_report`; table exists and is queryable; confirmed columns: `order_defect_rate_afn_rate` (numeric), `order_defect_rate_afn_status` (varchar), `download_date`, `account_id`
- **ODR query uncommented in postgres.py** — was blocked pending table name/column confirmation; now live with confirmed values
- **save_session.sh refactored** — removed `claude_session_log` (redundant with `claude_resume`); timestamp now Eastern Time with space between date and time (`2026-04-15 14:30:00 ET`); dedup logic added — if session ID already exists, updates "Last used:" line in place rather than appending a duplicate entry

#### Files Updated
- `.claude/hooks/save_session.sh` — single-file output (claude_resume only), ET timestamp, dedup/update logic
- `tools/postgres.py` — ODR query uncommented; table name and column name placeholders replaced with confirmed values
- `info/SETUP.md` — ODR item marked `[x]`; ODR fix todo in Part 4 checked off
- `info/New_POC_Plan_April13.md` — ODR columns added to Confirmed Facts; "Still Waiting On" updated to reflect only remaining action is uncommenting in postgres.py (now done)

#### Still To Do
- [ ] `python main.py` — local end-to-end test run
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 11 — Google auth Cloud Run fix, Slack chat:write scope fix, deploy doc updated
**Date:** 2026-04-14
**Participants:** Claude Code

#### Decisions Made
- **Shared Google auth helper created** — both sheets_reader.py and report_generator.py used `from_service_account_file()` which breaks on Cloud Run (no local filesystem); new `tools/google_auth.py` detects file path vs JSON string via `os.path.exists()` and calls the correct method; no .env change needed locally
- **Slack bot was missing `chat:write` scope** — local test failed with `missing_scope` / `chat:write:bot`; bot had `im:write` but not `chat:write`; fixed by adding `chat:write` in Slack app OAuth settings and reinstalling to workspace; new token copied to .env
- **CLOUD_RUN_DEPLOY.md Step 5 was missing BRAND_SHEET_ID and PEOPLE_SHEET_ID** — added to `--set-secrets` flag; Step 4 already had them

#### Files Created
- `tools/google_auth.py` — shared credential helper; handles file path (local) and JSON string (Cloud Run) automatically

#### Files Updated
- `tools/sheets_reader.py` — uses `get_service_account_credentials()` from google_auth; removed direct `from_service_account_file()` call
- `tools/report_generator.py` — same; removed april13 uncertainty comment
- `docs/CLOUD_RUN_DEPLOY.md` — added BRAND_SHEET_ID and PEOPLE_SHEET_ID to Step 5 `--set-secrets`

#### Still To Do
- [ ] Confirm `python main.py` passes end-to-end after Slack scope fix
- [ ] ODR: run pgAdmin query to find truncated table name or identify ODR row in sellerperformance_report
- [ ] GCP deployment (Parts 5–6 of SETUP.md) — follow CLOUD_RUN_DEPLOY.md Steps 1–7

---

### Session 10 — Schema created, ON CONFLICT upsert, always-notify DMs, GCP IAM clarified
**Date:** 2026-04-14
**Participants:** Claude Code

#### Decisions Made
- **`walk_the_store` schema created in Postgres** — user ran the SQL in pgAdmin; schema is now live; save_report() will succeed on every run
- **ON CONFLICT upsert added to save_report()** — schema has UNIQUE (brand_code, report_date); without conflict handling a re-run on the same day would crash; added DO UPDATE SET covering all non-key columns so re-runs safely overwrite
- **Two always-notify Slack users hardwired** — U5H5GLJLV and U0AJYBWU03X receive a DM for every warning/critical brand alert AND the ops summary after every run; hardcoded in settings.py as NOTIFY_ALWAYS_IDS (not env var — intentionally fixed)
- **GCP IAM clarified** — "Google Docs + Drive scopes" in CLOUD_RUN_DEPLOY.md are OAuth scopes in code, not IAM roles; actual IAM needed: secretmanager.secretAccessor + run.invoker; Drive/Sheets/Docs access is granted at resource level (share folder/sheets with service account); all confirmed complete
- **GOOGLE_SERVICE_ACCOUNT_JSON path approach needs to change for GCP** — local uses from_service_account_file() with a file path; Cloud Run has no local file; will need to switch to from_service_account_info() reading JSON from Secret Manager before GCP deploy

#### Files Updated
- `tools/postgres.py` — added ON CONFLICT (brand_code, report_date) DO UPDATE SET to save_report() INSERT; updated comment to reflect schema is live
- `config/settings.py` — added NOTIFY_ALWAYS_IDS list with two hardwired Slack user IDs
- `controllers/orchestrator.py` — added settings import; DMs NOTIFY_ALWAYS_IDS on every warning/critical brand alert and ops summary
- `docs/walk_the_store_schema.sql` — header updated to reflect schema is created and live
- `info/SETUP.md` — save_report() test item checked off with updated description
- `info/New_POC_Plan_April13.md` — architecture line updated to reflect schema is live with upserts
- `docs/CLOUD_RUN_DEPLOY.md` — BRAND_SHEET_ID and PEOPLE_SHEET_ID noted as missing from Step 4 secrets and Step 5 --set-secrets (not yet added to file)

#### Still To Do
- [ ] ODR: run pgAdmin query to find truncated table name or identify ODR row in sellerperformance_report
- [ ] Local test: `python main.py`
- [ ] Update CLOUD_RUN_DEPLOY.md Step 4 + Step 5 to add BRAND_SHEET_ID and PEOPLE_SHEET_ID secrets
- [ ] Before GCP deploy: switch sheets_reader.py and report_generator.py from from_service_account_file() to from_service_account_info() reading JSON content from Secret Manager
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 9 — AHR bug fix, iw_account_id from sheet, doc updates
**Date:** 2026-04-14
**Participants:** Claude Code

#### Decisions Made
- **AHR was querying the wrong table (bug)** — `account_health_rating_ahr_status` is in `sellercentral_sellerperformance_policycompliance_report`, not `sellercentral_sellerperformance_report`; the separate AHR query was silently returning None on every run; merged AHR into the existing policycompliance query
- **`sellercentral_sellerperformance_report` is a row-per-metric table** — columns are `id`, `status`, `target_value`, `defects_count`, `report_date`; no AHR or ODR percentage columns; `id` is a metric type identifier; ODR may or may not live here — needs pgAdmin investigation
- **`account_status_changed_report` uses `created_date` not `download_date`** — fixed ORDER BY clause; `download_date` is only confirmed for shipping + policycompliance tables
- **iw_account_id column added to Brand Code Mapping Sheet (col S)** — user added numeric Intentwise account_id directly to the sheet; eliminated the runtime Postgres MWS → account_id lookup entirely; simpler and eliminates dependency on `account_status_changed_report` having rows for every brand
- **ODR still unresolved** — original table name is 65 chars (Postgres limit 63); need pgAdmin query to find truncated name OR confirm if row-per-metric `sellerperformance_report` contains ODR by a specific `id` value

#### Files Updated
- `tools/sheets_reader.py` — removed `_resolve_account_id()` and `get_connection` import; now reads `iw_account_id` (col S) directly from sheet; simpler and more reliable
- `tools/postgres.py` — merged `account_health_rating_ahr_status` into policycompliance query (was querying wrong table); fixed `account_status_changed_report` ORDER BY to use `created_date`
- `info/New_POC_Plan_April13.md` — full update: architecture diagram, confirmed facts table, files list, env vars, deployment steps, Round 5 pivot note
- `info/SETUP.md` — all resolved items checked off; walk_the_store schema section removed; Google Sheets section added; ODR pgAdmin queries documented

#### Still To Do
- [ ] Populate `iw_account_id` (col S) for all active brands in Brand Code Mapping Sheet
- [ ] ODR: run pgAdmin query to find truncated table name or identify ODR row in `sellerperformance_report`
- [ ] Local test: `python main.py`
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 8 — Pre-test audit, Google Sheets account source, column fixes
**Date:** 2026-04-14
**Participants:** Claude Code

#### Decisions Made
- **Replace walk_the_store Postgres schema with Google Sheets** — user already has Brand Code Mapping Sheet and People Lookup Sheet with all brand config data; creating a new Postgres schema + populating it manually is unnecessary overhead for POC; sheets_reader.py replaces postgres.get_active_accounts() entirely
- **account_id resolved at runtime via Postgres lookup** — sheets have MWS seller IDs (bare, e.g. A2M0WKTGB6GQB6); Intentwise tables use numeric bigint account_id; `account_status_changed_report` has both columns and is used as the bridge; DB stores MWS IDs with `_com` suffix so lookup appends it
- **drive_folder_id hardcoded for POC** — all reports go to shared folder `1jsEyn48SYDGxhvAu2-VQve9LP22UNXdp`; per-brand folders deferred to v2
- **AM Slack ID lookup from People Lookup Sheet** — `am_brands` column is comma+space separated brand_codes; `slack_user_id` column is the Slack ID; sheet tab gid=2056938022
- **Teamwork: switch from project-based to task-list-based** — Brand Code Mapping Sheet has 12 individual tw_*_task_list IDs per brand (not project IDs); new get_completed_tasks_by_list() function added; report_builder loops over all 12
- **3 Postgres column names confirmed and fixed** — food_safety_count → food_and_product_safety_issues_defects_count; ip_complaint_count → received_intellectual_property_complaints_defects_count; account_status → current_account_status; account_health_rating_ahr_status was already correct
- **GOOGLE_SERVICE_ACCOUNT_JSON confirmed as file path** — from_service_account_file() in report_generator.py is correct; april13 ambiguity resolved

#### Files Created
- `tools/sheets_reader.py` — reads Brand Code Mapping + People Lookup sheets; resolves account_id; returns List[AccountConfig]

#### Files Updated
- `models/account.py` — full rewrite; new fields match Google Sheets columns; removed id/teamwork_project_id/is_active; added brand_code/mws_seller_id/am_slack_id/tw_task_lists
- `models/report.py` — account_config_id: int → brand_code: str
- `tools/postgres.py` — removed get_active_accounts(); fixed 3 column names; updated save_report() field reference and log line
- `tools/teamwork.py` — added get_completed_tasks_by_list(task_list_id)
- `controllers/report_builder.py` — account_id None guard; loop over tw_task_lists instead of single project ID; brand_code in HealthReport constructor
- `controllers/orchestrator.py` — sheets_reader.get_active_accounts() replaces postgres; account.am_slack_id replaces account.account_manager_slack_id
- `config/settings.py` — added BRAND_SHEET_ID, PEOPLE_SHEET_ID; fixed april13 comment
- `requirements.txt` — added gspread
- `.env.example` — added BRAND_SHEET_ID, PEOPLE_SHEET_ID; fixed stale comment

#### Still To Do
- [ ] `pip install gspread` (new dependency — not yet installed in venv)
- [ ] Add `BRAND_SHEET_ID` and `PEOPLE_SHEET_ID` to `.env`
- [ ] Enable Google Sheets API in GCP Console for `polino-agentic-solutions` project (service account currently only has Docs + Drive)
- [ ] Confirm all active brands have at least one row in `account_status_changed_report` — if a brand has never had a status change event, account_id lookup returns None and brand is skipped entirely
- [ ] ODR query still commented out — need truncated table name from pgAdmin (original name is 65 chars; Postgres truncates at 63); query: `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'sellercentral_sellerperformance_customer%'`
- [ ] Local test: `python main.py` — verify brands load, metrics return, Slack fires, Drive doc created
- [ ] GCP deployment (Parts 5–6 of SETUP.md)

---

### Session 7 — Credentials complete, ready for local test
**Date:** 2026-04-13
**Participants:** Claude Code

#### Decisions Made
- **Teamwork: Collaborator service account** — created a dedicated Collaborator user in Teamwork (not personal token, not full member seat); read-only by design, doesn't consume a paid seat
- **Google service account: reuse existing** — using `polino-agentic-solutions-servi@polino-agentic-solutions.iam.gserviceaccount.com` rather than creating a new one; APIs (Docs + Drive) activated; JSON key downloaded
- **Scopes not added in console** — `_SCOPES` in `report_generator.py` handles auth scopes in code; no console configuration needed
- **VS Code terminal env injection not needed** — `load_dotenv()` in `main.py` handles `.env` loading; VS Code setting irrelevant
- **Postgres queries blocked** — user entered pgAdmin but lacks permissions to view data yet; column name confirmations still pending
- **Ask Emplicit confirmed connected to Drive** — zero setup needed for chat layer

#### Files Updated
- `info/SETUP.md` — Parts 2 and 3 fully checked off; service account details noted

#### Still To Do
- [ ] Share each brand's Drive folder with service account email (Editor permission)
- [ ] Confirm Postgres column names with data team (pending permissions in pgAdmin)
- [ ] Confirm `walk_the_store.account_config` is active with Gilbert; populate with brand data from Google Sheets
- [ ] **Part 4: Local test run** — `pip install -r requirements.txt` then `python main.py`
  - Postgres queries will log gaps until column names confirmed — expected, won't crash
  - Need at least 1 row in `walk_the_store.account_config` before running
- [ ] Parts 5–6: GCP setup, Cloud Run Job, Cloud Scheduler
- [ ] After first live run: test Ask Emplicit → "What was [Brand]'s status today?"

---

### Session 6 — Ask Emplicit confirmed, Drive clarifications, account_config flow
**Date:** 2026-04-13
**Participants:** Claude Code

#### Decisions Made
- **Ask Emplicit = existing Claude Enterprise instance** — not a new claude.ai Project; it is the company-wide "Ask Emplicit" assistant already deployed and accessible from the left sidebar; Drive already connected; zero chat setup needed
- **Part 7 of SETUP.md is complete** — Ask Emplicit connected to Drive confirmed; reports will be available to employees immediately after first live run
- **account_config population flow confirmed** — user has Google Sheets with all brand data (seller ID, Slack channel IDs, Teamwork project IDs, AM Slack IDs, drive_folder_IDs); share sheet when ready → generate SQL INSERTs via `/add-brand` → user runs manually
- **Drive safety verified** — agent never reads, appends, overwrites, or deletes existing Drive files; only creates new doc per brand per run and moves it to the brand folder

#### Files Updated
- `docs/CLAUDE_ENTERPRISE_SETUP.md` — completely rewritten; removed incorrect "create a Project" instructions; now accurately describes Ask Emplicit + Drive connector flow in ~30 lines
- `info/SETUP.md` — Part 7 updated: Ask Emplicit/Drive confirmed checked off; only remaining step is post-run test

#### Still To Do
- [ ] Confirm Postgres column names with data team (seller_id col, marketplace col, date col, 5 metric table column names)
- [ ] Confirm `walk_the_store.account_config` is active with Gilbert; get CREATE TABLE SQL if needed
- [ ] Share Google Sheet with brand data → generate SQL INSERTs for account_config
- [ ] Set up Google service account (Drive + Docs scopes); download SA JSON
- [ ] Fill in `.env` with all credentials
- [ ] Run local test: `python main.py`
- [ ] GCP: enable APIs, Artifact Registry, Secret Manager, Cloud Run Job, Cloud Scheduler
- [ ] After first live run: test Ask Emplicit → "What was [Brand]'s status today?"

---

### Session 5 — Full POC rebuild: Cloud Run Jobs, Google Docs output, Claude Enterprise chat
**Date:** 2026-04-13
**Participants:** Claude Code

#### Decisions Made
- **Intentwise MCP removed** — data read directly from Intentwise-synced Postgres tables (`amazon_source_data`); no direct Intentwise API calls
- **LISTEN/NOTIFY → Cloud Scheduler + Cloud Run Jobs** — Intentwise syncs predictably by 6:45 AM PDT; scheduler fires at 7:00 AM PDT (14:00 UTC); no persistent connection needed, simpler and free
- **Output: Google Doc per brand** — matches example PDF format (header, exec summary, key metrics table, detailed findings, footer); saved to per-brand Drive folder; Slack posts brief notification with link
- **Claude Enterprise for chat** — Emplicit already has Claude Enterprise; Drive connector reads stored reports; no custom Slack bot needed
- **Gradio UI cut** — replaced by `python main.py` for manual runs and Claude Enterprise for viewing; `dashboard.py` deprecated per no-delete policy
- **Cloud Run Jobs over Cloud Run service** — no port, no health check, cleaner for batch work
- **Emplicit domain confirmed: `emplicit.co`** (not `.com`)
- **Schema confirmed: `amazon_source_data`** (also `amazon_marketing_cloud` exists but not used here)
- **Tables are append-only** — new rows inserted daily; `ORDER BY date DESC LIMIT 1` is correct
- **Sync completes by 6:45 AM PDT** — scheduler set to 7:00 AM PDT for 15-min buffer
- **Brand data for account_config lives in user's Google Sheets** — will be provided when ready to populate table; use `/add-brand` to generate INSERT statements

#### Files Created
- `tools/pg_listener.py` — created then immediately deprecated (replaced by Cloud Scheduler)
- `tools/report_generator.py` — Google Doc creator matching example PDF; saves to Drive; returns URL
- `Dockerfile` — Python 3.13-slim, no port, `CMD python main.py`
- `docs/pg_trigger_setup.sql` — created then deprecated (LISTEN/NOTIFY approach dropped)
- `docs/CLOUD_RUN_DEPLOY.md` — Cloud Run Jobs + Cloud Scheduler deploy guide
- `docs/CLAUDE_ENTERPRISE_SETUP.md` — claude.ai Walk the Store Project setup guide
- `info/SETUP.md` — full setup checklist for today: blockers → credentials → local test → GCP → deploy → Claude Enterprise

#### Files Updated
- `main.py` — simplified to ~20 lines: just calls `run_agent()` and exits
- `controllers/orchestrator.py` — calls `report_generator.create_report()` after build; passes `drive_url` to `_route_alerts`
- `views/slack_formatter.py` — added `format_notification(report, drive_url)` for brief Block Kit + Drive link
- `tools/slack_alerts.py` — added optional `drive_url` param
- `tools/postgres.py` — added `get_account_health_metrics()` querying 5 Intentwise tables; `#april13` comments on all unconfirmed column names; schema confirmed
- `controllers/report_builder.py` — removed Intentwise imports; pulls from `postgres.get_account_health_metrics()`
- `config/settings.py` — added `GOOGLE_SERVICE_ACCOUNT_JSON`
- `.env.example` — added Google service account section
- `requirements.txt` — added `google-api-python-client`, `google-auth`, `google-auth-httplib2`; removed `asyncpg`, `gradio`
- `tools/intentwise_mcp.py` — all functions return None (deprecated)
- `views/dashboard.py` — marked deprecated
- `info/New_POC_Plan_April13.md` — updated with final architecture

#### Still To Do
- [ ] Confirm Postgres column names: seller_id col, marketplace col, date col, all 5 metric table column names (ask data team)
- [ ] Confirm `walk_the_store.account_config` is active (ask Gilbert) and get CREATE TABLE SQL if needed
- [ ] Share Google Sheet with brand data → generate SQL INSERTs for account_config
- [ ] Set up Google service account with Drive + Docs scopes; download SA JSON
- [ ] Fill in `.env` with all credentials
- [ ] Run local test: `python main.py`
- [ ] GCP setup: enable APIs, Artifact Registry, Secret Manager, Cloud Run Job, Cloud Scheduler
- [ ] Claude Enterprise: create Walk the Store Project, connect Drive folders, share with ops team
- [ ] Confirm `drive_folder_id` values are in `account_config` for all active brands

---

### Session 4 — NotebookLM removed, schedule corrected
**Date:** 2026-04-10
**Participants:** Claude Code

#### Decisions Made
- NotebookLM fully removed from v1 — not stubbed for later, not replaced. Brand memory / agentic context is explicitly out of scope for POC and v1.
- Reason: NotebookLM Enterprise API has no query/chat endpoint; consumer notebooks inaccessible from any API. Decision: defer brand context entirely rather than substitute.
- Schedule corrected: 6:30 AM ET → 9:00 AM ET (Intentwise data ready at 5 AM PT = 8 AM ET; 9 AM ET gives safe margin).
- `tools/notebooklm.py` preserved per no-delete rule but hollowed out to unconditional `return None`.

#### Files Updated
- `tools/notebooklm.py` — hollowed out; returns None unconditionally, no credential logic
- `controllers/report_builder.py` — removed notebooklm import; brand_ctx = None inline; removed data_gaps "notebooklm" entry
- `config/settings.py` — removed NOTEBOOKLM_API_KEY
- `.env.example` — removed NOTEBOOKLM_API_KEY
- `models/report.py` — updated brand_context field comment to "reserved for future version"
- `PROJECT_SCOPE.md` — removed NotebookLM from tech stack, data sources, build order, blockers; schedule corrected; brand memory moved to "Not in Sprint 1"
- `.claude/commands/notebooklm-ready.md` — prepended deprecation header
- `.claude/skills/env-check/SKILL.md` — removed NOTEBOOKLM_API_KEY treatment
- `.claude/skills/new-session/SKILL.md` — removed NotebookLM from blockers list
- `.claude/commands/claude_skills_list.md` — marked /notebooklm-ready as deprecated

#### Still To Do
- [ ] Step 0 blockers: Intentwise OAuth credentials, Emplicit Postgres dev DB, Teamwork API token
- [ ] Step 9: Dockerfile, Cloud Run, Cloud Scheduler (9:00 AM ET), Secret Manager
- [ ] Step 10: End-to-end test against 2+ real accounts
- [ ] Step 11: Demo + threshold adjustment
- [ ] Intentwise: confirm OAuth token URL and exact MCP field names when credentials arrive

---

### Session 3 — Skills system, GCP setup, and project tooling
**Date:** 2026-04-08
**Participants:** Claude Code

#### Decisions Made
- `.claude/commands/` = explicit slash commands; `.claude/skills/` = semantic Agent Skills (directories with SKILL.md per agentskills.io spec)
- `model:` IS a valid SKILL.md frontmatter field per Anthropic course — used in all skills
- `allowed-tools` is space-delimited per the spec
- 4 skills converted to proper directory/SKILL.md structure: `explain-file`, `new-session`, `memory-update`, `env-check`
- Remaining commands stay as flat `.md` files in `.claude/commands/` for explicit `/` invocation
- Vertex AI not needed — LLM is Anthropic API, brand memory is NotebookLM, no Google-hosted inference
- GCP IAM: 13 roles assigned to service account covering full project lifecycle
- DWD OAuth scopes set in Google Admin for NotebookLM and Drive access
- `memory-update` skill trigger phrases expanded to include "done for the day", "signing off", "calling it", etc.

#### Files Created
- `.claude/skills/explain-file/SKILL.md` — semantic skill, spec-compliant
- `.claude/skills/new-session/SKILL.md` — semantic skill, spec-compliant
- `.claude/skills/memory-update/SKILL.md` — semantic skill, spec-compliant
- `.claude/skills/env-check/SKILL.md` — semantic skill, spec-compliant
- `how_to_build_claude_SKILLS.md` — full reference guide for template repo
- All 10 slash commands in `.claude/commands/` (new-session, step-status, memory-update, commit, env-check, add-brand, slack-preview, deploy-checklist, intentwise-ready, notebooklm-ready, explain-file)
- `.claude/commands/claude_skills_list.md` — skills index

#### Files Updated
- `CLAUDE.md` — added Section 14: skills management standards
- `memory-update/SKILL.md` — added "done for the day" and related trigger phrases
- `requirements.txt` + `pyproject.toml` — added `huggingface_hub` as explicit dependency

#### Still To Do
- [ ] Step 0 blockers: Intentwise OAuth creds, Postgres dev DB, Teamwork token, NotebookLM Enterprise API
- [ ] Step 9: Dockerfile, Cloud Run, Cloud Scheduler (6:30 AM ET), Secret Manager
- [ ] Step 10: End-to-end test against 2+ real accounts
- [ ] Step 11: Demo + threshold adjustment
- [ ] Intentwise: confirm OAuth token URL and exact MCP field names when credentials arrive

---

### Session 2 — Steps 2–8: Full Application Build
**Date:** 2026-04-08
**Participants:** Claude Code (AI Lead: Steven Polino)

#### Decisions Made
- All credentials pulled exclusively from `config/settings.py` → `.env`; no file requires live credentials to be structured — they activate when `.env` is filled
- Intentwise MCP client uses JSON-RPC over HTTP with Bearer token auth; OAuth token is cached in-memory per run
- Teamwork auth uses Basic auth with API token as the username (password blank) — standard Teamwork pattern
- NotebookLM is a deliberate stub (`tools/notebooklm.py`) — returns `None` gracefully until Enterprise API access is confirmed
- Orchestrator failure model: per-account errors are caught and logged; run continues for all remaining accounts; daily summary always attempted
- Slack alert routing: critical → channel post + AM DM; warning → channel post only; healthy → silent
- `views/dashboard.py` can be launched independently (`python views/dashboard.py`) or imported and launched by `main.py`

#### Files Created
- `models/account.py` — AccountConfig Pydantic model
- `models/findings.py` — Finding Pydantic model
- `models/report.py` — HealthReport Pydantic model
- `tools/postgres.py` — get_active_accounts(), save_report()
- `tools/intentwise_mcp.py` — OAuth + 5 MCP query methods
- `tools/teamwork.py` — get_completed_tasks()
- `tools/slack_alerts.py` — post_to_channel(), send_dm(), post_ops_summary()
- `tools/notebooklm.py` — stub, returns None
- `controllers/classifier.py` — 8 metric classifiers + roll-up
- `controllers/report_builder.py` — build_brand_report(), build_ops_summary()
- `controllers/orchestrator.py` — run_agent() main loop
- `views/slack_formatter.py` — format_brand_report() → Block Kit
- `views/dashboard.py` — Gradio manual trigger + account viewer

#### Files Updated
- `main.py` — wired to call orchestrator.run_agent()

#### Still To Do
- [ ] Step 0 blockers: Intentwise OAuth creds, Postgres dev DB, Teamwork token, NotebookLM Enterprise API
- [ ] Intentwise: confirm exact OAuth token URL (`INTENTWISE_TOKEN_URL` in intentwise_mcp.py may need update)
- [ ] Intentwise: confirm exact field names returned by each MCP table query (report_builder.py uses assumed keys)
- [ ] Intentwise: replace `config/intentwise_preferences.yaml` placeholder with actual file from Intentwise
- [ ] Step 9: Dockerfile, Cloud Run, Cloud Scheduler (6:30 AM ET), Secret Manager
- [ ] Step 10: End-to-end test against 2+ real accounts
- [ ] Step 11: Demo + threshold adjustment

---

### Session 1 — Step 1: Project Setup
**Date:** 2026-04-08
**Participants:** Claude Code (AI Lead: Steven Polino)

#### Decisions Made
- Python 3.13 pinned (template was already 3.13; exceeds 3.11+ requirement in scope)
- `main.py` created as the real entry point per PROJECT_SCOPE.md; `app.py` left as-is (template reference file)
- `config/settings.py` reads all env vars at import time and exposes typed constants
- `config/thresholds.py` defines all severity cutoffs as named constants
- `.claude/hooks/save_session.sh` created at the correct path referenced by settings.json

#### Files Created
- `main.py`, `requirements.txt`, `.python-version`
- `config/__init__.py`, `config/settings.py`, `config/thresholds.py`, `config/intentwise_preferences.yaml`
- `tools/__init__.py`
- `.claude/hooks/save_session.sh`

#### Files Updated
- `.env.example` — all 13 keys from PROJECT_SCOPE.md
- `pyproject.toml` — project name, description, full dependency list
- `.gitignore` — added `claude_resume` and `claude_session_log`
- `memory.md` — initialized

---

## Standards Reference
Full coding standards, Claude behavior rules, and git workflow are in `CLAUDE.md`.
