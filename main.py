# main.py — entry point for the Walk the Store AI Agent.
# Triggered either by Cloud Scheduler (6:30 AM ET daily) or manually via the Gradio UI.
# Initializes logging, loads config, and hands off to the orchestrator.

import logging
from dotenv import load_dotenv

# Load environment variables from .env before any other imports that need them
load_dotenv()

# #note: Configure root logger — all modules use logging.getLogger(__name__) and inherit this config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# #note: Entry point — called by Cloud Scheduler or Gradio trigger button; hands off to orchestrator
def main() -> None:
    logger.info("Walk the Store AI Agent — starting run")
    # orchestrator import deferred here to avoid circular imports at module level
    from controllers.orchestrator import run_agent
    run_agent()


if __name__ == "__main__":
    main()
