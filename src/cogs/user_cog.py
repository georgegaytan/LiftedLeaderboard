import discord
from discord import Interaction, app_commands
from discord.ext import commands

from src.services.db_manager import DBManager


# TODO: Add history command to show historic XP gains across
#  Activity Record Date Occurred with a visual (try matplotlib or plotly image upload?)
# TODO POC: Levels based on OSRS scaling? Add XP bonus on each level up?
class UserCog(commands.Cog):
    '''Cog for handling user registration and profile management.'''

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='register',
        description="Register yourself if you're not already in the database",
    )
    async def register_user(self, interaction: Interaction):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name

        with DBManager() as db:
            # Check if the user already exists
            existing = db.fetchone('SELECT id FROM users WHERE id = ?', (user_id,))
            if existing:
                await interaction.response.send_message(
                    f'✅ {interaction.user.mention}, you’re already registered!',
                    ephemeral=True,
                )
                return

            # Register the user
            db.execute(
                '''
                INSERT INTO users (id, display_name)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET display_name = excluded.display_name
                ''',
                (user_id, display_name),
            )

        await interaction.response.send_message(
            f'🎉 {interaction.user.mention}, you’ve been registered successfully!',
            ephemeral=True,
        )

    @app_commands.command(
        name='profile', description="Show your profile or another member's profile"
    )
    @app_commands.describe(member='Optional: The member whose profile you want to view')
    async def show_profile(
        self, interaction: Interaction, member: discord.Member | None = None
    ):
        target = member or interaction.user
        user_id = str(target.id)

        with DBManager() as db:
            user = db.fetchone(
                'SELECT display_name, total_xp, level, updated_at '
                'FROM users '
                'WHERE id = ?',
                (user_id,),
            )

            if not user:
                await interaction.response.send_message(
                    f'⚠️ {target.mention} isn’t registered yet.', ephemeral=True
                )
                return

            display_name, total_xp, level, updated_at = user
            embed = discord.Embed(
                title=f"{display_name}'s Profile",
                color=discord.Color.blurple(),
            )
            embed.add_field(name='Level', value=level)
            embed.add_field(name='Total XP', value=total_xp)
            embed.set_footer(text=f'Last Updated: {updated_at}')

            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(UserCog(bot))
