# QuestBot

| File | Description | 
| --- | --- |
| **app/** | Where everything web based happens |
| app/\_\_init\_\_.py | Base file |
| app/routes/api.py | Places for the webpages to communicate to the server |
| app/routes/pages.py | Places for your browser to get the webpages |
| app/routes/util.py | A few utility functions |
| **static/** | Files that get sent directly to your browser, like images or Javascript |
| static/css/ | All CSS files (page style info) |
| static/img/ | All images (not many)
| static/js/ | All Javascript files (code to run in your browser) |
| static/lib/ | All libraries (jQuery and Bootstrap mainly)
| **templates/** | All HTML template files used to build the pages |
| templates/base.html | The base HTML file that everything inherits from |
| templates/cards.html | Another HTML file to inherit from that already has a card deck |
| templates/{all the others} | Each file is a different webpage |
| **QuestBot.ini** | Config file for uWSGI |
| **bot.py** | The discord bot! |
| **database.py** | Base classes like "Player" and "Quest", and interaction with the Redis database |
| **roles.json** | Where the quest roles, effects and powers are stored |
