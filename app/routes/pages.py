from flask import render_template, redirect, send_file
import subprocess, requests

from app.routes.util import *
from app import app, config, db
from database import Quest, Roles

@app.route("/")
@needPlayerAuth
def index():
    player = db.getPlayer(session.get("discordId"))
    playerDict = {player.discordId:player for player in db.getAllPlayers()}
    quests = db.getAllQuests()
    quests = sorted(quests, key=lambda x: x.date if x.date else float('inf'))
    return render_template(
        "questboard.html",
        player=player,
        quests=quests,
        playerDict=playerDict,
        roles=Roles
    )

@app.route("/thechronicle")
def chronicle():
    player = db.getPlayer(session.get("discordId"))
    playerDict = {player.discordId:player for player in db.getAllPlayers()}
    pastQuests = db.getPastQuests()
    return render_template(
        "thechronicle.html",
        player=player,
        playerDict=playerDict,
        pastQuests=pastQuests,
        roles=Roles
    )

@app.route("/roles.json")
def rolesJson():
    return send_file("../roles.json")

@app.route("/actionlogs")
@needPlayerAuth
@needAdmin
def actionLogs():
    logs = subprocess.check_output(['/usr/bin/tail', '-20', './logs/questactions.log'])
    logs = logs.decode("utf-8").splitlines()[::-1]
    players = db.getAllPlayers()
    quests = db.getAllQuests()
    for i, log in enumerate(logs):
        for player in players:
            logs[i] = logs[i].replace(str(player.discordId),
            f"""
            <div class="inlinediv discord-{player.discordId}">
                <div class="innerdiv nick">{player.nick}</div>
                <div class="innerdiv discordId">{player.discordId}</div>
            </div>
            """
            )
    player = db.getPlayer(session.get("discordId"))
    return render_template("serverlogs.html",
        player=player,
        players=players,
        quests=quests,
        logs=logs
    )

@app.route("/controlcenter")
@needPlayerAuth
def questControlMenu():
    player = db.getPlayer(session.get("discordId"))
    quests = [quest for quest in db.getAllQuests() if quest.dm and (quest.commander == player.discordId or player.discordId in quest.players.keys())]
    # Sort by date (no date after everything else)
    quests = sorted(quests, key=lambda x: x.date if x.date else float('inf'))
    currentQuestId = request.args.get("questId")
    currentQuest = None
    if currentQuestId == None:
        if len(quests) > 0: # If the quest id wasn't specified, default the first on the list
            currentQuest = quests[0]
    else:
        for quest in quests: # Find the quest with the right id
            if quest.questId == currentQuestId:
                currentQuest = quest
    playerDict = {player.discordId:player for player in db.getAllPlayers()}
    return render_template("controlcenter.html",
        player=player,
        quests=quests,
        currentQuest=currentQuest,
        roles=Roles,
        playerDict=playerDict
    )


@app.route("/dmcorner")
@needPlayerAuth
@needDM
def dmCorner():
    player = db.getPlayer(session.get("discordId"))
    quests = db.getAllQuests()
    playerDict = {player.discordId:player for player in db.getAllPlayers()}
    return render_template("dmcorner.html",
        player=player,
        quests=quests,
        playerDict=playerDict
    )

@app.route("/playeradmin")
@needPlayerAuth
@needAdmin
def playeradmin():
    player = db.getPlayer(session.get("discordId"))
    return render_template(
        "playeradmin.html",
        player=player,
        players=db.getAllPlayers(),
        quests=db.getAllQuests()
    )

@app.route("/stampReference")
@needPlayerAuth
def stampReference():
    player = db.getPlayer(session.get("discordId"))
    stampData = []
    currentTotal = 0
    for level, stampsToNext in config.StampLevelToNext.items():
        stampData.append((level, currentTotal))
        currentTotal += stampsToNext
    return render_template(
        "stampReference.html",
        player=player,
        stampData=stampData
    )

@app.route("/questadmin")
@needPlayerAuth
@needAdmin
def questadmin():
    playerDict = {int(player.discordId):player for player in db.getAllPlayers()}
    quests = db.getAllQuests()
    player = db.getPlayer(session.get("discordId"))
    return render_template(
        "questadmin.html",
        player=player,
        quests=quests,
        playerDict=playerDict,
        roles=Roles
    )

@app.route("/addquest")
@needPlayerAuth
@needAdmin
def addQuestPagePrefilled():
    if request.args.get("questId"):
        questId = request.args.get('questId')
        quest = db.getQuest(questId)
        if quest == None: return (f"Quest id {questId} not found", 404)
    else:
        quest = Quest()
    player = db.getPlayer(session.get("discordId"))
    playerDict = {player.discordId:player for player in db.getAllPlayers()}
    return render_template("addquest.html", player=player, prefill=quest, DM=False, playerDict=playerDict)    

@app.route("/addquestDM")
@needPlayerAuth
@needDM
def addQuestPageDM():
    player = db.getPlayer(session.get("discordId"))
    playerDict = {player.discordId:player for player in db.getAllPlayers()}
    if request.args.get("questId"):
        questId = request.args.get('questId')
        quest = db.getQuest(questId)
        if quest == None: return (f"Quest id {questId} not found", 404)
    else:
        quest = Quest()
    return render_template("addquest.html", player=player, prefill=quest, DM=True, playerDict=playerDict)

@app.route("/setdate")
@needPlayerAuth
@needCommanderToQuest
@needDM
def setDatePage():
    player = db.getPlayer(session.get("discordId"))
    questId = request.args['questId']
    quest = db.getQuest(questId)
    if quest == None: return (f"Quest id {questId} not found", 404)
    return render_template(
        "setDate.html",
        player=player,
        quest=quest
    )

@app.route("/logincallback")
def discordlogin():
    error = request.args.get("error")
    if error:
        return ("", 403)
    code = request.args.get("code")
    data = {
        'client_id': config.ApiKeys['discord']['ClientId'],
        'client_secret': config.ApiKeys['discord']['ClientSecret'],
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.RedirectURI,
        'scope': 'identify'
    }
    r = requests.post("https://discordapp.com/api/oauth2/token", data=data)
    r.raise_for_status()
    access_token = r.json()['access_token']

    r = requests.get("https://discordapp.com/api/users/@me", headers={"Authorization":"Bearer "+access_token})
    r.raise_for_status()
    user_id = r.json()['id']

    session['discordId'] = user_id
    session.permanent = True
    logAction()
    return redirect("/", code=302)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(request.referrer or "/", code=302)
