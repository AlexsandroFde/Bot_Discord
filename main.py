import os
from dotenv import load_dotenv
from bot.client import aclient
from bot.commands.moderation.mensagem import message
from bot.commands.moderation.clear import clear_messages
from bot.commands.moderation.ditadura import ditadura
from bot.commands.moderation.democracy import democracy
from bot.commands.mute.mute import mute
from bot.commands.mute.unmute import unmute
from bot.commands.spam.spam import spam_message
from bot.commands.spam.spam_plus import spam_call
from bot.commands.spam.stop import interrupt_spam
from bot.commands.info import message_embed
from bot.commands.audio.play import play_soundpad, add_audio, top_audios
from bot.commands.audio.jukebox import jukebox, leave
from bot.commands.audio.library import del_audio, rename_audio
from bot.commands.audio.youtube import youtube
from bot.events.on_message import on_message

def main():
    load_dotenv()
    aclient.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()