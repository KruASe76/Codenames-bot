# Codenames-bot

[![Invite to server](https://img.shields.io/badge/-INVITE%20TO%20SERVER-555555?style=for-the-badge&logo=discord&logoWidth=32&logoColor=ffffff&labelColor=5865f2)](https://discord.com/api/oauth2/authorize?client_id=841776986246348851&permissions=108608&scope=bot)


## Features

- Complete **Codenames** gameplay adaptation to _Discord_ text channels (in the server and in DMs)
  - Move processing according to game rules
    - Captain (DMs)
      1. bot sends captain playing field (a new field after each opened word)
      2. captain responds with their move
      3. opened words notifications
    - Team (server text channel)
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

- [discord.py (v1.7.3)](https://pypi.org/project/discord.py/1.7.3/) as Discord API
- [Pillow (PIL)](https://pypi.org/project/Pillow/) for image generation
- [aiosqlite](https://pypi.org/project/aiosqlite/) for asynchronous database handling
- [python-dotenv](https://pypi.org/project/python-dotenv/) for loading environment variables


## Original game (reference)

[![Codenames logo](https://cdn.discordapp.com/attachments/797224818763104317/1026149729194754068/codenames-gradient.png)](https://en.codenames.me/)
