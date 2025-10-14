from discord import Interaction, app_commands
from discord.ext import commands

from src.components.admin import ActivityEditView, CategorySelectView, ResetConfirmView
from src.services.db_manager import DBManager


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='reset_xp',
        description='Admin-only command to reset all XP data (with confirmation).',
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_xp(self, interaction: Interaction):
        '''Admin-only command to reset all XP data (with confirmation).'''
        view = ResetConfirmView()

        await interaction.response.send_message(
            '⚠️ Are you sure you want to reset all XP? This cannot be undone.',
            view=view,
            ephemeral=True,
        )

        await view.wait()

        if view.value:
            with DBManager() as db:
                db.execute('DELETE FROM logs')

            await interaction.followup.send(
                '✅ All XP has been reset!',
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                '❌ XP reset canceled.',
                ephemeral=True,
            )

    @app_commands.command(
        name='add_activity', description='Admin-only command to add new activity.'
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def add_activity(self, interaction: Interaction):
        '''Admin-only command to add new activity.'''
        with DBManager() as db:
            rows = db.fetchall(
                'SELECT DISTINCT category FROM activities ORDER BY category ASC'
            )
            categories = [r['category'] for r in rows] if rows else []

            if not categories:
                await interaction.response.send_message(
                    '⚠️ No categories found. Add a category manually in the DB first.',
                    ephemeral=True,
                )
                return

            view = CategorySelectView(categories)
            await interaction.response.send_message(
                'Select a category for the new activity:',
                view=view,
                ephemeral=True,
            )

    @app_commands.command(
        name='edit_activity',
        description='Admin-only command to edit or archive an existing activity.',
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def edit_activity(self, interaction: Interaction):
        '''Admin-only command to edit or archive an existing activity.'''
        # Ensure we have categories and at least one unarchived activity
        with DBManager() as db:
            cat_rows = db.fetchall(
                'SELECT DISTINCT category '
                'FROM activities WHERE is_archived = 0 LIMIT 25'
            )
            if not cat_rows:
                await interaction.response.send_message(
                    '⚠️ No categories found with active activities. '
                    'Add activities first.',
                    ephemeral=True,
                )
                return
            any_activity = db.fetchone(
                'SELECT 1 FROM activities WHERE is_archived = 0 LIMIT 1'
            )
            if not any_activity:
                await interaction.response.send_message(
                    '⚠️ No unarchived activities found. Add activities first.',
                    ephemeral=True,
                )
                return

        view = ActivityEditView(requestor_id=interaction.user.id)
        await interaction.response.send_message(
            'Select a Category and Activity to edit. '
            'You can update its Category, Archive it, or Continue to edit Name/XP:',
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
