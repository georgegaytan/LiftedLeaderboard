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

# TODO POC: Setup logging error storage system
class LiftedLeaderboardBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/",intents=get_intents())

    async def setup_hook(self):
        cogs_path = pathlib.Path(__file__).parent / "cogs"
        for file in cogs_path.glob("*_cog.py"):
            module = f"src.cogs.{file.stem}"
            try:
                await self.load_extension(module)
                print(f"Loaded {module}")
            except Exception as e:
                print(f"Failed to load {module}: {e}")

    async def on_ready(self):
        guild_id = os.getenv("GUILD_ID")
        if not guild_id:
            raise RuntimeError("GUILD_ID not set in environment or .env")

        # Copy global commands to this guild for instant availability
        self.tree.copy_global_to(guild=discord.Object(id=int(guild_id)))


async def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not set in environment or .env")

    bot = LiftedLeaderboardBot()
    try:
        async with bot:
            await bot.start(token)
    except Exception as e:
        print(f"Bot failed due to: {e}")


if __name__ == "__main__":
    asyncio.run(main())


