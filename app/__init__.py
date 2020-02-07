from flask import Flask
from database import Database
from configuration import Config

import subprocess

db = Database()
db.regeneratePlayers()
db.regenerateQuests()

config = Config()

app = Flask(__name__)
app.template_folder = "../templates"
app.static_folder = "../static"
app.secret_key = Config.ApiKeys['flask']['SecretKey']

@app.template_filter()
def jsescape(s):
    if type(s) == str:
        s = s.replace("\'", "\\\'")
        s = s.replace("\"", "\\\"")
    return s

@app.template_global()
def vscodedetect():
    ps = subprocess.Popen(["/bin/ps", "aux"], stdout=subprocess.PIPE)
    try:
        grep = subprocess.check_output(["/bin/grep", "[n]ode.*vscode-server.*watcherService"], stdin=ps.stdout)
    except subprocess.CalledProcessError:
        return False
    return True

@app.template_global()
def roleUnpicked(discordId):
    for quest in db.getAllQuests():
        if discordId in quest.players.keys() and quest.players[discordId] == None:
            return True
        if discordId == quest.commander and quest.commanderRole == None:
            return True
    return False

from app.routes import util, api, pages
