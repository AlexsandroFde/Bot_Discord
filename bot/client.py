from bot.utils.helpers import *

class client(discord.Client):
  def __init__(self):
    super().__init__(intents=discord.Intents.default())
    self.synced = False
    self.servers = {}

  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced: #Checar se os comandos slash foram sincronizados 
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