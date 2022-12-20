from discord import Embed
from discord.ext.commands import Bot, Context, Command, Cog, command

from misc.constants import EMPTY, LOGO_LINK, Colors
from misc.database import Database
from misc.util import process_param, is_check_in_command


class HelpCog(Cog, name="help"):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.db = Database()

    @command()
    async def help(self, ctx: Context, command: str = None) -> None:
        loc = await self.db.localization(ctx)

        prefix = ctx.message.content.split("help")[0]  # Getting a prefix used when calling
        prefix = "cdn " if prefix.strip() == self.bot.user.mention else prefix

        if command:
            comm: Command | None = self.bot.get_command(command)

            if not comm:
                await ctx.reply(embed=Embed(
                    title=loc.errors.title,
                    description=loc.errors.invalid_command,
                    color=Colors.red
                ))
                return

            names = '{' + '|'.join((comm.name,) + comm.aliases) + '}'

            params = " ".join(filter(
                lambda p: p,
                map(process_param, *([*zip(*comm.clean_params.items())] if comm.clean_params else (tuple(), tuple())))
            ))

            guild = f"**[{loc.commands.help.guild}]**\n" if is_check_in_command(comm, "guild_only") else ""
            mod, note = (
                f"**[{loc.commands.help.moderator}]**\n",
                f"\n\n_**{loc.commands.help.note}:**\n{loc.commands.help.about_moderator}_"
            ) if is_check_in_command(comm, "is_moderator") and ctx.guild else ("", "")

            embed = Embed(
                title=loc.cogs[comm.cog_name].singular,
                description=f"**`{prefix}{names}{' ' if params else ''}{params}`**\n\n"
                            f"{guild}{mod}{loc.help[comm.name].help}{note}",
                color=Colors.purple
            )

        else:
            embed = Embed(
                title=loc.commands.help.command_list,
                color=Colors.purple
            )

            for cog_name, cog in self.bot.cogs.items():
                if cog_name in ("events", "help"):
                    continue

                def guild(command: Command) -> str:
                    return f"**[{loc.commands.help.guild}]** " if is_check_in_command(command, "guild_only") else ""

                def mod(command: Command) -> str:
                    return f"**[{loc.commands.help.moderator_shortened}]** " \
                        if is_check_in_command(command, "is_moderator") and ctx.guild else ""

                cog_comms = map(
                    lambda comm: f"**`{prefix}{comm.name}`** - {guild(comm)}{mod(comm)}{loc.help[comm.name].brief}",
                    cog.get_commands()
                )

                embed.add_field(name=loc.cogs[cog_name].plural, value="\n".join(cog_comms), inline=False)

            embed.add_field(
                name=EMPTY,
                value=f"**{loc.commands.help.hint}**\n**`{prefix}help <{loc.commands.help.command}>`**",
                inline=False
            )

        embed.set_thumbnail(url=LOGO_LINK)
        await ctx.reply(embed=embed)


async def add_help(bot: Bot) -> None:
    await bot.add_cog(HelpCog(bot))
