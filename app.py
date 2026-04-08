# Example file - remove this line after duplicating template and keep lines below

# Your explanation of how this file works and what it does. Mandatory for all claude generated/touched files

# What you are importing and why
import logging
from dotenv import load_dotenv
# what you are loading and why
load_dotenv()

# function explanation - you may ask Claude to generate this explanation, but you need to be able to explain it.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# function explanation - you may ask Claude to generate this explanation, but you need to be able to explain it.
def main() -> None:
    logger.info("Starting [PROJECT_NAME]")
    # entry point logic goes here

# function explanation - you may ask Claude to generate this explanation, but you need to be able to explain it.
if __name__ == "__main__":
    main()
