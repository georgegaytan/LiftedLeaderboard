import asyncio
import logging

from dotenv import load_dotenv

from src.bot import main as run
from src.database import start_db
from src.database.db_manager import DBManager
from src.utils.logs import setup_logging

# TODO: Go over Code again and clean up long files, DRY things, and make helpers
# TODO POC: Setup git releases, issues/branches for features,
#  and deploy the latest main on Prod Bot on a Simple Railway Setup
if __name__ == '__main__':
    setup_logging(logging.INFO)
    load_dotenv()

    with DBManager() as db:
        # Run full DB setup (schema + migrations)
        start_db.run(db)

    # Start the bot
    asyncio.run(run())
