from discord import Intents, Message
from discord.ext.commands import Bot, when_mentioned_or
import asyncio
from dotenv import find_dotenv, get_key
from typing import Iterable

from misc.database import Database
from handlers.events import add_events
from handlers.help import add_help
from handlers.commands import add_commands
from misc.constants import ADMINS


def main() -> None:
    loop = asyncio.get_event_loop()
    db = loop.run_until_complete(Database.create())

    async def get_prefix(bot: Bot, message: Message) -> Iterable[str]:
        if message.guild:
            prefix = (await db.fetch("SELECT prefix FROM guilds WHERE id=?", (message.guild.id,)))[0]
        else:
            request = (await db.fetch("SELECT prefix FROM players WHERE id=?", (message.author.id,)))
            
            if not request:
                await db.exec_and_commit(
                    "INSERT INTO players VALUES (?,strftime('%d/%m/%Y','now'),?,?,?,?,?,?)",
                    (message.author.id, "", "en", 0, 0, 0, 0)
                )
            
            prefix = request[0] if request else ""
        
        res = (prefix, "cdn") if prefix else ("cdn",)
        
        return when_mentioned_or(*res)(bot, message)
    
    intents: Intents = Intents.default()
    # intents.message_content = True
    bot = Bot(
        command_prefix=get_prefix,
        help_command=None,
        strip_after_prefix=True,
        intents=intents,
        owner_ids=ADMINS
    )

    add_events(bot, db)
    add_commands(bot, db)
    add_help(bot, db)


    TOKEN = get_key(find_dotenv(), "TOKEN")
    bot.run(TOKEN)
