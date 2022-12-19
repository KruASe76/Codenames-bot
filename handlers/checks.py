from discord.ext.commands import check, Context, MissingPermissions


def is_moderator():
    def predicate(ctx: Context) -> bool:
        if not (
            ctx.channel.permissions_for(ctx.message.author).manage_messages or ctx.bot.is_owner(ctx.message.author)
        ):
            raise MissingPermissions(["manage_messages"])
        
        return True
    
    return check(predicate)
