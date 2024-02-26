from bot.client import tree, discord, aclient

@tree.command(name='stop', description='Interrompe o comando de spam')
async def interrupt_spam(interaction: discord.Interaction):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)
  
  if server.spam_user == None and server.interromper:
    await interaction.followup.send(content="Nenhum comando de spam está sendo executado")    
  else:
    if server.spam_user == interaction.user or interaction.user.guild_permissions.administrator:
      server.interromper = True  
      server.spam_user = None
      await interaction.followup.send(content="O comando de spam atual será interrompido")     
    else:
      await interaction.followup.send(content="Você não tem a permissão de parar o comando de spam atual")