from os import getenv

from dotenv import load_dotenv
from discord.ext import commands

from cogs import Music


load_dotenv()

TOKEN = getenv('TOKEN')
client = commands.Bot(command_prefix='@')
client.add_cog(Music(client))
client.run(TOKEN)
