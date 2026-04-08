---
name: explain-file
description: Use this skill when the user wants to understand what a specific file does, how it fits into the project architecture, or what its functions mean. Triggers when the user says things like "explain this file", "what does this file do", "walk me through this", "help me understand this code", "what is [filename]", "break this down for me", "what's happening in this file", "how does this work", "describe what this does", "I don't understand this", "take me through this file", or opens a file and asks about it — even if they don't explicitly say "explain". Does not trigger for requests to modify, debug, or write code.
allowed-tools: Read Grep Glob
metadata:
  model: claude-sonnet-4-6
  project: walk-the-store
---

Explain the file currently open in the IDE or named in the user's message.

If no file is identifiable, ask: "Which file would you like explained? Please paste the path or select it in the IDE."

## Gotchas

- `app.py` is a template artifact — not active code. The real entry point is `main.py`. Flag this if the user asks about `app.py`.
- `#note:` comments are **required** above every Claude-generated function per CLAUDE.md Section 10. Missing ones are a violation, not a style choice.
- MVC layers in this project: `models/` = data shapes, `controllers/` = logic, `views/` = Slack/Gradio output, `tools/` = external API clients, `config/` = env vars and thresholds.
- `tools/notebooklm.py` is intentionally a stub — NotebookLM Enterprise API access is pending. Do not flag its empty body as a violation.

## Step 1 — File Overview

**Technical:** [1–2 sentences — what the file does and its role in the codebase]
**Plain English:** [1–2 sentences — same thing, no jargon, written for someone new to the project]

## Step 2 — MVC Flow

One short paragraph: which layer this file belongs to, what calls it (upstream), and what it calls (downstream).

## Step 3 — Function Breakdown

For every function:

**`function_name(params) -> return_type`**
- **Technical:** what it does and how
- **Plain English:** same, no jargon
- **#note check:** ✅ Present / ❌ Missing — check for a `# #note:` comment on the line immediately above the `def` statement

## Step 4 — CLAUDE.md Compliance

- [ ] Type hints on all params and return types
- [ ] `#note:` above every function (summarize from Step 3)
- [ ] No `import *`
- [ ] No hardcoded secrets or API keys
- [ ] No `print()` statements — logging only
- [ ] All external API/DB calls wrapped in `try/except`

`✅ No CLAUDE.md violations found.` or `⚠️ Violations found — address before committing.`

---

> "If any `#note:` comments are missing above Claude-generated functions, add them in your own words before committing — per CLAUDE.md Section 10."
