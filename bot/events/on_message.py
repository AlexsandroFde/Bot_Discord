from bot.client import aclient, asyncio, milenio

@aclient.event
async def on_message(message):
  try:
    server = aclient.get_server(message.guild.id)
    if message.channel == server.channel or server.channel == None and server.ditador != None:
      if message.author.id != milenio and message.author != aclient.user and message.author != server.ditador:
        await message.delete()
        await message.channel.send(f"Cala a boca {message.author.mention}")
        await asyncio.sleep(0.8)
  except:
    return