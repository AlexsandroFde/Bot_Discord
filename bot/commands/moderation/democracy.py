from bot.client import tree, discord, aclient 

@tree.command(name='democracia', description='Desativa a ditadura que impede que mandem mensagem')
async def democracy(interaction: discord.Interaction):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)

  if not interaction.user.guild_permissions.administrator:
    await interaction.followup.send(content="Você não tem permissão para usar este comando")
    return

  if server.ditador is None:
    await interaction.followup.send(content="A ditadura já está desativada")
    return

  server.channel = None
  server.ditador = None

  await interaction.followup.send(content="Ditadura desativada")