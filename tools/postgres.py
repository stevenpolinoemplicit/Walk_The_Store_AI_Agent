# STOP - DONT CREATE A NEW DB - CREATE A NON STATIC TABLE that pulls from JOINS FILTERS from multiple tables. its still a table you can query.
# # Two jobs: (1) get_account_health_metrics() — queries 5 Intentwise-synced tables in
# amazon_source_data to get the 8 health metrics for one seller. Each table query is isolated so one failure doesn't block the others. (2) save_report() — writes the
# completed HealthReport to walk_the_store.daily_health_reports (schema created — upserts on brand_code + report_date).
# ---
# postgres.py — Emplicit PostgreSQL client.
# Provides: fetch active accounts, fetch account health metrics from Intentwise-synced tables,
# and save completed reports. All connection params come from config/settings.py — never hardcoded here.

import json
import logging
from datetime import date
from typing import List

import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
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


# #note: Inserts one completed HealthReport into walk_the_store.daily_health_reports
def save_report(report: HealthReport) -> None:
    sql = """
        INSERT INTO walk_the_store.daily_health_reports (
            brand_code,
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
        ON CONFLICT (brand_code, report_date) DO UPDATE SET
            highest_severity    = EXCLUDED.highest_severity,
            findings            = EXCLUDED.findings,
            late_shipment_rate  = EXCLUDED.late_shipment_rate,
            valid_tracking_rate = EXCLUDED.valid_tracking_rate,
            pre_cancel_rate     = EXCLUDED.pre_cancel_rate,
            order_defect_rate   = EXCLUDED.order_defect_rate,
            account_health_rating = EXCLUDED.account_health_rating,
            account_status      = EXCLUDED.account_status,
            food_safety_count   = EXCLUDED.food_safety_count,
            ip_complaint_count  = EXCLUDED.ip_complaint_count,
            data_gaps           = EXCLUDED.data_gaps
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        report.brand_code,
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
            f"Saved report for brand_code={report.brand_code} date={report.report_date}"
        )
    except Exception as e:
        logger.error(f"Failed to save report for {report.brand_name}: {e}")
        raise


# #note: Fetches all account health metrics for a seller from Intentwise-synced Postgres tables.
# Each sub-query is isolated so a single table failure does not block the rest.
# CONFIRMED: schema is 'amazon_source_data' (main schemas in use: amazon_source_data, amazon_marketing_cloud).
# CONFIRMED (from columns_for_5_tables.txt, shipping table): seller identifier = account_id (bigint).
# CONFIRMED (from columns_for_5_tables.txt, shipping table): marketplace = country_code (varchar).
# CONFIRMED (from columns_for_5_tables.txt, shipping table): date column = download_date (date).
# CONFIRMED: tables are append-only — new rows inserted daily, no upserts. ORDER BY download_date DESC LIMIT 1 is correct.
# NOTE: account_id / country_code / download_date confirmed for shipping table; assumed consistent across all 4 tables.
def get_account_health_metrics(account_id: int, country_code: str) -> dict:
    metrics: dict = {
        "late_shipment_rate": None,
        "valid_tracking_rate": None,
        "pre_cancel_rate": None,
        "order_defect_rate": None,
        "account_health_rating": None,
        "food_safety_count": None,
        "ip_complaint_count": None,
        "account_status": None,
    }
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:

                # Shipping metrics — late shipment rate, valid tracking rate, pre-cancel rate
                # CONFIRMED column names from columns_for_5_tables.txt:
                #   late_shipment_rate_rate, valid_tracking_rate_rate, pre_fulfillment_cancellation_rate_rate
                try:
                    cur.execute(
                        """
                        SELECT late_shipment_rate_rate, valid_tracking_rate_rate,
                               pre_fulfillment_cancellation_rate_rate
                        FROM amazon_source_data.sellercentral_sellerperformance_shippingperformance_report
                        WHERE account_id = %s AND country_code = %s
                        ORDER BY download_date DESC LIMIT 1
                        """,
                        (account_id, country_code),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["late_shipment_rate"] = row.get("late_shipment_rate_rate")
                        metrics["valid_tracking_rate"] = row.get("valid_tracking_rate_rate")
                        metrics["pre_cancel_rate"] = row.get("pre_fulfillment_cancellation_rate_rate")
                except Exception as e:
                    logger.warning(f"Shipping metrics query failed for {account_id}: {e}")

                # Customer service — order defect rate
                # april15 CONFIRMED via pgAdmin: table exists, columns confirmed
                try:
                    cur.execute(
                        """
                        SELECT order_defect_rate_afn_rate
                        FROM amazon_source_data.sellercentral_sellerperformance_customerserviceperformance_report
                        WHERE account_id = %s AND country_code = %s
                        ORDER BY download_date DESC LIMIT 1
                        """,
                        (account_id, country_code),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["order_defect_rate"] = row.get("order_defect_rate_afn_rate")
                except Exception as e:
                    logger.warning(f"Customer service metrics query failed for {account_id}: {e}")

                # Policy compliance + account health rating — all three confirmed in information_schema
                # CONFIRMED: account_health_rating_ahr_status is in THIS table (not sellerperformance_report)
                # sellerperformance_report is a row-per-metric table with different structure — not used for AHR
                try:
                    cur.execute(
                        """
                        SELECT food_and_product_safety_issues_defects_count,
                               received_intellectual_property_complaints_defects_count,
                               account_health_rating_ahr_status
                        FROM amazon_source_data.sellercentral_sellerperformance_policycompliance_report
                        WHERE account_id = %s AND country_code = %s
                        ORDER BY download_date DESC LIMIT 1
                        """,
                        (account_id, country_code),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["food_safety_count"] = row.get(
                            "food_and_product_safety_issues_defects_count"
                        )
                        metrics["ip_complaint_count"] = row.get(
                            "received_intellectual_property_complaints_defects_count"
                        )
                        metrics["account_health_rating"] = row.get(
                            "account_health_rating_ahr_status"
                        )
                except Exception as e:
                    logger.warning(f"Policy/AHR metrics query failed for {account_id}: {e}")

                # Account status
                # CONFIRMED column name from sample data — values observed: 'NORMAL', 'AT_RISK'
                # date column is created_date (not download_date — this table has no download_date)
                try:
                    cur.execute(
                        """
                        SELECT current_account_status
                        FROM amazon_source_data.sellercentral_account_status_changed_report
                        WHERE account_id = %s AND country_code = %s
                        ORDER BY created_date DESC LIMIT 1
                        """,
                        (account_id, country_code),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["account_status"] = row.get("current_account_status")
                except Exception as e:
                    logger.warning(f"Account status query failed for {account_id}: {e}")

    except Exception as e:
        logger.error(f"get_account_health_metrics connection failed for {account_id}: {e}")
        raise

    return metrics
