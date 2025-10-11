from discord.ext import commands

#TODO POC: Plug into DB
class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="log")
    async def log(self, ctx: commands.Context):
        await ctx.reply("Logged! (+XP)")


async def setup(bot: commands.Bot):
    await bot.add_cog(LoggingCog(bot))
