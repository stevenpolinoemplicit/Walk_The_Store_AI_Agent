---
name: memory-update
description: Use this skill at the end of a Claude Code session to log what was accomplished into memory.md. Triggers when the user says "we're done", "end of session", "wrap up", "save our progress", "update memory", "log what we did", "session complete", "I'm done for today", "let's close out", "write up the session", "record what we built", "before we go", "that's it for today", "update memory.md", "save context", "commit and close", "done for the day", "calling it", "signing off", "finished for today", "all done", "shutting down", "logging off", "that's a wrap", or any indication the current work session is ending. Does not trigger mid-session when the user is still actively building.
allowed-tools: Read Edit Write
metadata:
  model: claude-sonnet-4-6
  project: walk-the-store
---

Update `memory.md` with a new session log entry covering what happened this session. Then review and update `README.md` if anything significant changed — new features, architectural decisions, new env vars, or updated behavior.

## README Update Rules

- Only update sections that are factually out of date. Do not rewrite sections that are still accurate.
- Add new features to "What It Does" if they change user-facing behavior.
- Update the Architecture diagram if the data flow changed.
- Add new env vars to the required env vars table.
- Keep the README concise — do not expand it beyond what is necessary to understand and operate the project.
- After updating both files, remind the user to stage and commit each separately:
  - `git add memory.md && git commit -m "docs: update session log"`
  - `git add README.md && git commit -m "docs: update README"`

## Gotchas

- New entries go at the **top** of `## Session Log` — reverse chronological order, newest first. Never append to the bottom.
- Never delete or overwrite existing log entries.
- Intentwise MCP integration has been removed — data is now read directly from Postgres. Do not log Intentwise credentials as a blocker.
- Session numbers increment from the last entry in memory.md — read it first to get the current count.
- After writing, remind the user to run `git add memory.md` and commit it separately with message `docs: update session log`.

## What to log

Read the current conversation and identify:
- Files created or significantly modified
- Decisions made and why (architecture, tooling, approach)
- Bugs found and how they were fixed
- New env vars, GCP resources, or external config added
- Anything unfinished
- Any context a future Claude session would need to avoid repeating work or making conflicting decisions

## What NOT to log

- Line-by-line code changes (summary level only)
- Anything already in CLAUDE.md standards
- Speculative conclusions

## Entry format

Prepend this to the `## Session Log` section:

```
### Session N — [short title: main work done this session]
**Date:** [today's date]
**Participants:** Claude Code

#### Decisions Made
- [decision — reason]

#### Files Created
- [filename] — [one-line purpose]

#### Files Updated
- [filename] — [what changed]

#### Still To Do
- [ ] [unfinished item]
```
