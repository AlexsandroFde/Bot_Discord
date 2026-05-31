"""Lógica de reprodução: iniciar próxima faixa e tratar fim de áudio."""
import asyncio
import discord

from bot.client import aclient
from bot.utils.voice import make_source

from . import state
from .player import PlayerView


def start_next(guild: discord.Guild) -> bool:
    """Tira o próximo item da fila e começa a tocar. Retorna True se algo iniciou."""
    vc = guild.voice_client
    q  = state.get_queue(guild.id)
    if not vc or not vc.is_connected() or not q.items:
        q.current = None
        return False

    item = q.items.popleft()
    q.current = item
    q.gen += 1
    gen = q.gen

    def after(_err):
        asyncio.run_coroutine_threadsafe(_on_end(guild, gen), aclient.loop)

    try:
        vc.play(make_source(item.url, guild.id, stream=True), after=after)
    except Exception:
        q.current = None
        return False
    return True


async def _on_end(guild: discord.Guild, gen: int) -> None:
    """Callback ao terminar uma faixa: avança a fila ou finaliza."""
    q = state.get_queue(guild.id)
    # Track já foi substituída por outra (ex.: nova chamada de /youtube).
    if q.gen != gen:
        return
    q.current = None
    if q.items:
        start_next(guild)
        await update_message(guild)
    else:
        await state.finish(guild)


async def update_message(guild: discord.Guild, *, paused: bool = False) -> None:
    q = state.get_queue(guild.id)
    if not q.message:
        return
    try:
        await q.message.edit(embed=state.make_embed(guild.id, paused=paused), view=PlayerView())
    except Exception:
        pass
