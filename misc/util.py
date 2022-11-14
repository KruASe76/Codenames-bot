from discord import Message, User, File, Embed, Reaction
from discord.ext.commands import Command, Context
import asyncio
import os
from typing import Iterable

from misc.constants import Colors


def is_check_in_command(command: Command, check: str) -> bool:
    return check in map(lambda check: check.__qualname__.split(".")[0], command.checks)


async def send_error(ctx: Context, title: str, description: str):
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
    counted_users = set(counted_users)
    filtered_reactions = tuple(filter(lambda r: r.me, msg.reactions))
    counts = []
    for r in filtered_reactions:
        counts.append(len(set([user async for user in r.users()]) & counted_users))
    max_reactions = tuple(map(
        lambda pair: pair[1],
        filter(lambda pair: counts[pair[0]] == max(counts), enumerate(filtered_reactions))
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
    with open(os.path.join("images", f"{ctx.guild.id}-player.png"), "rb") as pl_field_bin:
        pl_field = File(pl_field_bin, filename="player_field.png")
        await ctx.send(file=pl_field)
    with open(os.path.join("images", f"{ctx.guild.id}-captain.png"), "rb") as cap_field_bin:
        cap_field = File(cap_field_bin, filename="captain_field.png")
        await first_cap.send(file=cap_field)
    with open(os.path.join("images", f"{ctx.guild.id}-captain.png"), "rb") as cap_field_bin:
        cap_field = File(cap_field_bin, filename="captain_field.png")
        await second_cap.send(file=cap_field)
