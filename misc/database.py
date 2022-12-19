from typing import Iterable, Any

import aiosqlite
from discord import User
from discord.ext.commands import Context

from misc.messages import messages, Localization
from misc.constants import Paths


class Database:
    _instance = None
    _db: aiosqlite.Connection = None

    def __new__(cls, *args, **kwargs):
        return cls._instance
    
    @classmethod
    async def create(cls) -> None:
        """
        Creates a connection to the database to make it accessible as a singleton.

        :return: None
        """
        db = await aiosqlite.connect(Paths.db)
        
        await db.execute(
            "CREATE TABLE IF NOT EXISTS guilds "
            "(id int primary key, prefix text, localization text, players text, team1 text, team2 text)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS players "
            "(id int primary key, date text, prefix text, localization text, "
            "games int, games_cap int, wins int, wins_cap int)"
        )
        await db.commit()

        cls._db = db
        cls._instance = super(Database, cls).__new__(cls)


    async def fetch(self, sql: str, parameters: Iterable[Any] = None, *, fetchall: bool = False) -> tuple[Any]:
        """
        Helper function that executes the given SQL query and returns the result.

        :param sql: SQL query to execute
        :param parameters: Parameters for the SQL query
        :param fetchall: If the function should return a single row or all rows
        :return: Results as a tuple
        """

        cursor = await self._db.execute(sql, parameters)
        res = await cursor.fetchall() if fetchall else await cursor.fetchone()
        await cursor.close()
        
        return tuple(res)

    async def exec_and_commit(self, sql: str, parameters: Iterable[Any] = None) -> None:
        """
        Helper function that executes the given SQL statement with changes to the database and commits them.

        :param sql: SQL statement to execute
        :param parameters: Parameters to the sql statement
        :return: None
        """

        await self._db.execute(sql, parameters)
        await self._db.commit()


    async def localization(self, ctx: Context) -> Localization:
        """
        Determines which language the bot should use.

        :param ctx: Command context to access the guild or user id
        :return: The localization of the guild or player
        """

        if ctx.guild:
            return messages[(await self.fetch("SELECT localization FROM guilds WHERE id=?", (ctx.guild.id,)))[0]]
        else:
            return messages[(await self.fetch("SELECT localization FROM players WHERE id=?", (ctx.author.id,)))[0]]


    async def fetch_teams(self, ctx: Context) -> tuple[list[User], list[User], list[User]]:
        """
        Returns a tuple of three lists of Users (three teams).
        The first list contains players without team, the second two contain each team's members.

        :param ctx: Command context to access bot and guild id
        :return: A tuple of three teams
        """

        players, team1, team2 = map(
            lambda result: map(int, result.split()),
            await self.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        )
        return (
            [await ctx.bot.fetch_user(id) for id in players],
            [await ctx.bot.fetch_user(id) for id in team1],
            [await ctx.bot.fetch_user(id) for id in team2]
        )

    async def save_teams(self, ctx: Context, players: list[User], team1: list[User], team2: list[User]) -> None:
        """
        Saves the given teams to the database.

        :param ctx: Command context to access guild id
        :param players: Players without team
        :param team1: Members of the first team
        :param team2: Members of the second team
        :return: None
        """

        players_id = map(lambda player: str(player.id), players)
        team1_id = map(lambda player: str(player.id), team1)
        team2_id = map(lambda player: str(player.id), team2)
        await self.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            (" ".join(players_id), " ".join(team1_id), " ".join(team2_id), ctx.guild.id)
        )


    async def increase_stats(self, player_id: int, stats: Iterable[str]) -> None:
        """
        Increases the given stats by 1 for the given player, then commits the changes to the database.

        :param player_id: Player id
        :param stats: Stats to increase
        :return: None
        """

        await self.exec_and_commit(
            f"UPDATE players SET {'=?, '.join(stats)}=? WHERE id=?",
            (*map(
                lambda stat: stat+1,
                await self.fetch(f"SELECT {', '.join(stats)} FROM players WHERE id=?", (player_id,))
            ), player_id)
        )
