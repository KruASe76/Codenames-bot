import os

from discord.ext.commands import Context, Cog, command, is_owner

from bot import CodenamesBot


class MaintenanceCog(Cog, name="maintenance"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

    @command()
    @is_owner()
    async def sync(self, ctx: Context) -> None:
        synced = await self.bot.tree.sync()

        await ctx.send(f"Synced {len(synced)} commands globally")

    @command()
    @is_owner()
    async def reload(self, ctx: Context) -> None:
        for filename in filter(lambda fn: "cog" in fn, os.listdir("handlers")):
            await self.bot.reload_extension(f"handlers.{filename[:-3]}")

        await ctx.message.add_reaction("✅")


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(MaintenanceCog(bot))
