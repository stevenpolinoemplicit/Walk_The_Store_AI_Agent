# SETUP.md — Walk the Store: April 13 Setup Plan

> Code is built. This is the checklist to go from built → running.
> Work top to bottom. Blocked items are marked — get answers before proceeding past them.

---

## PART 1 — Get Answers (Blockers First)

These must be resolved before any live testing. Get these from the data team and boss today.

### Data Team Questions (Postgres)
- [ ] What is the exact Postgres **schema name** for Intentwise-synced tables? (assumed: `amazon_source_data`)
- [ ] What is the **seller identifier column** name in each table? (assumed: `seller_id`)
- [ ] What is the **marketplace column** name in each table? (assumed: `marketplace`)
- [ ] What is the **date column** name used for `ORDER BY` in each table? (assumed: `date`)
- [ ] Confirm column names in each of these 5 tables:
  - `sellercentral_sellerperformance_shippingperformance_report` — cols: `late_shipment_rate`, `valid_tracking_rate`, `pre_fulfillment_cancel_rate`
  - `sellercentral_sellerperformance_customerserviceperformance_report` — col: `order_defect_rate`
  - `sellercentral_sellerperformance_policycompliance_report` — cols: `food_safety_count`, `ip_complaint_count`
  - `sellercentral_sellerperformance_report` — col: `account_health_rating_ahr_status`
  - `sellercentral_account_status_changed_report` — col: `account_status`
- [x] What time does Intentwise **complete its daily sync**? → **6:45 AM PDT. Scheduler set to 7:00 AM PDT (14:00 UTC).**
- [ ] Are `drive_folder_id` values populated in `walk_the_store.account_config` for active brands?

### Boss Questions
- [ ] Confirm `walk_the_store.account_config` table is active and has at least 1 test brand row
- [ ] What is the Emplicit **Google Workspace domain**? (e.g. `emplicit.com` — needed for Drive sharing)

---

## PART 2 — Google Service Account Setup

- [ ] Go to [Google Cloud Console](https://console.cloud.google.com) → IAM → Service Accounts
- [ ] Create a service account: `walk-the-store-sa`
- [ ] Grant it these API scopes / roles:
  - Google Docs API (`https://www.googleapis.com/auth/documents`)
  - Google Drive API (`https://www.googleapis.com/auth/drive`)
- [ ] Download the JSON key file → save locally as `sa.json` (never commit this)
- [ ] Add `sa.json` path to your local `.env` as `GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/sa.json`

---

## PART 3 — Fill in .env

Copy `.env.example` to `.env` and fill in every key:

```
cp .env.example .env
```

- [ ] `ANTHROPIC_API_KEY` — from console.anthropic.com
- [ ] `EMPLICIT_PG_HOST` / `EMPLICIT_PG_DB` / `EMPLICIT_PG_USER` / `EMPLICIT_PG_PASSWORD`
- [ ] `SLACK_BOT_TOKEN` — Walk the Store Slack bot token
- [ ] `SLACK_OPS_CHANNEL` — ops channel ID (not name — the C... ID)
- [ ] `TEAMWORK_DOMAIN` / `TEAMWORK_API_TOKEN`
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON` — path to `sa.json` from Part 2

Run `/env-check` in Claude Code to verify all keys are set.

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

## PART 7 — Claude Enterprise Setup

Follow `docs/CLAUDE_ENTERPRISE_SETUP.md`:

- [ ] Create **Walk the Store Agent** Project in claude.ai
- [ ] Add system prompt (copy from `docs/CLAUDE_ENTERPRISE_SETUP.md`)
- [ ] Connect Google Drive folder(s) where reports are saved
- [ ] Share project with ops team
- [ ] Test: ask "What was [Brand]'s status today?" — Claude should cite the Drive report

---

## Status Legend
- [ ] Not started
- [~] In progress / blocked
- [x] Done
