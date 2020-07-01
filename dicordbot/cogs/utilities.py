import discord
from itertools import cycle
from discord.ext import commands, tasks
import asyncio
import os

class Utilities(commands.Cog):
    def __init__ (self, client):
        self.client=client
        self.postCoffee.start()
        #self.postInfo.start()
        self.postTwitter.start()


    @commands.Cog.listener()
    async def on_ready(self):
        print('Utilities Cog ready..')

        

    @commands.Cog.listener()
    async def on_command_error(self,ctx,error):
        if isinstance(error,commands.MissingRole):
            await ctx.send(ctx.author.mention+' you do not have permission to use that command.')
        if isinstance(error,commands.MissingRequiredArgument):
            await ctx.send(ctx.author.mention+' you did not provide enough arguments for this command. \n'+ 
            'Type !help "command" for more info.')
        if isinstance(error,commands.MissingAnyRole):
            await ctx.send(ctx.author.mention+' you do not have permission to use that command.')
        if isinstance(error,commands.CommandNotFound):
            await ctx.send(ctx.author.mention+' that command does not exist. Type !help for the full list of commands')
        
        print(error)


    @commands.Cog.listener()
    async def on_member_join(self,member):
        await member.create_dm()
        await member.dm_channel.send(
            f'Hi {member.name}, welcome to the beetbattle server!\n'+
            'I am the bot that runs everyting around here. Type !help for info about all my commands.\n'+
            'If you want to queue up for the next battle type !join in the #general chat over at the beetbattle server.\n'
        )


    def saveSample(self,msg):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "sampleflip.txt"), 'a') as f_write:
            f_write.write('\n'+msg)


    @tasks.loop(hours=37)
    async def postCoffee(self):
        general = self.client.get_channel(id=694807156570062852)
        await general.send(
            f':coffin: This bot is brought to you by Insert Tapes :coffin:\n'+
            'If you like what we do please consider supporting us.\n'+
            ':link: Patreon - https://www.patreon.com/inserttapes\n'+
            ':coffee:  Buy us a coffeee - https://ko-fi.com/inserttapes\n'
    )

    @postCoffee.before_loop
    async def before_postCoffee(self):
        print('Coffee waiting...')
        await asyncio.sleep(3600)
        await self.client.wait_until_ready()


    @tasks.loop(hours=35)
    async def postInfo(self):
        general = self.client.get_channel(id=694807156570062852)
        await general.send(
            f':musical_keyboard:  Do you have a track that you want us to use in the battle?  :musical_keyboard:\n'+
            'Type !flipthis followed by a link and we will check it out.'+
            '\n----------------------------------------------------------------------------\n'+
            ':moneybag: Type !prizes for prizes at stake in the next battle :moneybag:\n'
    )


    @postInfo.before_loop
    async def before_postInfo(self):
        print('Info waiting...')
        await asyncio.sleep(600)
        await self.client.wait_until_ready()


    @tasks.loop(hours=36)
    async def postTwitter(self):
        general = self.client.get_channel(id=694807156570062852)
        await general.send(
            f':coffin:  https://twitter.com/beetbattle  :coffin:\n')


    @postTwitter.before_loop
    async def before_postTwitter(self):
        print('Twitter waiting...')
        await asyncio.sleep(1800)
        await self.client.wait_until_ready()


    @commands.command(help='The battle rules and info.')
    async def rules(self,ctx):
        direct_m = await ctx.author.create_dm()
        await direct_m.send(
            f'How the beet battles work:\n'+
            '- Type !join to join the next match\n'+
            '- Wait until enough people has joined\n'+
            '- When the battle starts you will get access to a battle chat\n'+
            '- A link will be posted where you can download the track you are going to flip\n'+
            '- You got 24h to flip the sample\n'+
            '- When you are done with the track upload it to soundcloud\n'+
            '- Write "!submit" + "your soundcloud track link"\n'+
            '- When the battle is over all submissions will be posted in the #vote channel\n'+
            '- Everyone can vote with the !vote command, type !help vote for more info\n'+
            '- All votes will be counted and a winner will be selected\n'+
            '- A new battle will start when the votes are counted and a winner is announced\n'+
            '- All submissions will be mixed together and released on soundcloud\n\n'+
            'The rules of the battle:\n'+
            '1. You must flip the track provided in any way.\n'+
            '2. External instruments and samples are allowed but the sample should be prominent\n'+
            '3. Have fun.\n\n\n'+
            '- Type !help for all commands\n'+
            '- Type !help + command for more info about that command\n'
        )


    @commands.command(help='Clears textchat.')
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self,ctx, amount=5):
        await ctx.channel.purge(limit=amount)


    @commands.command(help='Submit tracks that can be used in the battles. \nWrite !flipthis followed by a link to the track.')
    async def flipthis(self,ctx,link):
        self.saveSample(link)


def setup(client):
    client.add_cog(Utilities(client))
