import discord
from discord.ext import commands

import os.path
import random
import time

class PlayerData:
    def __init__(self, player_name, upper_limit):
        self.old_limit = upper_limit
        self.new_limit = upper_limit
        self.last_update = time.time()
        self.player_name = player_name
        self.roll_round = 0
        self.lost = False
    

class ChanceGames(commands.Cog):
    expiration_time = 1800      # Time in seconds
    max_roll = 100
    lol_threshold = 10          # Inclusive

    def __init__(self, client):
        self.client = client
        self.deathroll_player_rolls = {}

    def new_player(self, player_id):
        return player_id not in self.deathroll_player_rolls
    
    def expired_roll(self, player_id):
        return self.deathroll_player_rolls[player_id].last_update + self.expiration_time < time.time()
    
    def game_in_progress(self):
        # Can join if all active players are at round 1
        for player_id in self.deathroll_player_rolls.keys():
            if self.deathroll_player_rolls[player_id].roll_round > 1:
                return True
        return False

    def delete_old_players(self):
        for player_id in self.deathroll_player_rolls.keys():
            if self.expired_roll(player_id):
                del self.deathroll_player_rolls[player_id]
        return

    def unrolled_players(self, roll_round):
        players = []
        self.delete_old_players()
        for player_id in self.deathroll_player_rolls.keys():
            if roll_round > self.deathroll_player_rolls[player_id].roll_round and not self.deathroll_player_rolls[player_id].lost:
                players.append(self.deathroll_player_rolls[player_id].player_name)
        return players
    
    def all_rolled_1(self):
        all_rolls_1 = True
        for player_id in self.deathroll_player_rolls.keys():
            if self.deathroll_player_rolls[player_id].new_limit > 1:
                all_rolls_1 = False
        return all_rolls_1

    def mark_lost_players(self):
        for player_id in self.deathroll_player_rolls.keys():
            if self.deathroll_player_rolls[player_id].new_limit == 1:
                self.deathroll_player_rolls[player_id].lost = True
        return
    
    def revert_limit(self):
        for player_id in self.deathroll_player_rolls.keys():
            if not self.deathroll_player_rolls[player_id].lost:
                self.deathroll_player_rolls[player_id].new_limit = self.deathroll_player_rolls[player_id].old_limit
        return
    
    def only_winner_left(self):
        winner = None
        for player_id in self.deathroll_player_rolls.keys():
            if not self.deathroll_player_rolls[player_id].lost:
                if winner:
                    # Multiple winners
                    return None
                winner = self.deathroll_player_rolls[player_id].player_name
        return winner

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

    # TODO Add turn order?
    # TODO Add server info so users can play across different servers
    @commands.command(description="Death roll. Option to add 'reset' or 'resetall',", aliases=['dr', 'deathroll', 'droll'])
    async def death_roll(self, ctx, *args):
        player_id = ctx.message.author.id
        player_name = ctx.message.author.name

        if not args:
            args = ["roll"]

        arg = args[0].lower()
        match(arg):
            case "roll":
                pass
            case "reset":
                self.deathroll_player_rolls[player_id] = PlayerData(player_name, self.max_roll)
                await ctx.send('Resetting roll for player ' + ctx.message.author.name)
                return
            case "resetall":
                self.deathroll_player_rolls = {}
                await ctx.send('Resetting all player rolls')
                return
            case "list":
                for temp_player_id in self.deathroll_player_rolls.keys():
                    await ctx.send(self.deathroll_player_rolls[temp_player_id].player_name + " has a max roll of " + str(self.deathroll_player_rolls[temp_player_id].upper_limit) + " after " + self.deathroll_player_rolls[temp_player_id].roll_round + " rolls")
                return
            case "set":
                if not args[1] or not args[1].isnumeric():
                    await ctx.send('Please provide a valid value to set upper limit to. Using old limit for now.')
                    self.deathroll_player_rolls[player_id].new_limit = self.deathroll_player_rolls[player_id].old_limit
                    return
                
                limit = args[1]
                self.deathroll_player_rolls[player_id].old_limit = self.deathroll_player_rolls[player_id].new_limit = min(self.max_roll, int(limit))
                return
            case _:
                if arg.isnumeric():
                    self.deathroll_player_rolls[player_id].old_limit = self.deathroll_player_rolls[player_id].new_limit = min(self.max_roll, int(arg))
                    await ctx.send('Resetting max roll to ' + str(min(self.max_roll, int(arg))))
                    return
                await ctx.send('Invalid argument ' + arg + '. Rolling as usual instead.')
        
        if self.new_player(player_id) or self.expired_roll(player_id):
            if self.game_in_progress():
                await ctx.send('Player cannot join due to game being in progress. Please wait for round to end.')
                return
            else:
                self.deathroll_player_rolls[player_id] = PlayerData(player_name, self.max_roll)
                await ctx.send('New player. Starting roll.')
        else:
            players_remaining = self.unrolled_players(self.deathroll_player_rolls[player_id].roll_round)
            if players_remaining:
                await ctx.send('Cannot roll. Waiting on players: ' + str(players_remaining))
                return

        self.deathroll_player_rolls[player_id].old_limit = self.deathroll_player_rolls[player_id].new_limit
        self.deathroll_player_rolls[player_id].new_limit = random.randint(1, self.deathroll_player_rolls[player_id].old_limit)
        self.deathroll_player_rolls[player_id].roll_round += 1
        self.deathroll_player_rolls[player_id].last_update = time.time()
        
        await ctx.send('Your number is **' + str(self.deathroll_player_rolls[player_id].new_limit) + '** out of ' + str(self.deathroll_player_rolls[player_id].old_limit) + ' for round ' + str(self.deathroll_player_rolls[player_id].roll_round))

        players_remaining = self.unrolled_players(self.deathroll_player_rolls[player_id].roll_round)
        if players_remaining:
            # Waiting for other players to finish rolls for round
            return

        if self.deathroll_player_rolls[player_id].new_limit == 1:
            # Should handle single player differently
            if self.deathroll_player_rolls[player_id].roll_round == 1 and self.max_roll >= self.lol_threshold:
                await ctx.send('lol')
            if self.all_rolled_1():
                await ctx.send('All remaining players rolled 1. Redoing round.')
                self.revert_limit()
                return
            
        # Ignore first round since others will probably be joining
        if self.deathroll_player_rolls[player_id].roll_round > 1 and len(self.deathroll_player_rolls) > 1:
            self.mark_lost_players()
            winner = self.only_winner_left()
            if winner:
                await ctx.send("The winner is **" + winner + "** after " + str(self.deathroll_player_rolls[player_id].roll_round) + " rounds!")

                await ctx.send("Resetting game")
                self.deathroll_player_rolls = {}
                return
            await ctx.send('All players have rolled for the round. You may begin round ' + str(self.deathroll_player_rolls[player_id].roll_round + 1))
        

async def setup(client):
    await client.add_cog(ChanceGames(client))
