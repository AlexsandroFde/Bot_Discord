from bot.client import tree, discord, aclient, asyncio

@tree.command(name='spam', description='Envia várias mensagens para um usuário')
async def spam_message(interaction: discord.Interaction, membro: discord.Member, quantia: int):
  server = aclient.get_server(interaction.guild.id)
  await interaction.response.defer(ephemeral=True)
  
  if server.spam_user != None and not server.interromper:
    await interaction.followup.send(content="Um comando de spam já está sendo executado")
    return
 
  server.interromper = False
  server.spam_user = interaction.user
  channel = interaction.channel

  await interaction.followup.send(content="Spamando...")

  for i in range(quantia):
    if server.interromper:
      await interaction.followup.send(content="O spam foi interrompido", ephemeral=True)
      return        
    message = await channel.send(content=f"{membro.mention}")
    await message.delete()
    await asyncio.sleep(0.75)

  server.interromper = True
  server.spam_user = None
  await interaction.followup.send(content="O spam terminou", ephemeral=True)   