# CLAUDE_ENTERPRISE_SETUP.md — Walk the Store + Ask Emplicit

Walk the Store reports are saved as Google Docs to Drive after every agent run.
"Ask Emplicit" (Claude Enterprise) reads Drive automatically — no custom bot, no extra code.

---

## How it works

1. Agent runs at 7:00 AM Los Angeles time
2. Google Doc report is saved to each brand's Drive folder
3. Employee opens Ask Emplicit and asks a question
4. Ask Emplicit reads the Drive doc and answers

---

## Only one thing to verify

**Is Ask Emplicit connected to Google Drive?**

- If yes → nothing to do. Reports are immediately available after each run.
- If no → ask whoever manages your Claude Enterprise account to add the Drive connector
  (one-time admin step, no code required).

---

## Example questions employees can ask

- "What was Brand X's Amazon health status today?"
- "Which brands are in critical status right now?"
- "What food safety issues came up this week?"
- "What does a high late shipment rate mean and how do we fix it?"

---

## Notes

- Reports are shared to `emplicit.co` domain automatically — any employee can access via Drive link
- Ask Emplicit will see new reports as soon as they land in Drive after the 7:00 AM run
- No system prompt, no Project setup, no additional configuration needed
