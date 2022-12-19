import inspect

from discord import Embed
from discord.ext.commands import Bot, Context, Command, Cog, command

from misc.constants import EMPTY, LOGO_LINK, Colors
from misc.database import Database
from misc.util import is_check_in_command


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

            else:
                title = loc.cogs[comm.cog_name].singular
                color = Colors.purple

                comm_info = inspect.getfullargspec(comm.callback)
                all_args = comm_info.args[2:]  # Removing "self" and "ctx"
                default_args = comm_info.defaults or tuple()

                names = (comm.name,) + comm.aliases
                display_name = "{" + '|'.join(names) + "}"
                display_args = []
                while len(all_args) > len(default_args):
                    display_args.append(f"<{all_args[0]}>")
                    all_args.pop(0)
                for arg, default_arg in zip(all_args, default_args):
                    if arg == "final":  # This argument is not for users
                        continue
                    def_arg = default_arg
                    if def_arg:
                        if not def_arg.isdigit():
                            def_arg = f'"{def_arg}"'  # String type defaults stylization
                    else:
                        def_arg = None
                    display_args.append(f"[{arg}={def_arg}]")

                guild = f"**[{loc.commands.help.guild}]**\n" if is_check_in_command(comm, "guild_only") else ""

                if is_check_in_command(comm, "is_moderator") and ctx.guild:
                    mod = f"**[{loc.commands.help.moderator}]**\n"
                    note = f"\n\n_**{loc.commands.help.note}:**\n{loc.commands.help.about_moderator}_"
                else:
                    mod = ""
                    note = ""

                desc = (f"**`{prefix}{display_name}{' ' if display_args else ''}{' '.join(display_args)}`**\n\n"
                        f"{guild}{mod}{loc.help[comm.name].help}{note}")

            embed = Embed(
                title=title,
                description=desc,
                color=color
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

        await ctx.reply(embed=embed)


async def add_help(bot: Bot) -> None:
    await bot.add_cog(HelpCog(bot))
