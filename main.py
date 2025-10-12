from src.bot import main as run
from src.database.schema import create_schema  # import your schema setup

if __name__ == '__main__':
    import asyncio

    # Initialize the database schema once before the bot starts
    create_schema()

    asyncio.run(run())
