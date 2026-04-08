---
name: env-check
description: Use this skill when the user wants to verify their .env file has all required credentials configured. Triggers when the user says "are my credentials set", "check my env", "is everything configured", "what keys am I missing", "can I run the agent", "are my API keys set up", "check my secrets", "is my .env ready", "do I have all my env vars", "verify my environment", "am I ready to run", "is my configuration complete", "check my .env file", "what's missing from my env", or any question about whether credentials or environment variables are in place. Never prints actual secret values.
allowed-tools: Read Bash
metadata:
  model: claude-sonnet-4-6
  project: walk-the-store
---

Check all required environment variables against `.env.example` without revealing values.

## Gotchas

- `NOTEBOOKLM_API_KEY` being empty is **expected and not a bug** — NotebookLM Enterprise API access is pending. Flag it as "Intentionally pending" not "Missing".
- `INTENTWISE_CLIENT_ID` and `INTENTWISE_CLIENT_SECRET` are also blocked pending delivery from Intentwise — same treatment.
- If `.env` does not exist at all, instruct: `cp .env.example .env` then fill in values. Do not attempt to create it automatically.
- Never print actual values — presence check only.

## Steps

1. Read `.env.example` to get the full required key list
2. Check if `.env` exists
3. For each key, check: exists in `.env` AND has a non-empty value

## Output

| Key | Status |
|---|---|
| ANTHROPIC_API_KEY | ✅ Set |
| INTENTWISE_CLIENT_ID | 🔲 Pending (blocked — awaiting Intentwise delivery) |
| NOTEBOOKLM_API_KEY | 🔲 Pending (blocked — awaiting Enterprise API access) |
| EMPLICIT_PG_HOST | ❌ Missing |

Then:
- **Ready to run:** Yes / No
- **Missing keys:** list any that are empty and not intentionally pending
- **Pending keys:** list intentionally blocked ones separately so they don't alarm the user
