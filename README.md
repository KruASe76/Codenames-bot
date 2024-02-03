# Codenames-bot

### Bot is down. More info: [#1][issue-1]
[![Invite to server](https://img.shields.io/badge/INVITE%20TO%20SERVER-555555?style=for-the-badge&logo=discord&logoWidth=32&logoColor=ffffff&labelColor=5865f2)](https://discord.com/api/oauth2/authorize?client_id=841776986246348851&permissions=274878015552&scope=bot%20applications.commands)


## Features

- Complete **Codenames** gameplay adaptation to _Discord_ text channels (in the server and in DMs)
  - Move processing according to game rules
    - Captain (DMs)
      1. bot sends captain playing field (a new field after each opened word)
      2. captain responds with their move
      3. opened words notifications
    - Team (server text channel or thread)
      1. bot sends common playing field (a new field after each opened word)
      2. any team member responds with their move (a word to open)
      3. end or continuation of the move (according to its colour)
  - Ability to finish the move (if the team is unsure which word to open next)
  - Ability to finish the game (with a voting)
- _Multiple games on the same server_
- Playing field image generation
- Per-player statistics collection
  - Player top (global, within a server, within a role) - **WIP**
- Custom bot prefixes for servers and DMs
- Bot messages localization for servers and DMs
  - 🇬🇧 English
  - 🇷🇺 Russian


## Running yourself
...if somebody even needs that

### Docker

Using bash script:  
```shell
curl -o run_docker.sh https://raw.githubusercontent.com/KruASe76/Codenames-bot/main/run_docker.sh
./run_docker.sh $TOKEN
```

Using docker directly:
```shell
docker pull kruase/codenames_bot
docker run -dti --name codenames_bot -e TOKEN="$TOKEN" -v codenames_bot_state:/bot/state kruase/codenames_bot
```

### Pipenv
```shell
git clone https://github.com/KruASe76/Codenames-bot.git
cd Codenames-bot
pipenv install
pipenv run python main.py
```

### Pure python 3.11
Windows (PowerShell):
```powershell
git clone https://github.com/KruASe76/Codenames-bot.git
cd Codenames-bot
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Linux / MacOS:
```shell
git clone https://github.com/KruASe76/Codenames-bot.git
cd Codenames-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```


## Stack

- [python 3.11](https://www.python.org/) - programming language
- [discord.py (v2)](https://pypi.org/project/discord.py/) as Discord API wrapper
- [Pillow (PIL)](https://pypi.org/project/Pillow/) for image generation
- [aiosqlite](https://pypi.org/project/aiosqlite/) for asynchronous database handling


## Original game (reference)

[![Codenames logo](https://cdn.discordapp.com/attachments/797224818763104317/1026149729194754068/codenames-gradient.png)](https://en.codenames.me/)

> Created by [deNULL](https://github.com/deNULL)


[issue-1]: https://github.com/KruASe76/Codenames-bot/issues/1
