import typing
import asyncio

from discord import VoiceClient, FFmpegPCMAudio
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from youtube_dl import YoutubeDL


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
    task_queue = []
    voice_client = None
    next = asyncio.Event()

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

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, url: str):
        """Play."""

        if self.voice_client is None:
            await self.connect_to_voice_chat(ctx)
        if isinstance(ctx.voice_client, VoiceClient):
            self.voice_client = ctx.voice_client
            if not ctx.voice_client.is_playing():
                await self.play_music(url, self.scroll_queue)
            else:
                self.task_queue.append(url)
                await ctx.send('Append to queue')

    def scroll_queue(self, error: Exception = None):
        self.next.set()

    async def connect_to_voice_chat(self, ctx: commands.Context):
        voice_channel = ctx.author.voice.channel
        if voice_channel:
            try:
                await voice_channel.connect()
            except CommandInvokeError:
                pass

    async def play_music(
        self,
        url: str,
        after: typing.Callable
    ):
        loop = asyncio.get_event_loop()
        processed_info = await loop.run_in_executor(
                            None,
                            self.ytdl.extract_info,
                            url,
                            False
                    )
        self.voice_client.play(
                FFmpegPCMAudio(
                        processed_info['formats'][0]['url'],
                        **self.FFMPEG_OPTIONS
                        ),
                after=after
                    )

        await asyncio.create_task(self.next_song())

    async def next_song(self):
        await self.next.wait()
        if len(self.task_queue) > 0:
            if self.voice_client.is_playing():
                return
            self.next.clear()
            await self.play_music(self.task_queue.pop(0), self.scroll_queue)
