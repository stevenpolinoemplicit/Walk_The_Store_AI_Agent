It is end of session. Update `memory.md` with a new session log entry.

Read the current conversation to identify:
- What files were created or modified this session
- What decisions were made and why
- Any bugs found and how they were fixed
- Any new environment variables, GCP resources, or external config added
- Anything left unfinished (format as `[ ]` todo items)
- Any context a future Claude session would need to avoid repeating work

Then prepend a new session entry to the `## Session Log` section of `memory.md` in this format:

```
### Session N — [short title describing main work done]
**Date:** [today's date]
**Participants:** Claude Code

#### Decisions Made
- [decision and reason]

#### Files Created
- [list]

#### Files Updated
- [list]

#### Still To Do
- [ ] [item]
```

Rules:
- Never delete existing session log entries
- Keep each entry summary-level — no line-by-line code changes
- Do not log anything already captured in CLAUDE.md standards
- After updating memory.md, remind the user to run `git add memory.md` and commit it
