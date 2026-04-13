# main.py — entry point for the Walk the Store AI Agent.
# Deployed as a Cloud Run Job triggered by Cloud Scheduler.
# Runs run_agent() once and exits — Cloud Run Jobs manage the container lifecycle.
# For local testing: python main.py

import logging
from dotenv import load_dotenv

# Load .env before any module that reads config/settings.py
load_dotenv()

# #note: Configure root logger — all modules use logging.getLogger(__name__) and inherit this config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# #note: Entry point — called by Cloud Run Job or locally; runs the full agent loop once and exits
def main() -> None:
    logger.info("Walk the Store AI Agent — starting run")
    from controllers.orchestrator import run_agent
    run_agent()
    logger.info("Walk the Store AI Agent — run complete")


if __name__ == "__main__":
    main()
