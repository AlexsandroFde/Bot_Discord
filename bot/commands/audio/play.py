from bot.client import tree, discord, aclient
from bot.utils.voice import connect_voice, make_source, get_volume, set_volume
from bot.utils.stats import record_play, top_plays
from discord import app_commands
import discord.ui
import asyncio
import random
import time
import os

ASSETS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets'))
ALLOWED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.m4a')
PAGE_SIZE = 25  # limite de opções do Select Menu do Discord

SELECT_COOLDOWN = 2.0  # segundos entre cliques no Select (anti-spam)

_panels:      dict[int, discord.Message] = {}   # guild_id   -> mensagem do painel
_now_playing: dict[int, str]             = {}   # guild_id   -> nome do áudio atual
_gen:         dict[int, int]             = {}   # guild_id   -> geração da reprodução
_page:        dict[int, int]             = {}   # message_id -> página atual
_select_cd:   dict[int, float]           = {}   # user_id    -> timestamp do último clique


# ── Helpers ───────────────────────────────────────────────────────────────────

def list_audios() -> list[str]:
    if not os.path.isdir(ASSETS_PATH):
        return []
    return sorted(
        os.path.join(ASSETS_PATH, f)
        for f in os.listdir(ASSETS_PATH)
        if f.lower().endswith(ALLOWED_EXTENSIONS)
    )


def _display_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _page_count() -> int:
    return max(1, (len(list_audios()) + PAGE_SIZE - 1) // PAGE_SIZE)


def _clamp_page(page: int) -> int:
    return max(0, min(page, _page_count() - 1))


def _resolve_path(audio: str) -> str | None:
    """Resolve um áudio pelo nome do arquivo ou pelo nome de exibição."""
    direct = os.path.join(ASSETS_PATH, audio)
    if os.path.isfile(direct):
        return direct
    for p in list_audios():
        if _display_name(p).lower() == audio.lower():
            return p
    return None


async def _audio_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    choices = []
    for p in list_audios():
        name = _display_name(p)
        if current in name.lower():
            choices.append(app_commands.Choice(name=name[:100], value=os.path.basename(p)))
        if len(choices) >= 25:
            break
    return choices


def _make_embed(guild_id: int, message_id: int | None = None) -> discord.Embed:
    audios = list_audios()
    total  = len(audios)
    pages  = _page_count()
    page   = _clamp_page(_page.get(message_id, 0)) if message_id is not None else 0

    embed = discord.Embed(title="🎵  Soundpad", color=0x5865F2)

    if total == 0:
        embed.description = "📭  Nenhum áudio disponível.\nUse **/add_audio** para enviar o primeiro."
    else:
        start = page * PAGE_SIZE
        lines = [
            f"`{start + i + 1:02d}.`  {_display_name(p)}"
            for i, p in enumerate(audios[start:start + PAGE_SIZE])
        ]
        embed.description = "\n".join(lines)

    now = _now_playing.get(guild_id)
    embed.add_field(
        name="▶  Tocando agora",
        value=f"```\n{now}\n```" if now else "*— nada —*",
        inline=False,
    )
    embed.add_field(name="🔊 Volume", value=f"{int(get_volume(guild_id) * 100)}%", inline=True)
    embed.add_field(name="📄 Página", value=f"{page + 1}/{pages}", inline=True)
    embed.set_footer(text=f"{total} áudio(s) na biblioteca")
    return embed


# ── Reprodução ────────────────────────────────────────────────────────────────

async def _play_path(vc: discord.VoiceClient, path: str, guild_id: int) -> None:
    name = _display_name(path)
    gen  = _gen.get(guild_id, 0) + 1
    _gen[guild_id] = gen
    _now_playing[guild_id] = name
    record_play(name)

    def after(_):
        asyncio.run_coroutine_threadsafe(_on_audio_end(guild_id, gen), aclient.loop)

    vc.play(make_source(path, guild_id), after=after)


async def _on_audio_end(guild_id: int, gen: int) -> None:
    # Ignora o fim de um áudio que já foi substituído por outro.
    if _gen.get(guild_id) != gen:
        return
    _now_playing.pop(guild_id, None)
    await _refresh_panel(guild_id)


async def _refresh_panel(guild_id: int) -> None:
    msg = _panels.get(guild_id)
    if not msg:
        return
    try:
        await msg.edit(embed=_make_embed(guild_id, msg.id), view=_build_view(_page.get(msg.id, 0)))
    except Exception:
        pass


# ── Componentes ───────────────────────────────────────────────────────────────

class AudioSelect(discord.ui.Select):
    def __init__(self, page: int = 0):
        audios = list_audios()
        start  = page * PAGE_SIZE
        chunk  = audios[start:start + PAGE_SIZE]
        options = [
            discord.SelectOption(
                label=f"{start + i + 1:02d}. {_display_name(p)}"[:100],
                value=os.path.basename(p)[:100],
            )
            for i, p in enumerate(chunk)
        ] or [discord.SelectOption(label="— nenhum áudio —", value="__none__")]
        super().__init__(
            placeholder="Selecione um áudio...",
            options=options,
            row=0,
            custom_id="sp:select",
        )
        self.disabled = not chunk

    async def callback(self, interaction: discord.Interaction):
        now  = time.monotonic()
        last = _select_cd.get(interaction.user.id, 0.0)
        if now - last < SELECT_COOLDOWN:
            await interaction.response.send_message(
                f"⏳ Espere {SELECT_COOLDOWN - (now - last):.1f}s.", ephemeral=True)
            return
        _select_cd[interaction.user.id] = now

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message(
                "O bot não está em nenhuma call. Use **/play** para reconectar.", ephemeral=True)
            return

        path = os.path.join(ASSETS_PATH, self.values[0])
        if not os.path.isfile(path):
            await interaction.response.send_message(
                "Áudio não encontrado (foi removido?).", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if vc.is_playing():
            vc.stop()
        try:
            await _play_path(vc, path, guild_id)
        except Exception as e:
            _now_playing.pop(guild_id, None)
            await interaction.response.send_message(f"Erro ao tocar: {e}", ephemeral=True)
            return

        await interaction.response.edit_message(
            embed=_make_embed(guild_id, interaction.message.id),
            view=_build_view(_page.get(interaction.message.id, 0)),
        )


class PageButton(discord.ui.Button):
    def __init__(self, delta: int, emoji: str, custom_id: str):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary, row=1, custom_id=custom_id)
        self.delta = delta

    async def callback(self, interaction: discord.Interaction):
        mid = interaction.message.id
        _page[mid] = _clamp_page(_page.get(mid, 0) + self.delta)
        await interaction.response.edit_message(
            embed=_make_embed(interaction.guild.id, mid),
            view=_build_view(_page[mid]),
        )


class RandomButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🔀", label="Aleatório", style=discord.ButtonStyle.success,
                         row=1, custom_id="sp:random")

    async def callback(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("O bot não está em nenhuma call.", ephemeral=True)
            return
        audios = list_audios()
        if not audios:
            await interaction.response.send_message("Biblioteca vazia.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        if vc.is_playing():
            vc.stop()
        await _play_path(vc, random.choice(audios), guild_id)
        await interaction.response.edit_message(
            embed=_make_embed(guild_id, interaction.message.id),
            view=_build_view(_page.get(interaction.message.id, 0)),
        )


class VolumeButton(discord.ui.Button):
    def __init__(self, delta: float, emoji: str, custom_id: str):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary, row=2, custom_id=custom_id)
        self.delta = delta

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        volume   = set_volume(guild_id, get_volume(guild_id) + self.delta)
        vc       = interaction.guild.voice_client
        if vc and isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = volume
        await interaction.response.edit_message(
            embed=_make_embed(guild_id, interaction.message.id),
            view=_build_view(_page.get(interaction.message.id, 0)),
        )


class StopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="⏹", label="Parar", style=discord.ButtonStyle.danger,
                         row=2, custom_id="sp:stop")

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
        _now_playing.pop(guild_id, None)
        await interaction.response.edit_message(
            embed=_make_embed(guild_id, interaction.message.id),
            view=_build_view(_page.get(interaction.message.id, 0)),
        )


class RefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🔄", style=discord.ButtonStyle.primary, row=2, custom_id="sp:refresh")

    async def callback(self, interaction: discord.Interaction):
        mid  = interaction.message.id
        page = _clamp_page(_page.get(mid, 0))
        _page[mid] = page
        await interaction.response.edit_message(
            embed=_make_embed(interaction.guild.id, mid),
            view=_build_view(page),
        )


# ── View ──────────────────────────────────────────────────────────────────────

def _build_view(page: int = 0) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(AudioSelect(page))
    view.add_item(PageButton(-1, "◀", "sp:prev"))
    view.add_item(RandomButton())
    view.add_item(PageButton(1, "▶", "sp:next"))
    view.add_item(VolumeButton(-0.1, "🔉", "sp:voldown"))
    view.add_item(StopButton())
    view.add_item(VolumeButton(+0.1, "🔊", "sp:volup"))
    view.add_item(RefreshButton())
    return view


def register_soundpad(client: discord.Client) -> None:
    """Registra a View como persistente para os botões funcionarem após reinício."""
    client.add_view(_build_view())


# ── Comandos ──────────────────────────────────────────────────────────────────

@tree.command(name='play', description='Entra na call e abre o painel de áudios (ou toca um áudio direto)')
@app_commands.describe(audio='Opcional: nome do áudio para tocar imediatamente')
@app_commands.autocomplete(audio=_audio_autocomplete)
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
        path = _resolve_path(audio)
        if not path:
            await interaction.followup.send(f"Áudio não encontrado: {audio}")
            return
        if vc.is_playing():
            vc.stop()
        await _play_path(vc, path, guild_id)
        await _refresh_panel(guild_id)
        await interaction.followup.send(f"▶ Tocando **{_display_name(path)}**")
        return

    # Modo painel.
    old = _panels.get(guild_id)
    if old:
        try:
            await old.delete()
        except Exception:
            pass

    msg = await interaction.channel.send(embed=_make_embed(guild_id), view=_build_view())
    _panels[guild_id] = msg
    _page[msg.id] = 0
    await interaction.followup.send("Soundpad aberto!")


@tree.command(name='add_audio', description='Adiciona um novo áudio à biblioteca')
@app_commands.checks.cooldown(1, 3.0)
async def add_audio(interaction: discord.Interaction, arquivo: discord.Attachment):
    await interaction.response.defer(ephemeral=True)

    if not arquivo.filename.lower().endswith(ALLOWED_EXTENSIONS):
        await interaction.followup.send("Formato inválido. Use: mp3, wav, ogg ou m4a")
        return

    os.makedirs(ASSETS_PATH, exist_ok=True)
    await arquivo.save(os.path.join(ASSETS_PATH, arquivo.filename))
    await _refresh_panel(interaction.guild.id)
    await interaction.followup.send(f"**{arquivo.filename}** adicionado!")


@tree.command(name='top', description='Mostra os áudios mais tocados')
async def top_audios(interaction: discord.Interaction):
    data = top_plays(15)
    if not data:
        await interaction.response.send_message("Nenhum áudio foi tocado ainda.", ephemeral=True)
        return

    medals = ['🥇', '🥈', '🥉']
    lines  = []
    for i, (name, count) in enumerate(data):
        prefix = medals[i] if i < 3 else f"`{i + 1:02d}.`"
        lines.append(f"{prefix} **{name}** — {count}x")

    embed = discord.Embed(
        title="🏆 Áudios mais tocados",
        description="\n".join(lines),
        color=0xF1C40F,
    )
    await interaction.response.send_message(embed=embed)
