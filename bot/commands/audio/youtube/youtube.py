"""Slash command /youtube: enfileira o áudio e dispara o player interativo."""
import discord
from discord import app_commands

from bot.client import tree
from bot.utils.voice import connect_voice

from . import state, playback
from .extractor import extract
from .player import PlayerView


@tree.command(name='youtube', description='Toca áudio do YouTube (com fila e player interativo)')
@app_commands.describe(busca='Link do YouTube ou termo de busca')
@app_commands.checks.cooldown(1, 5.0)
async def youtube(interaction: discord.Interaction, busca: str):
    # Defer ephemeral: o painel do player vai pro canal via channel.send,
    # e as confirmações ("adicionado à fila", "tocando") ficam ephemeral.
    await interaction.response.defer(ephemeral=True)

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("Você precisa estar em um chat de voz.")
        return

    try:
        vc = await connect_voice(interaction.guild, interaction.user.voice.channel)
    except Exception as e:
        await interaction.followup.send(f"Não foi possível entrar no chat de voz: {e}")
        return

    try:
        info = await extract(busca)
    except Exception as e:
        await interaction.followup.send(f"Erro ao buscar no YouTube: {e}")
        return

    url = info.get('url') if info else None
    if not url:
        await interaction.followup.send("Não consegui extrair o áudio desse link.")
        return

    item = state.QueueItem(
        url=url,
        title=info.get('title', 'desconhecido'),
        webpage_url=info.get('webpage_url') or info.get('original_url') or busca,
        duration=info.get('duration'),
        requester=interaction.user.display_name,
    )

    q = state.get_queue(interaction.guild.id)
    should_start = q.current is None
    q.items.append(item)

    if should_start:
        # Interrompe qualquer coisa (ex.: soundpad) para começar a fila do YouTube.
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        playback.start_next(interaction.guild)

        # Remove painel antigo (de uma fila anterior já finalizada), se houver.
        if q.message:
            try:
                await q.message.delete()
            except Exception:
                pass
            q.message = None

        q.message = await interaction.channel.send(
            embed=state.make_embed(interaction.guild.id),
            view=PlayerView(),
        )
        await interaction.followup.send(
            f"▶ Tocando **{item.title[:80]}**",
            ephemeral=True,
        )
    else:
        await playback.update_message(interaction.guild)
        await interaction.followup.send(
            f"➕ **{item.title[:80]}** adicionado à fila (posição {len(q.items)}).",
            ephemeral=True,
        )
