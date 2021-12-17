import pickle
import asyncio
import random
import os
from multiprocessing import get_context
import Levenshtein
from fuzzywuzzy import fuzz

import discord
from discord import ClientException
from discord.ext import commands

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import youtube_dl

# Load artistsDict
try:
    with open('cogs/artists.data', 'rb') as filehandle:
        artistDict = pickle.load(filehandle)
except FileNotFoundError:
    print('No artist data found. Generating file.')
    artistDict = {}
    with open('cogs/artists.data', 'wb') as filehandle:
        pickle.dump(artistDict, filehandle)

# Load tracksDict
try:
    with open('cogs/tracks.data', 'rb') as filehandle:
        tracksDict = pickle.load(filehandle)
except FileNotFoundError:
    print('No track data found. Generating file.')
    tracksDict = {}
    with open('cogs/tracks.data', 'wb') as filehandle:
        pickle.dump(tracksDict, filehandle)

# Set Spotify credentials
auth_manager = SpotifyClientCredentials(os.environ.get('SPOTIFY_CLIENT_ID'), os.environ.get('SPOTIFY_CLIENT_SECRET'))
spotify = spotipy.Spotify(auth_manager=auth_manager)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class MusicQuiz(commands.Cog):
    song_queue = []
    currently_playing = ''
    quiz_started = False
    song_guessed = 'False'
    artist_guessed = ''
    bot_ctx = ''
    voted_skip = {}

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel
        if len(self.song_queue) > 0 and message.author != self.client.user:
            # print('Name: ' + str(fuzz_compare(message.content, self.song_queue[0][1]['name'])) + '\t\tArtist: ' + str(fuzz_compare(message.content, self.song_queue[0][1]['artist'])))
            if self.song_guessed!=self.song_queue[0][1]['name'] and fuzz_compare(message.content, self.song_queue[0][1]['name'])>=85:
                self.song_guessed = self.song_queue[0][1]['name']
                await channel.send('Song guessed')
            if self.artist_guessed!=self.song_queue[0][1]['artist'] and fuzz_compare(message.content, self.song_queue[0][1]['artist'])>=85:
                self.artist_guessed = self.song_queue[0][1]['artist']
                await channel.send('Artist guessed')
            if self.song_guessed==self.song_queue[0][1]['name'] and self.artist_guessed==self.song_queue[0][1]['artist']:
                print(self.song_guessed + ' == ' + self.song_queue[0][1]['name'])
                print(self.artist_guessed + ' == ' + self.song_queue[0][1]['artist'])
                self.song_guessed = 'False'
                self.artist_guessed = 'False'
                self.bot_ctx.voice_client.stop()

    @commands.command(description="search for artist info on spotify by name")
    async def search_artist(self, ctx, *, name):
        await ctx.send(get_artist_message(name, False))

    @commands.command(description="add artist by name")
    async def add_artist(self, ctx, *, name):
        await ctx.send(get_artist_message(name, True))

    @commands.command(description="add artist by id")
    async def add_id(self, ctx, *, id):
        await ctx.send(add_id_message(id))

    @commands.command(description="remove artist by name")
    async def rm_artist(self, ctx, *, name):
        key_list = list(artistDict.keys())
        try:
            id = key_list[list(artistDict.values()).index(name)]
        except:
            try:
                id = get_artist_from_name(name)['id']
            except:
                await ctx.send('Artist **' + name + '** not found.')
                return
        await ctx.send(rm_id(id))

    @commands.command(description="remove artist by id")
    async def rm_id(self, ctx, *, id):
        await ctx.send(rm_id(id))

    # For debugging, only prints to console
    @commands.command(description="print top tracks for an id in console")
    async def top_tracks(self, ctx, *, id):
        uri = 'spotify:artist:' + id
        # print(uri)
        results = spotify.artist_top_tracks(uri)

        for track in results['tracks'][:10]:
            print('track    : ' + track['name'])
            if track['preview_url'] is not None:
                print('audio    : ' + track['preview_url'])
            print('cover art: ' + track['album']['images'][0]['url'])

    @commands.command(description="list artists and ids")
    async def list(self, ctx):
        await ctx.send(artistDict)

    @commands.command(description="list tracks")
    async def list_tracks(self, ctx):
        await ctx.send(tracksDict)

    @commands.command(description="print list of albums from artist id")
    async def search_albums_name(self, ctx, *, name):
        artist = get_artist_from_name(name)
        if artist is None:
            await ctx.send('No artists found from ***' + name + '***.')
        await self.search_albums_id(ctx, id=artist['id'])

    @commands.command(description="print list of albums from artist id")
    async def search_albums_id(self, ctx, *, id):
        results = spotify.artist_albums('spotify:artist:' + id, album_type='album')
        albums = results['items']
        albumList = ''
        while results['next']:
            results = spotify.next(results)
            albums.extend(results['items'])
        for album in albums:
            # print(album['name'] + ' ' + album['id'])
            albumList += '**' + album['name'] + '** *' + album['id'] + '*\n'
        await ctx.send(albumList.strip())

    @commands.command(description="print list of albums from album id")
    async def search_album_tracks_id(self, ctx, *, id):
        result = spotify.album('spotify:album:' + id)
        track_names = ''
        for track in result['tracks']['items']:
            track_names += track['name'] + ' ' + track['id'] + '\n'
        await ctx.send('**' + result['name'] + '** by ***' + result['artists'][0]['name'] + '***\t\t' + result['images'][0]['url'] + '\n' + track_names)

    @commands.command(description="add album by id")
    async def add_album_id(self, ctx, *, id):
        add_album_id_message(id)

    @commands.command(description="add album by id")
    async def rm_album_id(self, ctx, *, id):
        results = spotify.album('spotify:album:' + id)
        for track in results['tracks']['items']:
            if track['preview_url'] is not None:
                tracksDict.pop(track['preview_url'])
        await ctx.send('Album **' + results['name'] + '** by ***' + results['artists'][0]['name'] + '*** was removed.')

    @commands.command(description="return number of previews")
    async def size_tracks(self, ctx):
        await ctx.send(len(tracksDict))

    @commands.command(description="count valid previews for an id")
    async def count_previews(self, ctx, *, id):
        await ctx.send(count_previews_message(id))

    @commands.command(description="play song or resume playback")
    async def play(self, ctx):
        if ctx.voice_client.is_paused():
            await ctx.send('Resuming')
            ctx.voice_client.resume()
            return
        # else:
        #     entry_list = list(tracksDict.items())
        #     random_track = random.choice(entry_list)
        #     if random_track:
        #         print('Adding ' + random_track[1]['name'])
        #         self.song_queue.append(random_track)
        #         status = await self.is_playing(ctx)
        #         if status:
        #             queue_len = len(self.song_queue)
        #             return await ctx.send(f"Adding to queue position {queue_len+1}.")
        #         await self.play_song(ctx)

    @commands.command(description="start a music quiz")
    async def start_quiz(self, ctx):
        if not self.quiz_started:
            self.bot_ctx = ctx
            await self.join(ctx)
            if len(self.song_queue) == 0:
                entry_list = list(tracksDict.items())
                for x in range(15):
                    if len(entry_list) == 0:
                        print('Track list shorter than 15, stopping.')
                        break
                    track = random.choice(entry_list)
                    self.song_queue.append(track)
                    entry_list.remove(track)
                if self.song_queue:
                    self.quiz_started = True
                    self.artist_guessed = 'False'
                    self.song_guessed = 'False'
                    await ctx.send('Starting quiz.')
                    await self.play_song(ctx)
                    # Debug answers
                    await self.queue(ctx)
                else:
                    await ctx.send('No songs found. Cannot start quiz.')

    @commands.command(description="end music quiz")
    async def stop_quiz(self, ctx):
        await self.clear_queue(ctx)
        ctx.voice_client.stop()
        await ctx.send('Stopping quiz')
        self.voted_skip.clear()
        self.quiz_started = False
        self.artist_guessed = 'False'
        self.song_guessed = 'False'

    @commands.command(description="attempt to play song queue")
    async def force_play(self, ctx):
        await self.play_song(ctx)

    @commands.command(description="puase playback")
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.send('Pausing.')
            ctx.voice_client.pause()

    @commands.command(description="skip current track")
    async def stop(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.send('Skipping track.')
            ctx.voice_client.stop()

    @commands.command(description="print queue to console")
    async def queue(self, ctx):
        print('Queue (' + str(len(self.song_queue)) + '): ')
        for track in self.song_queue:
            print(track[1]['name'] + '\t\t' + track[1]['artist'])

    @commands.command(description="vote to skip song")
    async def skip(self, ctx):
        if not self.quiz_started:
            return await ctx.send('Can\'t skip when there is no quiz.')
        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            return await self.client.say("That is not a valid voice channel.")
        members = voice_channel.members
        self.voted_skip[ctx.message.author.id] = True
        print(str(len(self.voted_skip)) + '/' + str(len(members)-1))
        if len(self.voted_skip) >= len(members)-1:  # Test Further
            ctx.voice_client.stop()
            await ctx.send('Voted to skip.')

    @commands.command(description="clears song queue")
    async def clear_queue(self, ctx):
        self.song_queue.clear()
        print('Queue cleared.')

    @commands.command(description="clears artist dictionary (must readd all artist)")
    async def clear_artists(self, ctx):
        artistDict.clear()
        save_artists()

    @commands.command(description="clears track dictionary (must readd all tracks)")
    async def clear_tracks(self, ctx):
        tracksDict.clear()
        save_tracks()

    # Voice channel commands
    @commands.command(description="joins a voice channel")
    async def join(self, ctx):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send('You need to be in a voice channel to use this command!')

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

    @commands.command(description="stops and disconnects the bot from voice")
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    async def is_playing(self, ctx):
        return ctx.voice_client.is_playing()

    async def check_queue(self,ctx):
        self.artist_guessed = 'False'
        self.song_guessed = 'False'
        self.voted_skip.clear()
        if len(self.song_queue) > 0:
            await ctx.send('The song was: **' + self.song_queue[0][1]['name'] + '** by ***' + self.song_queue[0][1]['artist'] + '***. Songs remaining: **' + str(len(self.song_queue)-1) + '**')
            ctx.voice_client.stop()
            self.song_queue.pop(0)
            if len(self.song_queue) > 0:
                await self.play_song(ctx)
        if len(self.song_queue) == 0:
            self.quiz_started = False
            await ctx.send('Quiz is done. Thank you for playing.')

    async def play_song(self, ctx, task=None):
        url = self.song_queue[0][0]
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: ctx.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def get_valid_album_previews(results):
    tracks = {}
    name = results['artists'][0]['name']
    for index, track in enumerate(results['tracks']['items']):
        tempDict = {}
        if track['preview_url'] is not None:
            tempDict['artist'] = name
            tempDict['name'] = track['name']
            # tempDict['preview_url'] = track['preview_url']
            tracks[index] = tempDict
            # tempDict.pop('preview_url')
            tracksDict[track['preview_url']] = tempDict  # Add preview url to stored dict
    save_tracks()
    return tracks


def get_valid_previews(id):
    tracks = {}
    results = spotify.artist_top_tracks('spotify:artist:' + id)
    name = get_artist_name_from_id(id)
    for index, track in enumerate(results['tracks']):
        tempDict = {}
        if track['preview_url'] is not None:
            tempDict['artist'] = name
            tempDict['name'] = track['name']
            # tempDict['preview_url'] = track['preview_url']
            tracks[index] = tempDict
            # tempDict.pop('preview_url')
            tracksDict[track['preview_url']] = tempDict  # Add preview url to stored dict
    save_tracks()
    return tracks


def count_previews_message(id):
    tracks = get_valid_previews(id)
    return '**' + artistDict[id] + '** has ***' + str(len(tracks)) + '*** previews.'


def get_artist_name_from_id(id):
    try:
        name = spotify.artist(id)['name']
        return name
    except:
        print('No artist from id ***' + id + '***.')
        return None


def get_artist_from_name(name):
    results = spotify.search(q='artist:' + name, type='artist')
    items = results['artists']['items']
    if len(items) == 0:
        return None
    artist = items[0]
    return artist


def get_artist_message(name, addBool):
    artist = get_artist_from_name(name)
    if artist is None:
        return 'No artists found from ***' + name + '***.'
    if addBool:
        id = artist['id']
        return add_id_message(id)
    return '**' + artist['name'] + '** *' + artist['id'] + '* ' + artist['images'][0]['url']


def add_id(artist_results):
    if artist_results is None:
        return 'Invalid id ***' + id + '***.'
    artistDict[artist_results['id']] = artist_results['name']
    save_artists()


def add_id_message(id):
    artist_results = spotify.artist('spotify:artist:' + id)
    add_id(artist_results)
    count = len(get_valid_previews(id))
    if count > 0:
        return '**' + artist_results['name'] + '** (*' + id + '*) added to list with **' + str(count) + '** previews.' + artist_results['images'][0]['url']
    return '**' + artist_results['name'] + '** had no previews in top tracks. Not adding.'


def add_album_id_message(id):
    results = spotify.album('spotify:album:' + id)
    artist_id = results['artists'][0]['id']
    artist_results = spotify.artist('spotify:artist:' + artist_id)
    count = len(get_valid_album_previews(results))
    if count > 0:
        add_id(artist_results)
        return '**' + artist_results['name'] + '** (*' + id + '*) added to list with **' + str(count) + '** previews.' + \
               artist_results['images'][0]['url']
    return '**' + artist_results['name'] + '** had no previews in top tracks. Not adding.'


def rm_id(id):
    if id not in artistDict.keys():
        return '***' + id + '*** not in list.'
    name = artistDict[id]
    artistDict.pop(id)
    save_artists()
    rm_tracks(name)
    return '**' + name + '** removed from list.'


def rm_tracks(artist):
    key_list = list(tracksDict.keys())
    val_list = list(tracksDict.values())
    for val in val_list:
        if val['artist'] == artist:
            position = val_list.index(val)
            tracksDict.pop(key_list[position])
    save_tracks()


def save_tracks():
    with open('cogs/tracks.data', 'wb') as filehandle:
        pickle.dump(tracksDict, filehandle)


def save_artists():
    with open('cogs/artists.data', 'wb') as filehandle:
        pickle.dump(artistDict, filehandle)


def fuzz_compare(Str1, Str2):
    return max(fuzz.ratio(Str1.lower(),Str2.lower()),
               # fuzz.partial_ratio(Str1.lower(), Str2.lower()),
               fuzz.token_sort_ratio(Str1, Str2),
               fuzz.token_set_ratio(Str1, Str2))


def setup(client):
    client.add_cog(MusicQuiz(client))
