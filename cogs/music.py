import asyncio
import os

import discord
import yt_dlp
from discord.ext import commands

queuelist = []
filestodelete = []


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        await channel.connect()

    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, *, searchword):
        # ydl_opts = {}
        # voice = ctx.voice_client
        #
        # if searchword[0:4] == "http" or searchword[0:3] == "www":
        #     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #         info = ydl.extract_info(searchword, download=False)
        #         title = info["title"]
        #         url = searchword
        #
        # if searchword[0:4] != "http" and searchword[0:3] != "www":
        #     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #         info = ydl.extract_info(f"ytsearch:{searchword}", download=False)["entries"][0]
        #         title = info["title"]
        #         url = info["webpage_url"]
        #
        # ydl_opts = {
        #     'format': 'bestaudio/best',
        #     "outtmpl": f"local/music/{title}.mp3",
        #     "postprocessors":
        #         [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        # }
        #
        # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #     ydl.download([url], )
        #
        # # playing and queueing audio
        # if voice.is_playing():
        #     queuelist.append(title)
        #     await ctx.send(f"Added to queue: {title}")
        # else:
        #     voice.play(discord.FFmpegPCMAudio(f"{title}.mp3"), after=lambda e: check_queue())
        #     await ctx.send(f"Playing {title} !!!")
        #     filestodelete.append(title)
        #
        # def check_queue():
        #     try:
        #         if queuelist[0] is not None:
        #             voice.play(discord.FFmpegPCMAudio(f"{queuelist[0]}.mp3"), after=lambda e: check_queue())
        #             filestodelete.append(queuelist[0])
        #             queuelist.pop(0)
        #     except IndexError:
        #         for file in filestodelete:
        #             os.remove(f"{file}.mp3")
        #         filestodelete.clear()

        voice_client = ctx.voice_client

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        if searchword[0:4] == "http" or searchword[0:3] == "www":
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(searchword, download=False)
                # title = info["title"]
                url = info['url']

        if searchword[0:4] != "http" and searchword[0:3] != "www":
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{searchword}", download=False)["entries"][0]
                # title = info["title"]
                url = info['url']

        voice_client.stop()
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }
        voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options))


async def setup(bot):
    await bot.add_cog(Music(bot))
