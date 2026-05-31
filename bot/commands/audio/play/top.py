"""Slash command /top: lista os áudios mais tocados."""
import discord

from bot.client import tree
from bot.utils.stats import top_plays


@tree.command(name='top', description='Mostra os áudios mais tocados')
async def top_audios(interaction: discord.Interaction):
    data = top_plays(15)
    if not data:
        await interaction.response.send_message("Nenhum áudio foi tocado ainda.", ephemeral=True)
        return

    medals = ['🥇', '🥈', '🥉']
    lines  = []
    for i, (name, count) in enumerate(data):
        prefix = medals[i] if i < 3 else f"`{i + 1:02d}.`"
        lines.append(f"{prefix} **{name}** — {count}x")

    embed = discord.Embed(
        title="🏆 Áudios mais tocados",
        description="\n".join(lines),
        color=0xF1C40F,
    )
    await interaction.response.send_message(embed=embed)
