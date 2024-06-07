import discord
from discord.ext import commands

import os.path
import random

from cogs.music import Music


class animalFacts(commands.Cog):
    def __init__(self, bot):
        self.self = self
        self.bot = bot
        self.sloth_facts_path = 'data/facts/sloth.txt'
        self.opposite_snake_facts_path = 'data/facts/opposite_snake.txt'


    async def giveFact(self, ctx, facts_path):
        x = 0
        # Count lines in file
        with open(facts_path, 'r', encoding='utf-8') as fp:
            x = len(fp.readlines())
            if x == 0:
                await ctx.send('No sloth facts found')
                return
        # Select random fact then send and say it
        with open(facts_path, 'r', encoding='utf-8') as fp:
            fact_num = random.randint(1, x)
            for i, line in enumerate(fp):
                if i == fact_num - 1:
                    await ctx.send(str(fact_num) + '. ' + line)
                    # Call the say command function from the Music cog
                    music_cog = self.bot.get_cog("Music")
                    if music_cog:
                        await music_cog.say(ctx, text=line)
                    break

    @commands.command(description="sloth facts", aliases=['sloth_facts', 'sloth', 'sloths'])
    async def slothfacts(self, ctx):
        facts_path = self.sloth_facts_path
        await self.giveFact(ctx, facts_path)


    @commands.command(description="opposite snake facts", aliases=['opposite_snakes', 'opposite_snake', 'oppositesnake', 'oppositesnakefacts', 'opposite_snake_facts'])
    async def oppositesnakes(self, ctx):
        facts_path = self.opposite_snake_facts_path
        await self.giveFact(ctx, facts_path)


async def setup(client):
    await client.add_cog(animalFacts(client))
