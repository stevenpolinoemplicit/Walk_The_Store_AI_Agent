---
name: new-session
description: Use this skill at the start of a Claude Code session to brief the agent on current project state. Triggers when the user says "let's get started", "where were we", "catch me up", "resuming from last session", "what should we work on", "what's left to do", "bring me up to speed", "I'm back", "what did we do last time", "pick up where we left off", "starting a new session", "new session", "what's the status", "what's next on the build", "remind me where we are", or any indication they are beginning a work session and need context. Does not trigger for general status questions mid-session.
allowed-tools: Read
metadata:
  model: claude-sonnet-4-6
  project: walk-the-store
---

Read these files in order before responding:
1. `memory.md` — last session summary, decisions made, open todos
2. `PROJECT_SCOPE.md` — build order, sprint scope, blockers
3. `CLAUDE.md` — confirm behavior rules for this session

## Gotchas

- Read `memory.md` FIRST — it has the most recent session context. `PROJECT_SCOPE.md` has the static build plan.
- Step 0 blockers are still open: Intentwise OAuth credentials, Emplicit Postgres dev DB, and Teamwork API token are all pending. Do not recommend steps that require these until the user confirms credentials have arrived — use `/intentwise-ready` skill for that.
- `app.py` is a template artifact, not active code. The real entry point is `main.py`.
- Skills that are explicit slash commands live in `.claude/commands/`. Semantic skills live in `.claude/skills/` as directories with `SKILL.md`.

## Output format

**Where we left off**
2–3 sentences from memory.md summarizing the last session.

**Active blockers**
Bullet list of anything still waiting on external credentials or access. If none, say "No blockers."

**Recommended next step**
The single most logical next action based on the build order and what is currently unblocked. One sentence.

**Rules active**
"CLAUDE.md behavior rules active — ask permission before all actions, #note every function, no file deletion."

Do not start building or modifying anything. Wait for the user to confirm direction.
