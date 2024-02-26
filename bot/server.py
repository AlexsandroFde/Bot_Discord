class BotServer:
  def __init__(self):
    self.interromper = True
    self.spam_user = None
    
    self.mute = False
    self.mute_user = None
    
    self.ditador = None
    self.channel = None