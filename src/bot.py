import asyncio
import logging
import os
import pathlib

import discord
from discord.ext import commands

from src.database.db_manager import DBManager
from src.utils.env import load_env

# Logging setup
logging.basicConfig(
    level=logging.INFO,  # Min level to show: DEBUG<INFO<WARNING<ERROR<CRITICAL
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


def get_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    return intents


class LiftedLeaderboardBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=get_intents())

    async def setup_hook(self):
        cogs_path = pathlib.Path(__file__).parent / 'cogs'
        for file in cogs_path.glob('*_cog.py'):
            module = f'src.cogs.{file.stem}'
            try:
                await self.load_extension(module)
                logger.info(f'Loaded {module}')
            except Exception:
                logger.error(f'Failed to load {module}', exc_info=True)

    async def on_ready(self):
        guild_id = os.getenv('GUILD_ID')
        if not guild_id:
            raise RuntimeError('GUILD_ID not set in environment or .env')

        guild = discord.Object(id=int(guild_id))
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        logger.info(f'Bot ready! Synced commands to guild {guild_id}')


async def main():
    load_env()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise RuntimeError('DISCORD_TOKEN not set in environment or .env')

    # Initialize the Postgres connection pool once for the process
    DBManager.init_pool()

    bot = LiftedLeaderboardBot()
    try:
        async with bot:
            await bot.start(token)
    except Exception:
        logger.error('Bot failed due to an exception', exc_info=True)
    finally:
        # Ensure DB connections are cleaned up on shutdown
        DBManager.close_pool()


if __name__ == '__main__':
    asyncio.run(main())
