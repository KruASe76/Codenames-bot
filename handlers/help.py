from discord import Embed
from discord.ext.commands import Bot, Context, Command, Cog, command
import inspect
from typing import Optional

from misc.database import Database
from misc.constants import EMPTY, LOGO_LINK, Colors
from misc.util import is_check_in_command


class HelpCog(Cog, name="help"):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @command()
    async def help(self, ctx: Context, command: str = None) -> None:
        loc = await self.db.localization(ctx)

        prefix = ctx.message.content.split("help")[0]  # Getting a prefix used when calling
        prefix = "cdn " if prefix.strip() == self.bot.user.mention else prefix

        if command:
            comm: Optional[Command] = self.bot.get_command(command)

            if not comm:
                await ctx.reply(embed=Embed(
                    title=loc.errors.title,
                    description=loc.errors.invalid_command,
                    color=Colors.red
                ))
                return

            else:
                title = loc.cogs[comm.cog_name].singular
                col = Colors.purple

                comm_info = inspect.getfullargspec(comm.callback)
                arg_list = comm_info.args[2:]  # Removing "self" and "ctx"
                default_args = comm_info.defaults or tuple()

                names = (comm.name,) + comm.aliases
                name = "{" + "|".join(names) + "}"
                args = []
                while len(arg_list) > len(default_args):
                    args.append(f"<{arg_list[0]}>")
                    arg_list.pop(0)
                for ind, arg in enumerate(arg_list):
                    if arg == "final":  # This argument is not for users
                        continue
                    def_arg = default_args[ind]
                    if def_arg:
                        if not def_arg.isdigit():
                            def_arg = f'"{def_arg}"'  # String type defaults stylization
                    else:
                        def_arg = None
                    args.append(f"[{arg}={def_arg}]")

                guild = f"**[{loc.commands.help.guild}]**\n" if is_check_in_command(comm, "guild_only") else ""

                if is_check_in_command(comm, "is_moderator") and ctx.guild:
                    mod = f"**[{loc.commands.help.moderator}]**\n"
                    note = f"\n\n_**{loc.commands.help.note}:**\n{loc.commands.help.about_moderator}_"
                else:
                    mod = ""
                    note = ""

                desc = f"**`{prefix}{name}{' ' if args else ''}{' '.join(args)}`**\n\n{guild}{mod}{loc.help[comm.name].help}{note}"

            embed = Embed(
                title=title,
                description=desc,
                color=col
            )
            embed.set_thumbnail(url=LOGO_LINK)

        else:
            embed = Embed(
                title=loc.commands.help.command_list,
                color=Colors.purple
            )
            embed.set_thumbnail(url=LOGO_LINK)

            for cog_name, cog in self.bot.cogs.items():
                if cog_name in ("events", "help"):
                    continue

                def guild(command: Command):
                    return f"**[{loc.commands.help.guild}]** " if is_check_in_command(command, "guild_only") else ""

                def mod(command: Command):
                    return f"**[{loc.commands.help.moderator_shortened}]** " if is_check_in_command(command, "is_moderator") and ctx.guild else ""

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

        await ctx.reply(embed=embed)


def add_help(bot: Bot, db: Database) -> None:
    bot.add_cog(HelpCog(bot, db))
