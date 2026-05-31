"""Componentes interativos do soundpad (Select + botões) e refresh do painel."""
import os
import time
import random
import discord

from bot.utils.voice import get_volume, set_volume

from . import state, audios, playback


async def refresh_panel(guild_id: int) -> None:
    msg = state.panels.get(guild_id)
    if not msg:
        return
    try:
        await msg.edit(
            embed=state.make_embed(guild_id, msg.id),
            view=build_view(state.page.get(msg.id, 0)),
        )
    except Exception:
        pass


# ── Componentes ───────────────────────────────────────────────────────────────

class AudioSelect(discord.ui.Select):
    def __init__(self, p: int = 0):
        all_audios = audios.list_audios()
        start      = p * audios.PAGE_SIZE
        chunk      = all_audios[start:start + audios.PAGE_SIZE]
        options = [
            discord.SelectOption(
                label=f"{start + i + 1:02d}. {audios.display_name(path)}"[:100],
                value=os.path.basename(path)[:100],
            )
            for i, path in enumerate(chunk)
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
        last = state.select_cd.get(interaction.user.id, 0.0)
        if now - last < state.SELECT_COOLDOWN:
            await interaction.response.send_message(
                f"⏳ Espere {state.SELECT_COOLDOWN - (now - last):.1f}s.", ephemeral=True)
            return
        state.select_cd[interaction.user.id] = now

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message(
                "O bot não está em nenhuma call. Use **/play** para reconectar.", ephemeral=True)
            return

        path = os.path.join(audios.ASSETS_PATH, self.values[0])
        if not os.path.isfile(path):
            await interaction.response.send_message(
                "Áudio não encontrado (foi removido?).", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if vc.is_playing():
            vc.stop()
        try:
            await playback.play_path(vc, path, guild_id)
        except Exception as e:
            state.now_playing.pop(guild_id, None)
            await interaction.response.send_message(f"Erro ao tocar: {e}", ephemeral=True)
            return

        await interaction.response.edit_message(
            embed=state.make_embed(guild_id, interaction.message.id),
            view=build_view(state.page.get(interaction.message.id, 0)),
        )


class PageButton(discord.ui.Button):
    def __init__(self, delta: int, emoji: str, custom_id: str):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary, row=1, custom_id=custom_id)
        self.delta = delta

    async def callback(self, interaction: discord.Interaction):
        mid = interaction.message.id
        state.page[mid] = audios.clamp_page(state.page.get(mid, 0) + self.delta)
        await interaction.response.edit_message(
            embed=state.make_embed(interaction.guild.id, mid),
            view=build_view(state.page[mid]),
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
        all_audios = audios.list_audios()
        if not all_audios:
            await interaction.response.send_message("Biblioteca vazia.", ephemeral=True)
            return
        guild_id = interaction.guild.id
        if vc.is_playing():
            vc.stop()
        await playback.play_path(vc, random.choice(all_audios), guild_id)
        await interaction.response.edit_message(
            embed=state.make_embed(guild_id, interaction.message.id),
            view=build_view(state.page.get(interaction.message.id, 0)),
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
            embed=state.make_embed(guild_id, interaction.message.id),
            view=build_view(state.page.get(interaction.message.id, 0)),
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
        state.now_playing.pop(guild_id, None)
        await interaction.response.edit_message(
            embed=state.make_embed(guild_id, interaction.message.id),
            view=build_view(state.page.get(interaction.message.id, 0)),
        )


class RefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="🔄", style=discord.ButtonStyle.primary, row=2, custom_id="sp:refresh")

    async def callback(self, interaction: discord.Interaction):
        mid = interaction.message.id
        p   = audios.clamp_page(state.page.get(mid, 0))
        state.page[mid] = p
        await interaction.response.edit_message(
            embed=state.make_embed(interaction.guild.id, mid),
            view=build_view(p),
        )


# ── View ──────────────────────────────────────────────────────────────────────

def build_view(p: int = 0) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(AudioSelect(p))
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
    client.add_view(build_view())
