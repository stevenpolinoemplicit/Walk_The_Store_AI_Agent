NotebookLM Enterprise API access has been granted. Run this checklist to implement the integration.

**Step 1 — Add credential to .env**
Confirm `NOTEBOOKLM_API_KEY` has been added to `.env`.

**Step 2 — Gather API details**
Ask the user:
1. What is the NotebookLM Enterprise API base URL?
2. How are notebooks identified — by brand name, by notebook ID, or something else?
3. What does a query request look like — REST, gRPC, or something else?
4. What does the response look like — plain text summary, JSON, structured data?

Do not proceed to implementation until all four are answered.

**Step 3 — Implement tools/notebooklm.py**
Once API details are confirmed, replace the stub body in `tools/notebooklm.py` `get_brand_context()` with the real implementation:
- Add correct HTTP call using `httpx`
- Pass `NOTEBOOKLM_API_KEY` from `config/settings.py`
- Wrap in `try/except` per CLAUDE.md rules
- Add type hints and `#note` comment per CLAUDE.md rules
- Return a plain string summary or `None` on failure

**Step 4 — Map brands to notebooks**
Ask the user: how are the 20+ existing notebooks named — do they match `brand_name` exactly or is there a mapping needed?
If a mapping is needed, suggest adding a `notebooklm_notebook_id` column to `walk_the_store.account_config`.

**Step 5 — Test**
Test `get_brand_context()` against one brand before wiring into the full run.

Per CLAUDE.md: ask permission before modifying any file.
