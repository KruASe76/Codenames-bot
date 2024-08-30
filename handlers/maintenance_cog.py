import os

from discord import File
from discord.ext.commands import Context, Cog, command, is_owner

from bot import CodenamesBot
from misc.database import Database
from misc.constants import Paths


class MaintenanceCog(Cog, name="maintenance"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

    @command()
    @is_owner()
    async def sync(self, ctx: Context) -> None:
        synced = await self.bot.tree.sync()

        await ctx.reply(f"Synced {len(synced)} commands globally")

    @command()
    @is_owner()
    async def reload(self, ctx: Context) -> None:
        for filename in filter(lambda fn: "cog" in fn, os.listdir("handlers")):
            await self.bot.reload_extension(f"handlers.{filename[:-3]}")

        await ctx.message.add_reaction("✅")

    @command()
    @is_owner()
    async def save(self, ctx: Context) -> None:
        await ctx.reply(file=File(Paths.db, filename=Paths.db.name))

    @command()
    @is_owner()
    async def load(self, ctx: Context) -> None:
        if len(ctx.message.attachments) != 1 or not ctx.message.attachments[
            0
        ].filename.endswith(".db"):
            await ctx.message.add_reaction("❔")
            await ctx.message.delete(delay=3)
            return

        await Database.close()
        await ctx.message.attachments[0].save(Paths.db)
        await Database.create()

        await ctx.message.add_reaction("✅")


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(MaintenanceCog(bot))
