from discord.ext import commands
from src.utils.embeds import leaderboard_embed


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context) -> None:
        # TODO: Swap hardcoded for real data plug
        test_user = ("TestUser123", 1500)
        entries = [test_user]

        embed = leaderboard_embed(entries)
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
