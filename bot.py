import discord, asyncio, twitter, subprocess
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

        print('Logged on as {0}!'.format(self.user))
        for x in self.guilds:
            if x.id == guildId:
                self.guild = x
                break
        else:
            raise FileNotFoundError("The bot is not in the correct guild")
        
        self.announceChannel = self.get_channel(announceChannelId)

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
                await self.announceChannel.send(f"@everyone A new Quest is now available!", embed=embed)
                #twitter.PostUpdate(f"A new quest is available!\n{quest.title[:200]}")


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
            

    async def on_member_join(self, member):
        player = db.getPlayer(member.id)
        if not player:
            player = Player(member.id, member.nick)
        db.setPlayer(player)
    async def on_member_remove(self, member):
        db.delPlayer(member.id)
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            player = db.getPlayer(after.id)
            if player == None: return
            player.nick = after.nick
            db.setPlayer(player)

if __name__ == "__main__":
    client = Client()
    client.run(Config.ApiKeys['discord']['BotToken'])
