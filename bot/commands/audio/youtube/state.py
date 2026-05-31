"""Estado da fila por servidor e formatadores (embed/duração)."""
import asyncio
import discord
from collections import deque
from dataclasses import dataclass, field

from bot.utils.voice import on_disconnect


@dataclass
class QueueItem:
    url: str                # URL direta do áudio (extraída pelo yt-dlp)
    title: str
    webpage_url: str        # link original do YouTube
    duration: int | None
    requester: str


@dataclass
class GuildQueue:
    items: deque = field(default_factory=deque)
    current: QueueItem | None = None
    message: discord.Message | None = None
    gen: int = 0           # invalida 'after' callbacks de tracks substituídas


_queues: dict[int, GuildQueue] = {}


def get_queue(guild_id: int) -> GuildQueue:
    q = _queues.get(guild_id)
    if q is None:
        q = GuildQueue()
        _queues[guild_id] = q
    return q


# ── Formatadores ──────────────────────────────────────────────────────────────

def format_duration(seconds: int | None) -> str:
    if not seconds:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def make_embed(guild_id: int, *, paused: bool = False) -> discord.Embed:
    q   = get_queue(guild_id)
    cur = q.current

    if cur:
        embed = discord.Embed(
            title=("⏸ Pausado" if paused else "▶ Tocando agora"),
            description=f"**[{cur.title[:200]}]({cur.webpage_url})**",
            color=0xE74C3C,
        )
        embed.add_field(name="⏱ Duração", value=format_duration(cur.duration), inline=True)
        embed.add_field(name="👤 Pediu",   value=cur.requester, inline=True)
    else:
        embed = discord.Embed(title="⏹ Nada tocando", color=0x95A5A6)

    if q.items:
        lines = [
            f"`{i + 1:02d}.` {item.title[:60]}"
            for i, item in enumerate(list(q.items)[:10])
        ]
        if len(q.items) > 10:
            lines.append(f"*+{len(q.items) - 10} restantes*")
        embed.add_field(name=f"📜 Fila ({len(q.items)})", value="\n".join(lines), inline=False)
    else:
        embed.add_field(name="📜 Fila", value="*vazia*", inline=False)

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
