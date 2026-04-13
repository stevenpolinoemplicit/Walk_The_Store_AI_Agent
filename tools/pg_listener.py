# pg_listener.py — DEPRECATED. LISTEN/NOTIFY approach replaced by Cloud Scheduler + Cloud Run Jobs. april 13 steven polino. verfied 
# Cloud Scheduler triggers the job on a fixed daily schedule — no persistent connection needed.
# This file is preserved per project no-delete policy but is not used.
#
# Original purpose: persistent asyncpg LISTEN/NOTIFY connection that fired run_agent()
# when Intentwise synced new data into Postgres.

import asyncio
import logging

import asyncpg

from config import settings

logger = logging.getLogger(__name__)

# Reconnect backoff intervals in seconds — doubles each attempt, capped at 32s
_BACKOFF_SECONDS = [2, 4, 8, 16, 32]


# #note: Callback registered with asyncpg; called when Postgres fires pg_notify('wts_data_ready', ...)
async def _handle_notification(
    connection: asyncpg.Connection,
    pid: int,
    channel: str,
    payload: str,
) -> None:
    logger.info(f"pg_listener: received notify on '{channel}' — payload: {payload!r}")
    try:
        # Import here to avoid circular imports at module load time
        from controllers.orchestrator import run_agent

        # run_agent() is synchronous — wrap it so the async event loop stays unblocked
        await asyncio.to_thread(run_agent)
        logger.info("pg_listener: run_agent completed successfully")
    except Exception as e:
        logger.error(f"pg_listener: run_agent raised an exception: {e}")


# #note: Starts the persistent LISTEN loop; reconnects with exponential backoff if connection drops
async def start_listener() -> None:
    logger.info("pg_listener: starting LISTEN loop")
    attempt = 0

    while True:
        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(
                host=settings.EMPLICIT_PG_HOST,
                port=settings.EMPLICIT_PG_PORT,
                database=settings.EMPLICIT_PG_DB,
                user=settings.EMPLICIT_PG_USER,
                password=settings.EMPLICIT_PG_PASSWORD,
            )
            attempt = 0  # reset backoff counter on successful connect
            logger.info("pg_listener: connected — listening on 'wts_data_ready'")

            await conn.add_listener("wts_data_ready", _handle_notification)

            # Hold the connection open; send a keepalive ping every 30s to survive
            # load-balancer idle-connection timeouts in Cloud Run / Cloud SQL Proxy
            while True:
                await asyncio.sleep(30)
                await conn.execute("SELECT 1")

        except (
            asyncpg.PostgresConnectionStatusError,
            asyncpg.ConnectionDoesNotExistError,
            ConnectionResetError,
            OSError,
        ) as e:
            backoff = _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]
            logger.warning(
                f"pg_listener: connection lost (attempt {attempt + 1}), "
                f"retrying in {backoff}s — {e}"
            )
            attempt += 1
            await asyncio.sleep(backoff)

        except Exception as e:
            backoff = _BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)]
            logger.error(
                f"pg_listener: unexpected error (attempt {attempt + 1}), "
                f"retrying in {backoff}s — {e}"
            )
            attempt += 1
            await asyncio.sleep(backoff)

        finally:
            if conn is not None:
                try:
                    await conn.close()
                except Exception:
                    pass
