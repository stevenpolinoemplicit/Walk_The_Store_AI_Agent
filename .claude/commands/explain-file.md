Explain the file currently open or selected in the IDE.

If no file is visible in context, ask the user: "Which file would you like explained? Please paste the path or select it in the IDE."

---

## Step 1 — File Overview

Output two lines:

**Technical:** [1–2 sentences max — what the file does and its role in the codebase]
**Plain English:** [1–2 sentences max — what this file does as if explaining to someone new to the project]

---

## Step 2 — MVC Flow

In one short paragraph, explain where this file sits in the MVC architecture and how it connects to the rest of the project. Cover:
- Which layer it belongs to (Model / View / Controller / Tool / Config)
- What calls it (upstream)
- What it calls (downstream)

Example format:
> `postgres.py` lives in the Tool layer. It is called by `orchestrator.py` at the start of each run and by `report_builder.py` to save completed reports. It connects to the Emplicit PostgreSQL database and returns data to the controller layer — it does not format output or make decisions.

---

## Step 3 — Function Breakdown

For every function in the file, output a block in this format:

**`function_name(params) -> return_type`**
- **Technical:** [1–2 sentences — what it does and how]
- **Plain English:** [1–2 sentences — same thing, no jargon]
- **#note check:** ✅ Present / ❌ Missing — check whether a `#note:` comment exists on the line immediately above the `def` statement. Per CLAUDE.md Section 10, every Claude-generated function must have one.

---

## Step 4 — CLAUDE.md Compliance Check

Scan the file and flag any violations. Output as a checklist:

- [ ] **Type hints** — every function parameter and return type annotated? Flag any missing.
- [ ] **#note comments** — every function has a `#note:` above it? (already checked per-function above — summarize here)
- [ ] **No `import *`** — flag if found
- [ ] **No hardcoded secrets** — flag any tokens, passwords, or API keys in source
- [ ] **No `print()` statements** — flag any found (logging only per CLAUDE.md)
- [ ] **try/except on external calls** — any API or DB call not wrapped? Flag it.

If all pass: output `✅ No CLAUDE.md violations found.`
If violations found: output `⚠️ Violations found — address before committing.`

---

## Reminder to contributor

After this explanation, output:
> "If any `#note:` comments are missing above Claude-generated functions, add them in your own words before committing — per CLAUDE.md Section 10."
