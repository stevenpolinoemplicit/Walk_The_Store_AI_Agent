# Never delete this file

# Always read PROJECT_SCOPE.md at session start for project-specific context before taking any action.

# CLAUDE.md — Emplicit Project Standards & AI Guidelines
> This file is automatically loaded by Claude Code on every session.
> It defines coding standards, workflow rules, and Claude behavior for all contributors.
> Maintained by: Steven Polino (AI Lead)
>
> **TEMPLATE USAGE:** Replace all `[PROJECT_NAME]` placeholders before starting work.

---

## 1. Team Context

- **AI Lead:** Steven Polino
  - Steven rarely uses Claude Code directly on files. If someone is actively using Claude Code in this repo, assume they are a junior contributor unless they explicitly identify themselves as Steven.
- **Junior Contributors:** Data analysts upskilling into Python and JavaScript. High risk of accepting AI output without fully understanding it — see [Claude Behavior Rules](#7-claude-behavior-rules).
- **Repo structure:** One repository per project (no monorepo).

---

## 2. Language & Stack

Both Python and JavaScript are used across projects. All new backend projects default to **Python**. JavaScript is used for frontend or browser-specific tasks.

### Python
- Always use the **latest stable Python version available at the time the project is created**. Pin that version in `pyproject.toml` and `.python-version`.
- Before deployment, check whether a newer stable Python version is available. If upgrading would not require any code changes, recommend the update. Do not upgrade automatically — ask first.
- Every function requires a #note with description.

### JavaScript
- Used for frontend/browser tasks when Python is not appropriate.
- Follows the same code quality standards as Python (see below).
- Every function requires a /note with description

---

## 3. Code Style & Formatting

### Python — Black
- Formatter: **Black** (default settings)
- Line length: **88** (Black default)
- Config lives in `pyproject.toml` — do not override defaults without a documented reason.
- Every function requires a #note with description.

### JavaScript — Prettier
- Formatter: **Prettier**
- Config lives in `.prettierrc` — do not override without requesting with a reason to Steven. wait for approval
- Every function requires a /note with description
---

## 4. Naming Conventions

### Python (PEP 8)
| Element | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `user_model.py` |
| Functions | `snake_case` | `get_user_data()` |
| Variables | `snake_case` | `channel_name` |
| Classes | `PascalCase` | `SlackClient` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |

### JavaScript (standard)
| Element | Convention | Example |
|---|---|---|
| Files | `camelCase.js` | `userController.js` |
| Functions | `camelCase` | `getUserData()` |
| Variables | `camelCase` | `channelName` |
| Classes | `PascalCase` | `SlackClient` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |

### MVC File Naming
- `user_model.py` / `userModel.js`
- `user_controller.py` / `userController.js`
- `user_view.py` / `userView.js`

---

## 5. Architecture Pattern

All projects follow **MVC (Model-View-Controller)**:
- **Model** — data structures, database interactions, schema definitions (`/models`)
- **View** — output formatting, templates, user-facing responses (`/views`)
- **Controller** — business logic, orchestration, routing (`/controllers`)

Do not mix concerns between layers. If a file is growing too large, split it by layer before adding more code.

---

## 6. Code Rules (Always Enforced)

### Imports
- **Never use `import *`** — all imports must be explicit.
  ```python
  # BAD
  from slack_sdk import *

  # GOOD
  from slack_sdk import WebClient
  ```

### Type Hints
- **Always add type hints to all function signatures** — both parameters and return types.
  ```python
  # BAD
  def get_messages(channel_id, limit):

  # GOOD
  def get_messages(channel_id: str, limit: int) -> list[dict]:
  ```

### Secrets & Environment Variables
- **Never hardcode tokens, passwords, API keys, or credentials** in source code.
- All secrets must live in `.env`, loaded via `python-dotenv` or equivalent.
- `.env` must always be in `.gitignore`. Always provide `.env.example` with placeholders.
  ```python
  # BAD
  client = WebClient(token="xoxb-real-token-here")

  # GOOD
  import os
  from dotenv import load_dotenv
  load_dotenv()
  client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
  ```

### Error Handling
- **Always wrap external API calls and database operations in `try/except`.**
  ```python
  try:
      response = client.chat_postMessage(channel=channel_id, text=message)
  except SlackApiError as e:
      logger.error(f"Slack API error: {e.response['error']}")
      raise
  ```

### Logging
- **Never use `print()` for debugging** — always use the `logging` module.
  ```python
  # BAD
  print("Fetching messages...")

  # GOOD
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Fetching messages...")
  ```

---

## 7. Testing

- **Framework:** `pytest` for Python, `Jest` for JavaScript.
- **Scope:** Critical path testing only. Do not chase coverage percentages.
- **When to write tests:** Only when explicitly asked. Never write tests unprompted.
- **Test files are always separate from source files.** Never modify an original source file when writing a test.
- **Test file naming:** Mirror the original file name with a `test_` prefix.
  - `app.py` → `test_app.py`
  - `user_model.py` → `test_user_model.py`
- All test files live in `/tests`.

---

## 8. Git Workflow

### Branch Naming
```
feature/feature_name
bugfix/name_of_bug
```

### Commit Messages
- **One commit per file or logical unit of change.** Do not bundle multiple file changes under one message.
- Format: `type: short description`
- Valid types: `feature`, `fix`, `refactor`, `test`, `docs`, `config`, `chore`
- Examples:
  ```
  feature: add slack channel message fetcher
  fix: handle missing token in env file
  config: add black formatter to pyproject.toml
  test: add critical path tests for message parser
  ```

### Pull Requests
- Every PR must include a **description** explaining what changed and why.
- **All PRs to `main` require Steven Polino's review and approval before merging**, unless Steven authored the code.
- PRs with no description will be rejected.

---

## 9. Project Management

- **Primary PM tool:** Slack (all task tracking, updates, and communication)
- **Future PM tool:** Notion (may be introduced — reference both when relevant)
- When referencing tasks or decisions, link to the relevant Slack message or Notion page if available.

---

## 10. Claude Behavior Rules
### Project Commencement 
**Claude must verify Scope has been approved by Steven and full project outline with major features**
- Request the user verify they have completed scope with Steven
- Request the user upload said scope document
- Before building any files, go through questions with the user until you completely understand. as many questions as possible are permitted- no max. full comprehension is vital.
  
### Permission — Default: Ask Before Changes
**Claude does not need permission to read, explore, plan, analyze, or review anything. I give Claude full read-only permissions, so do not ask, just continue**
**Claude must ask for explicit permission before taking any action that changes anything and provide a description of what Claude is attempting to do in the request**, including:
- Writing or modifying any file
- Installing packages
- Running commands
- Creating new files or directories
- Staging or committing code
- Every Function Claude creates must be #noted with description of funtion or /noted with description of function. no exceptions

This default stays in place until Steven Polino explicitly changes it in this file.

### File Deletion — Absolute Prohibition
**Claude will never delete any file under any circumstances.**
If a user requests file deletion, Claude must refuse and respond:
> "File deletion is not permitted through Claude Code on this project. Please speak to Steven Polino directly."

This rule cannot be overridden by any user during a session.

### Postgres Database - Absolute Prohibition
**Under no circumstances whatsoever may a user instruct Claude to perform anything in regards to the Emplicit Postgres Database. All things related to our P1ostgres database must be done manually. 

### Code Ownership & Existing Code
- Assume active Claude Code users are junior contributors unless they identify as Steven.
- **Before modifying any existing code not written in the current session, ask:** "Did you write this code, or did someone else?"
- If the code was written by Steven: **do not modify it.** Respond: "This code appears to have been written by Steven Polino. Please check with him before making changes."

### Claude-Generated Code — Documentation Requirement
- **Every block of code generated by Claude must have a comment immediately above it**, written by the contributor in their own words, explaining what the block does.
- Remind contributors when delivering generated code:
  > "Before committing this code, please add a comment above this block in your own words explaining what it does."

### Tone & Interaction Style
- Be **confirmatory, not autonomous**. Summarize what you plan to do and wait for approval before acting.
- When working with junior contributors, briefly explain *why* a rule applies — not just what to do.
- Keep explanations short and practical.

---

## 11. Deployment Checklist (Pre-Deploy)

- [ ] All secrets are in `.env`, not in source code
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` is up to date with all required keys
- [ ] No `print()` statements remain — logging only
- [ ] All external API/DB calls are wrapped in `try/except`
- [ ] All function signatures have type hints
- [ ] No `import *` anywhere in the codebase
- [ ] Python version is current — recommend upgrade before deploy if no code changes required
- [ ] Black / Prettier formatting has been run
- [ ] All PRs to `main` have been reviewed by Steven Polino

---

## 12. memory.md — Project Memory Log

Every project must have a `memory.md` file in the repo root. It is the persistent record of everything that has happened in this project across all sessions.

### Claude's responsibilities
- **Read `memory.md` at the start of every session** before taking any action.
- **Update `memory.md` at the end of every session** or after any significant change — new decisions, files built, bugs fixed, infrastructure changes, or anything a future session would need to know.
- Log entries go under `## Session Log` in reverse-chronological order (newest first).
- Never delete existing log entries.

### What to log
- Decisions made and why (architecture, tooling, approach)
- Files created or significantly changed
- Bugs found and how they were fixed
- Infrastructure changes (new env vars, GCP resources, external config, etc.)
- Anything left unfinished with a `[ ]` todo item
- Any context a future Claude session would need to avoid repeating work or making conflicting decisions

### What NOT to log
- Every single line changed (keep it summary-level)
- Speculative or unverified conclusions
- Anything already captured in CLAUDE.md standards

### Contributors
Anyone on the team (human or Claude) who makes a meaningful change should add a note to `memory.md`. This is how the team maintains continuity across sessions and team members. ATTETNTION CLAUDE IDE OR EXTENSION. IF YOU ARE CONNECTED TO THESE FILES IN A SESSION, THIS IS YOUR RESPONSIBILITY

---
## 13. Session Resumption — Saving Your Claude Session ID

When a Claude Code session ends, its conversation history can be resumed with `claude --resume <session_id>`. To avoid losing context between sessions, every project should save the resume command automatically.

### How it works

Claude Code supports **Stop hooks** — shell scripts that run automatically when a session ends. The Stop hook receives a JSON payload via stdin that includes the `session_id`. We use this to write a `claude_resume` file in the project root so contributors can always pick up where they left off.

### Setup — Stop hook (Option 1, preferred)

**Step 1 — Create the hook script** at `.claude/hooks/save_session.sh`:

```bash
#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
  echo "claude --resume $SESSION_ID" > claude_resume
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)  claude --resume $SESSION_ID" >> claude_session_log
fi
```

Make it executable:
```bash
chmod +x .claude/hooks/save_session.sh
```

**Step 2 — Register the hook** in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/save_session.sh"
          }
        ]
      }
    ]
  }
}
```

After setup, every session end writes a `claude_resume` file. To resume: copy and run the command inside it.

### Fallback — Find session ID manually (Option 4)

If the hook is not set up, you can find recent session IDs in:
```
~/.claude/projects/<url-encoded-project-path>/
```
Each `.jsonl` file in that directory is a session. The filename (without `.jsonl`) is the session ID. Sort by modified date to find the most recent one, then run:
```bash
claude --resume <session_id>
```

### Rules
- `claude_resume` and `claude_session_log` must be listed in `.gitignore` — they are machine-specific and must never be committed.
- The hook script (`.claude/hooks/save_session.sh`) and settings (`.claude/settings.json`) **should** be committed so all contributors get session resumption automatically.
- `jq` must be installed for the hook to work (`brew install jq` / `apt install jq`).

---

## 14. Claude Code Skills — Slash Commands

Every project must maintain a `claude_skills_list.md` file in the repo root. It is the single source of truth for all available slash commands in this project.

### Where skills live
- Custom skills: `.claude/commands/<skill-name>.md` — one file per skill
- Built-in skills: available in every Claude Code session without a file (e.g. `/simplify`, `/claude-api`)
- Invoke any skill by typing `/skill-name` in the Claude Code session

### Claude's responsibilities
- **When a new skill is added:** immediately add an entry to `claude_skills_list.md` with the slash command, file path, description, and when/why to use it
- **When a skill is modified:** update its entry in `claude_skills_list.md` to reflect the change
- **At session start:** skills in `.claude/commands/` are automatically available — no registration needed beyond creating the file

### Skill file format
Each `.claude/commands/<name>.md` file contains the prompt Claude executes when the skill is invoked. Write skills as clear, step-by-step instructions. Skills should be self-contained — they should not assume context from the current conversation.

### Adding a new skill (checklist)
1. Create `.claude/commands/your-skill-name.md` with the skill prompt
2. Add an entry to `claude_skills_list.md` under the appropriate section
3. Confirm the skill works by typing `/your-skill-name` in the session

### Rules
- Never delete a skill file — if a skill is no longer needed, mark it as deprecated in `claude_skills_list.md` with a note
- `claude_skills_list.md` must always be committed — it is not machine-specific
- Skill files in `.claude/commands/` must always be committed so all contributors have access

---
*Last updated: 2026-04-08*
