import asyncio
from typing import Iterable, Callable, Any

from discord import File, Embed, PartialMessageable, User, Message, Reaction, Interaction, ButtonStyle
from discord.ext.commands import Parameter, Command, Context
from discord.ui import View, Button, button

from misc.messages import Localization
from misc.constants import Paths, Colors


# noinspection PyUnusedLocal
class AlertView(View):
    # noinspection PyUnresolvedReferences
    def __init__(self, loc: Localization, callback: Callable, *params: Any) -> None:
        super().__init__()
        self.callback = callback
        self.params = params

        self.children[0].label = loc.ui.cancel
        self.children[1].label = loc.ui.confirm

    @button(style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: Button) -> None:
        for button in self.children:
            button.disabled = True

        # noinspection PyUnresolvedReferences
        await interaction.response.edit_message(view=self)

    @button(style=ButtonStyle.green)
    async def confirm_button(self, interaction: Interaction, button: Button) -> None:
        for button in self.children:
            button.disabled = True

        # noinspection PyUnresolvedReferences
        await interaction.response.edit_message(view=self)

        await self.callback(*self.params)


def process_param(name: str, param: Parameter, slash: bool) -> str | None:
    """
    Helper function that converts a :class:`Parameter` object to a string displayed in `help` command embed

    :param name: Parameter name
    :param param: Parameter object
    :param slash: Whether the help command is invoked as a slash command
    :return: The parameter name and default value in a string
    """

    if name == "show" and not slash:
        return

    if param.required:
        return f"<{param.name}>"

    default = None if not param.default and not isinstance(param.default, bool) else param.default
    default = f'"{default}"' if isinstance(default, str) else default
    return f"[{param.name}={f'{default}'}]"


def if_command_has_check(command: Command, check: str) -> bool:
    """
    Determines whether the :class:`Command` has the check

    :param command: Command object
    :param check: Check
    :return: Whether the check is in the command
    """

    return check in map(lambda check: check.__qualname__.split(".")[0], command.checks)


async def send_error(ctx: Context | Interaction | PartialMessageable, title: str, description: str) -> None:
    """
    Sends error message to the given context with given title and description

    :param ctx: Context or Interaction object to send to
    :param title: Error title
    :param description: Error description
    :return: None
    """

    error_embed = Embed(
        title=title,
        description=description,
        color=Colors.red
    )

    if isinstance(ctx, Interaction):  # called from ui
        await ctx.followup.send(embed=error_embed, ephemeral=True)
    elif isinstance(ctx, PartialMessageable):  # called from start()
        await ctx.send(embed=error_embed)
    elif ctx.interaction:  # called from a hybrid command as an app command
        # noinspection PyUnresolvedReferences
        await ctx.interaction.response.send_message(embed=error_embed, ephemeral=True)
    else:  # called from a hybrid command as a text command or from event listener
        await ctx.reply(embed=error_embed, delete_after=7)
        await ctx.message.delete(delay=7)


async def send_alert(
    interaction: Interaction, loc: Localization, action: str, callback: Callable, *params: Any
) -> None:
    """
    Sends an alert to the given :class:`Interaction` with the given action and callback
\
    :param interaction: Interaction object to send to
    :param loc: Localization object to access translations
    :param action: Action for Embed description
    :param callback: Callback to send if confirmed
    :return: None
    """

    # noinspection PyUnresolvedReferences
    await interaction.response.send_message(  # not followup because it is always the first response
        embed=Embed(
            title=loc.ui.alert_title,
            description=loc.ui.alert_desc.format(action),
            color=Colors.purple
        ),
        view=AlertView(loc, callback, *params),
        ephemeral=True
    )


async def count_certain_reacted_users(reaction: Reaction, users: Iterable[User]) -> int:
    """
    Counts reactions from certain users

    :param reaction: Reaction object
    :param users: Users that should be counted
    :return: The number of certain users reacted with that reaction
    """

    return len(set([user async for user in reaction.users()]) & set(users))


# noinspection PyTypeChecker
async def most_count_reaction_emojis(msg: Message, counted_users: Iterable[User]) -> tuple[str]:
    """
    Returns emojis that were reacted to the most by given users, for given :class:`Message`

    :param msg: Message object
    :param counted_users: Users that should be counted
    :return: Emojis that were reacted the most by certain users
    """

    filtered_reactions = tuple(filter(lambda r: r.me, msg.reactions))
    counts = [await count_certain_reacted_users(r, counted_users) for r in filtered_reactions]
    max_reactions = tuple(map(
        lambda pair: pair[0],
        filter(lambda pair: pair[1] == max(counts), zip(filtered_reactions, counts))
    ))
    return tuple(map(lambda r: r.emoji, max_reactions))


# noinspection PyUnboundLocalVariable
async def pros_and_cons(msg: Message, delay: float, counted_users: Iterable[User]) -> tuple[int, int]:
    """
    Starts a "pros and cons" vote for the given :class:`Message` with the given delay to wait for users to react.

    Counts only given users.

    :param msg: Message object
    :param delay: Time to wait for users to react
    :param counted_users: Users that should be counted
    :return: Pros and cons as integers
    """

    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await asyncio.sleep(delay)

    new_msg = await msg.channel.fetch_message(msg.id)  # Have to get the message object again with reactions in it
    reactions = filter(lambda r: r.emoji in "👍👎", new_msg.reactions)
    for reaction in reactions:
        if reaction.emoji == "👍":
            pros = await count_certain_reacted_users(reaction, counted_users)
        else:
            cons = await count_certain_reacted_users(reaction, counted_users)

    return pros, cons


async def send_fields(
    game_uuid: str, channel: PartialMessageable, first_cap: User, second_cap: User, send_to_caps: bool = True
) -> None:
    """
    Sends fields to the game text channel (player filed) and to the captains (captain field)

    :param game_uuid: Game uuid to access field files
    :param channel: Game text channel
    :param first_cap: First captain User object
    :param second_cap: Second captain User object
    :param send_to_caps: Whether to send the field to captains
    :return: None
    """

    await channel.send(file=File(Paths.pl_img(game_uuid), filename="player_field.png"))

    if send_to_caps:
        await first_cap.send(file=File(Paths.cap_img(game_uuid), filename="captain_field.png"))
        await second_cap.send(file=File(Paths.cap_img(game_uuid), filename="captain_field.png"))
