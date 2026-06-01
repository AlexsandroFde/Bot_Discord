"""Wrapper assíncrono para o yt-dlp."""
import asyncio
from urllib.parse import urlparse, parse_qs

_YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

_YDL_PLAYLIST_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',  # metadados sem baixar cada faixa
    'source_address': '0.0.0.0',
}


def is_playlist_url(query: str) -> bool:
    """Retorna True se a query parece ser uma URL de playlist do YouTube."""
    try:
        parsed = urlparse(query)
        if parsed.scheme not in ('http', 'https'):
            return False
        qs = parse_qs(parsed.query)
        # Playlist pura: youtube.com/playlist?list=...
        # Vídeo dentro de playlist: ...?v=...&list=...
        return 'list' in qs
    except Exception:
        return False


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


async def extract_playlist(url: str) -> list[dict]:
    """Extrai todas as entradas de uma playlist do YouTube.

    Usa extract_flat para obter apenas metadados (sem baixar áudio de cada faixa).
    Cada entrada retornada contém ao menos: id, title, url, duration.
    """
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("yt-dlp não está instalado. Rode: `pip install yt-dlp`")

    def run() -> list[dict]:
        with yt_dlp.YoutubeDL(_YDL_PLAYLIST_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return []
            entries = info.get('entries') or []
            return [e for e in entries if e and e.get('id')]

    return await asyncio.get_running_loop().run_in_executor(None, run)
