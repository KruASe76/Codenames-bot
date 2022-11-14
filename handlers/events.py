from discord import Message, Activity, ActivityType
from discord.ext.commands import (
    Bot, Context, Command, Cog, CommandNotFound, BadArgument, MemberNotFound, MissingPermissions, NoPrivateMessage
)

from misc.database import Database
from misc.util import send_error


class EventCog(Cog, name="events"):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.change_presence(activity=Activity(type=ActivityType.watching, name="codenames.me"))

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.content.strip() == self.bot.user.mention:
            help_comm: Command = self.bot.get_command("help")
            await help_comm.__call__(await self.bot.get_context(message))
            return

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception) -> None:
        if isinstance(error, (CommandNotFound, BadArgument, MemberNotFound)):
            # MemberNotFound raises in "stats" if invalid member was given
            await ctx.message.add_reaction("❔")
            await ctx.message.delete(delay=3)
            return

        loc = await self.db.localization(ctx)

        if isinstance(error, NoPrivateMessage):
            await send_error(ctx, loc.errors.title, loc.errors.guild_only)
            return

        if isinstance(error, MissingPermissions):
            await send_error(ctx, loc.errors.title, loc.errors.no_permission)  # ЗАМЕНИТЬ ВЕЗДЕ
            return

        raise error


def add_events(bot: Bot, db: Database) -> None:
    bot.add_cog(EventCog(bot, db))
