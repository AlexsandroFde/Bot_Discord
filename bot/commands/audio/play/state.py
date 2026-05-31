"""Estado por servidor (painel, geração, paginação) e construtor do embed."""
import discord

from bot.utils.voice import get_volume

from . import audios

SELECT_COOLDOWN = 2.0  # segundos entre cliques no Select (anti-spam)

panels:      dict[int, discord.Message] = {}   # guild_id  -> mensagem do painel
now_playing: dict[int, str]             = {}   # guild_id  -> nome do áudio atual
gen:         dict[int, int]             = {}   # guild_id  -> geração da reprodução
page:        dict[int, int]             = {}   # msg_id    -> página atual
select_cd:   dict[int, float]           = {}   # user_id   -> timestamp último clique


def make_embed(guild_id: int, message_id: int | None = None) -> discord.Embed:
    all_audios = audios.list_audios()
    total      = len(all_audios)
    pages      = audios.page_count()
    p          = audios.clamp_page(page.get(message_id, 0)) if message_id is not None else 0

    embed = discord.Embed(title="🎵  Soundpad", color=0x5865F2)

    if total == 0:
        embed.description = "📭  Nenhum áudio disponível.\nUse **/add_audio** para enviar o primeiro."
    else:
        start = p * audios.PAGE_SIZE
        lines = [
            f"`{start + i + 1:02d}.`  {audios.display_name(path)}"
            for i, path in enumerate(all_audios[start:start + audios.PAGE_SIZE])
        ]
        embed.description = "\n".join(lines)

    now = now_playing.get(guild_id)
    embed.add_field(
        name="▶  Tocando agora",
        value=f"```\n{now}\n```" if now else "*— nada —*",
        inline=False,
    )
    embed.add_field(name="🔊 Volume", value=f"{int(get_volume(guild_id) * 100)}%", inline=True)
    embed.add_field(name="📄 Página", value=f"{p + 1}/{pages}", inline=True)
    embed.set_footer(text=f"{total} áudio(s) na biblioteca")
    return embed
