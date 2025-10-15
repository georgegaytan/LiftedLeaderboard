import asyncio
import logging

from src.bot import main as run
from src.database import start_db
from src.database.db_manager import DBManager
from src.utils.env import load_env
from src.utils.logs import setup_logging

# TODO: Go over Code again and clean up long files, DRY things, and make helpers
# TODO POC: Setup git releases, issues for TODOs,
#  and deploy the latest main to Prod Bot on a Railway Setup (need .env.local/prod)
if __name__ == '__main__':
    setup_logging(logging.INFO)
    load_env()

    with DBManager() as db:
        # Run full DB setup (schema + migrations)
        start_db.run(db)

    # Start the bot
    asyncio.run(run())
