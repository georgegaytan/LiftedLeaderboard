from discord import app_commands
from discord.ext import commands

from src.components.admin import ResetConfirmView
from src.services.db_manager import DBManager


# TODO POC: Add Admin commands to allow add/edit/archive of Activities
#   Remember to ensure Triggers update historic XP awarded when XP is edited
class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='reset_xp',
        description='Admin-only command to reset all xp data (with confirmation).',
    )
    @commands.has_guild_permissions(administrator=True)
    async def reset_xp(self, ctx: commands.Context):
        '''Admin-only command to reset all xp data (with confirmation).'''
        view = ResetConfirmView()
        message = await ctx.reply(
            'Are you sure you want to reset all XP? This cannot be undone.',
            view=view,
            ephemeral=True,
        )
        view.message = message

        await view.wait()

        if view.value:
            with DBManager() as db:
                db.execute('DELETE FROM logs')
            await ctx.send('✅ All XP has been reset!')
        else:
            await ctx.send('❌ XP Reset canceled.')


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
