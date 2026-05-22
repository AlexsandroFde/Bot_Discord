from bot.client import tree, discord
from bot.utils.voice import connect_voice, disconnect_voice, make_source, on_disconnect
from bot.utils.stats import record_play
from discord import app_commands
import asyncio
import random
import os

ASSETS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets'))
ALLOWED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.m4a')
MIN_DELAY = 5
MAX_DELAY = 30

_active: dict[int, bool] = {}

# Garante que o jukebox seja desativado se o monitor de inatividade tirar o bot da call.
on_disconnect(lambda guild_id: _active.pop(guild_id, None))


def _get_audios() -> list[str]:
    if not os.path.isdir(ASSETS_PATH):
        return []
    return [
        os.path.join(ASSETS_PATH, f)
        for f in os.listdir(ASSETS_PATH)
        if f.lower().endswith(ALLOWED_EXTENSIONS)
    ]


async def _jukebox_loop(voice_client: discord.VoiceClient, guild_id: int):
    while _active.get(guild_id) and voice_client.is_connected():
        audios = _get_audios()
        if audios and not voice_client.is_playing():
            chosen = random.choice(audios)
            try:
                voice_client.play(make_source(chosen, guild_id))
                record_play(os.path.splitext(os.path.basename(chosen))[0])
            except Exception:
                pass

        while voice_client.is_playing() and _active.get(guild_id):
            await asyncio.sleep(0.5)

        if not _active.get(guild_id):
            break

        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    _active.pop(guild_id, None)


@tree.command(name='jukebox', description='Bot entra na call e toca áudios aleatórios da biblioteca')
@app_commands.checks.cooldown(1, 5.0)
async def jukebox(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send(content="Você precisa estar em um chat de voz")
        return

    guild_id = interaction.guild.id
    if _active.get(guild_id):
        await interaction.followup.send(content="O jukebox já está ativo neste servidor")
        return

    audios = _get_audios()
    if not audios:
        await interaction.followup.send(content="Nenhum áudio encontrado. Use /add_audio para adicionar.")
        return

    try:
        voice_client = await connect_voice(interaction.guild, interaction.user.voice.channel)
    except Exception as e:
        await interaction.followup.send(content=f"Não foi possível entrar no chat de voz: {e}")
        return

    _active[guild_id] = True
    asyncio.create_task(_jukebox_loop(voice_client, guild_id))
    await interaction.followup.send(content=f"Jukebox ativo! {len(audios)} áudio(s) disponíveis.")


@tree.command(name='sair', description='Tira o bot do chat de voz')
async def leave(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    _active[interaction.guild.id] = False
    if await disconnect_voice(interaction.guild):
        await interaction.followup.send(content="Saí do chat de voz")
    else:
        await interaction.followup.send(content="O bot não está em nenhum chat de voz")
