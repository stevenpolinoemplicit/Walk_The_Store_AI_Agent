Walk through adding a new client brand to the Walk the Store agent.

Ask the user for the following information one section at a time and wait for their answers:

1. **Brand name** — the display name used in reports and Slack
2. **Seller ID** — Amazon seller ID for this brand
3. **Marketplace** — e.g. `US`, `CA`, `UK`
4. **Slack channel ID** — the channel where this brand's alerts will be posted
5. **Account manager Slack ID** — the Slack user ID of the AM who receives critical DMs
6. **Teamwork project ID** — the Teamwork project ID for this brand
7. **Drive folder ID** — Google Drive folder ID where reports will be stored

Once all answers are collected, output:

1. The SQL INSERT statement to add the brand to `walk_the_store.account_config`:
```sql
INSERT INTO walk_the_store.account_config 
(brand_name, seller_id, marketplace, slack_channel_id, account_manager_slack_id, teamwork_project_id, drive_folder_id, is_active)
VALUES ('[brand]', '[seller_id]', '[marketplace]', '[slack_channel]', '[am_slack_id]', '[tw_project]', '[drive_folder]', TRUE);
```

2. A checklist of things to verify before the brand's first run:
- [ ] Slack bot is invited to the brand's channel
- [ ] Teamwork project ID confirmed and accessible
- [ ] Account manager Slack ID is correct (DMs will go here on critical)
- [ ] Drive folder ID is correct and service account has write access
- [ ] Confirm Intentwise is syncing data for this seller ID to Postgres

Do not execute anything — output for user review only.
