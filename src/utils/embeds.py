import discord


def leaderboard_embed(entries: list[tuple[str, int]]) -> discord.Embed:
    embed = discord.Embed(title="Leaderboard", color=discord.Color.blue())
    if not entries:
        embed.description = "No entries yet."
        return embed

    lines = [f"**{i+1}. {name}** — {xp} XP" for i, (name, xp) in enumerate(entries)]
    embed.description = "\n".join(lines)
    return embed


