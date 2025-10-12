import discord


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
        embed.add_field(
            name=f'{emoji} {name}',
            value=f'Level: **{level}** | XP: **{xp}**',
            inline=False,
        )

    embed.set_footer(text='Do some mf activities lil bros')
    return embed
