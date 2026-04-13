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
