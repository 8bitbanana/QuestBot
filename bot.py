import discord, asyncio, twitter, subprocess, json, random
from configuration import Config
from database import Database, Player

config = Config()

guildId = config.serverId
jackId = config.DMid

announceChannelId = config.BotAnnounceChannel

db = Database()

# twitter = twitter.Api(
#     consumer_key=Config.ApiKeys['twitter']['ClientId'],
#     consumer_secret=Config.ApiKeys['twitter']['ClientSecret'],
#     access_token_key=Config.ApiKeys['twitter']['AccessKey'],
#     access_token_secret=Config.ApiKeys['twitter']['AccessSecret']
# )

class Client(discord.Client):

    async def on_ready(self):
        self.guild = None
        self.confirmCommand = None
        self.confirmData = None
        self.rig = None

        print('Logged on as {0}!'.format(self.user))
        for x in self.guilds:
            if x.id == guildId:
                self.guild = x
                break
        else:
            raise FileNotFoundError("The bot is not in the correct guild")
        
        self.announceChannel = self.get_channel(config.BotAnnounceChannel)
        self.voyagesChannel = self.get_channel(config.BotVoyagesChannel)
        self.generalChannel = self.get_channel(config.BotGeneralChannel)

        self.updateMemberDB()

        self.main_loop_instance = client.loop.create_task(self.schedule_task(2, self.main_loop))

    async def schedule_task(self, timeout, func):
        while True:
            await asyncio.sleep(timeout)
            await func()

    async def main_loop(self):
        tasks = db.popAllTasks()
        for task in tasks:
            print(task)
            command = task.split(" ")
            if command[0] == "LEVELUP":
                discordId = command[1]
                player = db.getPlayer(discordId)
                await self.announceChannel.send(f"<@{discordId}> leveled up to level {player.getLevel()}!")
                #twitter.PostUpdate(f"{player.nick} just leveled up to level {player.getLevel()}!")
            if command[0] == "NEWQUEST":
                questId = command[1]
                quest = db.getQuest(questId)
                if quest.dm:
                    dm = db.getPlayer(quest.dm).nick
                else:
                    dm = "No-one (why is this announcement here?)"    
                embed = discord.Embed(
                    title=quest.title,
                    description=f"*DMed by {dm}*\n{quest.description}",
                    url="https://quest.ethancrooks.com"
                )
                await self.voyagesChannel.send(f"@everyone A new Quest is now available!", embed=embed)
                #twitter.PostUpdate(f"A new quest is available!\n{quest.title[:200]}")
            # if command[0] == "WHISPER":
            #     self.generalChannel.send("bonk")


    def updateMemberDB(self):
        print("Updating member DB")
        members = []
        for member in self.guild.members:
            if member.bot:
                continue
            members.append(member)
        db.sanityCheck(members)
        print("Done updating member DB")

    async def on_message(self, message):
        if message.content == "QuestBot fucked my wife":
            await message.channel.send("prove it")
           
        if len(message.content) > 1 and message.content[0] == "!":
            command = message.content[1:].split(" ")
            if type(message.channel) == discord.DMChannel and message.channel.recipient.id == Config.EthanId:
                if command[0] == "stop":
                    await client.logout()
                if command[0] == "say":
                    if command[1] == "this":
                        channel = message.channel
                    else:
                        channel = self.get_channel(int(command[1]))
                    sentMessage = await channel.send(" ".join(command[2:]))
                    await message.channel.send(str(sentMessage.id))
                if command[0] == "delete":
                    channel = self.get_channel(int(command[1]))
                    messageToDelete = await channel.fetch_message(int(command[2]))
                    await message.channel.send(f"Are you sure you want to delete this message?\n> {messageToDelete.content}\nType !confirm to confirm")
                    self.confirmCommand = "DELETE"
                    self.confirmData = messageToDelete
                if command[0] == "confirm":
                    if self.confirmCommand != None:
                        if self.confirmCommand == "DELETE":
                            await self.confirmData.delete()
                        self.confirmCommand = None
                        self.confirmData = None
                if command[0] == "logs":
                    inttest = int(command[1])
                    logs = subprocess.check_output(['/usr/bin/tail', '-'+command[1], './logs/uwsgi.log'])
                    logs = logs.decode("utf-8").splitlines()[::-1]
                    async with message.channel.typing():
                        for log in logs:
                            await message.channel.send(log)
                if command[0] == "emoji":
                    for emoji in self.guild.emojis:
                        await message.channel.send(f"{emoji.name} - {emoji.id}")
                if command[0] == "rig":
                    if command[1] == "min":
                        self.rig = "min"
                    elif command[1] == "max":
                        self.rig = "max"
                    elif command[1] == "stop":
                        self.rig = "stop"
 
            if command[0] == "quests":
                quests = db.getAllQuests()
                embed = discord.Embed(
                    title = "Current Active Quests"
                )
                chars = 0
                for quest in quests:
                    if quest.dm == None: continue
                    questText = f"*DMed by {db.getPlayer(quest.dm).nick}*\n{quest.description[:300]}"
                    if len(quest.description) >= 300:
                        questText += "..."
                    chars += len(quest.title) + len(questText)
                    if chars >= 5000:
                        await message.channel.send("", embed=embed)
                        embed = discord.Embed(title="")
                        chars = len(quest.title) + len(questText)
                    embed.add_field(
                        name = quest.title,
                        value = questText,
                        inline = True
                    )
                await message.channel.send("", embed=embed)
            if command[0] == "meals":
                embed = discord.Embed(
                    title = "Gourmet Meals",
                    description = "Before a quest, characters can pay 10 Influence to have Gourmet live up to his namesake, and cook them up something special.\nYou gain the benefits for the duration of the quest."
                )
                with open("meals.json", "r") as f:
                    meals = json.load(f)
                for name, desc in meals.items():
                    embed.add_field(
                        name=name,
                        value=desc,
                        inline=True
                    )
                await message.channel.send("", embed=embed)
            if command[0] == "bees":
                await message.channel.send("There are bees here let's leave immediately")
            if command[0] == "banner":
                await message.channel.send("You may use your reaction to feel inspired by the banner.")
            if command[0] == "map":
                embed = discord.Embed(
                    title = "Chain Marches Map",
                    url = "https://cdn.discordapp.com/attachments/670998594697953283/683682968648155161/Chain_Marches_Nov30_13-54.png"
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/670998594697953283/683682968648155161/Chain_Marches_Nov30_13-54.png")
                await message.channel.send("", embed=embed)
            if command[0] == "fuck":
                embed = discord.Embed()
                embed.set_image(url="https://i.imgur.com/HyWrluy.png")
                await message.channel.send("", embed=embed)
            if command[0] == "today":
                await message.channel.send(f"Today is the {Config.GetCompanyDate()}")
            if command[0] == "nextlevel":
                quests = db.getAllQuests()
                quests = sorted(quests, key=lambda x: x.date if x.date else float('inf'))
                if len(quests) > 0:
                    quest = quests[0]
                    questPlayers = []
                    if quest.commander: questPlayers.append(quest.commander)
                    questPlayers += list(quest.players.keys())
                    willLevelUp = []
                    for discordId in questPlayers:
                        if discordId in quest.voidRewards: continue
                        player = db.getPlayer(discordId)
                        stampsNeeded = player.StampTotalToNextLevel() - player.stamps
                        if stampsNeeded <= quest.stampReward:
                            willLevelUp.append(player)
                    if len(willLevelUp) == 0:
                        await message.channel.send(f"Nobody will level up after {quest.title}")
                    elif len(willLevelUp) == 1:
                        await message.channel.send(f"{willLevelUp[0].nick} will level up after {quest.title}")
                    elif len(willLevelUp) == 2:
                        await message.channel.send(f"{willLevelUp[0].nick} and {willLevelUp[1].nick} will level up after {quest.title}")
                    else:
                        commaStr = ", ".join([x.nick for x in willLevelUp[:-2]])
                        await message.channel.send(f"{commaStr}, {willLevelUp[-2].nick} and {willLevelUp[-1].nick} will level up after {quest.title}")
                        
                else:
                    await channel.send("There are no upcoming quests.")
            if command[0] == "roll" or command[0] == "r":
                try:
                    elements = []
                    current = "+"
                    for char in command[1]:
                        if char == "+":
                            elements.append(current)
                            current = "+"
                        elif char == "-":
                            elements.append(current)
                            current = "-"
                        else:
                            current += char
                    elements.append(current)
                    rolls = []
                    total = 0
                    for element in elements:
                        sign, roll = element[0], element[1:]
                        if roll == "": continue
                        if sign == "+": sign = 1
                        elif sign == "-": sign = -1
                        else: raise ValueError("Sign invalid")
                        roll = roll.lower()
                        if "d" in roll:
                            number, sides = roll.split("d")
                            if number == "": number = 1
                            if sides == "": sides = 20
                            number, sides = int(number), int(sides)
                            results = []
                            for i in range(number):
                                result = random.randint(1, sides)
                                if self.rig == "min":
                                    result = 1
                                elif self.rig == "max":
                                    result = sides
                                results.append(result)
                                total += result * sign
                            rolls.append((f"{number}d{sides}", results, sign))
                        else:
                            number = int(roll)
                            total += number * sign
                    self.rig = None
                    rollstr = ""
                    for roll in rolls:
                        if roll[2] == 1:
                            rollstr += " "
                        elif roll[2] == -1:
                            rollstr += "-"
                        rollstr += f"{roll[0]}: "
                        t = 0
                        for x in roll[1]:
                            rollstr += f"[{x}] "
                            t += x
                        rollstr += f"-> Total {t}\n"
                    if len(rollstr) > 0:
                        await message.channel.send(f"***{total}***\n```{rollstr}```")
                    else:
                        await message.channel.send(f"***{total}***")
                except Exception as e:
                    print("Caught exception " + str(e))
                    await message.channel.send("I have no idea what the hell you are trying to do")
                

    async def on_member_join(self, member):
        player = db.getPlayer(member.id)
        if not player:
            player = Player(member.id, member.nick)
        db.setPlayer(player)
    async def on_member_remove(self, member):
        # db.delPlayer(member.id)
        pass
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            player = db.getPlayer(after.id)
            if player == None: return
            player.nick = after.nick
            db.setPlayer(player)

if __name__ == "__main__":
    client = Client()
    client.run(Config.ApiKeys['discord']['BotToken'])
