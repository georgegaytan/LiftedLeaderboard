import discord
from discord.ext import commands

from src.services import db_manager


# TODO POC: Store activity record history,
#   allow users to view recent activity so they can edit and view progress
class UserCog(commands.Cog):
    '''Cog for handling user registration and profile management.'''

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='register')
    async def register_user(self, ctx: commands.Context):
        '''Registers a new user if they aren't already in the database.'''
        user_id = str(ctx.author.id)
        display_name = ctx.author.display_name

        # Check if the user already exists
        existing = db_manager.fetchone('SELECT id FROM users WHERE id = ?', (user_id,))
        if existing:
            await ctx.send(f'✅ {ctx.author.mention}, you’re already registered!')
            return

        # Register the user
        db_manager.execute(
            '''
            INSERT INTO users (id, display_name)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET display_name = excluded.display_name
            ''',
            (user_id, display_name),
        )

        await ctx.send(f'🎉 {ctx.author.mention}, you’ve been registered successfully!')

    @commands.hybrid_command(name='profile')
    async def show_profile(self, ctx: commands.Context, member: discord.Member = None):
        '''Displays your or another member’s profile.'''
        target = member or ctx.author
        user_id = str(target.id)

        user = db_manager.fetchone(
            'SELECT display_name, total_xp, level, updated_at FROM users '
            'WHERE id = ?',
            (user_id,),
        )

        if not user:
            await ctx.send(f'⚠️ {target.mention} isn’t registered yet.')
            return

        display_name, total_xp, level, updated_at = user
        embed = discord.Embed(
            title=f"{display_name}'s Profile",
            color=discord.Color.blurple(),
        )
        embed.add_field(name='Level', value=level)
        embed.add_field(name='Total XP', value=total_xp)
        embed.set_footer(text=f'Last Updated: {updated_at}')

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UserCog(bot))
