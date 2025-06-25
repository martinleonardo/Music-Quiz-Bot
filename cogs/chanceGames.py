from discord import app_commands
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

    async def flip_logic(self, interaction: discord.Interaction):
        heads_path = 'cogs/ignore_heads.png'
        tails_path = 'cogs/ignore_tails.png'

        result = 'HEADS' if random.randint(0, 1) == 0 else 'TAILS'
        file_path = heads_path if result == 'HEADS' else tails_path

        if os.path.exists(file_path):
            await interaction.response.send_message(
                f'The coin lands on **{result}**',
                file=discord.File(file_path)
            )
        else:
            await interaction.response.send_message(f'The coin lands on **{result}**')

    @app_commands.command(name="flip", description="Flip a coin")
    async def flip(self, interaction: discord.Interaction):
        await self.flip_logic(interaction)

    @app_commands.command(name="coin", description="Flip a coin")
    async def coin(self, interaction: discord.Interaction):
        await self.flip_logic(interaction)

    @app_commands.command(name="coin_flip", description="Flip a coin")
    async def coin_flip(self, interaction: discord.Interaction):
        await self.flip_logic(interaction)


    async def random_number_logic(self, interaction: discord.Interaction, upper_limit: int):
        if upper_limit <= 0:
            await interaction.response.send_message("Please provide a positive integer.")
            return
        number = random.randint(1, upper_limit)
        await interaction.response.send_message(f'Your number is **{number}**.')

    @app_commands.command(name="random", description="Pick a number from 1-n (inclusive)")
    @app_commands.describe(upper_limit="The upper bound for the random number")
    async def random(self, interaction: discord.Interaction, upper_limit: int):
        await self.random_number_logic(interaction, upper_limit)

    @app_commands.command(name="roll", description="Pick a number from 1-n (inclusive)")
    @app_commands.describe(upper_limit="The upper bound for the random number")
    async def roll(self, interaction: discord.Interaction, upper_limit: int):
        await self.random_number_logic(interaction, upper_limit)

    # TODO Add turn order?
    # TODO Add server info so users can play across different servers
    async def deathroll_logic(self, interaction: discord.Interaction, action: str = "roll", limit: int = None):
        user = interaction.user
        player_id = user.id
        player_name = user.name

        action = action.lower()
        if action in ["reset", "resetall", "list", "set"] and limit is not None and action != "set":
            await interaction.response.send_message("This action doesn't take a limit. Ignoring it.", ephemeral=True)

        match action:
            case "reset":
                self.deathroll_player_rolls[player_id] = PlayerData(player_name, self.max_roll)
                await interaction.response.send_message(f"Resetting roll for player {player_name}")
                return

            case "resetall":
                self.deathroll_player_rolls = {}
                await interaction.response.send_message("Resetting all player rolls")
                return

            case "list":
                if not self.deathroll_player_rolls:
                    await interaction.response.send_message("No players currently active.")
                    return
                msg = "\n".join(
                    f"{p.player_name}: max roll {p.old_limit}, round {p.roll_round}"
                    for p in self.deathroll_player_rolls.values()
                )
                await interaction.response.send_message(msg)
                return

            case "set":
                if limit is None or limit <= 1:
                    await interaction.response.send_message("Please provide a valid upper limit (>1).")
                    return
                limit = min(self.max_roll, limit)
                self.deathroll_player_rolls[player_id] = PlayerData(player_name, limit)
                await interaction.response.send_message(f"Set new max roll to {limit} for {player_name}")
                return


        if self.new_player(player_id) or self.expired_roll(player_id):
            if self.game_in_progress():
                await interaction.response.send_message("Cannot join mid-game. Wait for round to end.")
                return
            else:
                self.deathroll_player_rolls[player_id] = PlayerData(player_name, self.max_roll)
                await interaction.response.send_message("New player. Starting roll.")
        else:
            players_remaining = self.unrolled_players(self.deathroll_player_rolls[player_id].roll_round)
            if players_remaining:
                await interaction.response.send_message(
                    "Cannot roll yet. Waiting on: " + ", ".join(players_remaining)
                )
                return

        pdata = self.deathroll_player_rolls[player_id]
        pdata.old_limit = pdata.new_limit
        pdata.new_limit = random.randint(1, pdata.old_limit)
        pdata.roll_round += 1
        pdata.last_update = time.time()

        await interaction.response.send_message(
            f"**{player_name}** rolled **{pdata.new_limit}** out of {pdata.old_limit} for round {pdata.roll_round}"
        )

        if self.unrolled_players(pdata.roll_round):
            return

        if pdata.new_limit == 1:
            if pdata.roll_round == 1 and self.max_roll >= self.lol_threshold:
                await interaction.channel.send("lol")
            if self.all_rolled_1():
                await interaction.channel.send("All players rolled 1. Redoing round.")
                self.revert_limit()
                return

        if pdata.roll_round > 1 and len(self.deathroll_player_rolls) > 1:
            self.mark_lost_players()
            winner = self.only_winner_left()
            if winner:
                await interaction.channel.send(f"The winner is **{winner}** after {pdata.roll_round} rounds!")
                await interaction.channel.send("Resetting game.")
                self.deathroll_player_rolls = {}
            else:
                await interaction.channel.send(f"All players rolled. Begin round {pdata.roll_round + 1}")


    @app_commands.command(name="deathroll", description="Death roll. Action = roll/reset/resetall/set/list")
    @app_commands.describe(action="Choose roll/reset/resetall/set/list", limit="Optional number (used with 'set')")
    async def deathroll(self, interaction: discord.Interaction, action: str = "roll", limit: int = None):
        await self.deathroll_logic(interaction, action, limit)

    @app_commands.command(name="dr", description="Death roll. Action = roll/reset/resetall/set/list")
    @app_commands.describe(action="Choose roll/reset/resetall/set/list", limit="Optional number (used with 'set')")
    async def dr(self, interaction: discord.Interaction, action: str = "roll", limit: int = None):
        await self.deathroll_logic(interaction, action, limit)

    @app_commands.command(name="droll", description="Death roll. Action = roll/reset/resetall/set/list")
    @app_commands.describe(action="Choose roll/reset/resetall/set/list", limit="Optional number (used with 'set')")
    async def droll(self, interaction: discord.Interaction, action: str = "roll", limit: int = None):
        await self.deathroll_logic(interaction, action, limit)
        
    async def cog_load(self):
        self.client.tree.add_command(self.flip)
        self.client.tree.add_command(self.coin)
        self.client.tree.add_command(self.coin_flip)
        self.client.tree.add_command(self.random)
        self.client.tree.add_command(self.roll)
        self.client.tree.add_command(self.deathroll)
        self.client.tree.add_command(self.dr)
        self.client.tree.add_command(self.droll)
        

async def setup(client):
    await client.add_cog(ChanceGames(client))
