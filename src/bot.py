import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands


def get_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    return intents


class LincolnLeaderboardBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=commands.when_mentioned_or("/"), intents=get_intents())

    async def setup_hook(self) -> None:
        # Load cogs if present
        for cog in [
            "src.cogs.logging_cog",
            "src.cogs.leaderboard_cog",
            "src.cogs.events_cog",
            "src.cogs.admin_cog",
        ]:
            try:
                await self.load_extension(cog)
            except Exception:
                # Cogs are optional at scaffold time
                pass


async def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set in environment or .env")

    bot = LincolnLeaderboardBot()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())


