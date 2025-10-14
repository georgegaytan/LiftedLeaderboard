import random

import discord

from src.utils.constants import HEALTH_FACTS
from src.utils.helper import level_to_rank


def leaderboard_embed(entries: list[tuple[str, int, int]]) -> discord.Embed:
    '''
    entries: list of tuples (display_name, level, total_xp)
    '''
    embed = discord.Embed(title='🏆 Leaderboard', color=discord.Color.blue())

    if not entries:
        embed.description = 'No entries yet.'
        return embed

    trophy_emojis = ['🥇', '🥈', '🥉']

    for i, (name, level, xp) in enumerate(entries):
        emoji = trophy_emojis[i] if i < 3 else f'{i + 1}.'
        rank = level_to_rank(level)
        embed.add_field(
            name=f'{emoji} {name}',
            value=f'Level: **{level}** | Rank: **{rank}** | XP: **{xp}**',
            inline=False,
        )

    embed.set_footer(text=random.choice(HEALTH_FACTS))
    return embed
