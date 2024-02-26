from bot.client import tree, discord, aclient, milenio, format_dt

@tree.command(name='info', description='Informações sobre a Sayoko')
async def message_embed(interaction: discord.Interaction):
  await interaction.response.defer()
  user = await aclient.fetch_user(milenio)
  time = aclient.user.created_at

  embed = discord.Embed(description=f'''Eu atualmente possuo **{len(tree.get_commands())-1} comandos** focados especificamente em causar o caos em seu servidor. Fui criada em {format_dt(time, style="D")} como forma de aprendizado.\nNo momento estou em desenvolvimento''', color=0x1e2e39) 
  embed.set_author(name=f"Prazer, {aclient.user.name}", icon_url=aclient.user.avatar.url)
  embed.set_thumbnail(url=aclient.user.avatar.url)
  embed.set_footer(text="Desenvolvido por milenio.", icon_url=user.avatar.url)

  button_style = discord.ButtonStyle.primary
  button_function = "https://discord.com/api/oauth2/authorize?client_id=1098056776479416424&permissions=8&scope=bot"

  button = discord.ui.Button(label="Me adicione", style=button_style, url=button_function)
  view = discord.ui.View()
  view.add_item(button)

  await interaction.followup.send(embed=embed, view=view)