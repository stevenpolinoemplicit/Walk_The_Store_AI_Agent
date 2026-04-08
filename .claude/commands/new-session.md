Read the following files in order and then give a structured session briefing:
1. `memory.md` — what was built last session, decisions made, what's blocked
2. `PROJECT_SCOPE.md` — the build order and current sprint scope
3. `CLAUDE.md` — confirm behavior rules are active for this session

After reading, output a session briefing with these sections:
- **Where we left off** — last session summary in 2-3 sentences
- **Active blockers** — anything still waiting on credentials or external access
- **Recommended next step** — the single most logical thing to work on right now based on the build order
- **Rules reminder** — one-line confirmation that CLAUDE.md behavior rules are active (ask permission, #note every function, no file deletion)

Keep the briefing concise. Do not start building anything — wait for the user to confirm the next step.
