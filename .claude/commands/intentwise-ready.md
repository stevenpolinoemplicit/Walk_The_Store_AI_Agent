Intentwise credentials have arrived. Run this checklist to wire them up correctly and verify the integration before the first live run.

**Step 1 — Add credentials to .env**
Confirm the user has added these keys to `.env`:
- `INTENTWISE_CLIENT_ID`
- `INTENTWISE_CLIENT_SECRET`
- `INTENTWISE_MCP_URL` (confirm it matches `https://mcp.intentwise.com/mcp` or update if different)

**Step 2 — Confirm OAuth token URL**
Open `tools/intentwise_mcp.py` and verify `INTENTWISE_TOKEN_URL` on line ~13.
Ask the user: "What OAuth token URL did Intentwise provide?" Update the file if it differs from the current value.

**Step 3 — Replace preferences YAML**
Check if `config/intentwise_preferences.yaml` is still the placeholder.
If Intentwise delivered a real YAML file, instruct the user to replace the placeholder content with the real file contents.

**Step 4 — Confirm field names**
The following field names in `controllers/report_builder.py` are assumed — confirm they match what Intentwise actually returns:
- `late_shipment_rate`
- `valid_tracking_rate`
- `pre_fulfillment_cancel_rate`
- `order_defect_rate`
- `account_health_rating_ahr_status`
- `food_safety_count`
- `ip_complaint_count`
- `account_status`

Ask the user to paste a sample Intentwise MCP response so field names can be verified and corrected if needed.

**Step 5 — Test with one account**
Once credentials and field names are confirmed, suggest testing with a single account before running all brands.

Do not modify any files until the user confirms field names are correct.
