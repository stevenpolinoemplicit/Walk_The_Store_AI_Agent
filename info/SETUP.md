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
- [x] ODR table — `sellercentral_sellerperformance_customerserviceperformance_report` ✅ confirmed via pgAdmin query. Columns: `order_defect_rate_afn_rate` (numeric), `order_defect_rate_afn_status` (varchar: GOOD/AT_RISK/CRITICAL), `download_date` (date), `account_id` (bigint)

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
- [x] `GOOGLE_IMPERSONATION_EMAIL` — Workspace user email the service account impersonates via DWD
- [x] `DRIVE_OPS_FOLDER_ID` — Drive folder ID for daily ops summary docs

---

## PART 4 — Local Test Run

Before touching GCP, confirm the agent runs locally end-to-end.

- [x] `pip install -r requirements.txt` (gspread installed)
- [x] `python main.py`
- [x] Verify in logs:
  - [x] Connects to Google Sheets — loads active brands (check for brand names in logs)
  - [x] No "iw_account_id missing" warnings (all brands in sheet have col S populated)
  - [x] Queries Intentwise-synced tables — pulls metrics (no column errors)
  - [x] Classifies severity correctly
  - [x] Creates Google Doc — appears in shared POC Drive folder
  - [x] Slack notification sent with Drive link
  - [x] `save_report()` writes to walk_the_store.daily_health_reports — schema created, upserts on (brand_code, report_date)
- [x] ODR query uncommented and implemented in `postgres.py` ✅

---

## PART 5 — GCP Setup

- [x] Create or confirm GCP project exists
- [x] Enable APIs:
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
