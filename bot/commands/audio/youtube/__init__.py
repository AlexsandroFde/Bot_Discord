"""Pacote do comando /youtube: fila + player interativo.

Reexporta os símbolos usados pelo restante do projeto (main.py e client.py)
para preservar a API anterior (`from bot.commands.audio.youtube import ...`).
"""
from .youtube import youtube
from .player import register_youtube

__all__ = ['youtube', 'register_youtube']
