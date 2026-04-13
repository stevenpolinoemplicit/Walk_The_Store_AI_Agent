# CLAUDE_ENTERPRISE_SETUP.md — Walk the Store Project Setup in Claude Enterprise

Employees access Walk the Store reports and ask questions about account health through
claude.ai's "Projects" feature. Claude reads the stored Google Drive reports automatically
via the Drive connector — no custom bot or API integration required.

---

## Prerequisites

- Emplicit Claude Enterprise account active (claude.ai)
- Walk the Store Drive folder(s) accessible (reports saved by the agent after each run)
- Admin access to claude.ai to create and share a Project

---

## Step 1: Create the Walk the Store Project

1. Go to **claude.ai** → left sidebar → **Projects** → **New Project**
2. Name it: `Walk the Store Agent`
3. Description: `Daily Amazon account health reports for all Emplicit brands. Ask questions about any brand's status, findings, or metrics.`

---

## Step 2: Add the system prompt

Paste this into the Project's **Custom Instructions** field:

```
You are the Walk the Store AI Agent for Emplicit.

You have access to daily Amazon account health reports stored in Google Drive. These reports
are generated automatically each morning after Intentwise syncs seller data.

Report format:
- Overall Status: 🔴 CRITICAL / 🟡 WARNING / 🟢 HEALTHY
- Metrics tracked: Late Shipment Rate, Valid Tracking Rate, Pre-fulfillment Cancel Rate,
  Order Defect Rate, Account Health Rating, Account Status, Food/Product Safety, IP Complaints
- Severity thresholds:
    Critical: Late shipment ≥4%, Valid tracking <95%, Cancel rate ≥2.5%, ODR ≥1%,
              AHR ≤250, any food safety or IP complaint, account status AT_RISK or worse
    Warning:  Late shipment 2–4%, Valid tracking 95–98%, Cancel rate 1–2.5%, ODR 0.5–1%, AHR 251–300

When asked about a brand's status, cite the most recent report from Drive.
When asked what to do about an issue, reference Emplicit SOPs if available in Drive.
Always specify which report date your answer is based on.
```

---

## Step 3: Connect Google Drive

1. In the Project settings → **Add content** → **Google Drive**
2. Connect the Google Drive folders where reports are saved:
   - The top-level Walk the Store folder that contains per-brand subfolders
   - Or individual per-brand folders if preferred
3. Claude will automatically index all `.gdoc` files in these folders

> The Drive connector re-reads documents on each conversation — reports added after the
> Project is created are available immediately, no re-sync needed.

---

## Step 4: Share the Project with the ops team

1. In the Project settings → **Share**
2. Add all account managers and ops team members by email
3. They will see Walk the Store in their Projects list on next login

---

## Step 5: Using the Project

Employees open claude.ai → **Walk the Store Agent** Project and ask naturally:

- *"What was Brand X's status today?"*
- *"Are any accounts in critical status right now?"*
- *"What food safety issues came up this week?"*
- *"How do we typically handle a high late shipment rate?"*

Claude reads the Drive reports and answers with specific data, citing the report date.

---

## Notes

- Reports must be accessible to the service account that created them AND to the Drive connector
  (set sharing to "anyone at emplicit.com with the link can view" — the agent does this automatically)
- If Drive connector is not available in your Enterprise tier, employees can manually upload
  today's report PDF to the Project as a file attachment — Claude will read it the same way
- The system prompt can be updated at any time without any code changes
