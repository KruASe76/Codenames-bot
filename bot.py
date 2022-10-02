from discord import Intents, Message
from discord.ext.commands import Bot, when_mentioned_or
import asyncio
import dotenv, os
from typing import Iterable

from misc.database import Database
from handlers.help import add_help
from handlers.cogs import add_cogs
from misc.constants import ADMINS


def main() -> None:
    loop = asyncio.get_event_loop()
    db = loop.run_until_complete(Database.create())

    async def get_prefix(bot: Bot, message: Message) -> Iterable[str]:
        if message.guild:
            prefix = (await db.fetch("SELECT prefix FROM guilds WHERE id=?", (message.guild.id,)))[0]
        else:
            prefix = (await db.fetch("SELECT prefix FROM players WHERE id=?", (message.author.id,)))[0]
        
        res = (prefix, "cdn") if prefix else ("cdn",)
        
        return when_mentioned_or(*res)(bot, message)
    
    intents = Intents.default()
    intents.members = True
    bot = Bot(
        command_prefix=get_prefix,
        help_command=None,
        strip_after_prefix=True,
        intents=intents,
        owner_ids=ADMINS
    )

    add_cogs(bot, db)
    add_help(bot)


    dotenv.load_dotenv()
    TOKEN = os.getenv("TOKEN")
    bot.run(TOKEN)
