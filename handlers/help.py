from discord import Embed
from discord.ext.commands import Bot, Command, Context
import inspect
from typing import Optional

from misc.constants import EMPTY, LOGO_LINK, Colors
from misc.messages import messages
from misc.util import is_check_in_command


async def help(ctx: Context, command: str = None) -> None:
    prefix = ctx.message.content.split("help")[0]  # Getting a prefix used when calling
    prefix = "cdn " if prefix.strip() == ctx.bot.user.mention else prefix

    if command:
        comm: Optional[Command] = ctx.bot.get_command(command)
        
        if not comm:
            title = "Error"
            desc = "Command not found"
            col = Colors.red
        
        else:
            title = comm.cog_name[:-1]  # Removing "..s" to get not plural, but singular
            col = Colors.purple

            comm_info = inspect.getfullargspec(comm.callback)
            arg_list = comm_info.args[2:]  # Removing "self" and "ctx"
            default_args = comm_info.defaults if comm_info.defaults else ()
            
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
            
            guild = "**[Guild]**\n" if is_check_in_command(comm, "guild_only") else ""
            
            if is_check_in_command(comm, "is_moderator") and ctx.guild:
                mod1 = "**[Moderator]**\n"
                mod2 = "\n\n_**Note:**\nModerator is the member who can manage messages in the channel where the command was called_"
            else:
                mod1 = ""
                mod2 = ""
            
            desc = f"**`{prefix}{name}{' ' if args else ''}{' '.join(args)}`**\n\n{guild}{mod1}{comm.help}{mod2}"

        embed = Embed(
            title=title,
            description=desc,
            color=col
        )
    
    else:
        embed = Embed(
            title="Command list",
            color=Colors.purple
        )
        embed.set_thumbnail(url=LOGO_LINK)

        for cog_name, cog in ctx.bot.cogs.items():
            if cog_name == "Listeners":
                continue
            
            guild = lambda comm: "**[Guild]** " if is_check_in_command(comm, "guild_only") else ""
            mod = lambda comm: "**[Mod]** " if is_check_in_command(comm, "is_moderator") and ctx.guild else ""
            
            cog_comms = map(lambda comm: f"**`{prefix}{comm.name}`** - {guild(comm)}{mod(comm)}{comm.brief if comm.brief else comm.help}", cog.get_commands())
            
            embed.add_field(name=cog_name, value="\n".join(cog_comms), inline=False)
        
        embed.add_field(
            name=EMPTY,
            value=f"**To learn a more detailed description of the command, type**\n**`{prefix}help [command]`**",
            inline=False
        )

    await ctx.reply(embed=embed)


def add_help(bot: Bot):
    bot.add_command(Command(help))
