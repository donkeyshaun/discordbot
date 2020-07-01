import discord
from itertools import cycle
from discord.ext import commands, tasks
from discord.utils import get
import datetime
from datetime import timedelta  
from dateutil.relativedelta import relativedelta
import os
import asyncio
import pickle
import re


class Beetbattle(commands.Cog):
    def __init__ (self, client):
        self.client=client
        self.ACTIVE_BATTLE = False
        self.BATTLERS = []
        self.ACTIVE_BATTLERS = []
        self.BATTLEDATE = ''
        self.MAX_BATTLERS = 20
        self.SUBMISSIONS = {}
        self.emoji = cycle([":fire:",":boom:",":star:",":earth_americas:",":face_with_monocle:",":eggplant:"])
        self.guild = None
        self.prize = None
        self.voteTime = 12
        self.battleTime = 24
        self.ACTIVE_VOTE = False
        self.votes = {}
        self.roles = {}
        self.battleloop.start()
        self.timeloop.start()


    @commands.Cog.listener()
    async def on_ready(self):
        await self.setGuild(694807156570062849)
        self.BATTLERS = await self.loadBattlers()
        await self.loadsubs()
        await self.loaddate()
        await self.loadvotes()
        print('Battle Cog ready..')
    

    async def setGuild(self,guildId):
        self.guild = self.client.get_guild(guildId)


    @commands.command(help='Type !join to join the next beat battle.')
    async def join(self,ctx):
        await self.checkGuild()
        guild = self.guild
        channel = discord.utils.get(guild.channels,name='news')
        if ctx.author not in self.BATTLERS:
            self.BATTLERS.append(ctx.author)
            self.saveBattlers(self.BATTLERS)
            await channel.send('-------------------------------------------------------------------')
            await channel.send(next(self.emoji)+' '+ctx.author.display_name+' has joined the next battle.')
            await self.startNext()    


    async def startNext(self):
        await self.checkGuild()
        guild = self.guild
        if self.BATTLERS == []:
            self.BATTLERS = await self.loadBattlers()
        news_channel = discord.utils.get(guild.channels,name='news')
        if not self.ACTIVE_BATTLE and len(self.BATTLERS) >= self.MAX_BATTLERS:
            self.ACTIVE_BATTLE = True
            await asyncio.sleep(2)
            await news_channel.send('We are enough beet battlers.. Battle starts in:')
            await news_channel.send(':alarm_clock: 5..')
            await asyncio.sleep(1)
            await news_channel.send(':alarm_clock: 4..')
            await asyncio.sleep(1)
            await news_channel.send(':alarm_clock: 3..')
            await asyncio.sleep(1)
            await news_channel.send(':alarm_clock: 2..')
            await asyncio.sleep(1)
            await news_channel.send(':alarm_clock: 1..')
            await asyncio.sleep(1)
            await self.beetbattle(self.BATTLERS)
        elif self.ACTIVE_BATTLE and len(self.BATTLERS) >= self.MAX_BATTLERS:
            await news_channel.send('There is an active battle going on, the next battle will start when it is finished.')
        elif (self.MAX_BATTLERS-len(self.BATTLERS)) > 1:
            await news_channel.send('We need '+str((self.MAX_BATTLERS-len(self.BATTLERS)))+' more beet battlers before the next battle starts.')
        else:
            await news_channel.send('We need '+str((self.MAX_BATTLERS-len(self.BATTLERS)))+' more beet battler before the next battle starts.')


    async def beetbattle(self,members,channel_name='beetbattle'):
        self.ACTIVE_BATTLERS = members.copy()
        members.clear() # = BATTLERS
        self.saveBattlers(members)
        await self.checkGuild()
        guild = self.guild
        battle_channel = discord.utils.get(guild.channels, name=channel_name)
        if not battle_channel:
            print(f'Creating a new channel: {channel_name}')
            await guild.create_text_channel(channel_name)

        role = get(guild.roles, name="contestant")
        for member in self.ACTIVE_BATTLERS:
            await member.add_roles(role)

        await battle_channel.purge(limit=10000)

        self.BATTLEDATE = datetime.datetime.now() + timedelta(hours=self.battleTime)
        await self.pickledate()
        await battle_channel.send('Battle has started and will end '+str(self.battleTime)+' hours from now. Write !timeleft for remaining time.')
        sample = self.getSample()
        await battle_channel.send(':arrow_double_down: Here is the donwload link to the sample :arrow_double_down:')
        await battle_channel.send(sample)
        await self.countDown(battle_channel,role)
        await self.endbattle()
        self.saveSubmissions(self.SUBMISSIONS)
        await self.startVote()


    @commands.command(help='Resume battle.\n It should follow format !resumebattle + hours til end.')
    @commands.has_role('admin')
    async def resumebattle(self,ctx,h=None):
        self.ACTIVE_BATTLE = True
        tempBattleTime = self.battleTime
        await self.checkGuild()
        guild = self.guild
        battle_channel = discord.utils.get(guild.channels, name='beetbattle')
        role = get(guild.roles, name="contestant")
        if self.BATTLEDATE == '' or h != None:
            if h == None:
                ctx.send("You did not provide a time and no time is currently saved.\n"+
                'Type !help resumebattle for more info.')
                return
            self.BATTLEDATE = datetime.datetime.now() + timedelta(hours=int(h))
            await self.pickledate()

        currDate = datetime.datetime.now()
        diff = relativedelta(self.BATTLEDATE, currDate)
        self.battleTime = diff.hours

        if self.battleTime >= 1:
            await self.countDown(battle_channel,role)
        elif diff.hours < 1 and diff.hours >= 0 and diff.minutes >= 0 and diff.seconds >= 0:
            #await battle_channel.send(':alarm_clock: Only '+str(diff.minutes)+' left.. :alarm_clock: Write !timeleft for remaining time.\n'+role.mention+"'"+'s make sure you send in your submission in time with !submit followed by your soundcloud link.')
            await asyncio.sleep(diff.minutes*60)

        self.battleTime = tempBattleTime
        await self.endbattle()
        self.saveSubmissions(self.SUBMISSIONS)
        await self.startVote()

    async def countDown(self,battle_channel,role):
        await asyncio.sleep((self.battleTime-1)*3600) #3600 1 hour in sec
        await battle_channel.send(':alarm_clock: Only one hour left.. :alarm_clock: Write !timeleft for remaining time.\n'+role.mention+"'"+'s make sure you send in your submission in time with !submit followed by your soundcloud link.')
        await asyncio.sleep(2400) #2400 40min
        await battle_channel.send(':alarm_clock: Only 20 minutes left.. :alarm_clock: Write !timeleft for remaining time.\n'+role.mention+"'"+'s make sure you send in your submission in time with !submit followed by your soundcloud link.')
        await asyncio.sleep(600) #600 10min
        await battle_channel.send(':alarm_clock: Only 10 minutes left.. :alarm_clock: Write !timeleft for remaining time.\n'+role.mention+"'"+'s make sure you send in your submission in time with !submit followed by your soundcloud link.')
        await asyncio.sleep(595) #595 10min ish
        await battle_channel.send(':alarm_clock: 5..')
        await asyncio.sleep(1)
        await battle_channel.send(':alarm_clock: 4..')
        await asyncio.sleep(1)
        await battle_channel.send(':alarm_clock: 3..')
        await asyncio.sleep(1)
        await battle_channel.send(':alarm_clock: 2..')
        await asyncio.sleep(1)
        await battle_channel.send(':alarm_clock: 1..')
        await asyncio.sleep(1)
        await battle_channel.send(':fire: The beat battle is now over :fire:')


    @commands.command(help='Type !vote + "contestant screen name".\n'+
    'Exampel: !vote "john doe" or !vote @john doe.\n'+ 
    'If you want to vote via PM to beetbot you can not use @ you must include the screen name within actual quotes.\n'+
    'If you vote in any other chat within the beetbattle room you can either @ them or write their name in quotes.\n'+
    'You can only vote on one person. If you vote multiple times it will only count the most recent.')
    async def vote(self,ctx,memb):
        await self.checkGuild()
        if not self.ACTIVE_VOTE:
            ctx.send("We are not taking votes right now..")
            return

        if memb[1] == '@': 
            try:
                self.votes[ctx.author.mention] = memb
            except:
                await ctx.send('Something went wrong. Type "!help vote" for more info.')
                return
        else:
            name = ctx.message.content
            name = name[name.find('"')+1:]
            name = name[:name.find('"')]
            member = await self.getMemberById(name)
            if member == None:
                await ctx.send('Something went wrong. Type "!help vote" for more info.')
                return

            self.votes[ctx.author.mention] = member.mention

        await ctx.send(ctx.author.mention + ' has voted.')
        await self.picklevote()



    async def startVote(self):
        self.ACTIVE_VOTE = True
        self.BATTLEDATE = datetime.datetime.now() + timedelta(hours=self.voteTime)
        await self.pickledate()
        self.votes = {}
        await self.picklevote()
        await self.checkGuild()
        guild = self.guild
        everyone = get(guild.roles, name="@everyone")
        vote_channel = discord.utils.get(guild.channels, name='vote')
        await vote_channel.purge(limit=10000)
        if len(self.SUBMISSIONS) < 2:
            await vote_channel.send("We did not get enough submissions this round..")
            return
        battleNum = str(self.getBattleNumber())
        await vote_channel.send(":small_red_triangle_down:  ALL TRACKS FROM BATTLE #"+battleNum+"  :small_red_triangle_down:")

        for submission in self.SUBMISSIONS:
            await asyncio.sleep(1)
            await vote_channel.send('\n----------------------------------------------------------------------------\n')
            await vote_channel.send(submission+' -- '+self.SUBMISSIONS[submission])
                
        await vote_channel.send('\n----------------------------------------------------------------------------\n')
        await vote_channel.send(everyone.name+" can vote with the !vote command. Type !help vote for more info.\n"+
        "You have "+str(self.voteTime)+" hours..")
        await asyncio.sleep((self.voteTime-1)*3600) #3600 1 hour
        await vote_channel.send(everyone.name+" 1 hour left.. :alarm_clock:")
        await asyncio.sleep(3000) #3000 50 min
        await vote_channel.send(':alarm_clock: '+everyone.name+' There is only 10 minutes left to vote.. :alarm_clock:')
        await asyncio.sleep(595) #595 10min ish
        await vote_channel.send(':alarm_clock: 5..')
        await asyncio.sleep(1)
        await vote_channel.send(':alarm_clock: 4..')
        await asyncio.sleep(1)
        await vote_channel.send(':alarm_clock: 3..')
        await asyncio.sleep(1)
        await vote_channel.send(':alarm_clock: 2..')
        await asyncio.sleep(1)
        await vote_channel.send(':alarm_clock: 1..')
        await asyncio.sleep(1)
        await self.countvotes()
        return


    @commands.command(help='Adds submission manually.\n It should follow format "battler screen name" (with quotes without #1234 at the end) +link')
    @commands.has_role('mods')
    async def addsubmission(self,ctx):
        link = self.getURL(ctx.message.content)
        if link:
            name = ctx.message.content
            name = name[name.find('"')+1:]
            name = name[:name.find('"')]
            member = await self.getMemberById(name)
            try:
                self.SUBMISSIONS[member.mention] = link
                await self.picklesubs()
                await ctx.send('Submission received')
            except:
                await ctx.send('Something went wrong..')
        else:
            await ctx.send('Something went wrong please try to submit again.\n'+ 
            'Check if you sent the full link to your track. Only single track works, make sure that you are not trying to share a set/playlist.\n'+
            'Make sure you link follows this format:\n'+
            '"https://soundcloud.com/username/trackid"')



    @commands.command(help='Count all votes and annouces a winner.')
    @commands.has_role('admin')
    async def countvotes(self,ctx=None):
        await self.checkGuild()
        battleNum = str(self.getBattleNumber())
        winner_channel = discord.utils.get(self.guild.channels, name='winners')
        vote_channel = discord.utils.get(self.guild.channels, name='vote')
        votesPerSub = {}
        for sub in self.SUBMISSIONS:
            votesPerSub[sub] = 0
        for vote in self.votes:
            try:
                cont = self.votes[vote]
                if cont[2] == '!':
                    cont = '<@'+cont[3:len(cont)]
                    votesPerSub[cont] += 1
                else:
                    votesPerSub[self.votes[vote]] += 1
            except:
                try:
                    cont = await self.getMemberById(self.votes[vote])
                    votesPerSub[cont.mention] += 1
                except:
                    print("Could not find contestant "+self.votes[vote])


        #Calculate first, second and third place
        first = 0
        firstArr = []
        second = 0
        secondArr = []
        third = 0
        thirdArr = []
        for contestant in votesPerSub:
            if first < votesPerSub[contestant]:
                third = second
                second = first
                first = votesPerSub[contestant]

                thirdArr = secondArr
                secondArr = firstArr
                firstArr = [contestant]
            elif first == votesPerSub[contestant]:
                firstArr.append(contestant)
            if second < votesPerSub[contestant] and votesPerSub[contestant] < first:
                third = second
                second = votesPerSub[contestant]

                thirdArr = secondArr
                secondArr = [contestant]
            elif second == votesPerSub[contestant]:
                secondArr.append(contestant)
            if third < votesPerSub[contestant] and votesPerSub[contestant] < second: 
                third = votesPerSub[contestant]
                thirdArr = [contestant]
            elif third == votesPerSub[contestant]:
                thirdArr.append(contestant)
        

        await vote_channel.send('\n----------------------------------------------------------------------------\n')
        await vote_channel.send(':drum: Votes are counted and the winner is... :drum:')
        await asyncio.sleep(5)
        await winner_channel.send('\n----------------------------------------------------------------------------\n')
        await winner_channel.send(':small_red_triangle_down: WINNER OF BATTLE #'+battleNum+' :small_red_triangle_down:')
        for winner in firstArr:
            if winner in self.SUBMISSIONS:
                await vote_channel.send(':first_place:  '+winner+'  :first_place:') 
                await winner_channel.send(winner+' -- '+self.SUBMISSIONS[winner])
        #Second place
        for winner in secondArr:
            if winner in self.SUBMISSIONS:
                await vote_channel.send(':second_place:  '+winner+'  :second_place:') 
        #Third place
        for winner in thirdArr:
            if winner in self.SUBMISSIONS:
                await vote_channel.send(':third_place:  '+winner+'  :third_place:') 

        await vote_channel.send('\n----------------------------------------------------------------------------\n')
        await asyncio.sleep(60) #1 min
        await vote_channel.send('All submissions will be uploaded to: https://soundcloud.com/inserttapes')
        self.SUBMISSIONS.clear()
        await self.picklesubs()
        await self.client.change_presence(activity=discord.Game('Waiting for contestants..'))
        self.incrementBattleNumber(self.getBattleNumber())
        self.ACTIVE_BATTLE = False
        self.ACTIVE_VOTE = False
        return


    async def endbattle(self):
        await self.checkGuild()
        guild = self.guild
        role = get(guild.roles, name="contestant")
        if len(self.ACTIVE_BATTLERS) == 0: #ÄNDRA DETTA BÅDE HÄR OCH NERE
            async for member in self.guild.fetch_members():
                for roles in member.roles:
                    if roles == role:
                        await member.remove_roles(role)
                        break
        else: 
            for member in self.ACTIVE_BATTLERS:
                try:
                    await member.remove_roles(role)
                except:
                    print("UNKNOWN MEMBER")
            self.ACTIVE_BATTLERS.clear()
        self.prize = None


    @commands.command(help='Stops battle if needed.')
    @commands.has_role('admin')
    async def stopbattle(self,ctx):
        self.ACTIVE_BATTLE = False
        await self.checkGuild()
        guild = self.guild
        role = get(guild.roles, name="contestant")
        if len(self.ACTIVE_BATTLERS) == 0:
            async for member in self.guild.fetch_members():
                if member.has_role(role):
                    await member.remove_roles(role)
        else:
            for member in self.ACTIVE_BATTLERS:
                await member.remove_roles(role)
            self.ACTIVE_BATTLERS.clear()
        self.incrementBattleNumber(self.getBattleNumber())
        self.prize = None


    @commands.command(help='Start battle if ready.\n If not ready it reminds how many is needed to start in #news.')
    @commands.has_role('admin')
    async def startbattle(self,ctx):
        await self.startNext()


    @commands.command(help='Change the battle time.\n The time contestants have to flip the sample.')
    @commands.has_role('admin')
    async def battletime(self,ctx,time):
        try:
            self.battleTime = int(time)
            await ctx.send("The battle time is now "+time+" hours")
        except:
            await ctx.send("Could not change the battle time")


    @commands.command(help='Change the vote time.')
    @commands.has_role('admin')
    async def votetime(self,ctx,time):
        try:
            self.voteTime = int(time)
            await ctx.send("The vote time is now "+time+" hours")
        except:
            await ctx.send("Could not change the vote time")


    @commands.command(help='Adds battler manually to queue.\n It should follow format "battler screen name" (with quotes without #1234 at the end).')
    @commands.has_role('mods')
    async def addbattler(self,ctx,battler):
        if self.guild == None:
            await self.setGuild(694807156570062849)
        member = await self.getMemberById(battler)
        if member not in self.BATTLERS and member != None:
            self.BATTLERS.append(member)
            self.saveBattlers(self.BATTLERS)


    @commands.command(help='Removes battler manually.')
    @commands.has_role('admin')
    async def removebattler(self,ctx,battler):
        if self.guild == None:
            await self.setGuild(694807156570062849)
        member = await self.getMemberById(battler)
        if member in self.BATTLERS and member != None:
            self.BATTLERS.remove(member)
            self.saveBattlers(self.BATTLERS)
        

    async def getMemberById(self,battler):
        async for member in self.guild.fetch_members():
            if member.display_name == battler:
                return member

    
    @commands.command(help='Submit your beat.\n Type !Submit followed by your sondcloud link.')
    @commands.has_role('contestant')
    async def submit(self,ctx):
        await self.checkGuild()
        guild = self.guild
        battle_channel = discord.utils.get(guild.channels, name='beetbattle')
        link = self.getURL(ctx.message.content)
        if link:
            await battle_channel.send('Submission received from '+ctx.author.mention+' '+next(self.emoji))
            self.SUBMISSIONS[ctx.author.mention] = link
            await self.picklesubs()
        else:
            await battle_channel.send(ctx.author.mention+' something went wrong please try to submit again.\n'+ 
            'Check if you sent the full link to your track. Only single track works, make sure that you are not trying to share a set/playlist.\n'+
            'Make sure you link follows this format:\n'+
            '"https://soundcloud.com/username/trackid"')


    @commands.command(help='Set your own role. Type "!help role" for more info.\n'+
    'We have special roles in this server that can define you as a musician and help you get in contact with people that are searching for your expertise.\n'+
    'To claim a role simply type "!role"+"name of role", you can join multiple roles.\n'+
    'For all roles available type !getroles.')
    async def role(self,ctx,r):
        await self.checkGuild()
        guild = self.guild
        await self.checkRoles()
        try:
            if r in self.roles:
                role = get(guild.roles, name=r)
                await ctx.author.add_roles(role)
            else:
                await ctx.send(r+' is not a selectable role. Type !getroles to get a list of all roles.')
        except:
            await ctx.send('Something went wrong type "!help role" for all info about this command. Make sure you are doing this within the beetbattle server.')


    @commands.command(help='Sends a list of all roles')
    async def getroles(self,ctx):
        direct_m = await ctx.author.create_dm()
        await direct_m.send(":small_red_triangle_down:  All roles  :small_red_triangle_down:")
        await self.checkRoles()
        for role in self.roles:
            await direct_m.send(':robot:    '+role+' -- '+self.roles[role])
        
        await direct_m.send('If you are missing a role then post your suggestion in the #suggestions channel.')


    async def checkRoles(self):
        if not self.roles:
            await self.loadroles()
        return


    @commands.command(help='Adds role to list that can be used in !role.\n' 
    'Type "!addrole role"+"Role description.')
    @commands.has_role('admin')
    async def addrole(self,ctx,r):
        await self.checkGuild()
        guild = self.guild
        await self.checkRoles()
        role = get(guild.roles, name=r)
        if role != None:
            desc = ctx.message.content
            desc = desc[desc.find(r)+len(r)+1:len(desc)]
            self.roles[r] = desc
            await self.pickleroles()
            await ctx.send('Role added.')
        else:
            await ctx.send('Something went wrong..')


    @commands.command(help='Removes role to list that can be used in !role.\n' 
    'Type "!removerole role".')
    @commands.has_role('admin')
    async def removerole(self,ctx,r):
        await self.checkRoles()
        if r in self.roles:
            del self.roles[r]
            await self.pickleroles()
            await ctx.send('Role removed.')
        else:
            await ctx.send('Something went wrong..')


    def getURL(self,msg):
        msg = str(msg).split(" ")
        for i in msg:
            i = i.strip() 
            if i.find("https://soundcloud.com/") != -1 and i.find("/sets/") == -1:
                i = i[i.find("https://soundcloud.com/"):len(i)]
                substring = "/"
                count = i.count(substring)
                if count == 4 or count == 5:
                    return i
        return False


    def getBattleNumber(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "battlenumber.txt"), 'r') as f_read:
            num = int(f_read.read().strip())
            f_read.close()
        return num


    def incrementBattleNumber(self,num):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "battlenumber.txt"), 'w') as f:
            f.write(str(num+1))
            f.close()
        return num


    def saveSubmissions(self,subs):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        num = self.getBattleNumber()
        with open(os.path.join(locallDir, "submissions.txt"), 'a') as f_write:
            f_write.write('\n'+str(num))
            for sub in subs:
                f_write.write(','+subs[sub])
            f_write.close()


    @commands.command(help='Save all submissions.')
    @commands.has_role('admin')
    async def picklesubs(self,ctx=None):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "picklesub.pickle"), 'wb') as f:
            pickle.dump(self.SUBMISSIONS,f)
            f.close()


    @commands.command(help='Load all submissions.')
    @commands.has_role('admin')
    async def loadsubs(self,ctx=None):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "picklesub.pickle"),'rb') as f:
            self.SUBMISSIONS = pickle.load(f)
            f.close()  


    async def pickledate(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "date.pickle"), 'wb') as f:
            pickle.dump(self.BATTLEDATE,f)
            f.close()


    async def loaddate(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "date.pickle"),'rb') as f:
            self.BATTLEDATE = pickle.load(f)
            f.close()  


    async def picklevote(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "votes.pickle"), 'wb') as f:
            pickle.dump(self.votes,f)
            f.close()


    async def loadvotes(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "votes.pickle"),'rb') as f:
            self.votes = pickle.load(f)
            f.close()


    async def pickleroles(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "roles.pickle"), 'wb') as f:
            pickle.dump(self.roles,f)
            f.close()


    async def loadroles(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "roles.pickle"),'rb') as f:
            self.roles = pickle.load(f)
            f.close()                

    def addSample(self,link):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        urls = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', link)
        if len(urls) > 0:
            with open(os.path.join(locallDir, "samples.txt"), 'r') as fin:
                contents = fin.readlines()
                fin.close
            for url in urls:
                contents.append(url)
            with open(os.path.join(locallDir, "samples.txt"), 'w') as fout:
                fout.writelines(contents)
                fin.close
            return True
        return False


    def getSample(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "samples.txt"), 'r') as fin:
            contents = fin.readlines()
            fin.close
        with open(os.path.join(locallDir, "samples.txt"), 'w') as fout:
            fout.writelines(contents[1:])
            fin.close
        return contents[0]


    @commands.command(help='Adds a price for the next battle.')
    @commands.has_role('admin')
    async def addprize(self,ctx):
        self.prize = ctx.message.content[10:]
        await self.checkGuild()
        guild = self.guild
        channel = discord.utils.get(guild.channels,name='news')
        everyone = get(guild.roles, name="@everyone")
        await channel.send(everyone.name+' PRIZE FOR NEXT BATTLE :arrow_down:')
        await channel.send(':first_place: '+self.prize+' :first_place:')


    @commands.command(help='The price up for stake in the next battle.')
    async def prizes(self,ctx):
        if self.prize != None:
            await ctx.send(ctx.author.mention+' grand prize of next battle is: :first_place: '+ self.prize+' :first_place:')
        else:
            await ctx.send(ctx.author.mention+' no prize for the next battle.')


    @commands.command(help='Time left on current battle.')
    async def timeleft(self,ctx):
        currDate = datetime.datetime.now()
        diff = relativedelta(self.BATTLEDATE, currDate)

        if self.ACTIVE_VOTE:
            await ctx.send(':alarm_clock: Votes will be counted in '+str(diff.hours)+':'+str(diff.minutes)+':'+str(diff.seconds))           
        elif self.ACTIVE_BATTLE:

            await ctx.send(':alarm_clock: Battle ends in '+str(diff.hours)+':'+str(diff.minutes)+':'+str(diff.seconds))
        else:
            await ctx.send("There is no active battle..")


    @commands.command(help='Changes group size.')
    @commands.has_role('admin')
    async def groupsize(self,ctx, numBattlers=20):
        self.MAX_BATTLERS = numBattlers
        await ctx.send('Number of battlers required is now '+str(numBattlers))


    @commands.command(help='Adds a direct download link to sample queue.\n Write for example "!addsample https://www.google.com/"'+
    ' to add the link to the queue. The queue contains download links of samples to flip in future battles.')
    @commands.has_role('admin')
    async def addsample(self,ctx):
        if(self.addSample(ctx.message.content)):
            await ctx.send("Link added to download queue.")
        

    def saveBattlers(self,battlers):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        battler_ids = []
        for battler in battlers:
            battler_ids.append(battler.id)

        with open(os.path.join(locallDir, "battlers.pickle"), 'wb') as f:
            pickle.dump(battler_ids, f)


    async def loadBattlers(self):
        locallDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(locallDir, "battlers.pickle"),'rb') as f:
            battler_ids = pickle.load(f)
        battlers = []
        for battlers_id in battler_ids:
            async for member in self.guild.fetch_members():
                if member.id == battlers_id:
                    battlers.append(member)
        return battlers

    
    async def checkGuild(self):
        if self.guild == None:
            await self.setGuild(694807156570062849)
        return

    #TASK LOOPS
    @tasks.loop(seconds=5)
    async def battleloop(self):
        if not self.ACTIVE_BATTLE and not self.ACTIVE_VOTE and len(self.BATTLERS) >= self.MAX_BATTLERS:
            await self.startNext() 

    @battleloop.before_loop
    async def before_battleloop(self):
        await asyncio.sleep(1800)
        await self.client.wait_until_ready()
      

    @tasks.loop(minutes=1)
    async def timeloop(self):
        if self.ACTIVE_VOTE and self.ACTIVE_BATTLE:
            currDate = datetime.datetime.now()
            diff = relativedelta(self.BATTLEDATE, currDate)
            await self.client.change_presence(activity=discord.Game('Vote ends in: '+str(diff.hours)+'h:'+str(diff.minutes)+'m'))
        elif self.ACTIVE_BATTLE:
            currDate = datetime.datetime.now()
            diff = relativedelta(self.BATTLEDATE, currDate)
            await self.client.change_presence(activity=discord.Game('Battle ends in: '+str(diff.hours)+'h:'+str(diff.minutes)+'m'))
        


    @timeloop.before_loop
    async def before_timeloop(self):
        await self.client.wait_until_ready()
   

def setup(client):
    client.add_cog(Beetbattle(client))
