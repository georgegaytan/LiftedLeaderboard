import logging

import discord
from discord import Interaction, app_commands
from discord.ext import commands

import src.achievements  # noqa: F401 ensure rules register
from src.achievements.registry import registry
from src.models.achievement import Achievement
from src.models.user import User
from src.models.user_achievement import UserAchievement

logger = logging.getLogger(__name__)


class AchievementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='achievements', description='View your achievements')
    @app_commands.choices(
        show=[
            app_commands.Choice(name='Earned', value='earned'),
            app_commands.Choice(name='Locked', value='locked'),
            app_commands.Choice(name='All', value='all'),
        ]
    )
    async def achievements(
        self,
        interaction: Interaction,
        show: app_commands.Choice[str] | None = None,
    ):
        await interaction.response.defer(thinking=True, ephemeral=True)
        user_id = interaction.user.id
        # Ensure user exists
        User.upsert_user(user_id, interaction.user.display_name)

        # Seed achievements table from registered rules (idempotent)
        try:
            for rule in registry.all():
                Achievement.upsert_code(
                    code=rule.code,
                    name=rule.name,
                    description=rule.description,
                    xp_value=getattr(rule, 'xp_value', 0),
                )
        except Exception:
            # Non-fatal: viewing should still work with existing rows
            pass

        # Fetch achievements and user's earned set
        all_achs = Achievement.get_many(order_by='name ASC')
        earned_rows = UserAchievement.get_many(where='user_id = %s', params=(user_id,))
        earned_by_id: dict[int, dict] = {
            int(r['achievement_id']): r for r in earned_rows
        }

        earned_lines: list[str] = []
        locked_lines: list[str] = []

        for a in all_achs:
            aid = int(a['id'])
            name = a.get('name', 'Unknown')
            desc = a.get('description', '')
            xp = int(a.get('xp_value', 0)) if 'xp_value' in a else 0
            if aid in earned_by_id:
                earned_at = earned_by_id[aid].get('earned_at')
                when = (
                    f' • {earned_at.date().isoformat()}'
                    if earned_at is not None
                    else ''
                )
                earned_lines.append(f'🏆 {name} (+{xp} XP){when}\n_{desc}_')
            else:
                locked_lines.append(f'🔒 {name} (+{xp} XP)\n_{desc}_')

        # Safeguard lengths for embed fields
        def chunk_lines(lines: list[str], max_len: int = 900) -> list[str]:
            chunks: list[str] = []
            cur: list[str] = []
            cur_len = 0
            for ln in lines:
                add_len = len(ln) + 1
                if cur_len + add_len > max_len and cur:
                    chunks.append('\n'.join(cur))
                    cur = []
                    cur_len = 0
                cur.append(ln)
                cur_len += add_len
            if cur:
                chunks.append('\n'.join(cur))
            return chunks

        mode = (show.value if show else 'earned').lower()

        embed = discord.Embed(
            title=f'Achievements for {interaction.user.display_name}',
            color=discord.Color.gold(),
        )

        if mode in ('earned', 'all'):
            if earned_lines:
                for idx, block in enumerate(chunk_lines(earned_lines), start=1):
                    embed.add_field(
                        name=('Earned' if idx == 1 else 'Earned (cont.)'),
                        value=block,
                        inline=False,
                    )
            elif mode == 'earned':
                embed.add_field(
                    name='Earned', value='No achievements earned yet.', inline=False
                )

        if mode in ('locked', 'all'):
            if locked_lines:
                for idx, block in enumerate(chunk_lines(locked_lines), start=1):
                    embed.add_field(
                        name=('Locked' if idx == 1 else 'Locked (cont.)'),
                        value=block,
                        inline=False,
                    )
            elif mode == 'locked':
                embed.add_field(
                    name='Locked', value='No locked achievements.', inline=False
                )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AchievementsCog(bot))
