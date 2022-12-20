import asyncio
from typing import Iterable

from discord import Message, User, File, Embed, Reaction
from discord.ext.commands import Parameter, Command, Context

from misc.constants import Paths, Colors


def process_param(name: str, param: Parameter) -> str | None:
    if name == "final":
        return

    if param.required:
        return f"<{param.name}>"

    default = None if not param.default else param.default
    default = f'"{default}"' if isinstance(default, str) else default
    return f"[{param.name}={f'{default}'}]"

def is_check_in_command(command: Command, check: str) -> bool:
    return check in map(lambda check: check.__qualname__.split(".")[0], command.checks)


async def send_error(ctx: Context, title: str, description: str) -> None:
    await ctx.reply(
        embed=Embed(
            title=title,
            description=description,
            color=Colors.red
        ),
        delete_after=7
    )
    await ctx.message.delete(delay=7)


async def count_certain_reacted_users(reaction: Reaction, users: Iterable[User]) -> int:
    return len(set([user async for user in reaction.users()]) & set(users))


# noinspection PyTypeChecker
async def most_count_reaction_emojis(msg: Message, counted_users: Iterable[User]) -> tuple[str]:
    filtered_reactions = tuple(filter(lambda r: r.me, msg.reactions))
    counts = [await count_certain_reacted_users(r, counted_users) for r in filtered_reactions]
    max_reactions = tuple(map(
        lambda pair: pair[0],
        filter(lambda pair: pair[1] == max(counts), zip(filtered_reactions, counts))
    ))
    return tuple(map(lambda r: r.emoji, max_reactions))


# noinspection PyUnboundLocalVariable
async def pros_and_cons(msg: Message, delay: float, counted_users: Iterable[User]) -> tuple[int, int]:
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


async def send_fields(ctx: Context, first_cap: User, second_cap: User) -> None:
    pl_field = File(Paths.pl_img(ctx.guild.id), filename="player_field.png")
    await ctx.send(file=pl_field)

    cap_field = File(Paths.cap_img(ctx.guild.id), filename="captain_field.png")
    await first_cap.send(file=cap_field)
    cap_field = File(Paths.cap_img(ctx.guild.id), filename="captain_field.png")
    await second_cap.send(file=cap_field)
