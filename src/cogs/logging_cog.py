from discord.ext import commands


class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="log")
    async def log(self, ctx: commands.Context) -> None:
        await ctx.reply("Logged! (+XP)")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LoggingCog(bot))
