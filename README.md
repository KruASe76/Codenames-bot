# Codenames-bot

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
- Playing field image generation
- Per-player statistics collection
  - Best players list (global, within a server, within a role)
- Custom bot prefixes for servers and DMs
- Bot messages localization for servers and DMs
  - 🇬🇧 English
  - 🇷🇺 Russian


## Used libraries

- [discord.py (v2)](https://pypi.org/project/discord.py/) as Discord API wrapper
- [Pillow (PIL)](https://pypi.org/project/Pillow/) for image generation
- [aiosqlite](https://pypi.org/project/aiosqlite/) for asynchronous database handling


## Original game (reference)

[![Codenames logo](https://cdn.discordapp.com/attachments/797224818763104317/1026149729194754068/codenames-gradient.png)](https://en.codenames.me/)

> Created by [deNULL](https://github.com/deNULL)
