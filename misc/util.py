from discord import Message, User, File
from discord.ext.commands import Command, Context
import asyncio
import os


def is_check_in_command(command: Command, check: str) -> bool:
    return check in map(lambda check: check.__qualname__.split(".")[0], command.checks)


def get_most_count_reaction_emojis(msg: Message) -> tuple[str]:
    filt_reactions = tuple(filter(lambda r: r.me, msg.reactions))
    max_count = max(filt_reactions, key=lambda r: r.count).count
    max_reactions = tuple(filter(lambda r: r.count == max_count, filt_reactions))
    return tuple(map(lambda r: r.emoji, max_reactions))

async def pros_and_cons(msg: Message, delay: float) -> tuple[int, int]:
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await asyncio.sleep(delay)

    new_msg = await msg.channel.fetch_message(msg.id)  # Have to get the message object again with reactions in it
    reactions = filter(lambda r: r.emoji in "👍👎", new_msg.reactions)
    for reaction in reactions:
        if reaction.emoji == "👍":
            upvotes = reaction.count
        else:
            downvotes = reaction.count
    
    return upvotes, downvotes


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
