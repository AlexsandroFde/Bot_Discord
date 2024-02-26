from bot.client import tree, discord

@tree.command(name='clear', description='Limpa as mensagens do bot ou de um usuario no chat')
async def clear_messages(interaction: discord.Interaction, membro: discord.Member = None):
  user = interaction.user
  user_mention = user.mention
  await interaction.response.defer(ephemeral=True)

  if not user.guild_permissions.manage_messages:
    await interaction.followup.send(content="Você não tem permissão para limpar mensagens")
    return

  channel = interaction.channel
  deleted = await channel.purge(limit = 999, bulk = True, check=lambda m: m.author == (interaction.client.user if membro == None else membro))

  if deleted:
    await interaction.followup.send(content=f"{user_mention} {len(deleted)} mensagens apagadas com sucesso!")
  else:
    await interaction.followup.send(content=f"{user_mention} não há mensagens para apagar")
