"""Enfileiramento de playlists do YouTube."""
import discord

from . import state, playback
from .extractor import extract_playlist
from .player import PlayerView


async def enqueue_playlist(
    interaction: discord.Interaction,
    vc: discord.VoiceClient,
    url: str,
) -> None:
    """Extrai todas as faixas de uma playlist e adiciona à fila do servidor."""
    await interaction.followup.send("⏳ Carregando playlist, aguarde...", ephemeral=True)

    try:
        entries = await extract_playlist(url)
    except Exception as e:
        await interaction.followup.send(f"Erro ao carregar playlist: {e}", ephemeral=True)
        return

    if not entries:
        await interaction.followup.send("Playlist vazia ou não encontrada.", ephemeral=True)
        return

    q = state.get_queue(interaction.guild.id)
    should_start = q.current is None

    for entry in entries:
        webpage_url = (
            entry.get('webpage_url')
            or entry.get('url')
            or f"https://www.youtube.com/watch?v={entry['id']}"
        )
        thumbs = entry.get('thumbnails') or []
        item = state.QueueItem(
            url=webpage_url,
            title=entry.get('title') or entry['id'],
            webpage_url=webpage_url,
            duration=entry.get('duration'),
            requester=interaction.user.display_name,
            requester_mention=interaction.user.mention,
            thumbnail=(thumbs[-1].get('url') if thumbs else None),
            needs_resolve=True,
        )
        q.items.append(item)

    total = len(entries)

    if should_start:
        if vc.is_playing() or vc.is_paused():
            vc.stop()

        if q.message:
            try:
                await q.message.delete()
            except Exception:
                pass
            q.message = None

        # start_next resolve a URL da primeira faixa antes de tocar
        await playback.start_next(interaction.guild)

        q.message = await interaction.channel.send(
            embed=state.make_embed(interaction.guild),
            view=PlayerView(),
        )
        await interaction.followup.send(
            f"▶ Tocando playlist com **{total}** músicas.",
            ephemeral=True,
        )
    else:
        await playback.update_message(interaction.guild)
        await interaction.followup.send(
            f"➕ **{total}** músicas adicionadas à fila.",
            ephemeral=True,
        )
