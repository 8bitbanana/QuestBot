from flask import session, redirect, request
import functools, logging

from app import config, db

questLog = logging.getLogger("questLog")
f_handler = logging.FileHandler("./logs/questactions.log")
f_handler.setLevel(logging.INFO)
f_format = logging.Formatter("%(asctime)s - %(message)s")
f_handler.setFormatter(f_format)
questLog.addHandler(f_handler)

def logAction():
    questLog.error(f"{request.full_path} - {session.get('discordId')} - {request.form.to_dict()}")

def needPlayerAuth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        discordId = session.get("discordId")
        if discordId == None:
            return redirect(config.ApiKeys['discord']['OAuthUrl'], code=302)
        player = db.getPlayer(session.get("discordId"))
        if player == None:
            session.clear()
            return redirect(config.ApiKeys['discord']['OAuthUrl'], code=302)
        return func(*args, **kwargs)
    return wrapper

def needAdmin(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        player = db.getPlayer(session.get("discordId"))
        if player == None or not player.admin:
            return "You require admin permission to access this resource", 403
        return func(*args, **kwargs)
    return wrapper

def needAccessToQuest(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        player = db.getPlayer(session.get("discordId"))
        questId = request.args.get("questId") or request.form.to_dict().get("questId")
        if questId == None:
            return func(*args,)
        quest = db.getQuest(questId)
        if quest == None:
            return func(*args, **kwargs)
        if player.admin or quest.dm == player.discordId:
            return func(*args, **kwargs)
        return "You do not have write access to this quest", 403
    return wrapper

def needCommanderToQuest(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        player = db.getPlayer(session.get("discordId"))
        questId = request.args.get("questId") or request.form.to_dict().get("questId")
        if questId == None:
            return func(*args,)
        quest = db.getQuest(questId)
        if quest == None:
            return func(*args, **kwargs)
        if player.admin or quest.commander == player.discordId or quest.dm == player.discordId:
            return func(*args, **kwargs)
        return "You do not have write access to this quest", 403
    return wrapper

def needDM(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        player = db.getPlayer(session.get("discordId"))
        if player == None or not (player.canDM or player.admin):
            return "You are not able to DM a quest", 403
        return func(*args, **kwargs)
    return wrapper
