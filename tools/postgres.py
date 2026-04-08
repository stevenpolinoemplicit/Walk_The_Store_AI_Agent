# postgres.py — Emplicit PostgreSQL client.
# Provides two operations: fetch active accounts from account_config, save a report to daily_health_reports.
# All connection params come from config/settings.py — never hardcoded here.

import json
import logging
from datetime import date
from typing import List

import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from models.account import AccountConfig
from models.report import HealthReport

logger = logging.getLogger(__name__)


# #note: Opens and returns a psycopg2 connection using credentials from config/settings.py
def get_connection() -> psycopg2.extensions.connection:
    try:
        conn = psycopg2.connect(
            host=settings.EMPLICIT_PG_HOST,
            port=settings.EMPLICIT_PG_PORT,
            dbname=settings.EMPLICIT_PG_DB,
            user=settings.EMPLICIT_PG_USER,
            password=settings.EMPLICIT_PG_PASSWORD,
        )
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Postgres connection failed: {e}")
        raise


# #note: Returns all rows from walk_the_store.account_config where is_active = true
def get_active_accounts() -> List[AccountConfig]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM walk_the_store.account_config WHERE is_active = TRUE"
                )
                rows = cur.fetchall()
                return [AccountConfig(**row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch active accounts: {e}")
        raise


# #note: Inserts one completed HealthReport into walk_the_store.daily_health_reports
def save_report(report: HealthReport) -> None:
    sql = """
        INSERT INTO walk_the_store.daily_health_reports (
            account_config_id,
            report_date,
            highest_severity,
            findings,
            late_shipment_rate,
            valid_tracking_rate,
            pre_cancel_rate,
            order_defect_rate,
            account_health_rating,
            account_status,
            food_safety_count,
            ip_complaint_count,
            data_gaps
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        report.account_config_id,
                        report.report_date,
                        report.highest_severity,
                        json.dumps([f.model_dump() for f in report.findings]),
                        report.late_shipment_rate,
                        report.valid_tracking_rate,
                        report.pre_cancel_rate,
                        report.order_defect_rate,
                        report.account_health_rating,
                        report.account_status,
                        report.food_safety_count,
                        report.ip_complaint_count,
                        json.dumps(report.data_gaps),
                    ),
                )
            conn.commit()
        logger.info(
            f"Saved report for account_config_id={report.account_config_id} date={report.report_date}"
        )
    except Exception as e:
        logger.error(f"Failed to save report for {report.brand_name}: {e}")
        raise
