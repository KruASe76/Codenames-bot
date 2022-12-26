from discord import Message, Guild, Activity, ActivityType
from discord.ext.commands import (
    Context, Command, Cog,
    CommandNotFound, BadArgument, MemberNotFound, NoPrivateMessage, MissingPermissions, NotOwner
)

from bot import CodenamesBot
from misc.util import send_error


class EventCog(Cog, name="events"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

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
            # MemberNotFound is raised in "stats" if invalid member was given
            await ctx.message.add_reaction("❔")
            await ctx.message.delete(delay=3)
            return

        loc = await self.bot.db.localization(ctx)

        if isinstance(error, NoPrivateMessage):
            await send_error(ctx, loc.errors.title, loc.errors.guild_only)
            return

        if isinstance(error, (MissingPermissions, NotOwner)):
            await send_error(ctx, loc.errors.title, loc.errors.no_permission)
            return

        raise error

    @Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        await self.bot.db.exec_and_commit("INSERT INTO guilds VALUES (?,?,?,?,?,?)", (guild.id, "", "en", "", "", ""))

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        await self.bot.db.exec_and_commit("DELETE FROM guilds WHERE id=?", (guild.id,))


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(EventCog(bot))
