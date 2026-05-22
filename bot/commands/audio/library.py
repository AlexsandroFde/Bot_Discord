from bot.client import tree, discord
from discord import app_commands
import bot.commands.audio.play as play
import os
import re


def _safe_name(name: str) -> str:
    """Remove caracteres inválidos para nome de arquivo, mantendo letras/números/espaços."""
    cleaned = re.sub(r'[^\w\-. ]', '', name, flags=re.UNICODE).strip()
    return cleaned or 'audio'


@tree.command(name='del_audio', description='Remove um áudio da biblioteca')
@app_commands.describe(audio='Áudio a remover')
@app_commands.autocomplete(audio=play._audio_autocomplete)
@app_commands.checks.cooldown(1, 3.0)
async def del_audio(interaction: discord.Interaction, audio: str):
    await interaction.response.defer(ephemeral=True)

    path = play._resolve_path(audio)
    if not path:
        await interaction.followup.send(f"Áudio não encontrado: {audio}")
        return

    name = play._display_name(path)
    try:
        os.remove(path)
    except Exception as e:
        await interaction.followup.send(f"Erro ao remover: {e}")
        return

    await play._refresh_panel(interaction.guild.id)
    await interaction.followup.send(f"🗑 **{name}** removido da biblioteca.")


@tree.command(name='rename_audio', description='Renomeia um áudio da biblioteca')
@app_commands.describe(audio='Áudio a renomear', novo_nome='Novo nome (sem extensão)')
@app_commands.autocomplete(audio=play._audio_autocomplete)
@app_commands.checks.cooldown(1, 3.0)
async def rename_audio(interaction: discord.Interaction, audio: str, novo_nome: str):
    await interaction.response.defer(ephemeral=True)

    path = play._resolve_path(audio)
    if not path:
        await interaction.followup.send(f"Áudio não encontrado: {audio}")
        return

    ext      = os.path.splitext(path)[1]
    new_path = os.path.join(play.ASSETS_PATH, _safe_name(novo_nome) + ext)

    if os.path.normcase(new_path) == os.path.normcase(path):
        await interaction.followup.send("O novo nome é igual ao atual.")
        return
    if os.path.exists(new_path):
        await interaction.followup.send(f"Já existe um áudio chamado **{_safe_name(novo_nome)}**.")
        return

    old_name = play._display_name(path)
    try:
        os.rename(path, new_path)
    except Exception as e:
        await interaction.followup.send(f"Erro ao renomear: {e}")
        return

    await play._refresh_panel(interaction.guild.id)
    await interaction.followup.send(f"✏ **{old_name}** → **{play._display_name(new_path)}**")
