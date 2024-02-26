from bot.client import tree, discord, aclient

@tree.command(name='mute', description='Muta um membro')
async def mute(interaction: discord.Interaction, membro: discord.Member):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)
  
  if server.mute_user != None and server.mute:
    await interaction.followup.send(content="O comando já está sendo executado")
    return
    
  try: 
    await membro.edit(mute=True)  
    server.mute_user = membro
    server.mute = True
    await interaction.followup.send(content=f"{membro.mention} foi mutado com sucesso")
  except: 
    await interaction.followup.send(content="O usuario não está em call", ephemeral=True)