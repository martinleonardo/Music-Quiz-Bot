import os

import discord
import yt_dlp
from discord.ext import commands
import json


class Music(commands.Cog):
    def __init__(self, bot):
        self.self = self
        self.bot = bot
        self.volume = self.load_volume()  # Load volume settings from file
        self.queue = []

    def load_volume(self):
        try:
            with open('data/volume_settings.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print('No volume file found. Using default values.')
            return {}  # Return an empty dictionary if the file doesn't exist

    def save_volume(self):
        data_folder = "data"
        os.makedirs(data_folder, exist_ok=True)  # Create the 'data' folder if it doesn't exist
        file_path = os.path.join(data_folder, 'volume_settings.json')

        with open(file_path, 'w') as file:
            json.dump(self.volume, file, indent=4)

    def cog_unload(self):
        self.save_volume()  # Save volume settings before the cog is unloaded

    @commands.command()
    async def join(self, ctx):
        # Check is user is a voice channel
        user_voice = ctx.author.voice
        if not user_voice:
            await ctx.send('Please join a voice channel to play something.')
            return

        # Check if bot is already in a voice channel
        bot_voice = ctx.voice_client
        if bot_voice:
            # Do nothing if bot is already in user's voice channel
            if user_voice.channel == bot_voice.channel:
                return
            # Leave current voice channel if not user's
            await bot_voice.disconnect()

        # Join user's voice channel
        await user_voice.channel.connect()

    @commands.command()
    async def leave(self, ctx):
        bot_voice = ctx.voice_client
        # Check bot is in voice channel before trying to disconnect
        if ctx.voice_client:
            await bot_voice.disconnect()

    @commands.command()
    async def play(self, ctx, *, search_word):
        self.self = self
        bot_voice = ctx.voice_client
        # Join user's voice channel if not already in it
        await self.join(ctx)

        ydl_opts = {
            'format': 'bestaudio[ext=mp3]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Given a url
            if search_word[0:4] == "http" or search_word[0:3] == "www":
                info = ydl.extract_info(search_word, download=False)
            # Else, search instead
            else:
                info = ydl.extract_info(f"ytsearch:{search_word}", download=False)["entries"][0]
            url = info['url']
            title = info.get('title', 'Unknown')

        self.queue.append({"url": url, "title": title})

        if not bot_voice.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            voice_client = ctx.voice_client
            song = self.queue.pop(0)
            ffmpeg_options = {
                'before_options': f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': f'-vn -af volume={self.volume.get(ctx.guild.id, 0.5)}',
            }
            try:
                voice_client.play(discord.FFmpegPCMAudio(song["url"], **ffmpeg_options),
                                  after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next, ctx))
            except Exception as e:
                print(f"Error playing song: {e}")
                await self.play_next(ctx)  # Try playing the next song

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            await self.play_next(ctx)

    @commands.command()
    async def volume(self, ctx, vol: float):
        if 0.0 <= vol <= 1.0:
            self.volume[ctx.guild.id] = vol  # Save volume for the current server
            self.save_volume()  # Save updated volume settings to file

            if ctx.voice_client:
                ctx.voice_client.source.volume = vol
            await ctx.send(f'Volume set to {vol}')
        else:
            await ctx.send('Volume must be between 0.0 and 1.0')

    @commands.command()
    async def queue(self, ctx):
        if self.queue:
            queue_message = "\n".join([f"{index + 1}. {entry['title']}" for index, entry in enumerate(self.queue)])
            await ctx.send(f"**Queued Titles:**\n{queue_message}")
        else:
            await ctx.send("The queue is currently empty.")

    @commands.command()
    async def clearqueue(self, ctx):
        self.queue.clear()
        await ctx.send("Queue has been cleared.")


async def setup(bot):
    await bot.add_cog(Music(bot))
