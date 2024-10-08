from typing import Iterable, Any, Self

import aiosqlite
from discord import Interaction
from discord.ext.commands import Context

from misc.messages import messages, Localization
from misc.constants import Paths


class Database:
    _instance: Self = None
    _db: aiosqlite.Connection = None

    def __new__(cls, *args, **kwargs):
        """
        Access the :class:`Database` singleton.

        **WARNING**: ``await Database.create()`` should be called once previously

        :return: Database object
        """

        return cls._instance

    @classmethod
    async def create(cls) -> None:
        """
        Creates a :class:`aiosqlite.Connection` to the database to make it accessible as a singleton.

        :return: None
        """

        db = await aiosqlite.connect(Paths.db)

        await db.execute(
            "CREATE TABLE IF NOT EXISTS guilds "
            "(id int primary key, prefix text, localization text)"
        )
        await db.execute(
            "CREATE TABLE IF NOT EXISTS players "
            "(id int primary key, date text, prefix text, localization text, "
            "games int, games_cap int, wins int, wins_cap int)"
        )
        await db.commit()

        cls._db = db
        cls._instance = super(Database, cls).__new__(cls)

    @classmethod
    async def close(cls) -> None:
        """
        Closes the connection to the database

        :return: None
        """

        await cls._db.close()

    async def fetch(
        self,
        sql: str,
        parameters: Iterable[Any] | None = None,
        *,
        fetchall: bool = False,
    ) -> tuple[Any] | None:
        """
        Executes the given SQL query and returns the result.

        :param sql: SQL query to execute
        :param parameters: Parameters for the SQL query
        :param fetchall: Whether the function should return a single row or all rows
        :return: Results as a tuple
        """

        cursor = await self._db.execute(sql, parameters)
        res = await cursor.fetchall() if fetchall else await cursor.fetchone()
        await cursor.close()

        return tuple(res) if res else (tuple() if fetchall else None)

    async def exec_and_commit(
        self, sql: str, parameters: Iterable[Any] | None = None
    ) -> None:
        """
        Executes the given SQL statement with changes to the database and commits them.

        :param sql: SQL statement to execute
        :param parameters: Parameters to the sql statement
        :return: None
        """

        await self._db.execute(sql, parameters)
        await self._db.commit()

    async def localization(self, ctx: Context | Interaction) -> Localization:
        """
        Determines which language the bot should use.

        :param ctx: Context or Interaction object to access the guild or user id
        :return: The localization of the guild or player
        """

        if ctx.guild:
            request = await self.fetch(
                "SELECT localization FROM guilds WHERE id = ?", (ctx.guild.id,)
            )

            if not request:  # should not normally happen
                await self.exec_and_commit(
                    "INSERT INTO guilds VALUES (?, ?, ?)", (ctx.guild.id, "", "en")
                )
        else:
            user_id = ctx.author.id if isinstance(ctx, Context) else ctx.user.id
            request = await self.fetch(
                "SELECT localization FROM players WHERE id = ?", (user_id,)
            )

            if (
                not request
            ):  # if the user sends a slash command to the bot as the first use in DMs
                await self.exec_and_commit(
                    "INSERT INTO players VALUES (?, strftime('%d/%m/%Y','now'), ?, ?, ?, ?, ?, ?)",
                    (user_id, "", "en", 0, 0, 0, 0),
                )

        return messages[request[0]] if request else messages["en"]

    async def increase_stats(self, player_id: int, stats: Iterable[str]) -> None:
        """
        Increases the given stats by 1 for the given player, then commits the changes to the database.

        :param player_id: Player id
        :param stats: Stats to increase
        :return: None
        """

        if not (
            current_stats := await self.fetch(
                f"SELECT {', '.join(stats)} FROM players WHERE id = ?", (player_id,)
            )
        ):  # should not normally happen
            await self.exec_and_commit(
                "INSERT INTO players VALUES (?, strftime('%d/%m/%Y','now'), ?, ?, ?, ?, ?, ?)",
                (player_id, "", "en", 0, 0, 0, 0),
            )

        await self.exec_and_commit(
            f"UPDATE players SET {' = ?, '.join(stats)} = ? WHERE id = ?",
            (*map(lambda stat: stat + 1, current_stats), player_id),
        )
