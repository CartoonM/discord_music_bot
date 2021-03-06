import typing
import asyncio
from functools import partial

from discord import VoiceClient, FFmpegPCMAudio
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, ClientException
from youtube_dl import YoutubeDL, utils
from loguru import logger


class Music(commands.Cog):

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': '-vn'}

    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'}

    ytdl = YoutubeDL(YTDL_OPTIONS)
    song_queue = list()
    voice_client = None
    next = asyncio.Event()
    current_task = None

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        """Joins a voice channel."""

        await self.connect_to_voice_chat(ctx)

    @commands.command(name='leave', aliases=['disconnect'])
    async def leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if ctx.voice_client:
            await ctx.voice_client.disconnect()

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx: commands.Context, url: str):
        """Play."""

        await asyncio.create_task(self.add_task(url, ctx))
        if self.voice_client is None:
            await self.connect_to_voice_chat(ctx)
        if isinstance(ctx.voice_client, VoiceClient):
            self.voice_client = ctx.voice_client
            await asyncio.create_task(self.next_song())

    @commands.command(name='qs')
    async def queue_size(self, ctx: commands.Context):

        await ctx.send(str(len(self.song_queue)))

    async def add_task(self, url: str, ctx: commands.Context):
        loop = asyncio.get_running_loop()
        try:
            processed_info = await loop.run_in_executor(
                                None,
                                self.ytdl.extract_info,
                                url,
                                False
                            )
            self.song_queue.append(processed_info['formats'][0]['url'])
            await ctx.send(f'Место в очереди: {len(self.song_queue)}')
        except utils.DownloadError:
            await ctx.send('Не удалось загрузить видео 🤬')

    def scroll_queue(self, error: Exception = None):
        self.next.set()

    async def connect_to_voice_chat(self, ctx: commands.Context):
        voice_channel = ctx.author.voice.channel
        if voice_channel:
            try:
                await voice_channel.connect()
            except(CommandInvokeError, ClientException):
                pass

    async def play_music(self):

        loop = asyncio.get_running_loop()

        while True:
            await self.next.wait()
            self.next.clear()

            if len(self.song_queue) < 1:
                continue

            discord_play_partial = partial(
                self.voice_client.play,
                FFmpegPCMAudio(self.song_queue.pop(0), **self.FFMPEG_OPTIONS),
                after=self.scroll_queue
            )
            await loop.run_in_executor(None, discord_play_partial)

    async def next_song(self):
        if self.current_task is None:
            self.current_task = asyncio.create_task(self.play_music())
            self.scroll_queue()
            await self.current_task
        else:
            if not self.voice_client.is_playing():
                self.scroll_queue()
