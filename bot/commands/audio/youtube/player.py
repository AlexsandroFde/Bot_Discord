"""Player interativo (View do discord.py) com botões pausar/pular/parar."""
import discord

from . import state


class PlayerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="⏯", label="Pausar/Continuar",
                       style=discord.ButtonStyle.primary, custom_id="yt:pause")
    async def pause_resume(self, interaction: discord.Interaction, _b: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("Bot não está em call.", ephemeral=True)
            return
        if vc.is_paused():
            vc.resume()
            await interaction.response.edit_message(
                embed=state.make_embed(interaction.guild.id, paused=False), view=self,
            )
        elif vc.is_playing():
            vc.pause()
            await interaction.response.edit_message(
                embed=state.make_embed(interaction.guild.id, paused=True), view=self,
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
        await interaction.response.defer()
        vc.stop()  # dispara 'after' → playback._on_end → próxima ou state.finish

    @discord.ui.button(emoji="⏹", label="Parar",
                       style=discord.ButtonStyle.danger, custom_id="yt:stop")
    async def stop(self, interaction: discord.Interaction, _b: discord.ui.Button):
        q  = state.get_queue(interaction.guild.id)
        vc = interaction.guild.voice_client
        q.items.clear()
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()  # _on_end achará fila vazia → state.finish deleta a mensagem
        else:
            await state.finish(interaction.guild)
        try:
            await interaction.response.send_message("⏹ Fila parada e limpa.", ephemeral=True)
        except discord.InteractionResponded:
            pass


def register_youtube(client: discord.Client) -> None:
    """Registra a View como persistente para os botões funcionarem após reinício."""
    client.add_view(PlayerView())
