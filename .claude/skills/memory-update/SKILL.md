---
name: memory-update
description: Use this skill at the end of a Claude Code session to log what was accomplished into memory.md. Triggers when the user says "we're done", "end of session", "wrap up", "save our progress", "update memory", "log what we did", "session complete", "I'm done for today", "let's close out", "write up the session", "record what we built", "before we go", "that's it for today", "update memory.md", "save context", "commit and close", "done for the day", "calling it", "signing off", "finished for today", "all done", "shutting down", "logging off", "that's a wrap", or any indication the current work session is ending. Does not trigger mid-session when the user is still actively building.
allowed-tools: Read Edit Write
metadata:
  model: claude-sonnet-4-6
  project: walk-the-store
---

Update `memory.md` with a new session log entry covering what happened this session.

## Gotchas

- New entries go at the **top** of `## Session Log` — reverse chronological order, newest first. Never append to the bottom.
- Never delete or overwrite existing log entries.
- NOTEBOOKLM_API_KEY and Intentwise credentials are still pending — if work was blocked on these, log them as open todos.
- Session numbers increment from the last entry in memory.md — read it first to get the current count.
- After writing, remind the user to run `git add memory.md` and commit it separately with message `docs: update session log`.

## What to log

Read the current conversation and identify:
- Files created or significantly modified
- Decisions made and why (architecture, tooling, approach)
- Bugs found and how they were fixed
- New env vars, GCP resources, or external config added
- Anything unfinished

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
