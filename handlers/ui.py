from discord import Interaction, ButtonStyle, Embed
from discord.ui import Button, View

from misc.database import Database
from misc.constants import flags_rev, Colors


class LocalizationButton(Button):
    def __init__(self, flag: str, db: Database):
        super().__init__(emoji=flag, style=ButtonStyle.grey)
        self.flag = flag
        self.db = db

    async def callback(self, interaction: Interaction) -> None:
        new_loc: str = flags_rev[self.flag]

        if interaction.guild:
            await self.db.exec_and_commit(
                "UPDATE guilds SET localization=? WHERE id=?",
                (new_loc, interaction.guild.id)
            )
        else:
            await self.db.exec_and_commit(
                "UPDATE players SET localization=? WHERE id=?",
                (new_loc, interaction.user.id)
            )

        loc = await self.db.localization(interaction)

        await interaction.response.edit_message(
            embed=Embed(
                title=loc.commands.language.title,
                description=loc.commands.language.desc_set.format(new_loc.upper(), self.flag),
                color=Colors.purple
            ),
            view=None
        )


class LocalizationView(View):
    def __init__(self):
        super().__init__()
        self.db = Database()

        for flag in flags_rev.keys():
            self.add_item(LocalizationButton(flag, self.db))
