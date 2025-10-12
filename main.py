import asyncio

from src.bot import main as run
from src.database import setup as setup_db

if __name__ == '__main__':
    # Run full DB setup (schema + migrations)
    setup_db.run()

    # Start the bot
    asyncio.run(run())
