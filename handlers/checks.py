from discord.ext.commands import check, Context, MissingPermissions


def is_moderator():
    def predicate(ctx: Context):
        if not (ctx.message.author.permissions_in(ctx.channel).manage_messages or ctx.bot.is_owner(ctx.message.author)):
            raise MissingPermissions(None)
        
        return True
    
    return check(predicate)
