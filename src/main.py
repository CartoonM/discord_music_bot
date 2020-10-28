from os import getenv

from dotenv import load_dotenv
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get
from youtube_dl import YoutubeDL

from cogs import Music


load_dotenv()

TOKEN = getenv('TOKEN')
client = commands.Bot(command_prefix='!!')
client.add_cog(Music(client))
client.run(TOKEN)
