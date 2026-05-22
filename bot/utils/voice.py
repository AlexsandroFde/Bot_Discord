import asyncio
import discord


# ── Estado ─────────────────────────────────────────────────────────────────────
_volume:          dict[int, float]        = {}   # guild_id -> volume (0.0 - 2.0)
_monitors:        dict[int, asyncio.Task] = {}   # guild_id -> task do monitor ocioso
_disconnect_hooks: list                   = []   # callbacks(guild_id) ao sair da call

DEFAULT_VOLUME = 1.0
MIN_VOLUME     = 0.0
MAX_VOLUME     = 2.0

ALONE_TIMEOUT = 60     # segundos sozinho na call antes de sair
IDLE_TIMEOUT  = 300    # segundos sem tocar nada antes de sair
CHECK_EVERY   = 15     # intervalo entre verificações do monitor

# loudnorm padroniza o volume percebido entre áudios de origens diferentes
_LOUDNORM = 'loudnorm=I=-16:TP=-1.5:LRA=11'


# ── Volume ──────────────────────────────────────────────────────────────────────

def get_volume(guild_id: int) -> float:
    return _volume.get(guild_id, DEFAULT_VOLUME)


def set_volume(guild_id: int, value: float) -> float:
    """Define o volume do servidor, limitado a [MIN_VOLUME, MAX_VOLUME]."""
    value = max(MIN_VOLUME, min(MAX_VOLUME, round(value, 2)))
    _volume[guild_id] = value
    return value


# ── Fonte de áudio ──────────────────────────────────────────────────────────────

def make_source(path: str, guild_id: int, *, stream: bool = False) -> discord.AudioSource:
    """Cria uma fonte de áudio com normalização de loudness e volume ajustável.

    ``stream=True`` adiciona opções de reconexão do FFmpeg, necessárias para
    tocar de URLs (ex.: YouTube) que podem cair no meio da reprodução.
    """
    kwargs: dict = {'options': f'-vn -af {_LOUDNORM}'}
    if stream:
        kwargs['before_options'] = (
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        )
    source = discord.FFmpegPCMAudio(path, **kwargs)
    return discord.PCMVolumeTransformer(source, volume=get_volume(guild_id))


# ── Hooks de desconexão ─────────────────────────────────────────────────────────

def on_disconnect(callback) -> None:
    """Registra um callback síncrono chamado com guild_id quando o bot sai da call."""
    _disconnect_hooks.append(callback)


def _run_hooks(guild_id: int) -> None:
    for hook in _disconnect_hooks:
        try:
            hook(guild_id)
        except Exception:
            pass


# ── Conexão ─────────────────────────────────────────────────────────────────────

async def connect_voice(guild: discord.Guild, channel: discord.VoiceChannel) -> discord.VoiceClient:
    """Conecta (ou move) o bot a um canal de voz de forma resiliente.

    Se existir um voice client 'zumbi' — desconectado após uma queda 1006
    mas ainda preso em ``guild.voice_client`` — ele é forçado a limpar antes
    de tentar uma nova conexão. Sem isso, ``channel.connect()`` lança
    ``ClientException("Already connected to a voice channel.")``.
    """
    vc = guild.voice_client

    if vc is not None:
        if vc.is_connected():
            if vc.channel != channel:
                await vc.move_to(channel)
            _start_monitor(guild)
            return vc
        # Conexão morta: força a limpeza para liberar guild.voice_client.
        try:
            await vc.disconnect(force=True)
        except Exception:
            pass
        try:
            vc.cleanup()
        except Exception:
            pass

    try:
        vc = await channel.connect(timeout=20.0, reconnect=True)
    except discord.ClientException:
        # Última proteção contra um zumbi que escapou da limpeza acima.
        stale = guild.voice_client
        if stale is not None:
            try:
                await stale.disconnect(force=True)
            except Exception:
                pass
        vc = await channel.connect(timeout=20.0, reconnect=True)

    _start_monitor(guild)
    return vc


async def disconnect_voice(guild: discord.Guild) -> bool:
    """Para a reprodução, desconecta o bot e dispara os hooks. Retorna se estava conectado."""
    vc = guild.voice_client
    if not vc:
        _run_hooks(guild.id)
        return False
    if vc.is_playing() or vc.is_paused():
        vc.stop()
    try:
        await vc.disconnect(force=True)
    except Exception:
        try:
            vc.cleanup()
        except Exception:
            pass
    _run_hooks(guild.id)
    return True


# ── Monitor de inatividade ──────────────────────────────────────────────────────

def _start_monitor(guild: discord.Guild) -> None:
    task = _monitors.get(guild.id)
    if task and not task.done():
        return
    _monitors[guild.id] = asyncio.create_task(_idle_monitor(guild))


async def _idle_monitor(guild: discord.Guild) -> None:
    """Sai da call se o bot ficar sozinho ou ocioso por tempo demais."""
    alone = idle = 0
    try:
        while True:
            await asyncio.sleep(CHECK_EVERY)
            vc = guild.voice_client
            if not vc or not vc.is_connected():
                break

            humans = [m for m in vc.channel.members if not m.bot]
            alone = 0 if humans else alone + CHECK_EVERY
            idle  = 0 if vc.is_playing() else idle + CHECK_EVERY

            if alone >= ALONE_TIMEOUT or idle >= IDLE_TIMEOUT:
                await disconnect_voice(guild)
                break
    finally:
        _monitors.pop(guild.id, None)
