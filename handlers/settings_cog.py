from discord import Embed
from discord.ext.commands import Context, Cog, hybrid_command
from discord.app_commands import describe, locale_str

from bot import CodenamesBot
from handlers.checks import is_moderator
from handlers.ui import LocalizationView
from misc.constants import flags, Colors


class SettingsCog(Cog, name="settings"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

    @hybrid_command(aliases=("pre",), description=locale_str("prefix"))
    @describe(new_prefix=locale_str("prefix_new_prefix_param"))
    @is_moderator()
    async def prefix(self, ctx: Context, new_prefix: str = "cdn") -> None:
        new_prefix = "" if new_prefix == "cdn" else new_prefix

        loc = await self.bot.db.localization(ctx)

        if ctx.guild:
            await self.bot.db.exec_and_commit("UPDATE guilds SET prefix=? WHERE id=?", (new_prefix, ctx.guild.id))
        else:
            await self.bot.db.exec_and_commit("UPDATE players SET prefix=? WHERE id=?", (new_prefix, ctx.author.id))

        await ctx.send(embed=Embed(
            title=loc.commands.prefix.prefix_changed_title,
            description=loc.commands.prefix.prefix_changed_desc.format(
                loc.commands.prefix.new_prefix.format(new_prefix) if new_prefix else loc.commands.prefix.prefix_deleted
            ),
            color=Colors.purple
        ))

    @hybrid_command(aliases=("lang",), description=locale_str("language"))
    @is_moderator()
    async def language(self, ctx: Context) -> None:
        loc = await self.bot.db.localization(ctx)

        if ctx.guild:
            current_loc = (await self.bot.db.fetch("SELECT localization FROM guilds WHERE id=?", (ctx.guild.id,)))[0]
        else:
            current_loc = (await self.bot.db.fetch("SELECT localization FROM players WHERE id=?", (ctx.author.id,)))[0]

        language_embed = Embed(
            title=loc.commands.language.title,
            description=loc.commands.language.desc_current.format(current_loc.upper(), flags[current_loc]),
            color=Colors.purple
        )

        await ctx.send(embed=language_embed, view=LocalizationView())


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(SettingsCog(bot))
