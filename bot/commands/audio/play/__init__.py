"""Pacote do soundpad: painel /play + comandos /add_audio e /top.

Reexporta símbolos usados por main.py, client.py e library.py para preservar
a API anterior (`from bot.commands.audio.play import ...`).
"""
from .play import play_soundpad
from .add_audio import add_audio
from .top import top_audios
from .view import register_soundpad, refresh_panel as _refresh_panel
from .audios import (
    ASSETS_PATH,
    ALLOWED_EXTENSIONS,
    audio_autocomplete as _audio_autocomplete,
    resolve_path as _resolve_path,
    display_name as _display_name,
)

__all__ = [
    'play_soundpad', 'add_audio', 'top_audios',
    'register_soundpad',
    '_refresh_panel', '_audio_autocomplete', '_resolve_path', '_display_name',
    'ASSETS_PATH', 'ALLOWED_EXTENSIONS',
]
