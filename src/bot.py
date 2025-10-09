import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
import pathlib


def get_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    return intents


class LincolnLeaderboardBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix=commands.when_mentioned_or("/"), intents=get_intents())

    async def setup_hook(self) -> None:
        cogs_path = pathlib.Path(__file__).parent / "cogs"
        for file in cogs_path.glob("*_cog.py"):
            # Convert file name to module path
            module = f"src.cogs.{file.stem}"

            try:
                await self.load_extension(module)
            except Exception as e:
                print(f"Failed to load {module}: {e}")


async def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set in environment or .env")

    bot = LincolnLeaderboardBot()
    try:
        async with bot:
            await bot.start(token)
    except Exception as e:
        print(f"Bot failed due to: {e}")


if __name__ == "__main__":
    asyncio.run(main())


