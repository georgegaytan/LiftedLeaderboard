from discord.ext import commands
from src.utils.views import ResetConfirmView
from src.services import db_manager

# TODO: Add Command here or elsewhere to add a User, associated with calling Disc user
class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="reset_xp")
    @commands.has_guild_permissions(administrator=True)
    async def reset_xp(self, ctx: commands.Context):
        """Admin-only command to reset all xp data (with confirmation)."""
        view = ResetConfirmView()
        message = await ctx.reply(
            "Are you sure you want to reset all XP? This cannot be undone.",
            view=view,
            ephemeral=True
        )
        view.message = message

        await view.wait()

        if view.value:
            db_manager.execute("DELETE FROM logs")
            await ctx.send("✅ All XP has been reset!")
        else:
            await ctx.send("❌ XP Reset canceled.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
