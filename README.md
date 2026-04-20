# Walk the Store AI Agent (claude_code)

Autonomous daily agent that reads Amazon account health data for all Emplicit brands, classifies severity, generates Google Doc reports saved to Drive, and delivers a cross-brand ops summary to Slack. Runs every day at 7:00 AM Los Angeles time via Cloud Scheduler + Cloud Run Jobs on GCP.

**Owner:** Steven Polino | **Status:** Live — deployed to GCP, running daily

---

## What It Does

1. **Reads** brand config from Google Sheets (Brand Code Mapping Sheet)
2. **Queries** Intentwise-synced Postgres tables for 8 Amazon health metrics per brand
3. **Checks** Teamwork task lists for open and recently completed tasks per brand
4. **Classifies** each brand as Critical, Warning, or Healthy using Amazon's official thresholds
5. **Generates** a Google Doc report per brand — written by Claude (Sonnet executor + Opus advisor) — saved to a dated subfolder (`April 20 2026`) inside the brand's Drive folder, shared with the emplicit.co domain
6. **Posts** a cross-brand daily ops summary to the Slack ops channel
7. **DMs** each ops manager a filtered summary of only their brands
8. **DMs** Steven, Adam, and Emily the full cross-brand summary with a Drive link
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
        │   ├── Generate report narrative via Claude (Sonnet + Opus advisor)
        │   ├── Create Google Doc → save to dated subfolder in Drive
        │   └── Save report to Postgres (walk_the_store schema)
        │
        └── After all brands:
            ├── Post ops summary → Slack ops channel
            ├── Create ops summary Google Doc → Drive
            ├── DM full summary → Steven + Adam + Emily (always-notify)
            ├── DM filtered summary → each ops manager (their brands only)
            └── On weekends: DM on-call team instead of ops managers
                (Axel, Kay, Milagros, Albenis)
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
├── info/
│   ├── walk_the_store_schema.sql  # Postgres schema for walk_the_store.daily_health_reports
│   ├── CLOUD_RUN_DEPLOY.md        # Step-by-step GCP deployment guide
│   ├── CLAUDE_ENTERPRISE_SETUP.md # Ask Emplicit / Drive connector setup
│   └── SETUP.md                   # Setup checklist (local → GCP)
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
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account key — full JSON as a single line (Cloud Run reads from Secret Manager) |
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

Deployed as a **Cloud Run Job** triggered by **Cloud Scheduler** at 7:00 AM Los Angeles time (`0 7 * * *` — handles daylight saving automatically).

Follow `info/CLOUD_RUN_DEPLOY.md` for the full step-by-step guide covering:
- GCP project setup and IAM
- Artifact Registry + Docker build
- Secret Manager configuration
- Cloud Run Job creation
- Cloud Scheduler configuration

---

## Report Output

Each daily run produces:
- **Per-brand Google Doc** — titled `{Brand Name} - Month DD YYYY - Amazon Health Report`, saved inside a `Month DD YYYY` dated subfolder within the brand's Drive folder
- **Ops summary Google Doc** — titled `Walk the Store - Month DD YYYY - Daily Ops Summary`, saved inside a `Month DD YYYY` dated subfolder within the ops Drive folder

The dated subfolder is created automatically on the first report of the day and reused for all subsequent reports in the same run.

### Report Narrative (Advisor Strategy)

Report narratives are written by Claude using the **advisor strategy**: Sonnet (`claude-sonnet-4-6`) drives the full run as the executor; Opus (`claude-opus-4-6`) is consulted as the advisor (up to 3 times per report) when Sonnet encounters complex or multi-issue situations. This produces near-Opus-quality analysis at near-Sonnet cost.

- **LLM sections:** Executive Summary and Key Findings prose
- **Deterministic sections:** Key Metrics table (exact values), Detailed Findings, Teamwork Activity, Footer
- **Fallback:** if the API call fails for any reason, the templated version is used — the report always ships

---

## Google Sheets Dependencies

| Sheet | Purpose |
|---|---|
| Brand Code Mapping Sheet | Active brands, seller IDs, Teamwork task list IDs, iw_account_id, Drive folder ID |
| People Lookup Sheet | Slack user IDs, ops manager brand assignments (`ops_brands` column I) |

The service account email must be shared as **Viewer** on both Google Sheets, and the impersonated Workspace user must have **Editor** access to the Drive folders where reports are saved.

> **Note:** All secrets stored in Secret Manager must be stored without trailing newlines. Use `printf 'value' | gcloud secrets versions add SECRET_NAME --data-file=-` — never `echo`.

---

## Slack Routing

- **Ops channel** — full cross-brand daily summary (all brands, all severities)
- **Steven + Adam + Emily DM** — full summary + Drive link to ops summary doc (every day)
- **Each ops manager DM** — filtered summary showing only their brands (weekdays only)
- **Weekend on-call DM** — Axel, Kay, Milagros, Albenis receive the summary on Sat/Sun instead of ops managers
- **Individual brand alerts** — disabled (summary-only design)
- **Postgres unreachable** — error DM sent to Steven + Adam + Emily instead of a false report

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
