import discord
from discord.ext import commands

import os.path
import random
import time

class PlayerData:
    def __init__(self, upper_limit):
        self.upper_limit = upper_limit
        self.last_update = time.time()
    

class ChanceGames(commands.Cog):
    expiration_time = 1800      # Time in seconds

    def __init__(self, client):
        self.client = client
        self.deathroll_player_rolls = {}

    def new_player(self, player_id):
        return player_id not in self.deathroll_player_rolls
    
    def expired_roll(self, player_id):
        return self.deathroll_player_rolls[player_id].last_update + self.expiration_time < time.time()

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
    async def random_number(self, ctx, *, upper_limit):
        try:
            upper_limit = int(upper_limit)
            await ctx.send('Your number is **' + str(random.randint(1, upper_limit)) + '**.')
        except:
            await ctx.send('Please provide a valid integer')

    @commands.command(description="Death roll. Option to add 'reset' or 'resetall',", aliases=['dr', 'deathroll', 'droll'])
    async def death_roll(self, ctx, arg='none'):
        player_id = ctx.message.author.id

        arg = arg.lower()
        match(arg):
            case "none":
                pass
            case "reset":
                self.deathroll_player_rolls[player_id] = PlayerData(100)
                await ctx.send('Resetting roll for player ' + ctx.message.author.name)
                # return
            case "resetall":
                self.deathroll_player_rolls = {}
                await ctx.send('Resetting all player rolls')
            case _:
                await ctx.send('Invalid argument ' + arg + '. Ignoring.')
        

        if self.new_player(player_id):
            print("New player")
            self.deathroll_player_rolls[player_id] = PlayerData(100)
        
        elif self.expired_roll(player_id):
            print("Expired")
            self.deathroll_player_rolls[player_id] = PlayerData(100)

        elif self.deathroll_player_rolls[player_id].upper_limit == 1:
            print("Player already lost")
            self.deathroll_player_rolls[player_id] = PlayerData(100)

        old_limit = self.deathroll_player_rolls[player_id].upper_limit
        new_limit = random.randint(1, old_limit)
        
        await ctx.send('Your number is **' + str(new_limit) + '** out of ' + str(old_limit) + '.')

        if new_limit != 1:
            self.deathroll_player_rolls[player_id].upper_limit = random.randint(1, old_limit)
        else:
            await ctx.send('You have hit **1**. Keeping old roll for ties. Reset (!dr reset) to start over.')
        


async def setup(client):
    await client.add_cog(ChanceGames(client))
