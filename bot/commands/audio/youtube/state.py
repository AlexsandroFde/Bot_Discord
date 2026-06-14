"""Estado da fila por servidor e formatadores (embed/duração)."""
import asyncio
import time
import discord
from collections import deque
from dataclasses import dataclass, field

from bot.utils.voice import on_disconnect, get_volume

# Barra de progresso estilo "slider": trilho contínuo com um botão (knob).
_BAR_WIDTH = 14
_BAR_TRACK = '▬'
_BAR_THUMB = '🔘'

_ACCENT = 0x5865F2   # azul (blurple) do cabeçalho
_IDLE   = 0x95A5A6   # cinza quando nada toca


@dataclass
class QueueItem:
    url: str                # URL direta do áudio (extraída pelo yt-dlp)
    title: str
    webpage_url: str        # link original do YouTube
    duration: int | None
    requester: str
    requester_mention: str = ""  # menção (<@id>) para exibir "Adicionado por"
    thumbnail: str | None = None  # capa/arte do vídeo
    needs_resolve: bool = False  # True para faixas de playlist (stream ainda não extraído)


@dataclass
class GuildQueue:
    items: deque = field(default_factory=deque)
    current: QueueItem | None = None
    message: discord.Message | None = None
    gen: int = 0             # invalida 'after' callbacks de tracks substituídas
    started_at: float | None = None   # time.monotonic() quando a faixa atual começou/retomou
    paused_at:  float | None = None   # time.monotonic() quando foi pausado (None = tocando)
    loop: bool = False           # repete a faixa atual ao terminar
    skip_requested: bool = False  # pular ignora o loop nesta transição


_queues: dict[int, GuildQueue] = {}


def get_queue(guild_id: int) -> GuildQueue:
    q = _queues.get(guild_id)
    if q is None:
        q = GuildQueue()
        _queues[guild_id] = q
    return q


# ── Tempo decorrido ───────────────────────────────────────────────────────────

def elapsed(q: GuildQueue) -> int:
    """Segundos decorridos da faixa atual, congelado enquanto pausado."""
    if q.started_at is None:
        return 0
    ref = q.paused_at if q.paused_at is not None else time.monotonic()
    return max(0, int(ref - q.started_at))


# ── Formatadores ──────────────────────────────────────────────────────────────

def format_duration(seconds: int | None) -> str:
    if not seconds:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _progress_bar(elapsed_s: int, total_s: int | None) -> str:
    """Trilho contínuo com um knob na posição atual (estilo slider)."""
    elapsed_fmt = format_duration(elapsed_s)
    total_fmt   = format_duration(total_s)

    if not total_s or total_s <= 0:
        bar = _BAR_TRACK * _BAR_WIDTH
        return f"`{elapsed_fmt}` {bar} `{total_fmt}`"

    ratio = min(elapsed_s / total_s, 1.0)
    pos   = round(ratio * (_BAR_WIDTH - 1))
    bar   = _BAR_TRACK * pos + _BAR_THUMB + _BAR_TRACK * (_BAR_WIDTH - 1 - pos)
    return f"`{elapsed_fmt}` {bar} `{total_fmt}`"


def make_embed(guild: discord.Guild, *, paused: bool = False) -> discord.Embed:
    q   = get_queue(guild.id)
    cur = q.current

    if not cur:
        return discord.Embed(title="⏹ Nada tocando", color=_IDLE)

    vc      = guild.voice_client
    channel = vc.channel.name if vc and vc.channel else "—"
    volume  = int(get_volume(guild.id) * 100)
    loop    = "Faixa" if q.loop else "Off"
    pedido  = cur.requester_mention or cur.requester

    description = (
        f"### [{cur.title[:200]}]({cur.webpage_url})\n"
        f"- Adicionado por {pedido}\n"
        f"- 🔊 {channel}\n\n"
        f"Fila: `{len(q.items)}`  ·  Volume: `{volume}%`  ·  Loop: `{loop}`\n\n"
        f"{_progress_bar(elapsed(q), cur.duration)}"
    )

    embed = discord.Embed(
        title=("⏸ Pausado" if paused else "▶ Tocando agora"),
        description=description,
        color=_ACCENT,
    )
    if cur.thumbnail:
        embed.set_thumbnail(url=cur.thumbnail)

    if q.items:
        lines = [
            f"`{i + 1:02d}.` {item.title[:55]}"
            for i, item in enumerate(list(q.items)[:8])
        ]
        if len(q.items) > 8:
            lines.append(f"*+{len(q.items) - 8} restantes*")
        embed.add_field(name="📜 Próximas", value="\n".join(lines), inline=False)

    return embed


# ── Cleanup ───────────────────────────────────────────────────────────────────

async def finish(guild: discord.Guild) -> None:
    """Fila acabou: deleta a mensagem do player (ou edita se não puder deletar)."""
    q   = get_queue(guild.id)
    msg = q.message
    q.message = None
    q.current = None
    if not msg:
        return
    try:
        await msg.delete()
    except Exception:
        try:
            embed = discord.Embed(title="⏹ Fila finalizada", color=0x95A5A6)
            await msg.edit(embed=embed, view=None)
        except Exception:
            pass


async def _safe_delete(msg: discord.Message) -> None:
    try:
        await msg.delete()
    except Exception:
        pass


# Ao sair da call (timeout/sair), limpa estado e remove o player.
def _on_voice_disconnect(guild_id: int) -> None:
    q = _queues.pop(guild_id, None)
    if q and q.message:
        msg = q.message
        q.message = None
        try:
            asyncio.create_task(_safe_delete(msg))
        except RuntimeError:
            pass

on_disconnect(_on_voice_disconnect)
