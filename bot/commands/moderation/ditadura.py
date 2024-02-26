from bot.client import tree, discord, aclient 

@tree.command(name='ditadura', description='Impede que mandem mensagem')
async def ditadura(interaction: discord.Interaction, chat: discord.TextChannel = None):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)

  if not interaction.user.guild_permissions.administrator:
    await interaction.followup.send(content="Você não tem permissão para usar este comando")
    return

  server.channel = (None if server.ditador != None else chat)
  server.ditador = (None if server.ditador != None else interaction.user)
  
  await interaction.followup.send(content="Ditadura instaurada") if server.ditador != None else await interaction.followup.send(content="Fim da ditadura")