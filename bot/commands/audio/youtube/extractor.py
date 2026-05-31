"""Wrapper assíncrono para o yt-dlp."""
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


async def extract(query: str) -> dict | None:
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
