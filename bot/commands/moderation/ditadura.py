from bot.client import tree, discord, aclient 

@tree.command(name='ditadura', description='Impede que mandem mensagem')
async def ditadura(interaction: discord.Interaction, chat: discord.TextChannel = None):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)

  if not interaction.user.guild_permissions.administrator:
    await interaction.followup.send(content="Você não tem permissão para usar este comando")
    return
  
  if server.ditador is not None:
    await interaction.followup.send(content="A ditadura já está ativa")
    return

  server.channel = chat
  server.ditador = interaction.user
  
  await interaction.followup.send(content="Ditadura instaurada")