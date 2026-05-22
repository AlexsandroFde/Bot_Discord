from bot.client import tree, discord
from bot.utils.voice import connect_voice, make_source
from discord import app_commands
import asyncio

# Opções do yt-dlp: melhor faixa de áudio, sem playlists, saída silenciosa.
_YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}


async def _extract(query: str) -> dict:
    """Extrai metadados/URL do áudio em uma thread separada (yt-dlp é bloqueante)."""
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("yt-dlp não está instalado. Rode: `pip install yt-dlp`")

    def run() -> dict:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)
            if info and 'entries' in info:  # resultado de busca
                info = info['entries'][0]
            return info

    return await asyncio.get_running_loop().run_in_executor(None, run)


@tree.command(name='youtube', description='Toca o áudio de um link ou busca do YouTube na call')
@app_commands.describe(busca='Link do YouTube ou termo de busca')
@app_commands.checks.cooldown(1, 5.0)
async def youtube(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("Você precisa estar em um chat de voz.")
        return

    try:
        vc = await connect_voice(interaction.guild, interaction.user.voice.channel)
    except Exception as e:
        await interaction.followup.send(f"Não foi possível entrar no chat de voz: {e}")
        return

    try:
        info = await _extract(busca)
    except Exception as e:
        await interaction.followup.send(f"Erro ao buscar no YouTube: {e}")
        return

    url   = info.get('url') if info else None
    title = info.get('title', 'desconhecido') if info else 'desconhecido'
    if not url:
        await interaction.followup.send("Não consegui extrair o áudio desse link.")
        return

    if vc.is_playing():
        vc.stop()
    try:
        vc.play(make_source(url, interaction.guild.id, stream=True))
    except Exception as e:
        await interaction.followup.send(f"Erro ao tocar: {e}")
        return

    await interaction.followup.send(f"▶ Tocando do YouTube: **{title}**")
