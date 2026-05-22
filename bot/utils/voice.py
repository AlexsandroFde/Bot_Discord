import discord


async def connect_voice(guild: discord.Guild, channel: discord.VoiceChannel) -> discord.VoiceClient:
    """Conecta (ou move) o bot a um canal de voz de forma resiliente.

    Se existir um voice client 'zumbi' — desconectado após uma queda 1006
    mas ainda preso em ``guild.voice_client`` — ele é forçado a limpar antes
    de tentar uma nova conexão. Sem isso, ``channel.connect()`` lança
    ``ClientException("Already connected to a voice channel.")``.
    """
    vc = guild.voice_client

    if vc is not None:
        if vc.is_connected():
            if vc.channel != channel:
                await vc.move_to(channel)
            return vc
        # Conexão morta: força a limpeza para liberar guild.voice_client.
        try:
            await vc.disconnect(force=True)
        except Exception:
            pass
        try:
            vc.cleanup()
        except Exception:
            pass

    try:
        return await channel.connect(timeout=20.0, reconnect=True)
    except discord.ClientException:
        # Última proteção contra um zumbi que escapou da limpeza acima.
        stale = guild.voice_client
        if stale is not None:
            try:
                await stale.disconnect(force=True)
            except Exception:
                pass
        return await channel.connect(timeout=20.0, reconnect=True)
