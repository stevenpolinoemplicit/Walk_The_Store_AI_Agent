# claude_skills_list.md — Walk the Store AI Agent
> Master list of all Claude Code slash commands available in this project.
> **Keep this file updated every time a new skill is added.**
> Skills live in `.claude/commands/` — one `.md` file per skill.
> Run any skill by typing `/skill-name` in the Claude Code session.

---

## How to Use Skills
Type the slash command in the Claude Code terminal session (not a separate terminal).
Skills are prompts — Claude reads the command file and executes the instructions automatically.

---

## Session Management

### `/new-session`
**File:** `.claude/commands/new-session.md`
**Description:** Session startup briefing — reads `memory.md` and `PROJECT_SCOPE.md` and summarizes where things left off, active blockers, and the recommended next step.
**When to use:** Run this at the start of every session before doing anything else. Eliminates ramp-up time and ensures Claude has full project context.

---

### `/step-status`
**File:** `.claude/commands/step-status.md`
**Description:** Reads `PROJECT_SCOPE.md` and `memory.md` and outputs a checklist of all 12 build steps (Steps 0–11) with status: Complete, Blocked, In Progress, or Not Started.
**When to use:** When you want a quick overview of where the project stands and what can be worked on next.

---

### `/memory-update`
**File:** `.claude/commands/memory-update.md`
**Description:** End-of-session prompt — reviews the conversation and writes a new session log entry to `memory.md` covering files created, decisions made, and todos.
**When to use:** Run at the end of every session before closing. Required per CLAUDE.md Section 12.

---

## Development

### `/explain-file`
**File:** `.claude/commands/explain-file.md`
**Description:** Explains the currently open IDE file two ways — one technical line and one plain English line — then walks through every function, shows how the file fits in the MVC flow, and flags any CLAUDE.md violations (missing `#note` comments, type hints, `print()` statements, etc.).
**When to use:** Any time you or a contributor needs to understand what a file does before modifying it, reviewing it, or handing it off.

---

### `/commit`
**File:** `.claude/commands/commit.md`
**Description:** Reviews git status and diff, then outputs correctly formatted `git add` and `git commit` commands per CLAUDE.md Section 8 rules (one file per commit, type: description format).
**When to use:** Whenever you're ready to commit changes. Outputs commands for you to review and run — does not commit automatically.

---

### `/env-check`
**File:** `.claude/commands/env-check.md`
**Description:** Compares `.env` against `.env.example` and reports which keys are set, missing, or pending. Never prints actual values.
**When to use:** Before running the agent for the first time, after adding new credentials, or when onboarding a new contributor.

---

### `/add-brand`
**File:** `.claude/commands/add-brand.md`
**Description:** Walks through adding a new client brand — collects seller ID, marketplace, Slack channel, Teamwork project ID, and AM Slack ID, then outputs the SQL INSERT and a pre-launch checklist.
**When to use:** Every time a new brand/client account needs to be added to the agent.

---

### `/slack-preview`
**File:** `.claude/commands/slack-preview.md`
**Description:** Given a set of metric values, simulates the classifier and renders a text preview of what the Slack report would look like — no live credentials required.
**When to use:** When testing threshold logic, verifying report formatting, or demoing to the ops team without running the live agent.

---

## Deployment & Quality

### `/trim-bash`
**File:** `.claude/commands/trim-bash.md`
**Description:** Reviews the last Bash command output and suggests trimmed alternatives using `| head`, `| grep`, `--limit`, or `--async`. Reminds Claude of the output efficiency rules for this project.
**When to use:** If a Bash command returned a large wall of output. Also serves as a reminder — the rules from this skill are enforced automatically via CLAUDE.md Section 10.

---

### `/deploy-checklist`
**File:** `.claude/commands/deploy-checklist.md`
**Description:** Runs through the full pre-deployment checklist from CLAUDE.md Section 11 — secrets, code quality, formatting, Python version, GCP setup — and reports pass/fail for each item.
**When to use:** Before every deployment to Cloud Run. Do not deploy without running this first.

---

## Integration Activation (run when credentials arrive)

### `/intentwise-ready` [DEPRECATED — Intentwise MCP integration removed]
**File:** `.claude/commands/intentwise-ready.md`
**Description:** ~~Intentwise MCP credential wiring checklist.~~ Intentwise MCP integration removed. Data is now read directly from Postgres after Intentwise syncs it there.
**When to use:** Do not use.

---

### `/notebooklm-ready` [DEPRECATED — brand context removed from v1]
**File:** `.claude/commands/notebooklm-ready.md`
**Description:** ~~Guides NotebookLM implementation.~~ NotebookLM and brand context are not in scope for POC or v1. This command is deprecated and should not be run.
**When to use:** Do not use.

---

## Built-in Claude Code Skills (no file needed)

### `/claude-api`
**Built-in** — no file in `.claude/commands/`
**Description:** Helper for building with the Anthropic SDK — tool-use wiring, agent loops, API patterns.
**When to use:** When working on `controllers/orchestrator.py` or any file that uses `import anthropic`.

### `/simplify`
**Built-in** — no file in `.claude/commands/`
**Description:** Reviews recently changed code for reuse, quality, and efficiency, then fixes issues found.
**When to use:** After any significant file change before committing.

---

## Adding a New Skill

1. Create `.claude/commands/your-skill-name.md` with the skill prompt
2. Add an entry to this file (`claude_skills_list.md`) under the appropriate section
3. The skill is immediately available as `/your-skill-name` in any Claude Code session

---
*Last updated: 2026-04-17*
