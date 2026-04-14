-- walk_the_store_schema.sql
-- Run this manually in pgAdmin when ready to persist daily reports.
-- NOT required for POC — save_report() fails gracefully until this schema exists.
-- The walk_the_store schema does NOT exist yet — run these statements in order.
-- This schema holds agent-owned data only. All Intentwise data lives in amazon_source_data (never modified).
--
-- NOTE: account_config table removed — brand config now comes from Google Sheets (Brand Code Mapping Sheet).
--
-- IMPORTANT: Run manually. Claude Code will never execute database commands.

-- Step 1: Create the schema
CREATE SCHEMA IF NOT EXISTS walk_the_store;


-- Step 2: daily_health_reports — one row per brand per day, written by the agent after each run.
-- brand_code matches the brand_code column in the Brand Code Mapping Google Sheet.
CREATE TABLE walk_the_store.daily_health_reports (
    id                    SERIAL PRIMARY KEY,
    brand_code            VARCHAR(50)     NOT NULL,           -- matches brand_code in Brand Code Mapping Sheet
    report_date           DATE            NOT NULL,
    highest_severity      VARCHAR(20)     NOT NULL,           -- 'critical', 'warning', or 'healthy'
    findings              JSONB           NOT NULL DEFAULT '[]',
    late_shipment_rate    NUMERIC,
    valid_tracking_rate   NUMERIC,
    pre_cancel_rate       NUMERIC,
    order_defect_rate     NUMERIC,                            -- NULL until ODR table/column confirmed
    account_health_rating INT,
    account_status        VARCHAR(50),
    food_safety_count     INT,
    ip_complaint_count    INT,
    data_gaps             JSONB           NOT NULL DEFAULT '[]',
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    UNIQUE (brand_code, report_date)                          -- one report per brand per day
);
