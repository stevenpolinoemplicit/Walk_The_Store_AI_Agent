# PROJECT_SCOPE.md — Walk the Store AI Agent

> This file contains all project-specific context, architecture, data sources, and build order.
> Claude Code must read this file at the start of every session alongside CLAUDE.md.
> For coding standards, behavior rules, and git workflow, see CLAUDE.md.

---

## Project Overview

An autonomous AI agent that runs daily at 7:00 AM Los Angeles time. It checks Amazon account health for multiple client brands, classifies issues by severity, cross-references Teamwork for resolution activity, and delivers actionable reports via Slack.

**Sprint 1 Scope:** Account Health only.
**Owner:** Steven Polino
**Approvers:** Adam Weiler, Emily Lindahl

---

## What Sprint 1 Delivers

- Shipping metrics, policy compliance, customer service (ODR, A-to-Z), account health rating, account status alerts
- Auto-classification: 🔴 Critical / 🟡 Warning / 🟢 Healthy
- Teamwork read-only — shows completed tasks per brand
- Slack alerts: channel + DM on critical, channel only on warning
- Per-brand daily report + cross-brand summary to ops channel
- Graceful handling of missing data (no crashes)

## Not in Sprint 1

Inventory health, inbound/shipment status, performance notifications, case log review, Walmart checks, PDF reports, Teamwork task creation, employee activity tracking, brand memory / per-brand context.

---

## Tech Stack

| Component | Tool |
|---|---|
| Language | Python 3.11+ |
| Agent Framework | Anthropic Python SDK (`anthropic`) |
| LLM | Claude Sonnet |
| Amazon Data | Emplicit Postgres — Intentwise-synced tables (`amazon_source_data` schema) |
| Operational Data | Emplicit PostgreSQL (`psycopg2`) |
| Task Tracking | Teamwork API via `httpx` (read-only) |
| Alerts | Slack (`slack_sdk`) |
| Data Validation | `pydantic` |
| Hosting | Google Cloud (Cloud Run + Cloud Scheduler) |
| Containerization | Docker |
| Formatter | Black (see CLAUDE.md) |
| Testing | pytest (see CLAUDE.md) |

---

## MVC Project Structure

Per CLAUDE.md, this project follows MVC architecture.

```
walk-the-store/
├── .env                          # Secrets (never commit)
├── .env.example                  # Placeholder keys
├── .gitignore
├── requirements.txt
├── Dockerfile
├── README.md
├── CLAUDE.md                     # Company-wide standards
├── PROJECT_SCOPE.md              # This file
├── memory.md                     # Session log
├── main.py                       # Entry point (scheduled or manual)
│
├── config/
│   ├── settings.py               # Environment config loader
│   ├── thresholds.py             # Severity threshold definitions
│   └── intentwise_preferences.yaml  # DEPRECATED — preserved per no-delete policy
│
├── models/
│   ├── account.py                # AccountConfig pydantic model
│   ├── report.py                 # HealthReport pydantic model
│   └── findings.py               # Finding + severity pydantic models
│
├── controllers/
│   ├── orchestrator.py           # Main agent loop (Claude tool-use)
│   ├── classifier.py             # Severity classification logic
│   └── report_builder.py         # Report generation (per-brand + summary)
│
├── views/
│   ├── slack_formatter.py        # Format reports/alerts for Slack
│   └── dashboard.py              # Gradio UI (manual trigger + view reports)
│
├── tools/
│   ├── intentwise_mcp.py         # DEPRECATED — preserved per no-delete policy
│   ├── postgres.py               # Emplicit Postgres read/write
│   ├── teamwork.py               # Teamwork API client (read-only)
│   ├── slack_alerts.py           # Slack channel posts + DMs
│   └── notebooklm.py            # Preserved placeholder — brand context not in v1
│
└── tests/
    ├── test_classifier.py        # Severity logic tests
    ├── test_tools.py             # Tool integration tests
    └── test_orchestrator.py      # End-to-end agent tests
```

---

## Agent Data Flow

```
1. main.py triggers (cron or Gradio button)
2. orchestrator.py gets active accounts from Emplicit Postgres
3. For each account:
   a. Query Postgres (Intentwise-synced tables) for account health data
   b. Query Teamwork for completed tasks per brand
   c. Classify each metric via classifier.py
   d. Build report via report_builder.py
   e. Format output via slack_formatter.py
   f. Route alerts via slack_alerts.py
   g. Save report to Emplicit Postgres
4. After all accounts: build cross-brand summary, post to ops Slack channel
```

---

## Data Sources

### Emplicit Postgres — Amazon Account Health (Intentwise-synced)

Intentwise syncs Amazon Seller Central data directly into Emplicit Postgres.
All account health metrics are read from these tables — no direct Intentwise API calls.

**TODO: Confirm schema name and exact column names with data team before live testing.**
Assumed schema: `amazon_source_data` (based on Intentwise dataset names).

| Check | Postgres Table |
|---|---|
| Shipping Metrics | `amazon_source_data.sellercentral_sellerperformance_shippingperformance_report` |
| Policy Compliance | `amazon_source_data.sellercentral_sellerperformance_policycompliance_report` |
| Customer Service (ODR) | `amazon_source_data.sellercentral_sellerperformance_customerserviceperformance_report` |
| Seller Performance (AHR) | `amazon_source_data.sellercentral_sellerperformance_report` |
| Account Status | `amazon_source_data.sellercentral_account_status_changed_report` |

Key fields (confirm against actual Postgres schema):
- `account_health_rating_ahr_status` — AHR score/status
- `late_shipment_rate`, `valid_tracking_rate`, `pre_fulfillment_cancel_rate`
- `order_defect_rate`
- `food_safety_count`, `ip_complaint_count`
- `account_status`

### Emplicit Postgres — Walk the Store Schema

| Table | Purpose |
|---|---|
| `walk_the_store.account_config` | Active accounts, seller ID, marketplace, Slack channel ID, Teamwork project ID, account manager Slack ID, Drive folder ID |
| `walk_the_store.daily_health_reports` | Write: account_config_id, report_date, highest_severity, findings (JSONB), all metric values |

### Teamwork (Read-Only)

- Endpoint: `https://{TEAMWORK_DOMAIN}.teamwork.com/projects/{project_id}/tasks.json`
- Auth: Basic auth (API token)
- Pull: task name, status, assignee, completion date

---

## Severity Thresholds

Define in `config/thresholds.py`:

| Metric | 🔴 Critical | 🟡 Warning | 🟢 Healthy |
|---|---|---|---|
| Late Shipment Rate | ≥4% | 2-4% | <2% |
| Valid Tracking Rate | <95% | 95-98% | >98% |
| Pre-fulfillment Cancel Rate | ≥2.5% | 1-2.5% | <1% |
| Order Defect Rate (ODR) | ≥1% | 0.5-1% | <0.5% |
| Account Health Rating | ≤250 | 251-300 | >300 |
| Food/Product Safety | Any count > 0 | — | 0 |
| IP Complaints | Any count > 0 | — | 0 |
| Account Status | AT_RISK or worse | — | NORMAL |

---

## Alert Routing

| Severity | Slack Channel | Slack DM to AM | Teamwork |
|---|---|---|---|
| 🔴 Critical | ✅ | ✅ | Read-only |
| 🟡 Warning | ✅ | ❌ | Read-only |
| 🟢 Healthy | ❌ | ❌ | — |

Daily summary always posts to ops channel regardless of severity.

---

## Environment Variables (.env)

```
# Anthropic
ANTHROPIC_API_KEY=

# Emplicit Postgres
EMPLICIT_PG_HOST=
EMPLICIT_PG_PORT=5432
EMPLICIT_PG_DB=
EMPLICIT_PG_USER=
EMPLICIT_PG_PASSWORD=

# Slack
SLACK_BOT_TOKEN=
SLACK_OPS_CHANNEL=

# Teamwork
TEAMWORK_DOMAIN=
TEAMWORK_API_TOKEN=
```

---

## Build Order

Complete each step before moving to the next. Per CLAUDE.md, ask permission before every action.

### Step 0: Prerequisites
- [ ] Confirm Postgres schema name for Intentwise-synced tables (`amazon_source_data`?)
- [ ] Confirm exact column names in each Intentwise-synced table
- [ ] Emplicit Postgres dev/test database connection details
- [ ] Teamwork API token

### Step 1: Project Setup
- [ ] Create MVC folder structure per this document
- [ ] Set up Python venv
- [ ] Install: `anthropic psycopg2-binary slack_sdk pydantic gradio httpx python-dotenv`
- [ ] Create `.env.example` with all keys above
- [ ] Create `.gitignore`
- [ ] Create `requirements.txt`

### Step 2: Pydantic Models (`/models`)
- [ ] `account.py` — AccountConfig matching `walk_the_store.account_config`
- [ ] `findings.py` — Finding (check, type, severity, message)
- [ ] `report.py` — HealthReport (all metrics + findings + metadata)

### Step 3: Tool Layer (`/tools`) — test each independently
- [ ] `postgres.py` — connect, get active accounts, get health metrics, save report
- [ ] `teamwork.py` — HTTP client, get tasks by project ID
- [ ] `slack_alerts.py` — post to channel, DM user

### Step 4: Severity Classifier (`/controllers`)
- [ ] `classifier.py` — raw data in → severity + findings out
- [ ] `tests/test_classifier.py` — unit tests with known values

### Step 5: Orchestrator (`/controllers`)
- [ ] `orchestrator.py` — Claude tool-use loop
- [ ] Register all tools, define agent system prompt
- [ ] Flow: get accounts → loop → query → classify → report → alert → save
- [ ] Error handling: missing data → log gap, continue
- [ ] Test with 1 account

### Step 6: Report Builder + Views
- [ ] `controllers/report_builder.py` — per-brand + cross-brand summary
- [ ] `views/slack_formatter.py` — format for Slack markdown
- [ ] Include Teamwork status in reports

### Step 7: Alert Routing
- [ ] Wire severity → Slack routing
- [ ] Wire report → Postgres save
- [ ] Test all routing paths

### Step 8: Gradio UI (`/views`)
- [ ] `views/dashboard.py` — manual trigger, view reports, run history
- [ ] Keep it simple

### Step 9: Deploy
- [ ] Dockerfile
- [ ] Google Cloud Run
- [ ] Cloud Scheduler (9:00 AM ET)
- [ ] Secret Manager for env vars
- [ ] Logging + monitoring

### Step 10: Test & Validate
- [ ] Run against 2+ real accounts
- [ ] Verify severity, alerts, reports, Postgres writes
- [ ] No crashes on missing data

### Step 11: Feedback & Adjust (Week 2)
- [ ] Demo to ops team
- [ ] Adjust thresholds, fields, report layout
- [ ] Final validation

---

## Error Handling Rules

- Postgres health metric query fails → log gap per metric, classify as "unknown", continue
- Specific metric column missing → log gap, treat as None, continue
- Postgres write fails → log error, still send Slack alert
- Slack fails → log error, still save to Postgres
- Never crash the entire run for one account or one metric
- Always produce a daily summary even if all accounts fail

---

## Pre-Sprint Blockers

| Blocker | Owner | Status |
|---|---|---|
| Confirm Postgres schema name for Intentwise-synced tables | Steven → Data Team | Open |
| Confirm column names in each Intentwise-synced table | Steven → Data Team | Open |
| Emplicit Postgres dev/test database connection details | Steven → Data Team | Open |
| Teamwork API token with read access | Steven → Boss | Open |
| Confirm `walk_the_store.account_config` still active | Steven → Boss | Open |

---

## Effort & Timeline

| | Week 1: Build & Test | Week 2: Feedback & Adjust | Total |
|---|---|---|---|
| Dev (Steven) | 30 hrs | 8 hrs | 38 hrs |
| PM (Steven) | 4 hrs | 4 hrs | 8 hrs |
| Ops review | 0 hrs | 4 hrs | 4 hrs |
| **TOTAL** | **34 hrs** | **16 hrs** | **50 hrs** |

---
