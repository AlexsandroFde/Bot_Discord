from bot.client import tree, discord, milenio

@tree.command(name='mensagem', description='Envia uma mensagens pelo bot')
async def message(interaction: discord.Interaction, mensagem: str):
  user = interaction.user
  user_mention = user.mention
  channel = interaction.channel
  
  if not user.guild_permissions.administrator and user.id != milenio:
    await interaction.followup.send(content=f"{user_mention} você não tem permissão para mandar em mim")
    return
    
  await interaction.response.defer(ephemeral=True)
  await interaction.followup.send(content="Mandando mensagem...")      
  await channel.send(content=f"{mensagem}")