from bot.client import tree, discord, aclient
from bot.utils.voice import connect_voice
import discord.ui
import asyncio
import os

ASSETS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets'))
ALLOWED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.m4a')
MAX_AUDIOS = 25  # limite do Select Menu do Discord

_panels:      dict[int, discord.Message] = {}
_now_playing: dict[int, str]             = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def list_audios() -> list[str]:
    if not os.path.isdir(ASSETS_PATH):
        return []
    return sorted([
        os.path.join(ASSETS_PATH, f)
        for f in os.listdir(ASSETS_PATH)
        if f.lower().endswith(ALLOWED_EXTENSIONS)
    ])


def _make_embed(audios: list[str], guild_id: int | None = None) -> discord.Embed:
    total = len(audios)
    now   = _now_playing.get(guild_id) if guild_id else None
    embed = discord.Embed(title="🎵  Soundpad", color=0x5865F2)

    if total == 0:
        embed.description = "📭  Nenhum áudio disponível.\nUse **➕ Adicionar** para enviar o primeiro."
    else:
        lines = []
        for i, path in enumerate(audios[:MAX_AUDIOS]):
            name = os.path.splitext(os.path.basename(path))[0]
            lines.append(f"`{i + 1:02d}.`  {name}")
        if total > MAX_AUDIOS:
            lines.append(f"*… e mais {total - MAX_AUDIOS} áudio(s) não exibidos*")
        embed.description = "\n".join(lines)

    embed.add_field(
        name="▶  Tocando agora",
        value=f"```\n{now}\n```" if now else "*— nada —*",
        inline=False,
    )
    embed.set_footer(text=f"{total} áudio(s) na biblioteca")
    return embed


async def _on_audio_end(guild_id: int):
    _now_playing.pop(guild_id, None)
    if guild_id in _panels:
        try:
            view = SoundpadView()
            await _panels[guild_id].edit(embed=_make_embed(list_audios(), guild_id), view=view)
        except Exception:
            pass


# ── Components ────────────────────────────────────────────────────────────────

class AudioSelect(discord.ui.Select):
    def __init__(self, audios: list[str]):
        options = [
            discord.SelectOption(
                label=f"{i + 1:02d}. {os.path.splitext(os.path.basename(p))[0]}"[:100],
                value=os.path.basename(p)[:100],
            )
            for i, p in enumerate(audios[:MAX_AUDIOS])
        ]
        super().__init__(
            placeholder="Selecione um áudio...",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("O bot não está em nenhuma call.", ephemeral=True)
            return
        if vc.is_playing():
            vc.stop()

        filename = self.values[0]
        path     = os.path.join(ASSETS_PATH, filename)
        guild_id = interaction.guild.id
        name     = os.path.splitext(filename)[0]
        _now_playing[guild_id] = name

        def after(_):
            asyncio.run_coroutine_threadsafe(_on_audio_end(guild_id), aclient.loop)

        try:
            vc.play(discord.FFmpegPCMAudio(path), after=after)
        except Exception as e:
            _now_playing.pop(guild_id, None)
            await interaction.response.send_message(f"Erro ao tocar: {e}", ephemeral=True)
            return

        await interaction.response.edit_message(
            embed=_make_embed(list_audios(), guild_id),
            view=self.view,
        )


class StopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="⏹ Parar", style=discord.ButtonStyle.danger, row=1)

    async def callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
        _now_playing.pop(guild_id, None)
        await interaction.response.edit_message(
            embed=_make_embed(list_audios(), guild_id),
            view=self.view,
        )


class RefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔄 Atualizar", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        v: SoundpadView = self.view
        v._build()
        await interaction.response.edit_message(
            embed=_make_embed(list_audios(), interaction.guild.id),
            view=v,
        )


# ── View ──────────────────────────────────────────────────────────────────────

class SoundpadView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self._build()

    def _build(self):
        self.clear_items()
        audios = list_audios()
        if audios:
            self.add_item(AudioSelect(audios))
        self.add_item(StopButton())
        self.add_item(RefreshButton())


# ── Commands ──────────────────────────────────────────────────────────────────

@tree.command(name='play', description='Entra na call e abre o painel de áudios')
async def play_soundpad(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("Você precisa estar em um chat de voz.")
        return

    try:
        await connect_voice(interaction.guild, interaction.user.voice.channel)
    except Exception as e:
        await interaction.followup.send(f"Não foi possível entrar no chat de voz: {e}")
        return

    guild_id = interaction.guild.id
    if guild_id in _panels:
        try:
            await _panels[guild_id].delete()
        except Exception:
            pass

    view = SoundpadView()
    msg  = await interaction.channel.send(embed=_make_embed(list_audios(), guild_id), view=view)
    _panels[guild_id] = msg
    await interaction.followup.send("Soundpad aberto!")


@tree.command(name='add_audio', description='Adiciona um novo áudio à biblioteca')
async def add_audio(interaction: discord.Interaction, arquivo: discord.Attachment):
    await interaction.response.defer(ephemeral=True)

    if not arquivo.filename.lower().endswith(ALLOWED_EXTENSIONS):
        await interaction.followup.send("Formato inválido. Use: mp3, wav, ogg ou m4a")
        return

    os.makedirs(ASSETS_PATH, exist_ok=True)
    await arquivo.save(os.path.join(ASSETS_PATH, arquivo.filename))

    guild_id = interaction.guild.id
    if guild_id in _panels:
        try:
            view = SoundpadView()
            await _panels[guild_id].edit(embed=_make_embed(list_audios(), guild_id), view=view)
        except Exception:
            pass

    await interaction.followup.send(f"**{arquivo.filename}** adicionado!")
