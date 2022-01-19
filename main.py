import discord
import os
from discord.ext import commands

client = commands.Bot(command_prefix='.')


@client.event
async def on_ready():
    print ('Bot has started')

@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    print('Loaded ', extension)


@client.command()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    print('Unloaded ', extension)


@client.command(description="[all] - reload cogs")
async def reload(ctx, extension):
    if extension == 'all':
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                client.unload_extension(f'cogs.{filename[:-3]}')
                client.load_extension(f'cogs.{filename[:-3]}')
        print('All extensions reloaded')
    else:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        print('Reloaded ', extension)


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(os.environ.get('DISCORD_BOT_TOKEN'))
