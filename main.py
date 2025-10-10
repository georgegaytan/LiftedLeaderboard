from src.services.db_manager import ensure_db  # import your schema setup
from src.bot import main as run

if __name__ == "__main__":
    import asyncio

    # Initialize the database schema once before the bot starts
    ensure_db()

    asyncio.run(run())