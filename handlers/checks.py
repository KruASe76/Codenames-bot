from discord import Interaction
from discord.ext.commands import check, Context, MissingPermissions

from misc.constants import ADMINS


def is_moderator():
    async def predicate(ctx: Context | Interaction) -> bool:
        user = ctx.author if isinstance(ctx, Context) else ctx.user

        if not ctx.guild or ctx.channel.permissions_for(user).manage_messages or user in ADMINS:
            return True

        if isinstance(ctx, Interaction):
            return False
        else:
            raise MissingPermissions(["manage_messages"])

    return check(predicate)
