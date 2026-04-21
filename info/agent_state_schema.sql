-- agent_state_schema.sql
-- Run this manually in pgAdmin before the first agent run that includes the suppression watcher.
-- Creates the agent_state schema and suppression_alerts table used for deduplication.
-- agent_state is agent-owned — never write to amazon_source_data tables.
-- IMPORTANT: Run manually. Claude Code will never execute database commands.

-- Step 1: Create schema
CREATE SCHEMA IF NOT EXISTS agent_state;

-- Step 2: suppression_alerts — tracks which suppressed listings have already been alerted.
-- Unique on (account_id, asin, status_change_date) so a re-suppression of the same ASIN
-- on a new date triggers a fresh alert, but the same suppression never alerts twice.
CREATE TABLE IF NOT EXISTS agent_state.suppression_alerts (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER      NOT NULL,
    asin                VARCHAR(20)  NOT NULL,
    sku                 VARCHAR(200),
    status_change_date  DATE,
    issue_description   TEXT,
    alerted_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    report_date         DATE         NOT NULL,
    UNIQUE (account_id, asin, status_change_date)
);
