import discord
import os
from discord.ext import commands

prefix = '!'

intents = discord.Intents.default()
intents.voice_states = True
# intents.messages = True
intents.message_content = True

client = commands.Bot(command_prefix=prefix, intents=intents)
tree = client.tree


@client.event
async def on_ready():
    await load_cogs()
    await tree.sync()  # Syncs slash commands with Discord
    print(f'Logged in as {client.user.name} - {client.user.id}')


@client.command()
async def load(ctx, extension):
    await client.load_extension(f'cogs.{extension}')
    print('Loaded ', extension)


# @client.command()
# async def unload(ctx, extension):
#     await client.unload_extension(f'cogs.{extension}')
#     print('Unloaded ', extension)


# @client.command(description="[all] - reload cogs")
# async def reload(ctx, extension):
#     if extension == 'all':
#         for filename in os.listdir('./cogs'):
#             if filename.endswith('.py'):
#                 client.unload_extension(f'cogs.{filename[:-3]}')
#                 client.load_extension(f'cogs.{filename[:-3]}')
#         print('All extensions reloaded')
#     else:
#         client.unload_extension(f'cogs.{extension}')
#         client.load_extension(f'cogs.{extension}')
#         print('Reloaded ', extension)


# Function to load extensions with await
async def load_extension_cog(cog_name):
    try:
        await client.load_extension(cog_name)
        print(f'Cog {cog_name} loaded')
    except Exception as e:
        print(f'Failed to load cog {cog_name}: {e}')


# Automatically load cogs from the 'cogs' folder
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await load_extension_cog(f'cogs.{filename[:-3]}')


client.run(os.environ.get('ABBOT_TOKEN'))
