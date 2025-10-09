from discord.ext import commands


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # Event and scheduled hooks placeholder


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventsCog(bot))


