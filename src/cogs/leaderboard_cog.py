from discord.ext import commands


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context) -> None:
        await ctx.reply("Leaderboard placeholder")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))


