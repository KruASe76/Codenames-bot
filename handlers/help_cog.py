from itertools import repeat

from discord import Embed, Interaction
from discord.ext.commands import Context, Command, Cog, command as text_command
from discord.app_commands import Choice, choices, command as app_command, describe, locale_str

from bot import CodenamesBot
from misc.util import process_param, if_command_has_check, send_error
from misc.constants import EMPTY, LOGO_LINK, Colors


class HelpCog(Cog, name="help"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

    async def help_embed(self, ctx: Context | Interaction, command: str | None, prefix: str) -> Embed | None:
        sl = isinstance(ctx, Interaction)  # kinda short for "slash"

        loc = await self.bot.db.localization(ctx)

        if command:
            comm: Command | None = self.bot.get_command(command)

            if not comm or comm.cog_name == "maintenance":
                await send_error(ctx, loc.errors.title, loc.errors.invalid_command)
                return

            names = comm.name if sl else '{' + '|'.join((comm.name,) + comm.aliases) + '}'

            params = " ".join(filter(
                lambda p: p,
                map(
                    process_param,
                    *(
                        [*zip(*comm.clean_params.items())] if comm.clean_params else ((), ())
                    ), repeat(sl)
                )
            ))

            guild = f"**[{loc.commands.help.guild}]**\n" if if_command_has_check(comm, "guild_only") else ""
            mod, note = (
                f"**[{loc.commands.help.moderator}]**\n",
                f"\n\n_**{loc.commands.help.note}:**\n{loc.commands.help.about_moderator}_"
            ) if if_command_has_check(comm, "is_moderator") and ctx.guild else ("", "")

            help_embed = Embed(
                title=loc.cogs[comm.cog_name].singular,
                description=f"**`{prefix}{names}{' ' if params else ''}{params}`**\n\n"
                            f"{guild}{mod}{loc.help[comm.name].help}{note}",
                color=Colors.purple
            )

        else:
            help_embed = Embed(
                title=loc.commands.help.command_list,
                color=Colors.purple
            )

            for cog_name, cog in self.bot.cogs.items():
                if cog_name in ("events", "help", "maintenance"):
                    continue

                def guild(command: Command) -> str:
                    return f"**[{loc.commands.help.guild}]** " if if_command_has_check(command, "guild_only") else ""

                def mod(command: Command) -> str:
                    return f"**[{loc.commands.help.moderator_shortened}]** " \
                        if if_command_has_check(command, "is_moderator") and ctx.guild else ""

                cog_comms = map(
                    lambda comm: f"**`{prefix}{comm.name}`** - {guild(comm)}{mod(comm)}{loc.help[comm.name].brief}",
                    cog.get_commands()
                )

                help_embed.add_field(name=loc.cogs[cog_name].plural, value="\n".join(cog_comms), inline=False)

            help_embed.add_field(
                name=EMPTY,
                value=f"**{loc.commands.help.hint}**\n"
                      f"**`{prefix}{'cdn' if sl else ''}help <{loc.commands.help.command}>`**",
                inline=False
            )

        help_embed.set_thumbnail(url=LOGO_LINK)

        return help_embed

    @app_command(name="cdnhelp", description=locale_str("help"))
    @describe(command=locale_str("help_command_param"))
    @choices(
        command=[
            Choice(name="game", value="game"),
            Choice(name="stats", value="stats"),
            # Choice(name="top", value="top"),
            Choice(name="language", value="language"),
            Choice(name="prefix", value="prefix")
        ]
    )
    async def slash_help(self, interaction: Interaction, command: Choice[str] | None = None) -> None:
        help_embed = await self.help_embed(interaction, command.value if command else None, "/")

        if help_embed:
            await interaction.response.send_message(embed=help_embed, ephemeral=True)

    @text_command(name="help")
    async def text_help(self, ctx: Context, command: str | None = None) -> None:
        prefix = ctx.message.content.split("help")[0]  # Getting a prefix used when calling
        prefix = "cdn " if prefix.strip() == self.bot.user.mention else prefix

        help_embed = await self.help_embed(ctx, command, prefix)

        if help_embed:
            await ctx.reply(embed=help_embed)


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(HelpCog(bot))
