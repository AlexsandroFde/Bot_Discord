from bot.client import tree, discord, aclient, random, asyncio

@tree.command(name='spam_plus', description='Move um usuário entre diferentes calls')
async def spam_call(interaction: discord.Interaction, membro: discord.Member, quantia: int):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)

  if server.spam_user != None and not server.interromper:
    await interaction.followup.send(content="Um comando de spam já está sendo executado")
    return

  server.interromper = False
  server.spam_user = interaction.user
  try: voice_channel = interaction.user.voice.channel 
  except: voice_channel = None
    
  calls = [i.id for i in interaction.guild.voice_channels if i != voice_channel]

  if len(calls) <= 2:
    await interaction.followup.send(content="Não existem chats de voz o suficiente para o spam+")
    return
       
  await interaction.followup.send(content="Movendo...")

  for i in range(quantia):
    if server.interromper:
      await interaction.followup.send(content="O spam+ foi interrompido", ephemeral=True)
      return        
    try:  
      new_channel = membro.guild.get_channel(random.choice(calls))
      while new_channel == membro.voice.channel:
        new_channel = membro.guild.get_channel(random.choice(calls))
      await asyncio.sleep(0.8)
      await membro.move_to(new_channel)
    except:
      server.interromper = True
      server.spam_user = None
      await interaction.followup.send(content="O usuario não está em call", ephemeral=True)
      return
  server.interromper = True
  server.spam_user = None
  await interaction.followup.send(content="O spam+ terminou", ephemeral=True)   