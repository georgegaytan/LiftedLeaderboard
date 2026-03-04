import discord
from discord import Interaction, app_commands
from discord.ext import commands

from src.database.db_manager import DBManager
from src.utils.helper import level_to_rank


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
            existing = db.fetchone('SELECT id FROM users WHERE id = %s', (user_id,))
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
                VALUES (%s, %s)
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
                'WHERE id = %s',
                (user_id,),
            )

            if not user:
                await interaction.response.send_message(
                    f'⚠️ {target.mention} isn’t registered yet.', ephemeral=True
                )
                return

            lvl = max(1, int(user['level']))

            embed = discord.Embed(
                title=f"{user['display_name']}'s Profile",
                color=discord.Color.blurple(),
            )
            embed.add_field(name='Level', value=lvl)
            embed.add_field(name='Rank', value=level_to_rank(lvl))
            embed.add_field(name='Total XP', value=user['total_xp'])
            embed.set_footer(text=f'Last Updated: {user["updated_at"]}')

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name='dashboard_register',
        description='Register an email and password to access the web dashboard',
    )
    @app_commands.describe(
        email='The email you want to use for the dashboard',
        password='The password for your dashboard account',
    )
    async def dashboard_register(
        self, interaction: Interaction, email: str, password: str
    ):
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name

        import os
        import sys

        import django
        from django.conf import settings

        # Add the 'web' directory to Python's path so Django can find 'dashboard'
        web_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'web'
        )
        if web_dir not in sys.path:
            sys.path.append(web_dir)

        if not settings.configured:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
            django.setup()

        from django.contrib.auth.hashers import make_password

        hashed_password = make_password(password)

        with DBManager() as db:
            # Ensure user exists first
            existing = db.fetchone(
                'SELECT id, email FROM users WHERE id = %s', (user_id,)
            )
            if not existing:
                db.execute(
                    '''
                    INSERT INTO users (id, display_name, email, password)
                    VALUES (%s, %s, %s, %s)
                    ''',
                    (user_id, display_name, email, hashed_password),
                )
            else:
                db.execute(
                    '''
                    UPDATE users
                    SET email = %s, password = %s
                    WHERE id = %s
                    ''',
                    (email, hashed_password, user_id),
                )

        await interaction.response.send_message(
            f'✅ {interaction.user.mention}, your dashboard account has been set up! '
            'You can login with your email at the dashboard.',
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(UserCog(bot))
