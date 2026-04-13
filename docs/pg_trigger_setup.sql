-- pg_trigger_setup.sql — DEPRECATED. No longer needed.
-- Trigger approach replaced by Cloud Scheduler + Cloud Run Jobs on a fixed daily schedule.
-- Preserved per project no-delete policy. Do not run this.
--
-- Original purpose: Postgres trigger that fires pg_notify when Intentwise syncs new data.
-- Run this manually in the Emplicit Postgres database (never automated by the agent).
-- The notification wakes up pg_listener.py, which calls run_agent() in a thread.
--
-- HOW TO RUN: Connect to the Emplicit Postgres DB and execute this file once.
--   psql -h <host> -U <user> -d <dbname> -f docs/pg_trigger_setup.sql

-- Step 1: Create the trigger function
-- When a new row is inserted into the Intentwise-synced table, notify the 'wts_data_ready' channel.
-- The payload is the report_date of the inserted row so the agent knows which date to process.
CREATE OR REPLACE FUNCTION notify_wts_data_ready()
RETURNS trigger AS $$
BEGIN
  -- april13 waiting on confirmation - confirm the date column name in the trigger table.
  -- Replace 'report_date' below with the actual column name if different.
  PERFORM pg_notify('wts_data_ready', NEW.report_date::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 2: Attach the trigger to the Intentwise-synced table
-- april13 waiting on confirmation - which table does Intentwise write to LAST in its sync sequence?
-- This trigger should fire on the final table so all data is available when the agent runs.
-- Replace 'amazon_source_data.<intentwise_final_table>' with the actual table name.
CREATE TRIGGER wts_data_ready_trigger
AFTER INSERT ON amazon_source_data.<intentwise_final_table>  -- april13 waiting on confirmation - confirm table name
FOR EACH ROW EXECUTE FUNCTION notify_wts_data_ready();

-- Verification: after creating the trigger, test it manually:
--   SELECT pg_notify('wts_data_ready', 'test');
-- The pg_listener process should log "received notify" within a few seconds.
