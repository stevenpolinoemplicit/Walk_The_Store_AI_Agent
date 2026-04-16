# Walk the Store AI Agent (claude_code)

Autonomous daily agent that reads Amazon account health data for all Emplicit brands, classifies severity, generates Google Doc reports saved to Drive, and delivers a cross-brand ops summary to Slack. Runs every day at 7:00 AM PDT via Cloud Scheduler + Cloud Run Jobs.

**Owner:** Steven Polino | **Approvers:** Adam Weiler, Emily Lindahl

---

## What It Does

1. **Reads** brand config from Google Sheets (Brand Code Mapping Sheet)
2. **Queries** Intentwise-synced Postgres tables for 8 Amazon health metrics per brand
3. **Checks** Teamwork task lists for open and recently completed tasks per brand
4. **Classifies** each brand as Critical, Warning, or Healthy using Amazon's official thresholds
5. **Generates** a Google Doc report per brand, saved to Drive, shared with the emplicit.co domain
6. **Posts** a cross-brand daily ops summary to the Slack ops channel
7. **DMs** each ops manager a filtered summary of only their brands
8. **DMs** Steven + Adam the full cross-brand summary with a Drive link
9. **Saves** all report data to the `walk_the_store.daily_health_reports` Postgres table

---

## Architecture

```
Cloud Scheduler (7:00 AM PDT)
        │
        ▼
Cloud Run Job → python main.py
        │
        ├── Google Sheets ─────── Brand config + people lookup
        ├── Postgres (amazon_source_data) ── Intentwise health metrics (read)
        ├── Teamwork API ─────── Open + completed tasks per brand
        │
        ├── Per brand:
        │   ├── Classify severity (Critical / Warning / Healthy)
        │   ├── Create Google Doc → save to Drive folder
        │   └── Save report to Postgres (walk_the_store schema)
        │
        └── After all brands:
            ├── Post ops summary → Slack ops channel
            ├── Create ops summary Google Doc → Drive
            ├── DM full summary → Steven + Adam
            └── DM filtered summary → each ops manager (their brands only)
```

**Metrics checked per brand:**

| Metric | Warning | Critical |
|---|---|---|
| Late Shipment Rate | ≥ 2% | ≥ 4% |
| Valid Tracking Rate | < 98% | < 95% |
| Pre-fulfillment Cancel Rate | ≥ 1% | ≥ 2.5% |
| Order Defect Rate | ≥ 0.5% | ≥ 1% |
| Account Health Rating | Fair | At Risk / Critical |
| Food/Product Safety | — | Any violation |
| IP Complaints | — | Any complaint |
| Account Status | — | AT_RISK / SUSPENDED / DEACTIVATED |

---

## Project Structure

```
Walk_The_Store_AI_Agent/
├── main.py                        # Entry point — calls orchestrator.run_agent()
├── config/
│   ├── settings.py                # All env vars loaded here; never read os.environ directly elsewhere
│   └── thresholds.py              # Amazon severity thresholds as named constants
├── models/
│   ├── account.py                 # AccountConfig — one brand loaded from Sheets
│   ├── findings.py                # Finding — one classified metric result
│   └── report.py                  # HealthReport — complete daily snapshot for one brand
├── controllers/
│   ├── orchestrator.py            # Main run loop — coordinates all tools, routing, and summary
│   ├── report_builder.py          # Builds HealthReport per brand; generates cross-brand summary
│   └── classifier.py              # 8 metric classifiers + severity roll-up
├── views/
│   └── slack_formatter.py         # Formats reports as Slack Block Kit messages
├── tools/
│   ├── postgres.py                # Reads Intentwise metrics; saves daily reports
│   ├── sheets_reader.py           # Loads active brands from Brand Code Mapping Sheet
│   ├── report_generator.py        # Creates Google Docs (per-brand + ops summary)
│   ├── google_auth.py             # Shared Google auth helper (file path + JSON string + DWD)
│   ├── slack_alerts.py            # Posts to channels, sends DMs
│   └── teamwork.py                # Fetches open + completed tasks per task list
├── docs/
│   ├── walk_the_store_schema.sql  # Postgres schema for walk_the_store.daily_health_reports
│   ├── CLOUD_RUN_DEPLOY.md        # Step-by-step GCP deployment guide
│   └── CLAUDE_ENTERPRISE_SETUP.md # Ask Emplicit / Drive connector setup
├── Dockerfile                     # Python 3.13-slim, CMD python main.py
├── CLAUDE.md                      # AI coding standards (auto-loaded by Claude Code)
├── pyproject.toml                 # Python project config + Black settings
├── .env.example                   # All required env vars with descriptions
└── requirements.txt               # Python dependencies
```

---

## Getting Started

### 1. Clone and set up environment

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Fill in .env with real values — never commit this file
```

**Required env vars:**

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `EMPLICIT_PG_HOST` | Postgres host |
| `EMPLICIT_PG_PORT` | Postgres port (default 5432) |
| `EMPLICIT_PG_DB` | Postgres database name |
| `EMPLICIT_PG_USER` | Postgres username |
| `EMPLICIT_PG_PASSWORD` | Postgres password |
| `SLACK_BOT_TOKEN` | Slack bot token (needs `chat:write`, `im:write`) |
| `SLACK_OPS_CHANNEL` | Slack channel ID for daily ops summary |
| `TEAMWORK_DOMAIN` | Teamwork subdomain (e.g. `emplicit` for `emplicit.teamwork.com`) |
| `TEAMWORK_API_TOKEN` | Teamwork API token (Collaborator account) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account key — paste the full JSON as a single line |
| `GOOGLE_IMPERSONATION_EMAIL` | Workspace user email for DWD impersonation (required for emplicit.co) |
| `BRAND_SHEET_ID` | Google Sheet ID for Brand Code Mapping Sheet |
| `PEOPLE_SHEET_ID` | Google Sheet ID for People Lookup Sheet |
| `DRIVE_OPS_FOLDER_ID` | Drive folder ID where daily ops summary docs are saved |

### 3. Google Auth Setup (required for emplicit.co Workspace)

The service account uses **Domain-Wide Delegation** to access Docs and Drive:

1. In Google Admin Console → **Security → API controls → Domain-wide delegation**
2. Add the service account client ID with these scopes:
   - `https://www.googleapis.com/auth/documents`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/spreadsheets.readonly`
   - `https://www.googleapis.com/auth/drive.readonly`
3. Set `GOOGLE_IMPERSONATION_EMAIL` in `.env` to a real Workspace user who has Drive access

### 4. Run locally

```bash
python main.py
```

Check logs for:
- `Google Doc created: doc_id=...` — Drive is working
- `Ops summary posted to Slack ops channel` — channel post working
- `Filtered ops summary DM sent to ops manager` — per-manager routing working

---

## Deployment

Deployed as a **Cloud Run Job** triggered by **Cloud Scheduler** at 14:00 UTC (7:00 AM PDT).

Follow `docs/CLOUD_RUN_DEPLOY.md` for the full step-by-step guide covering:
- GCP project setup and IAM
- Artifact Registry + Docker build
- Secret Manager configuration
- Cloud Run Job creation
- Cloud Scheduler configuration

---

## Google Sheets Dependencies

| Sheet | Purpose |
|---|---|
| Brand Code Mapping Sheet | Active brands, seller IDs, Teamwork task list IDs, iw_account_id, Drive folder ID |
| People Lookup Sheet | Slack user IDs, ops manager brand assignments (`ops_brands` column I) |

The service account email must be shared as **Editor** on the Brand Code Mapping Sheet and as **Viewer** on any Drive folders where reports are saved.

---

## Slack Routing

- **Ops channel** — full cross-brand daily summary (all brands, all severities)
- **Steven + Adam DM** — full summary + Drive link to ops summary doc
- **Each ops manager DM** — filtered summary showing only their brands
- **Individual brand alerts** — disabled (summary-only design)

---

## Postgres Schemas

| Schema | Purpose |
|---|---|
| `amazon_source_data` | Intentwise-synced Amazon Seller Central tables (read-only by agent) |
| `walk_the_store` | Agent-owned schema; `daily_health_reports` table stores one row per brand per day |

The `daily_health_reports` table uses an upsert on `(brand_code, report_date)` — re-running the agent on the same day safely overwrites the previous run's data.

---

## Standards

This project follows Emplicit engineering standards defined in `CLAUDE.md`. All contributors must read `CLAUDE.md` before writing code.

---

## Running Tests

```bash
pytest
```
