from discord import Interaction
from discord.ext.commands import check, Context, MissingPermissions, is_owner


def is_moderator():
    async def predicate(ctx: Context | Interaction) -> bool:
        if ctx.channel.permissions_for(ctx.author).manage_messages or await is_owner().predicate(ctx):
            return True

        raise MissingPermissions(["manage_messages"])

    return check(predicate)
