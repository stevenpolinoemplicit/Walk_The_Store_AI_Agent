# PROJECT_SCOPE.md — Walk the Store AI Agent

> This file contains all project-specific context, architecture, data sources, and build order.
> Claude Code must read this file at the start of every session alongside CLAUDE.md.
> For coding standards, behavior rules, and git workflow, see CLAUDE.md.

---

## Project Overview

An autonomous AI agent that runs daily at 6:30 AM ET. It checks Amazon account health for multiple client brands, classifies issues by severity, cross-references Teamwork for resolution activity, incorporates per-brand knowledge from NotebookLM, and delivers actionable reports via Slack.

**Sprint 1 Scope:** Account Health + Brand Memory only.
**Owner:** Steven Chicken
**Approvers:** Adam Weiler, Emily Lindahl

---

## What Sprint 1 Delivers

- Shipping metrics, policy compliance, customer service (ODR, A-to-Z), account health rating, account status alerts
- Auto-classification: 🔴 Critical / 🟡 Warning / 🟢 Healthy
- Teamwork read-only — shows completed tasks per brand
- Per-brand knowledge from NotebookLM (20+ existing notebooks)
- Slack alerts: channel + DM on critical, channel only on warning
- Per-brand daily report + cross-brand summary to ops channel
- Graceful handling of missing data (no crashes)

## Not in Sprint 1

Inventory health, inbound/shipment status, performance notifications, case log review, Walmart checks, PDF reports, Teamwork task creation, employee activity tracking.

---

## Tech Stack

| Component | Tool |
|---|---|
| Language | Python 3.11+ |
| Agent Framework | Anthropic Python SDK (`anthropic`) |
| LLM | Claude Sonnet |
| Amazon Data | Intentwise MCP Server (`https://mcp.intentwise.com/mcp`) via OAuth |
| Operational Data | Emplicit PostgreSQL (`psycopg2`) |
| Task Tracking | Teamwork API via `httpx` (read-only) |
| Alerts | Slack (`slack_sdk`) |
| Brand Memory | NotebookLM Enterprise API (details TBD) |
| Data Validation | `pydantic` |
| UI | `gradio` |
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
│   └── intentwise_preferences.yaml  # From Intentwise (when received)
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
│   ├── intentwise_mcp.py         # Intentwise MCP client (OAuth + queries)
│   ├── postgres.py               # Emplicit Postgres read/write
│   ├── teamwork.py               # Teamwork API client (read-only)
│   ├── slack_alerts.py           # Slack channel posts + DMs
│   └── notebooklm.py            # NotebookLM API client (TBD)
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
   a. Query Intentwise MCP for account health data
   b. Query Teamwork for completed tasks per brand
   c. Query NotebookLM for brand context (when available)
   d. Classify each metric via classifier.py
   e. Build report via report_builder.py
   f. Format output via slack_formatter.py
   g. Route alerts via slack_alerts.py
   h. Save report to Emplicit Postgres
4. After all accounts: build cross-brand summary, post to ops Slack channel
```

---

## Data Sources

### Intentwise MCP — Amazon Account Health

Server URL: `https://mcp.intentwise.com/mcp`
Auth: OAuth (client_credentials grant — pending confirmation)
Status: Access requested. Awaiting OAuth Client ID, credentials, and preferences YAML.

| Check | Intentwise Table |
|---|---|
| Shipping Metrics | `sellercentral_sellerperformance_shippingperformance_report` |
| Policy Compliance | `sellercentral_sellerperformance_policycompliance_report` |
| Customer Service (ODR, A-to-Z) | `sellercentral_sellerperformance_customerserviceperformance_report` |
| Seller Performance | `sellercentral_sellerperformance_report` |
| Customer Feedback | `sellercentral_flatfilefeedback_report` |
| Account Status Alerts | `sellercentral_account_status_changed_report` |

Key fields:
- `account_health_rating_ahr_status` — AHR score/status
- `order_defect_rate_afn_claims_status` / `_count` — A-to-Z FBA claims
- `order_defect_rate_mfn_claims_status` / `_count` — A-to-Z merchant fulfilled claims

### Emplicit Postgres

| Table | Purpose |
|---|---|
| `walk_the_store.account_config` | Active accounts, seller ID, marketplace, Slack channel ID, Teamwork project ID, account manager Slack ID, Drive folder ID |
| `walk_the_store.daily_health_reports` | Write: account_config_id, report_date, highest_severity, findings (JSONB), all metric values |

### Teamwork (Read-Only)

- Endpoint: `https://{TEAMWORK_DOMAIN}.teamwork.com/projects/{project_id}/tasks.json`
- Auth: Basic auth (API token)
- Pull: task name, status, assignee, completion date

### NotebookLM (20+ existing notebooks, one per brand)

- NotebookLM Enterprise API (access pending upgrade)
- Contains: client history, SOPs, brand guidelines, past issues, escalation notes
- Integration method TBD pending API access

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

# Intentwise MCP
INTENTWISE_CLIENT_ID=
INTENTWISE_CLIENT_SECRET=
INTENTWISE_MCP_URL=https://mcp.intentwise.com/mcp

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

# NotebookLM (TBD)
NOTEBOOKLM_API_KEY=
```

---

## Build Order

Complete each step before moving to the next. Per CLAUDE.md, ask permission before every action.

### Step 0: Prerequisites (BLOCKED until credentials received)
- [ ] Intentwise MCP OAuth credentials
- [ ] Confirm headless OAuth supported
- [ ] Emplicit Postgres dev/test database
- [ ] Teamwork API token
- [ ] NotebookLM Enterprise API access

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
- [ ] `postgres.py` — connect, get active accounts, save report
- [ ] `intentwise_mcp.py` — OAuth, connect to MCP, test query
- [ ] `teamwork.py` — HTTP client, get tasks by project ID
- [ ] `slack_alerts.py` — post to channel, DM user
- [ ] `notebooklm.py` — stub until API access confirmed

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
- [ ] Include Teamwork status and brand context in reports

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
- [ ] Cloud Scheduler (6:30 AM ET)
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

- Intentwise MCP unreachable → log error, skip account, note in report
- Specific metric query fails → log gap, classify as "unknown", continue
- Postgres write fails → log error, still send Slack alert
- Slack fails → log error, still save to Postgres
- Never crash the entire run for one account or one metric
- Always produce a daily summary even if all accounts fail

---

## Pre-Sprint Blockers

| Blocker | Owner | Status |
|---|---|---|
| Intentwise MCP access (OAuth Client ID, credentials, YAML) | Steven → Intentwise | Requested |
| Confirm OAuth supports client_credentials (headless) | Steven → Intentwise | Requested |
| NotebookLM Enterprise API access | Steven | Pending upgrade |
| Emplicit Postgres dev/test database | Steven → Data Team | Open |
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
