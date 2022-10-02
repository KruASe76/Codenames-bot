from discord.ext.commands import check, Context


def is_moderator():
    def predicate(ctx: Context):
        return ctx.message.author.permissions_in(ctx.channel).manage_messages or ctx.bot.is_owner(ctx.message.author)
    return check(predicate)
