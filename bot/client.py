from bot.utils.helpers import *

class client(discord.Client):
  def __init__(self):
    super().__init__(intents=discord.Intents.default())
    self.synced = False
    self.servers = {}

  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced:
      # Registra a View do Soundpad como persistente: os botões continuam
      # funcionando mesmo depois que o bot reinicia.
      from bot.commands.audio.play import register_soundpad
      from bot.commands.audio.youtube import register_youtube
      register_soundpad(self)
      register_youtube(self)

      # Sincroniza por servidor primeiro (usa a lista global em memória para copiar).
      for guild in self.guilds:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)

      # Limpa o registro global no Discord para evitar duplicatas.
      tree.clear_commands(guild=None)
      await tree.sync()
      self.synced = True
    print(f"Entramos como {self.user}.")

  async def on_voice_state_update(self, member, before, after):
    server = self.get_server(member.guild.id)
    if not after.mute and member == server.mute_user and server.mute:
      await member.edit(mute=True)
      
  def get_server(self, guild_id):
    if guild_id not in self.servers:
      self.servers[guild_id] = BotServer()
    return self.servers[guild_id]
  
aclient = client()
tree = app_commands.CommandTree(aclient)


@tree.error
async def on_app_command_error(interaction, error):
  """Trata erros de slash commands — principalmente cooldown — sem derrubar nada."""
  if isinstance(error, app_commands.CommandOnCooldown):
    msg = f"⏳ Calma! Tente de novo em {error.retry_after:.1f}s."
  elif isinstance(error, app_commands.CheckFailure):
    msg = "Você não pode usar este comando agora."
  else:
    raise error
  try:
    if interaction.response.is_done():
      await interaction.followup.send(msg, ephemeral=True)
    else:
      await interaction.response.send_message(msg, ephemeral=True)
  except Exception:
    pass