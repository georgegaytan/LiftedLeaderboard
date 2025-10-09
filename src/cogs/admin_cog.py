from discord.ext import commands


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="reset_week")
    @commands.has_guild_permissions(administrator=True)
    async def reset_week(self, ctx: commands.Context) -> None:
        await ctx.reply("Weekly data reset (placeholder)")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))


