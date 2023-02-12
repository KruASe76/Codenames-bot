import random
from typing import Any, Callable, Coroutine

from discord import Interaction, ButtonStyle, Embed, User
from discord.ui import View, Button, button

from handlers.checks import is_moderator
from misc.database import Database
from misc.util import send_alert, send_error
from misc.messages import Localization
from misc.constants import flags_loc_rev, Colors, EMPTY


class LocalizationButton(Button):
    def __init__(self, flag: str) -> None:
        super().__init__(emoji=flag, style=ButtonStyle.grey)
        self.flag = flag

    async def callback(self, interaction: Interaction) -> None:
        new_loc: str = flags_loc_rev[self.flag]

        db = Database()

        if interaction.guild:
            await db.exec_and_commit(
                "UPDATE guilds SET localization = ? WHERE id = ?",
                (new_loc, interaction.guild.id)
            )
        else:
            await db.exec_and_commit(
                "UPDATE players SET localization = ? WHERE id = ?",
                (new_loc, interaction.user.id)
            )

        loc = await db.localization(interaction)

        await interaction.response.edit_message(
            embed=Embed(
                title=loc.commands.language.title,
                description=loc.commands.language.desc_set.format(new_loc.upper(), self.flag),
                color=Colors.purple
            ),
            view=None
        )


class LocalizationView(View):
    def __init__(self) -> None:
        super().__init__()

        for flag in flags_loc_rev.keys():
            self.add_item(LocalizationButton(flag))


# noinspection PyUnusedLocal
class RegistrationView(View):
    # noinspection PyUnresolvedReferences
    def __init__(
        self,
        loc: Localization,
        start_callback: Callable[[Interaction, list[User], list[User]], Coroutine[Any, Any, None]],
        caller_id: int
    ) -> None:
        super().__init__()

        self.loc = loc

        self.start_callback = start_callback
        self.caller_id = caller_id

        self.game_started = False

        self.no_team: list[User] = []
        self.team1: list[User] = []
        self.team2: list[User] = []

        self.children[1].label = loc.ui.random
        self.children[3].label = loc.ui.leave
        self.children[4].label = loc.ui.cancel_reg
        self.children[5].label = loc.ui.start_game

    def remove_player(self, player: User) -> None:
        if player in self.no_team:
            self.no_team.remove(player)
        elif player in self.team1:
            self.team1.remove(player)
        elif player in self.team2:
            self.team2.remove(player)

    async def update_player_list(self, interaction: Interaction, *, final: bool = False) -> None:
        if self.no_team or self.team1 or self.team2:
            players_embed = Embed(
                title=self.loc.commands.game.registration_over if final else self.loc.commands.game.registration,
                color=Colors.purple
            )

            players_embed.add_field(
                name=self.loc.commands.game.team1,
                value="\n".join(map(lambda p: p.mention, self.team1)) or EMPTY
            )

            if not final:
                players_embed.add_field(
                    name=self.loc.commands.game.no_team,
                    value="\n".join(map(lambda p: p.mention, self.no_team)) or EMPTY
                )

            players_embed.add_field(
                name=self.loc.commands.game.team2,
                value="\n".join(map(lambda p: p.mention, self.team2)) or EMPTY
            )
        else:
            players_embed = Embed(
                title=self.loc.commands.game.registration,
                description=self.loc.commands.game.empty_list,
                color=Colors.purple
            )

        if not final:
            players_embed.add_field(
                name=EMPTY,
                value=f"_{self.loc.commands.game.registration_instructions}_",
                inline=False
            )

        await interaction.followup.edit_message(
            interaction.message.id,
            embed=players_embed, view=None if final else self
        )

    @button(emoji="1️⃣", style=ButtonStyle.grey, row=1)
    async def team1_button(self, interaction: Interaction, button: Button) -> None:
        self.remove_player(interaction.user)

        self.team1.append(interaction.user)

        await interaction.response.defer()
        await self.update_player_list(interaction)

    @button(emoji="❔", style=ButtonStyle.grey, row=1)
    async def no_team_button(self, interaction: Interaction, button: Button) -> None:
        self.remove_player(interaction.user)

        self.no_team.append(interaction.user)

        await interaction.response.defer()
        await self.update_player_list(interaction)

    @button(emoji="2️⃣", style=ButtonStyle.grey, row=1)
    async def team2_button(self, interaction: Interaction, button: Button) -> None:
        self.remove_player(interaction.user)

        self.team2.append(interaction.user)

        await interaction.response.defer()
        await self.update_player_list(interaction)

    @button(emoji="❌", style=ButtonStyle.grey, row=1)
    async def leave_button(self, interaction: Interaction, button: Button) -> None:
        self.remove_player(interaction.user)

        await interaction.response.defer()
        await self.update_player_list(interaction)

    @button(emoji="⛔", style=ButtonStyle.red, row=2)
    async def cancel_button(self, interaction: Interaction, button: Button) -> None:
        if not interaction.user.id == self.caller_id and not await is_moderator().predicate(interaction):
            await interaction.response.defer()  # so ctx.followup.send() from send_error won't crash
            await send_error(
                interaction, self.loc.errors.title, self.loc.errors.no_permission.format(self.loc.errors.not_a_mod)
            )
            return

        await send_alert(interaction, self.loc, self.loc.ui.cancel_reg, self.cancel_callback, interaction)

    @button(emoji="▶️", style=ButtonStyle.green, row=2)
    async def start_button(self, interaction: Interaction, button: Button) -> None:
        if interaction.user not in self.no_team + self.team1 + self.team2:
            await interaction.response.defer()  # so ctx.followup.send() from send_error won't crash
            await send_error(
                interaction, self.loc.errors.title, self.loc.errors.no_permission.format(self.loc.errors.not_registered)
            )
            return

        await send_alert(interaction, self.loc, self.loc.ui.start_game, self.start_pre_callback, interaction)


    async def start_pre_callback(self, interaction: Interaction) -> None:
        if self.game_started:  # ignoring duplicate starts from same registration
            return

        no_team_temp = self.no_team.copy()
        team1_temp = self.team1.copy()
        team2_temp = self.team2.copy()

        random.shuffle(no_team_temp)
        for member in no_team_temp:  # Dividing no_team into two teams randomly
            if len(team1_temp) <= len(team2_temp):
                team1_temp.append(member)
            else:
                team2_temp.append(member)

        if len(team1_temp) < 2 or len(team2_temp) < 2:
            await send_error(interaction, self.loc.errors.title, self.loc.errors.not_enough_players)
            return

        if len(team1_temp) > 25 or len(team2_temp) > 25:
            await send_error(interaction, self.loc.errors.title, self.loc.errors.too_many_players)
            return

        self.no_team = []
        self.team1 = team1_temp
        self.team2 = team2_temp

        # Adding players to the database
        db = Database()
        all_players_ids = tuple(map(lambda p: p.id, self.team1 + self.team2))
        registered_ids = tuple(map(
            lambda row: row[0],
            await db.fetch(
                f"SELECT id FROM players WHERE id IN ({', '.join(map(str, all_players_ids))})",
                fetchall=True
            )
        ))
        for id in all_players_ids:
            if id not in registered_ids:
                await db.exec_and_commit(
                    "INSERT INTO players VALUES (?, strftime('%d/%m/%Y','now'), ?, ?, ?, ?, ?, ?)",
                    (id, "", self.loc.literal, 0, 0, 0, 0)
                )

        self.game_started = True

        await self.update_player_list(interaction, final=True)

        await self.start_callback(interaction, self.team1, self.team2)

    # noinspection PyMethodMayBeStatic
    async def cancel_callback(self, interaction: Interaction) -> None:
        registration_cancelled_embed = Embed(
            title=self.loc.commands.game.registration_cancelled,
            color=Colors.purple
        )

        await interaction.followup.edit_message(
            interaction.message.id,
            embed=registration_cancelled_embed, view=None
        )
