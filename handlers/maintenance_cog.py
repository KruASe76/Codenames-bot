import os
from typing import Literal

from discord import Object, HTTPException
from discord.ext.commands import Context, Cog, command, is_owner, Greedy

from bot import CodenamesBot


class MaintenanceCog(Cog, name="maintenance"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

    @command()
    @is_owner()
    async def sync(self, ctx: Context, guilds: Greedy[Object], spec: Literal["~", "*", "^"] | None = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await self.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @command()
    @is_owner()
    async def reload(self, ctx: Context) -> None:
        for filename in filter(lambda fn: "cog" in fn, os.listdir("handlers")):
            await self.bot.reload_extension(f"handlers.{filename[:-3]}")

        await ctx.message.add_reaction("✅")


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(MaintenanceCog(bot))
