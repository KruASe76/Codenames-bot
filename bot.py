import os
from typing import Iterable

from discord import Intents, Message
from discord.ext.commands import Bot, when_mentioned_or

from handlers.commands import add_commands
from handlers.events import add_events
from handlers.help import add_help
from misc.constants import ADMINS
from misc.database import Database


class CodenamesBot(Bot):
    db: Database = None

    @classmethod
    def custom_intents(cls) -> Intents:
        intents = Intents.default()
        intents.message_content = True
        return intents

    async def setup_hook(self) -> None:
        await Database.create()
        self.db = Database()

        await add_events(self)
        await add_commands(self)
        await add_help(self)


async def get_prefix(bot: CodenamesBot, message: Message) -> Iterable[str]:
    if message.guild:
        prefix = (await bot.db.fetch("SELECT prefix FROM guilds WHERE id=?", (message.guild.id,)))[0]
    else:
        request = (await bot.db.fetch("SELECT prefix FROM players WHERE id=?", (message.author.id,)))

        if not request:
            await bot.db.exec_and_commit(
                "INSERT INTO players VALUES (?,strftime('%d/%m/%Y','now'),?,?,?,?,?,?)",
                (message.author.id, "", "en", 0, 0, 0, 0)
            )

        prefix = request[0] if request else ""

    res = (prefix, "cdn") if prefix else ("cdn",)

    return when_mentioned_or(*res)(bot, message)


async def main() -> None:
    bot = CodenamesBot(
        command_prefix=get_prefix,
        help_command=None,
        strip_after_prefix=True,
        intents=CodenamesBot.custom_intents(),
        owner_ids=ADMINS
    )

    token = os.environ.get("TOKEN")
    await bot.start(token)
