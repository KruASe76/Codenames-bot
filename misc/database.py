import aiosqlite
import os
from discord.ext.commands import Context
from typing import Iterable, Any

from misc.messages import messages, Localization


class Database:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
    
    @classmethod
    async def create(cls):        
        db = await aiosqlite.connect(os.path.join(os.getcwd(), "base.db"))
        
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
        
        return Database(db)


    async def fetch(self, sql: str, parameters: Iterable[Any] = None, *, fetchall: bool = False) -> tuple[Any]:
        cursor = await self.db.execute(sql, parameters)
        res = await cursor.fetchall() if fetchall else await cursor.fetchone()
        await cursor.close()
        
        return tuple(res)

    async def exec_and_commit(self, sql: str, parameters: Iterable[Any] = None) -> None:
        await self.db.execute(sql, parameters)
        await self.db.commit()


    async def localization(self, ctx: Context) -> Localization:
        if ctx.guild:
            return messages[(await self.fetch("SELECT localization FROM guilds WHERE id=?", (ctx.guild.id,)))[0]]
        else:
            return messages[(await self.fetch("SELECT localization FROM players WHERE id=?", (ctx.author.id,)))[0]]
    
    async def increase_stats(self, player_id: int, stats: Iterable[str]) -> None:
        await self.exec_and_commit(
            f"UPDATE players SET {'=?, '.join(stats)}=? WHERE id=?",
            (*map(
                lambda stat: stat+1,
                await self.fetch(f"SELECT {', '.join(stats)} FROM players WHERE id=?", (player_id,))
            ), player_id)
        )
