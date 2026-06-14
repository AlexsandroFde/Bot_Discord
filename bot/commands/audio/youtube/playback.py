"""Lógica de reprodução: iniciar próxima faixa e tratar fim de áudio."""
import asyncio
import time
import discord

from bot.client import aclient
from bot.utils.voice import make_source

from . import state
from .player import PlayerView

_PROGRESS_INTERVAL = 5   # segundos entre atualizações da barra de progresso
_updaters: dict[int, asyncio.Task] = {}


async def start_next(guild: discord.Guild) -> bool:
    """Tira o próximo item da fila e começa a tocar. Retorna True se algo iniciou.

    Faixas marcadas com needs_resolve têm sua URL de stream extraída aqui,
    evitando que o FFmpeg receba uma URL de página web (ex.: playlists).
    """
    vc = guild.voice_client
    q  = state.get_queue(guild.id)
    if not vc or not vc.is_connected() or not q.items:
        q.current = None
        return False

    item = q.items.popleft()

    if item.needs_resolve:
        from .extractor import extract as extract_audio
        try:
            info = await extract_audio(item.webpage_url)
            if info and info.get('url'):
                item.url       = info['url']
                item.title     = info.get('title') or item.title
                item.duration  = info.get('duration') or item.duration
                item.thumbnail = info.get('thumbnail') or item.thumbnail
            else:
                return await start_next(guild)
        except Exception:
            return await start_next(guild)
        item.needs_resolve = False

    q.current    = item
    q.started_at = time.monotonic()
    q.paused_at  = None
    q.gen += 1
    gen = q.gen

    def after(_err):
        asyncio.run_coroutine_threadsafe(_on_end(guild, gen), aclient.loop)

    try:
        vc.play(make_source(item.url, guild.id, stream=True), after=after)
    except Exception:
        q.current = None
        return False

    _start_progress_updater(guild, gen)
    return True


async def _on_end(guild: discord.Guild, gen: int) -> None:
    """Callback ao terminar uma faixa: avança a fila ou finaliza."""
    q = state.get_queue(guild.id)
    if q.gen != gen:
        return
    finished = q.current
    q.current = None
    if q.loop and finished is not None and not q.skip_requested:
        finished.needs_resolve = True  # re-extrai a URL (streams do YouTube expiram)
        q.items.appendleft(finished)
    q.skip_requested = False
    if q.items:
        await start_next(guild)
        await update_message(guild)
    else:
        await state.finish(guild)


async def update_message(guild: discord.Guild, *, paused: bool = False) -> None:
    q = state.get_queue(guild.id)
    if not q.message:
        return
    try:
        await q.message.edit(embed=state.make_embed(guild, paused=paused), view=PlayerView())
    except Exception:
        pass


# ── Atualizador periódico da barra de progresso ───────────────────────────────

def _start_progress_updater(guild: discord.Guild, gen: int) -> None:
    task = _updaters.get(guild.id)
    if task and not task.done():
        task.cancel()
    _updaters[guild.id] = asyncio.create_task(_progress_loop(guild, gen))


async def _progress_loop(guild: discord.Guild, gen: int) -> None:
    try:
        while True:
            await asyncio.sleep(_PROGRESS_INTERVAL)
            q = state.get_queue(guild.id)
            if q.gen != gen or q.current is None or not q.message:
                break
            vc = guild.voice_client
            if not vc or not vc.is_connected() or vc.is_paused():
                continue  # pausado: barra congelada, não precisa atualizar
            await update_message(guild)
    finally:
        _updaters.pop(guild.id, None)
