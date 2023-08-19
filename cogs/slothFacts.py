import discord
from discord.ext import commands

import os.path
import random

from cogs.music import Music


class slothFacts(commands.Cog):
    def __init__(self, bot):
        self.self = self
        self.bot = bot
        self.facts_path = 'data/facts/sloth.txt'


    @commands.command(description="sloth facts", aliases=['sloth_facts', 'sloth', 'sloths'])
    async def slothfacts(self, ctx):
        x = 0
        # Count lines in file
        with open(self.facts_path, 'r', encoding='utf-8') as fp:
            x = len(fp.readlines())
            if x == 0:
                await ctx.send('No sloth facts found')
                return
        # Select random fact then send and say it
        with open(self.facts_path, 'r', encoding='utf-8') as fp:
            fact_num = random.randint(1, x)
            for i, line in enumerate(fp):
                print(str(x) + ' ' + str(fact_num))
                if i == fact_num - 1:
                    await ctx.send(str(fact_num) + '. ' + line)
                    # Call the say command function from the Music cog
                    music_cog = self.bot.get_cog("Music")
                    if music_cog:
                        await music_cog.say(ctx, text=line)
                    break


async def setup(client):
    await client.add_cog(slothFacts(client))
