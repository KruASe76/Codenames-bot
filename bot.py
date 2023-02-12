import os
from typing import Iterable

from discord import Intents, Message
from discord.ext.commands import Bot, when_mentioned_or

from handlers.translator import CodenamesTranslator
from misc.database import Database
from misc.constants import ADMINS, Paths


class CodenamesBot(Bot):
    db: Database = None

    @staticmethod
    def custom_intents() -> Intents:
        intents = Intents.default()
        intents.message_content = True  # to process moves
        intents.members = True  # to be able to wait_for() reactions in DMs
        return intents

    async def setup_hook(self) -> None:
        await Database.create()
        self.db = Database()

        await self.tree.set_translator(CodenamesTranslator())

        for filename in filter(lambda fn: "cog" in fn, os.listdir("handlers")):
            await self.load_extension(f"handlers.{filename[:-3]}")  # removing ".py" at the end of the filename


async def get_prefix(bot: CodenamesBot, message: Message) -> Iterable[str]:
    if message.guild:
        request = await bot.db.fetch("SELECT prefix FROM guilds WHERE id = ?", (message.guild.id,))

        if not request:  # should not normally happen
            await bot.db.exec_and_commit("INSERT INTO guilds VALUES (?, ?, ?)", (message.guild.id, "", "en"))
    else:
        request = await bot.db.fetch("SELECT prefix FROM players WHERE id = ?", (message.author.id,))

        if not request:  # if the user sends a text command to the bot as the first use in DMs
            await bot.db.exec_and_commit(
                "INSERT INTO players VALUES (?, strftime('%d/%m/%Y','now'), ?, ?, ?, ?, ?, ?)",
                (message.author.id, "", "en", 0, 0, 0, 0)
            )

    prefix = request[0] if request else ""
    res = (prefix, "cdn") if prefix else ("cdn",)

    return when_mentioned_or(*res)(bot, message)


def main() -> None:
    os.makedirs(Paths.img_dir, exist_ok=True)

    bot = CodenamesBot(
        command_prefix=get_prefix,
        help_command=None,
        strip_after_prefix=True,
        intents=CodenamesBot.custom_intents(),
        owner_ids=ADMINS
    )

    token = os.environ.get("TOKEN")
    bot.run(token)
