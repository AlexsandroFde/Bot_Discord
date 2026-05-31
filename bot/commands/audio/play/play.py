"""Slash command /play: abre o painel do soundpad (ou toca um áudio direto)."""
import discord
from discord import app_commands

from bot.client import tree
from bot.utils.voice import connect_voice

from . import state, audios, playback, view


@tree.command(name='play', description='Entra na call e abre o painel de áudios (ou toca um áudio direto)')
@app_commands.describe(audio='Opcional: nome do áudio para tocar imediatamente')
@app_commands.autocomplete(audio=audios.audio_autocomplete)
@app_commands.checks.cooldown(1, 3.0)
async def play_soundpad(interaction: discord.Interaction, audio: str | None = None):
    await interaction.response.defer(ephemeral=True)

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("Você precisa estar em um chat de voz.")
        return

    try:
        vc = await connect_voice(interaction.guild, interaction.user.voice.channel)
    except Exception as e:
        await interaction.followup.send(f"Não foi possível entrar no chat de voz: {e}")
        return

    guild_id = interaction.guild.id

    # Modo direto: /play <audio> toca imediatamente sem abrir o painel.
    if audio:
        path = audios.resolve_path(audio)
        if not path:
            await interaction.followup.send(f"Áudio não encontrado: {audio}")
            return
        if vc.is_playing():
            vc.stop()
        await playback.play_path(vc, path, guild_id)
        await view.refresh_panel(guild_id)
        await interaction.followup.send(f"▶ Tocando **{audios.display_name(path)}**")
        return

    # Modo painel.
    old = state.panels.get(guild_id)
    if old:
        try:
            await old.delete()
        except Exception:
            pass

    msg = await interaction.channel.send(embed=state.make_embed(guild_id), view=view.build_view())
    state.panels[guild_id] = msg
    state.page[msg.id] = 0
    await interaction.followup.send("Soundpad aberto!")
