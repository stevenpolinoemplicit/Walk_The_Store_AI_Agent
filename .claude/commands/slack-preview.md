Preview what a Slack report would look like for a given set of metric values, without needing live credentials.

Ask the user for the following test values (they can press Enter to skip any and use defaults):
- Brand name (default: "Test Brand")
- Late shipment rate % (default: 1.5)
- Valid tracking rate % (default: 97.0)
- Pre-fulfillment cancel rate % (default: 0.5)
- Order defect rate % (default: 0.3)
- Account health rating score (default: 320)
- Food safety violations count (default: 0)
- IP complaints count (default: 0)
- Account status (default: NORMAL)

Then:
1. Run the values through the classifier thresholds from `config/thresholds.py`
2. Build a simulated HealthReport
3. Show what the Slack message would look like rendered as plain text (since Block Kit won't render in terminal)

Output format:
```
--- SLACK PREVIEW ---
[emoji] BRAND NAME — SEVERITY (date)
━━━━━━━━━━━━━━━━━━━━
Account Health Findings:
[emoji] Late shipment rate: X%
[emoji] Valid tracking rate: X%
...

Data gaps: none
Recent Teamwork completions: none (test mode)
---------------------
Highest severity: CRITICAL/WARNING/HEALTHY
```

This is read-only and uses no live credentials — useful for verifying threshold logic and report formatting before a live run.
