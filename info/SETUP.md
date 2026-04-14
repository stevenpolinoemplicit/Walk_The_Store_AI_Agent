# SETUP.md — Walk the Store: Setup Checklist
> Last updated: April 14, 2026 — Session 8
> Code is built. This is the checklist to go from built → running.
> Work top to bottom. Blocked items are marked — get answers before proceeding past them.

---

## PART 1 — Confirm Data (Blockers First)

### Postgres Column Names
- [x] Schema: `amazon_source_data` ✅
- [x] Seller identifier: `account_id` (bigint) ✅
- [x] Marketplace: `country_code` (varchar) ✅
- [x] Date column (shipping + policycompliance): `download_date` ✅
- [x] Date column (account_status_changed): `created_date` ✅
- [x] Shipping table columns: `late_shipment_rate_rate`, `valid_tracking_rate_rate`, `pre_fulfillment_cancellation_rate_rate` ✅
- [x] Policy compliance columns: `food_and_product_safety_issues_defects_count`, `received_intellectual_property_complaints_defects_count` ✅
- [x] AHR column: `account_health_rating_ahr_status` (in policycompliance table) ✅
- [x] Account status column: `current_account_status` ✅
- [~] ODR table — `sellercentral_sellerperformance_customerserviceperformance_report` name is 65 chars (Postgres limit is 63). Run this in pgAdmin to find the actual table name:
  ```sql
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema = 'amazon_source_data'
  AND table_name LIKE 'sellercentral_sellerperformance_c%';
  ```
  Alternatively, check if ODR exists in `sellercentral_sellerperformance_report` (row-per-metric table) — run:
  ```sql
  SELECT id, status, target_value, defects_count, report_date
  FROM amazon_source_data.sellercentral_sellerperformance_report
  WHERE account_id = 2029940
  ORDER BY report_date DESC
  LIMIT 20;
  ```

### Google Sheets (Brand Config — replaces walk_the_store Postgres schema)
- [x] Brand Code Mapping Sheet shared with service account ✅
- [x] People Lookup Sheet shared with service account ✅
- [ ] Column `iw_account_id` (col S) populated for all active brands in Brand Code Mapping Sheet

---

## PART 2 — Google Service Account Setup

- [x] Service account: `polino-agentic-solutions-servi@polino-agentic-solutions.iam.gserviceaccount.com`
- [x] APIs activated: Google Docs, Google Drive, Google Sheets
- [x] JSON key downloaded and path added to `.env`
- [x] Brand Drive folders shared with service account (Editor)
- [x] Both Google Sheets shared with service account (Viewer)

---

## PART 3 — Fill in .env

- [x] `ANTHROPIC_API_KEY`
- [x] `EMPLICIT_PG_HOST` / `EMPLICIT_PG_DB` / `EMPLICIT_PG_USER` / `EMPLICIT_PG_PASSWORD`
- [x] `SLACK_BOT_TOKEN` / `SLACK_OPS_CHANNEL`
- [x] `TEAMWORK_DOMAIN` / `TEAMWORK_API_TOKEN` — Teamwork Collaborator service account
- [x] `GOOGLE_SERVICE_ACCOUNT_JSON`
- [x] `BRAND_SHEET_ID`
- [x] `PEOPLE_SHEET_ID`

---

## PART 4 — Local Test Run

Before touching GCP, confirm the agent runs locally end-to-end.

- [x] `pip install -r requirements.txt` (gspread installed)
- [ ] `python main.py`
- [ ] Verify in logs:
  - [ ] Connects to Google Sheets — loads active brands (check for brand names in logs)
  - [ ] No "iw_account_id missing" warnings (all brands in sheet have col S populated)
  - [ ] Queries Intentwise-synced tables — pulls metrics (no column errors)
  - [ ] Classifies severity correctly
  - [ ] Creates Google Doc — appears in shared POC Drive folder
  - [ ] Slack notification sent with Drive link
  - [ ] `save_report()` fails gracefully — schema not created, confirm error is caught not crashed
- [ ] Fix ODR once table name is confirmed (see Part 1)

---

## PART 5 — GCP Setup

- [ ] Create or confirm GCP project exists
- [ ] Enable APIs:
  ```
  gcloud services enable run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com
  ```
- [ ] Create Artifact Registry repo (see `docs/CLOUD_RUN_DEPLOY.md` Step 2)
- [ ] Store all `.env` values as Secret Manager secrets (see `docs/CLOUD_RUN_DEPLOY.md` Step 4)

---

## PART 6 — Build & Deploy

Follow `docs/CLOUD_RUN_DEPLOY.md` steps 3–6:

- [ ] Build and push Docker image: `gcloud builds submit --tag $IMAGE .`
- [ ] Create Cloud Run Job: `gcloud run jobs create ...`
- [ ] Set Cloud Scheduler trigger (7:00 AM PDT — `0 14 * * *` UTC)
- [ ] Test manual execution: `gcloud run jobs execute walk-the-store ...`
- [ ] Verify logs show clean run end-to-end

---

## PART 7 — Ask Emplicit (Claude Enterprise)

No code required. Reports land in Drive automatically after each agent run.

- [x] Ask Emplicit is connected to Google Drive — confirmed. No setup needed.
- [ ] Test: after first live agent run, open Ask Emplicit → ask "What was [Brand]'s status today?" → it should cite the Drive report

---

## Status Legend
- [ ] Not started
- [~] In progress / blocked
- [x] Done
