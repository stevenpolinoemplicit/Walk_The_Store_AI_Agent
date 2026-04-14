# SETUP.md — Walk the Store: April 13 Setup Plan

> Code is built. This is the checklist to go from built → running.
> Work top to bottom. Blocked items are marked — get answers before proceeding past them.

---

## PART 1 — Get Answers (Blockers First)

These must be resolved before any live testing. Get these from the data team and boss today.

### Data Team Questions (Postgres)
- [x] What is the exact Postgres **schema name** for Intentwise-synced tables? → **`amazon_source_data`** (confirmed; also `amazon_marketing_cloud` exists but not used here)
- [x] What is the **seller identifier column** name? → **`account_id`** (bigint) — confirmed from shipping table
- [x] What is the **marketplace column** name? → **`country_code`** (varchar) — confirmed from shipping table
- [x] What is the **date column** name for `ORDER BY`? → **`download_date`** (date) — confirmed from shipping table
- [ ] Confirm remaining column names (3 tables still unconfirmed — query each in pgAdmin):
  - [x] `sellercentral_sellerperformance_shippingperformance_report` → `late_shipment_rate_rate`, `valid_tracking_rate_rate`, `pre_fulfillment_cancellation_rate_rate` ✅
  - [~] `sellercentral_sellerperformance_customerserviceperformance_report` → **TABLE NOT FOUND** — name is 65 chars, Postgres truncates at 63. Ask data team for the actual table name. ODR metric is currently skipped.
  - [ ] `sellercentral_sellerperformance_policycompliance_report` → confirm: `food_safety_count`, `ip_complaint_count`
  - [ ] `sellercentral_sellerperformance_report` → confirm: `account_health_rating_ahr_status`
  - [ ] `sellercentral_account_status_changed_report` → confirm: `account_status`
- [x] What time does Intentwise **complete its daily sync**? → **6:45 AM PDT. Scheduler set to 7:00 AM PDT (14:00 UTC).**
- [ ] Are `drive_folder_id` values populated in `walk_the_store.account_config` for active brands?

### walk_the_store Schema (New — Must Be Created Manually)
- `walk_the_store` schema does **not** exist in Postgres yet.
- SQL to create it is in `docs/walk_the_store_schema.sql` — run manually in pgAdmin.
- [ ] Run `docs/walk_the_store_schema.sql` in pgAdmin (creates schema + `account_config` + `daily_health_reports`)
- [ ] Insert at least 1 test brand row into `walk_the_store.account_config` before running `python main.py`

### Gilbert Questions
- [ ] Confirm `walk_the_store.account_config` table exists (after running schema SQL above) and has at least 1 test brand row
- [x] What is the Emplicit **Google Workspace domain**? → **`emplicit.co`** (confirmed)

---

## PART 2 — Google Service Account Setup

- [x] Service account: `polino-agentic-solutions-servi@polino-agentic-solutions.iam.gserviceaccount.com`
- [x] APIs activated: Google Docs + Google Drive
- [x] JSON key downloaded and path added to `.env`
- [x] Brand Drive folders shared with service account (Editor)

---

## PART 3 — Fill in .env

- [x] `ANTHROPIC_API_KEY`
- [x] `EMPLICIT_PG_HOST` / `EMPLICIT_PG_DB` / `EMPLICIT_PG_USER` / `EMPLICIT_PG_PASSWORD`
- [x] `SLACK_BOT_TOKEN` / `SLACK_OPS_CHANNEL`
- [x] `TEAMWORK_DOMAIN` / `TEAMWORK_API_TOKEN` — Teamwork Collaborator service account
- [x] `GOOGLE_SERVICE_ACCOUNT_JSON`

---

## PART 4 — Local Test Run

Before touching GCP, confirm the agent runs locally end-to-end.

- [ ] `pip install -r requirements.txt`
- [ ] `python main.py`
- [ ] Verify in output:
  - [ ] Connects to Postgres — fetches active accounts
  - [ ] Queries Intentwise-synced tables — pulls metrics
  - [ ] Classifies severity correctly
  - [ ] Creates Google Doc — appears in Drive
  - [ ] Slack notification sent with Drive link
  - [ ] Report saved to `walk_the_store.daily_health_reports`
- [ ] Fix any `#april13 waiting on confirmation` issues found during this run

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
- [ ] Set Cloud Scheduler trigger (use sync completion time confirmed in Part 1)
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
