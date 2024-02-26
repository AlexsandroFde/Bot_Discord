from bot.client import tree, discord, aclient

@tree.command(name='unmute', description='Desmuta um membro')
async def unmute(interaction: discord.Interaction):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)
  
  if server.mute_user == None and not server.mute:
    await interaction.followup.send(content="O comando mute não está sendo executado")
    return
  if server.mute_user == interaction.user and not interaction.user.guild_permissions.administrator:
    await interaction.followup.send(content="Você não pode se desmutar")
    return

  try: 
    membro = server.mute_user
    mute_user = server.mute_user
    server.mute_user = None
    server.mute = False
    await mute_user.edit(mute=False)
    await interaction.followup.send(content=f"{membro.mention} não está mais mutado", ephemeral=True)
  except: 
    await interaction.followup.send(content="O usuario não está em call", ephemeral=True)