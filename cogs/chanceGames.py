import discord
from discord.ext import commands

import os.path
import random


class ChanceGames(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(description="flip a coin", aliases=['coin_flip', 'flip', 'coin'])
    async def flip_coin(self, ctx):
        heads_path = 'cogs/ignore_heads.png'
        tails_path = 'cogs/ignore_tails.png'

        # 0 = Heads,    1 = Tails
        if random.randrange(2) == 0:
            file_exists = os.path.exists(heads_path)
            if file_exists:
                await ctx.send('The coin lands on **HEADS**', file=discord.File(heads_path))
            else:
                await ctx.send('The coin lands on **HEADS**')
        else:
            file_exists = os.path.exists(tails_path)
            if file_exists:
                await ctx.send('The coin lands on **TAILS**', file=discord.File(tails_path))
            else:
                await ctx.send('The coin lands on **TAILS**')

    @commands.command(description="Pick a number from 1-n (inclusive)", aliases=['random', 'roll', 'number', 'randomnumber'])
    async def random_number(self, ctx, *, max):
        try:
            max = int(max)
            await ctx.send('Your number is **' + str(random.randint(1, max)) + '**.')
        except:
            await ctx.send('Please provide a valid integer')


def setup(client):
    client.add_cog(ChanceGames(client))
