from flask import Flask
from database import Database
from configuration import Config

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

from app.routes import util, api, pages
