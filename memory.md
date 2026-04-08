# memory.md — Walk the Store AI Agent
> Running log of decisions, changes, and context for this project.
> Updated by Claude and contributors as work progresses.
> Claude Code automatically loads CLAUDE.md — read this file at the start of every session.

---

## Project Overview

Autonomous AI agent that runs daily at 6:30 AM ET. Checks Amazon account health for multiple client brands via Intentwise MCP, classifies issues by severity (Critical/Warning/Healthy), cross-references Teamwork for resolution activity, incorporates per-brand knowledge from NotebookLM, and delivers actionable reports via Slack.

Sprint 1 scope: Account Health + Brand Memory only.
Owner: Steven Chicken | Approvers: Adam Weiler, Emily Lindahl

---

## Session Log

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
