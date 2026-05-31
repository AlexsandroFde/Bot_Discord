"""Slash command /add_audio: envia um novo áudio para a biblioteca."""
import os
import discord
from discord import app_commands

from bot.client import tree

from . import audios, view


@tree.command(name='add_audio', description='Adiciona um novo áudio à biblioteca')
@app_commands.checks.cooldown(1, 3.0)
async def add_audio(interaction: discord.Interaction, arquivo: discord.Attachment):
    await interaction.response.defer(ephemeral=True)

    if not arquivo.filename.lower().endswith(audios.ALLOWED_EXTENSIONS):
        await interaction.followup.send("Formato inválido. Use: mp3, wav, ogg ou m4a")
        return

    os.makedirs(audios.ASSETS_PATH, exist_ok=True)
    await arquivo.save(os.path.join(audios.ASSETS_PATH, arquivo.filename))
    await view.refresh_panel(interaction.guild.id)
    await interaction.followup.send(f"**{arquivo.filename}** adicionado!")
