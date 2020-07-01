import discord
import os
from discord.ext import commands

client = commands.Bot(command_prefix = '!')

@client.command()
@commands.has_role('admin')
async def load(ctx,extension):
    client.load_extension(f'cogs.{extension}')


@client.command()
@commands.has_role('admin')
async def unload(ctx,extension):
    client.unload_extension(f'cogs.{extension}')


locallDir = os.path.dirname(os.path.abspath(__file__))
for filename in os.listdir(locallDir+'/cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run('CLIENT ID')

