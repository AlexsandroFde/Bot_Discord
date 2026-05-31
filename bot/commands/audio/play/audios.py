"""Helpers de filesystem para a biblioteca de áudios."""
import os
import discord
from discord import app_commands

# `play/` está 4 níveis abaixo da raiz do projeto: play → audio → commands → bot → root
ASSETS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'assets')
)
ALLOWED_EXTENSIONS = ('.mp3', '.wav', '.ogg', '.m4a')
PAGE_SIZE = 25  # limite de opções do Select Menu do Discord


def list_audios() -> list[str]:
    if not os.path.isdir(ASSETS_PATH):
        return []
    return sorted(
        os.path.join(ASSETS_PATH, f)
        for f in os.listdir(ASSETS_PATH)
        if f.lower().endswith(ALLOWED_EXTENSIONS)
    )


def display_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def page_count() -> int:
    return max(1, (len(list_audios()) + PAGE_SIZE - 1) // PAGE_SIZE)


def clamp_page(p: int) -> int:
    return max(0, min(p, page_count() - 1))


def resolve_path(audio: str) -> str | None:
    """Resolve um áudio pelo nome do arquivo ou pelo nome de exibição."""
    direct = os.path.join(ASSETS_PATH, audio)
    if os.path.isfile(direct):
        return direct
    for p in list_audios():
        if display_name(p).lower() == audio.lower():
            return p
    return None


async def audio_autocomplete(interaction: discord.Interaction, current: str):
    current = current.lower()
    choices = []
    for p in list_audios():
        name = display_name(p)
        if current in name.lower():
            choices.append(app_commands.Choice(name=name[:100], value=os.path.basename(p)))
        if len(choices) >= 25:
            break
    return choices
