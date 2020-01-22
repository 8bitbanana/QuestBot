from flask import request, session, redirect, abort
from datetime import datetime
import pytz, json

from app.routes.util import *
from app import app, config, db
from database import Quest, Roles

@app.route("/questBoardAction/<action>", methods=['POST'])
@needPlayerAuth
def questPlayerAction(action):
    logAction()
    questId = request.args['questId']
    discordId = session.get("discordId")
    quest = db.getQuest(questId)
    player = db.getPlayer(discordId)
    if action == "claimCommander":
        result, message = quest.setCommander(player)
        if result:
            player.leadership -= quest.leadershipReq
    elif action == "releaveCommander":
        result, message = quest.setCommander(None)
        if result:
            player.leadership += quest.leadershipReq
    elif action == "joinQuest":
        # Recredit the leadership if they are currently a commander
        if player.discordId == quest.commander:
            player.leadership += quest.leadershipReq
        result, message = quest.addPlayer(player)
    elif action == "leaveQuest":
        result, message = quest.removePlayer(player)
    else:
        return "Unknown action", 400
    if result:
        db.setQuest(quest)
        db.setPlayer(player)
        return message, 200
    else:
        return message, 400

@app.route("/controlCenterAction/<action>", methods=['POST'])
@needPlayerAuth
def controlCenterAction(action):
    logAction()
    questId = request.args['questId']
    discordId = session.get("discordId")
    quest = db.getQuest(questId)
    player = db.getPlayer(discordId)
    if action == "claimRole":
        roleId = request.args['roleId']
        result, message = quest.setRole(player, roleId)
        if result:
            role = Roles[roleId]
            player.leadership -= role['cost']
    elif action == "releaveRole":
        roleId = quest.players.get(int(discordId))
        result, message = quest.setRole(player, None)
        if result:
            role = Roles[roleId]
            player.leadership += role['cost']
    elif action == "useActive":
        activeId = request.args['activeId']
        result, message = quest.activateRolePower(player, activeId)
        if result:
            active = Roles[quest.players[int(discordId)]]['actives'][activeId]
            player.leadership -= active['cost']
    else:
        return "Unknown action", 400
    if result:
        db.setQuest(quest)
        db.setPlayer(player)
        return message, 200
    else:
        return message, 400
    
    

@app.route("/questAdminAction/<action>", methods=['POST'])
@needPlayerAuth
@needAdmin
def questAdminAction(action):
    logAction()
    questId = request.args['questId']
    discordId = request.args.get("discordId")
    quest = db.getQuest(questId)
    if discordId == None:
        player = None
    else:
        player = db.getPlayer(discordId)
    if action == "changeCommander":
        result, message = quest.setCommander(player, forceAdd=True)
    elif action == "changeDM":
        result, message = quest.setDm(player, forceAdd=True)
    elif action == "addPlayer":
        result, message = quest.addPlayer(player, removeCommander=False, forceAdd=True)
    elif action == "removePlayer":
        result, message = quest.removePlayer(player)
    elif action == "changeRole":
        roleId = request.args['roleId']
        if roleId == "unselected":
            roleId = None
        result, message = quest.setRole(player, roleId, forceAdd=True)
    elif action == "refreshPlayerRole":
        result, message = quest.refreshPlayerRole(player)
    else:
        return "Unknown action", 400
    if result:
        db.setQuest(quest)
        return message, 200
    else:
        return message, 400

@app.route("/dmClaimQuest", methods=['POST'])
@needPlayerAuth
@needDM
def dmClaimQuest():
    logAction()
    questId = request.args['questId']
    discordId = session.get("discordId")
    quest = db.getQuest(questId)
    player = db.getPlayer(discordId)
    if quest.dm != None:
        return "This quest already has a DM", 403
    quest.setDm(player)
    db.setQuest(quest)
    if quest.dm != None:
        db.pushTask("NEWQUEST " + quest.questId)
    return redirect("/dmcorner", code=302)

@app.route("/dmCornerAction/<action>/", methods=["POST"])
@needPlayerAuth
@needAccessToQuest
def dmCornerAction(action):
    logAction()
    questId = request.args['questId']
    discordId = request.args.get('discordId')
    quest = db.getQuest(questId)
    if discordId == None:
        player = None
    else:
        player = db.getPlayer(discordId)
    result, message = None, None
    # if action == "setDate":
    #     result, message = quest.setDate(request.args.get("date"))
    if action == "kickPlayer":
        result, message = quest.removePlayer(player)
    elif action == "releaveDM":
        result, message = quest.setDm(None)
    else:
        return "Unknown action", 400
    if result:
        db.setQuest(quest)
        return message, 200
    else:
        return message, 400

@app.route("/delquest", methods=["POST"])
@needPlayerAuth
@needAccessToQuest
def delQuest():
    logAction()
    questId = request.args['questId']
    quest = db.getQuest(questId)
    if quest == None: abort(404)
    creditStamps = request.args.get('credit') == "1"
    db.delQuest(request.args['questId'], creditStamps=creditStamps)
    if creditStamps:
        return "Success", 200
    else:
        return "Success, credited stamps", 200

@app.route("/setDateSubmit", methods=['POST'])
@needPlayerAuth
@needCommanderToQuest
def setDateSubmit():
    logAction()
    quest = db.getQuest(request.form.to_dict().get("questId"))
    if quest == None:
        return "Unknown Quest", 404
    if request.form.to_dict().get("date") == None:
        utc_date = None
    else:
        date = request.form['date']
        try:
            date = int(date)
        except ValueError:
            return "Invalid timestamp", 400
        tz = pytz.timezone(config.TimeZone)
        date = datetime.fromtimestamp(date)
        local_date = tz.localize(date, is_dst=None)
        utc_date = local_date.astimezone(pytz.utc).timestamp()
    quest.setDate(utc_date)
    db.setQuest(quest)
    return redirect("/dmcorner", code=302)

@app.route("/unsetdate", methods=['POST'])
@needPlayerAuth
@needCommanderToQuest
def unsetDate():
    logAction()
    quest = db.getQuest(request.args['questId'])
    if quest == None:
        return "Unknown Quest", 404
    result, message = quest.setDate(None)
    if result:
        db.setQuest(quest)
        return message, 200
    else:
        return message, 400

@app.route("/setquestsubmit", methods=['POST'])
@needPlayerAuth
@needAdmin
def addQuest():
    logAction()
    formData = request.form.to_dict()
    questId = formData.get("questId")
    quest = None
    if questId == "" or questId == None:
        formData.pop("questId")
        newquest = True
    else:
        quest = db.getQuest(questId)
    if quest:
        quest.deserialise(json.dumps(formData))
        newquest = False
    else:
        quest = Quest(jsonData=json.dumps(formData))
        newquest = True
    db.setQuest(quest)
    if newquest and quest.dm != None:
        db.pushTask("NEWQUEST " + quest.questId)
    return redirect("/questadmin", code=302)

@app.route("/setquestDMsubmit", methods=['POST'])
@needPlayerAuth
@needAccessToQuest
@needDM
def addQuestDM():
    logAction()
    formData = request.form.to_dict()
    questId = formData.get("questId")
    quest = None
    if questId == "" or questId == None:
        formData.pop("questId")
    else:
        quest = db.getQuest(questId)
    if quest:
        quest.deserialise(json.dumps(formData))
        newquest = False
    else:
        quest = Quest(jsonData=json.dumps(formData))
        newquest = True
    if quest.dm and quest.dm != int(session.get("discordId")):
        return "You cannot set other people to be the DM of your quest", 403
    else:
        db.setQuest(quest)
        if newquest and quest.dm != None:
            db.pushTask("NEWQUEST " + quest.questId)
        return redirect("/dmcorner", code=302)

@app.route("/updatePlayerStats", methods=['POST'])
@needPlayerAuth
@needAdmin
def updatePlayerStats():
    logAction()
    formData = request.form.to_dict()
    discordId = formData.pop("discordId")
    player = db.getPlayer(discordId)
    if player == None:
        return "Player not found", 404
    player.deserialise(formData)
    db.setPlayer(player)
    return redirect("/playeradmin", code=302)

@app.route("/updateSelfStats", methods=['POST'])
@needPlayerAuth
def updateSelfStats():
    logAction()
    formData = request.form.to_dict()
    discordId = session.get("discordId")
    player = db.getPlayer(discordId)
    if "influence" in formData:
        assert int(formData['influence']) >= 0
        player.influence = formData['influence']
    if "leadership" in formData:
        assert int(formData['leadership']) >= 0
        player.leadership = formData['leadership']
    db.setPlayer(player)
    return redirect(request.referrer or "/")

@app.route("/spendPoints", methods=['POST'])
@needPlayerAuth
def spendCompanyPoints():
    logAction()
    influence = int(request.form['influence'])
    leadership = int(request.form['leadership'])
    discordId = session.get("discordId")
    player = db.getPlayer(discordId)
    result, message = player.spendPoints(influence, leadership)
    db.setPlayer(player)
    if result:
        return redirect(request.referrer or "/")
    else:
        return message, 400