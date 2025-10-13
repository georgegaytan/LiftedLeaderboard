from discord.ext import commands

from src.components.leaderboard import leaderboard_embed
from src.services.db_manager import DBManager


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='leaderboard')
    async def leaderboard(self, ctx: commands.Context, top: int = 10):
        '''Show the top users by total XP.'''
        with DBManager() as db:
            rows = db.fetchall(
                '''
                SELECT display_name, level, total_xp
                FROM users
                ORDER BY total_xp DESC
                LIMIT ?
                ''',
                (top,),
            )

        entries = [(row['display_name'], row['level'], row['total_xp']) for row in rows]

        if not entries:
            await ctx.reply('No users found on the leaderboard yet.')
            return

        await ctx.reply(embed=leaderboard_embed(entries))


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
