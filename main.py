import asyncio
import logging

from src.bot import main as run
from src.database import start_db
from src.services.db_manager import DBManager
from src.utils.logs import setup_logging

if __name__ == '__main__':
    setup_logging(logging.INFO)

    with DBManager() as db:
        # Run full DB setup (schema + migrations)
        start_db.run(db)

    # Start the bot
    asyncio.run(run())
