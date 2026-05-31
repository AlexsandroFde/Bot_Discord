"""Reprodução de áudios locais e callback de fim de áudio."""
import asyncio
import discord

from bot.client import aclient
from bot.utils.voice import make_source
from bot.utils.stats import record_play

from . import state, audios


async def play_path(vc: discord.VoiceClient, path: str, guild_id: int) -> None:
    name = audios.display_name(path)
    g    = state.gen.get(guild_id, 0) + 1
    state.gen[guild_id]         = g
    state.now_playing[guild_id] = name
    record_play(name)

    def after(_err):
        asyncio.run_coroutine_threadsafe(_on_audio_end(guild_id, g), aclient.loop)

    vc.play(make_source(path, guild_id), after=after)


async def _on_audio_end(guild_id: int, g: int) -> None:
    # Ignora o fim de um áudio que já foi substituído por outro.
    if state.gen.get(guild_id) != g:
        return
    state.now_playing.pop(guild_id, None)
    # Import tardio: view.py importa playback no topo (componentes chamam play_path).
    from .view import refresh_panel
    await refresh_panel(guild_id)
