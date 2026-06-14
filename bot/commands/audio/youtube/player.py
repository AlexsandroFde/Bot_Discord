"""Player interativo (View do discord.py) com botões pausar/pular/parar."""
import time
import discord

from . import state


class PlayerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="⏯", label="Pausar",
                       style=discord.ButtonStyle.primary, custom_id="yt:pause")
    async def pause_resume(self, interaction: discord.Interaction, _b: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("Bot não está em call.", ephemeral=True)
            return
        q = state.get_queue(interaction.guild.id)
        if vc.is_paused():
            # Avança started_at pelo tempo que ficou pausado para manter elapsed correto
            if q.paused_at is not None:
                q.started_at = (q.started_at or time.monotonic()) + (time.monotonic() - q.paused_at)
            q.paused_at = None
            vc.resume()
            await interaction.response.edit_message(
                embed=state.make_embed(interaction.guild, paused=False), view=self,
            )
        elif vc.is_playing():
            q.paused_at = time.monotonic()
            vc.pause()
            await interaction.response.edit_message(
                embed=state.make_embed(interaction.guild, paused=True), view=self,
            )
        else:
            await interaction.response.send_message("Nada tocando.", ephemeral=True)

    @discord.ui.button(emoji="⏭", label="Pular",
                       style=discord.ButtonStyle.secondary, custom_id="yt:skip")
    async def skip(self, interaction: discord.Interaction, _b: discord.ui.Button):
        vc = interaction.guild.voice_client
        q  = state.get_queue(interaction.guild.id)
        if not vc or (not vc.is_playing() and not vc.is_paused()) or q.current is None:
            await interaction.response.send_message("Nada para pular.", ephemeral=True)
            return
        q.skip_requested = True  # pular tem prioridade sobre o loop nesta transição
        await interaction.response.defer()
        vc.stop()  # dispara 'after' → playback._on_end → próxima ou state.finish

    @discord.ui.button(emoji="⏹", label="Parar",
                       style=discord.ButtonStyle.danger, custom_id="yt:stop")
    async def stop(self, interaction: discord.Interaction, _b: discord.ui.Button):
        q  = state.get_queue(interaction.guild.id)
        vc = interaction.guild.voice_client
        q.items.clear()
        q.loop = False  # parar zera o loop para não re-tocar a faixa atual
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()  # _on_end achará fila vazia → state.finish deleta a mensagem
        else:
            await state.finish(interaction.guild)
        try:
            await interaction.response.send_message("⏹ Fila parada e limpa.", ephemeral=True)
        except discord.InteractionResponded:
            pass

    @discord.ui.button(emoji="🔁", label="Loop",
                       style=discord.ButtonStyle.secondary, custom_id="yt:loop")
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("Bot não está em call.", ephemeral=True)
            return
        q = state.get_queue(interaction.guild.id)
        q.loop = not q.loop
        button.style = (discord.ButtonStyle.success if q.loop
                        else discord.ButtonStyle.secondary)
        await interaction.response.edit_message(
            embed=state.make_embed(interaction.guild, paused=vc.is_paused()), view=self,
        )


def register_youtube(client: discord.Client) -> None:
    """Registra a View como persistente para os botões funcionarem após reinício."""
    client.add_view(PlayerView())
