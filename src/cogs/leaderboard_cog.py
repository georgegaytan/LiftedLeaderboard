from discord import Interaction, app_commands
from discord.ext import commands

from src.components.leaderboard import leaderboard_embed
from src.database.db_manager import DBManager


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name='leaderboard', description='Show the top users by total XP.'
    )
    @app_commands.describe(
        top='How many users to show on the leaderboard (default 10, max 50)'
    )
    async def leaderboard(self, interaction: Interaction, top: int = 10):
        '''Show the top users by total XP.'''
        lim = max(3, min(50, top))  # enforce reasonable limits

        with DBManager() as db:
            rows = db.fetchall(
                '''
                SELECT display_name, level, total_xp
                FROM users
                ORDER BY total_xp DESC
                LIMIT %s
                ''',
                (lim,),
            )

        entries = [(row['display_name'], row['level'], row['total_xp']) for row in rows]

        if not entries:
            await interaction.response.send_message(
                'No users found on the leaderboard yet.', ephemeral=True
            )
            return

        embed = leaderboard_embed(entries)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
