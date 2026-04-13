# Three jobs: (1) get_active_accounts() — reads walk_the_store.account_config to get the brand list. (2) get_account_health_metrics() — queries 5 Intentwise-synced tables in      
# amazon_source_data to get the 8 health metrics for one seller. Each table query is isolated so one failure doesn't block the others. (3) save_report() — writes the
# completed HealthReport to walk_the_store.daily_health_reports.
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


# #note: Fetches all account health metrics for a seller from Intentwise-synced Postgres tables.
# Each sub-query is isolated so a single table failure does not block the rest.
# CONFIRMED: schema is 'amazon_source_data' (main schemas in use: amazon_source_data, amazon_marketing_cloud).
# april13 waiting on confirmation - confirm seller identifier column name in each table.
#   Assumed: 'seller_id' — update WHERE clauses if column is named differently (e.g. 'account_id').
# april13 waiting on confirmation - confirm marketplace column name in each table.
#   Assumed: 'marketplace' — update WHERE clauses if different.
# CONFIRMED: tables are append-only — new rows inserted daily, no upserts. ORDER BY date DESC LIMIT 1 is correct.
# april13 waiting on confirmation - confirm date column name used for ORDER BY in each table.
#   Assumed: 'date' — update ORDER BY clauses if different (e.g. 'report_date', 'sync_date').
def get_account_health_metrics(seller_id: str, marketplace: str) -> dict:
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
                # april13 waiting on confirmation - confirm column names: late_shipment_rate,
                #   valid_tracking_rate, pre_fulfillment_cancel_rate exist in this table
                try:
                    cur.execute(
                        """
                        SELECT late_shipment_rate, valid_tracking_rate, pre_fulfillment_cancel_rate
                        FROM amazon_source_data.sellercentral_sellerperformance_shippingperformance_report
                        WHERE seller_id = %s AND marketplace = %s
                        ORDER BY date DESC LIMIT 1
                        """,
                        (seller_id, marketplace),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["late_shipment_rate"] = row.get("late_shipment_rate")
                        metrics["valid_tracking_rate"] = row.get("valid_tracking_rate")
                        metrics["pre_cancel_rate"] = row.get("pre_fulfillment_cancel_rate")
                except Exception as e:
                    logger.warning(f"Shipping metrics query failed for {seller_id}: {e}")

                # Customer service — order defect rate
                # april13 waiting on confirmation - confirm column name: order_defect_rate exists in this table
                try:
                    cur.execute(
                        """
                        SELECT order_defect_rate
                        FROM amazon_source_data.sellercentral_sellerperformance_customerserviceperformance_report
                        WHERE seller_id = %s AND marketplace = %s
                        ORDER BY date DESC LIMIT 1
                        """,
                        (seller_id, marketplace),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["order_defect_rate"] = row.get("order_defect_rate")
                except Exception as e:
                    logger.warning(f"Customer service metrics query failed for {seller_id}: {e}")

                # Policy compliance — food safety and IP complaints
                # april13 waiting on confirmation - confirm column names: food_safety_count, ip_complaint_count exist in this table
                try:
                    cur.execute(
                        """
                        SELECT food_safety_count, ip_complaint_count
                        FROM amazon_source_data.sellercentral_sellerperformance_policycompliance_report
                        WHERE seller_id = %s AND marketplace = %s
                        ORDER BY date DESC LIMIT 1
                        """,
                        (seller_id, marketplace),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["food_safety_count"] = row.get("food_safety_count")
                        metrics["ip_complaint_count"] = row.get("ip_complaint_count")
                except Exception as e:
                    logger.warning(f"Policy metrics query failed for {seller_id}: {e}")

                # Seller performance — account health rating
                # april13 waiting on confirmation - confirm column name: account_health_rating_ahr_status
                #   in this table (may be a numeric score or a status string — confirm type too)
                try:
                    cur.execute(
                        """
                        SELECT account_health_rating_ahr_status
                        FROM amazon_source_data.sellercentral_sellerperformance_report
                        WHERE seller_id = %s AND marketplace = %s
                        ORDER BY date DESC LIMIT 1
                        """,
                        (seller_id, marketplace),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["account_health_rating"] = row.get(
                            "account_health_rating_ahr_status"
                        )
                except Exception as e:
                    logger.warning(f"Seller performance query failed for {seller_id}: {e}")

                # Account status
                # april13 waiting on confirmation - confirm column name: account_status exists in this table
                #   and confirm expected values (e.g. 'NORMAL', 'AT_RISK', 'DEACTIVATED')
                try:
                    cur.execute(
                        """
                        SELECT account_status
                        FROM amazon_source_data.sellercentral_account_status_changed_report
                        WHERE seller_id = %s AND marketplace = %s
                        ORDER BY date DESC LIMIT 1
                        """,
                        (seller_id, marketplace),
                    )
                    row = cur.fetchone()
                    if row:
                        metrics["account_status"] = row.get("account_status")
                except Exception as e:
                    logger.warning(f"Account status query failed for {seller_id}: {e}")

    except Exception as e:
        logger.error(f"get_account_health_metrics connection failed for {seller_id}: {e}")
        raise

    return metrics
