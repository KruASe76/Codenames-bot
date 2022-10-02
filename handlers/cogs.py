from discord import Message, Guild, TextChannel, Member, Embed, Activity, ActivityType
from discord.ext.commands import Bot, Context, Command, Cog, command, guild_only, CommandNotFound, CheckFailure, NoPrivateMessage, BadArgument, MemberNotFound
import asyncio
import random
import os, re

from handlers.checks import is_moderator
from misc.database import Database
from misc.constants import EMPTY, ALPHABET, REACTION_ALPHABET, REACTION_NUMBERS, dictionaries, flags, flags_rev, Colors
import misc.generation as gen
from misc.messages import messages
from misc import util


class Listeners(Cog):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.change_presence(activity = Activity(type=ActivityType.watching, name="codenames.me"))

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.content.strip() == self.bot.user.mention:
            help_comm: Command = self.bot.get_command("help")
            await help_comm.__call__(await self.bot.get_context(message))
            return

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: Exception) -> None:
        if isinstance(error, (CommandNotFound, BadArgument, MemberNotFound)):  # MemberNotFound raises in "stats" if invalid member was given
            await ctx.message.add_reaction("❔")
            await ctx.message.delete(delay=3)
            return

        if isinstance(error, NoPrivateMessage):
            loc = await self.db.localization(ctx)
            await ctx.reply(embed=Embed(
                title=messages[loc].errors.guild_only,
                color=Colors.red
            ))
            return

        if isinstance(error, CheckFailure):
            loc = await self.db.localization(ctx)
            await ctx.reply(embed=Embed(
                title=messages[loc].errors.no_permission,
                color=Colors.red
            ))
            return

        raise error

    @Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        await self.db.exec_and_commit("INSERT INTO guilds VALUES (?,?,?,?,?,?)", (guild.id, "", "en", "", "", ""))

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        await self.db.exec_and_commit("DELETE FROM guilds WHERE id=?", (guild.id,))


class GameCommands(Cog, name="Game"):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @command(aliases=("ready", "reg", "r"), brief="Registers the user for the game",
        help="Registers the user for the game.\nIf you won't enter the team number it will be selected randomly when the game starts.\nTo change the team call the commang again with another argument; to reset team, do not input the argument"
    )
    @guild_only()
    async def register(self, ctx: Context, team_number: int = 0) -> None:
        players, team1, team2 = map(
            lambda result: map(int, result.split()),
            await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        )
        players = [await self.bot.fetch_user(id) for id in players]
        team1 = [await self.bot.fetch_user(id) for id in team1]
        team2 = [await self.bot.fetch_user(id) for id in team2]

        if ctx.author in players + team1 + team2:
            if (ctx.author in players and team_number == 0) or (ctx.author in team1 and team_number == 1) or (ctx.author in team2 and team_number == 2):
                await ctx.reply(embed=Embed(
                    title="Error",
                    description="You're already in that team!",
                    color=Colors.red,
                ))
                return

            leave_comm = self.bot.get_command("leave")  # Removing author from any team, then processing main code
            await leave_comm.__call__(ctx)  # Changes are not visible from this function running
            
            if ctx.author in players:  # Getting relevant player list again
                players = map(int, (await self.db.fetch("SELECT players FROM guilds WHERE id=?", (ctx.guild.id,)))[0].split())
                players = [await self.bot.fetch_user(id) for id in players]
            if ctx.author in team1:
                team1 = map(int, (await self.db.fetch("SELECT team1 FROM guilds WHERE id=?", (ctx.guild.id,)))[0].split())
                team1 = [await self.bot.fetch_user(id) for id in team1]
            if ctx.author in team2:
                team2 = map(int, (await self.db.fetch("SELECT team2 FROM guilds WHERE id=?", (ctx.guild.id,)))[0].split())
                team2 = [await self.bot.fetch_user(id) for id in team2]
        
        if team_number == 0:
            players.append(ctx.author)
        elif team_number == 1:
            team1.append(ctx.author)
        elif team_number == 2:
            team2.append(ctx.author)
        else:
            reply = await ctx.reply(embed=Embed(
                title="Invalid team number",
                description="There are only 2 teams in the game\nSelect one of them or don't type the number to select randomly",
                color=Colors.red
            ))
            await reply.delete(delay=3)
            return

        if ctx.author.id not in map(lambda row: row[0], await self.db.fetch("SELECT id FROM players", fetchall=True)):
            await self.db.exec_and_commit("INSERT INTO players VALUES (?,strftime('%d/%m/%Y','now'),?,?,?,?,?,?)", (ctx.author.id, "", "en", 0, 0, 0, 0))

        await ctx.message.add_reaction("✅")
        
        players_id = map(lambda player: str(player.id), players)
        team1_id = map(lambda player: str(player.id), team1)
        team2_id = map(lambda player: str(player.id), team2)
        await self.db.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            (" ".join(players_id), " ".join(team1_id), " ".join(team2_id), ctx.guild.id)
        )

        await ctx.message.delete(delay=3)

    @command(aliases=("unregister", "unreg", "l"), help="Unregisters the user from the game")
    @guild_only()
    async def leave(self, ctx: Context) -> None:
        players, team1, team2 = map(
            lambda result: map(int, result.split()),
            await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        )
        players = [await self.bot.fetch_user(id) for id in players]
        team1 = [await self.bot.fetch_user(id) for id in team1]
        team2 = [await self.bot.fetch_user(id) for id in team2]
        
        if ctx.author not in players + team1 + team2:
            await ctx.reply(embed=Embed(
                title="Error",
                description="You're not registered to the game",
                color=Colors.red,
            ))
            return

        if ctx.author in players:
            players.remove(ctx.author)
        elif ctx.author in team1:
            team1.remove(ctx.author)
        elif ctx.author in team2:
            team2.remove(ctx.author)
        
        await ctx.message.add_reaction("✅")

        players_id = map(lambda player: str(player.id), players)
        team1_id = map(lambda player: str(player.id), team1)
        team2_id = map(lambda player: str(player.id), team2)
        await self.db.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            (" ".join(players_id), " ".join(team1_id), " ".join(team2_id), ctx.guild.id)
        )

        await ctx.message.delete(delay=3)

    @command(aliases=("clr", "cl", "c"), help="Clears registered players list")
    @guild_only()
    @is_moderator()
    async def clear(self, ctx: Context) -> None:
        await self.db.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            ("", "", "", ctx.guild.id)
        )
        
        await ctx.message.add_reaction("✅")
        await ctx.message.delete(delay=3)

    @command(name="players", aliases=("ps", "p",), help="Shows registered players")
    @guild_only()
    async def show_players(self, ctx: Context, final: bool = False) -> None:
        async with ctx.typing():
            players, team1, team2 = map(
                lambda result: map(int, result.split()),
                await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
            )
            players = [await self.bot.fetch_user(id) for id in players]
            team1 = [await self.bot.fetch_user(id) for id in team1]
            team2 = [await self.bot.fetch_user(id) for id in team2]

            players_embed = Embed(
                title="Final player list" if final else "Player list",
                color=Colors.purple
            )
            if team1:
                players_embed.add_field(name="Team 1", value="\n".join(map(lambda p: p.mention, team1)))
            if players:
                players_embed.add_field(name="No Team", value="\n".join(map(lambda p: p.mention, players)))
            if team2:
                players_embed.add_field(name="Team 2", value="\n".join(map(lambda p: p.mention, team2)))

            if players or team1 or team2:
                await ctx.reply(embed=players_embed)
            else:
                await ctx.reply(embed=Embed(
                    title="Player list",
                    description="Nobody is ready to play",
                    color=Colors.purple
                ))

    @command(aliases=("s",), brief="Starts the game",
        help="Starts the game.\nIf there are players without a team they will be evenly distributed among the teams."
    )
    @guild_only()
    async def start(self, ctx: Context) -> None:
        async with ctx.typing():  # Final player list preparation and show
            players, team1, team2 = map(
                lambda result: map(int, result.split()),
                await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
            )
            players = [await self.bot.fetch_user(id) for id in players]
            team1 = [await self.bot.fetch_user(id) for id in team1]
            team2 = [await self.bot.fetch_user(id) for id in team2]

            if players:  # Dividing players into two teams randomly
                random.shuffle(players)
                for member in players:
                    if len(team1) <= len(team2):
                        team1.append(member)
                    else:
                        team2.append(member)
            
            if len(team1) < 2 or len(team2) < 2:
                await ctx.reply(embed=Embed(
                    title="Error",
                    description="There are not enough players.\nEach team must have at least 2 players.",
                    color=Colors.red
                ))
                return
            
            if len(team1) > 25 or len(team2) > 25:
                await ctx.reply(embed=Embed(
                    title="Error",
                    description="There are too much players.\nEach team must have **no more** than 25 players.",
                    color=Colors.red
                ))
                return

            team1_id = map(lambda player: str(player.id), team1)
            team2_id = map(lambda player: str(player.id), team2)
            await self.db.exec_and_commit(
                "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
                ("", " ".join(team1_id), " ".join(team2_id), ctx.guild.id)  # There are no players without team left
            )
            
            final_show = self.bot.get_command("players")
            await final_show.__call__(ctx, final=True)
        await asyncio.sleep(1)

        # Dictionary selecting
        await ctx.send(embed=Embed(
            title="Select language",
            description="**en** - English\n**ru** - Russian\n\nType answer in response message",
            color=Colors.purple
        ))
        language = await self.bot.wait_for(
            "message",
            check=lambda msg: msg.channel == ctx.channel and msg.author in (team1 + team2) and msg.content.lower() in dictionaries.keys()
        )
        language = language.content.lower()

        dict_msg_desc = map(lambda num, value: f"**{num}** - {value}", range(1, 10), dictionaries[language].values())
        dict_msg = await ctx.send(embed=Embed(
            title="Select dictionary",
            description="\n".join(dict_msg_desc) + "\n\nYou have 15 seconds to vote",
            color=Colors.purple
        ))
        for ind, _ in enumerate(dictionaries[language]):
            await dict_msg.add_reaction(REACTION_NUMBERS[ind*3 : ind*3 + 3])
        await asyncio.sleep(15)

        new_dict_msg = await ctx.channel.fetch_message(dict_msg.id)
        emojis = util.get_most_count_reaction_emojis(new_dict_msg)

        potential_dicts = map(lambda em: tuple(dictionaries[language].keys())[REACTION_NUMBERS.index(em) // 3], emojis)
        game_dict_name = random.choice(tuple(potential_dicts))
        await ctx.send(embed=Embed(
            title="Dictionary selected",
            description=dictionaries[language][game_dict_name],
            color=Colors.purple
        ))

        # Captains selecting
        cap_selecting_list = map(lambda ind, player: f"**{ALPHABET[ind]}** - {player.mention}", range(len(team1)), team1)
        cap_msg = await ctx.send(embed=Embed(
            title="RED team: Captain selecting",
            description="**R** - Random captain\n\n" + "\n".join(cap_selecting_list) + "\n\nYou have 15 seconds to vote",
            color=Colors.red
        ))
        await cap_msg.add_reaction("🇷")
        for ind, _ in enumerate(team1):
            await cap_msg.add_reaction(REACTION_ALPHABET[ind])
        await asyncio.sleep(15)

        new_cap_msg = await ctx.channel.fetch_message(cap_msg.id)  # Have to get the message object again with reactions in it
        emojis = util.get_most_count_reaction_emojis(new_cap_msg)
        
        if "🇷" in emojis:
            team1_cap = random.choice(team1)
        else:
            potential_caps = map(lambda em: team1[REACTION_ALPHABET.index(em)], emojis)
            team1_cap = random.choice(tuple(potential_caps))
        team1_pl = team1.copy()
        team1_pl.remove(team1_cap)

        await ctx.send(embed=Embed(
            title="RED team: Captain selected",
            description=f"Your captain is {team1_cap.mention}!",
            color=Colors.red
        ))

        # The same code for team2_cap
        cap_selecting_list = map(lambda ind, player: f"**{ALPHABET[ind]}** - {player.mention}", range(len(team2)), team2)
        msg = await ctx.send(embed=Embed(
            title="BLUE team: Captain selecting",
            description="**R** - Random captain\n\n" + "\n".join(cap_selecting_list) + "\n\nYou have 15 seconds to vote",
            color=Colors.blue
        ))
        await msg.add_reaction("🇷")
        for ind, _ in enumerate(team2):
            await msg.add_reaction(REACTION_ALPHABET[ind])
        await asyncio.sleep(15)

        new_cap_msg = await ctx.channel.fetch_message(cap_msg.id)  # Have to get the message object again with reactions in it
        emojis = util.get_most_count_reaction_emojis(new_cap_msg)
        
        if "🇷" in emojis:
            team2_cap = random.choice(team2)
        else:
            potential_caps = map(lambda em: team2[REACTION_ALPHABET.index(em)], emojis)
            team2_cap = random.choice(tuple(potential_caps))
        team2_pl = team2.copy()
        team2_pl.remove(team2_cap)

        await ctx.send(embed=Embed(
            title="BLUE team: Captain selected",
            description=f"Your captain is {team2_cap.mention}!",
            color=Colors.blue
        ))


        await ctx.send(embed=Embed(
            title="GAME STARTED!",
            color=Colors.purple
        ))
        
        # Notifying everyone in direct messages
        await team1_cap.send(embed=Embed(
            title="Game started",
            description="**You're the captain of the RED team**\n\nYour teammates are:\n" + "\n".join([p.mention for p in team1_pl]),
            color=Colors.red
        ))
        for player in team1_pl:
            team1_pl_without = team1_pl.copy()  # Team1 player list without recipient of the message
            team1_pl_without.remove(player)
            await player.send(embed=Embed(
                title="Game started",
                description=f"**You're a member of the RED team**\n\nThe captain of your team is {team1_cap.mention}\n\nYour teammates are:\n" + "\n".join([p.mention for p in team1_pl_without]),
                color=Colors.red
            ))
        
        await team2_cap.send(embed=Embed(
            title="Game started",
            description="**You're the captain of the BLUE team**\n\nYour teammates are:\n" + "\n".join([p.mention for p in team2_pl]),
            color=Colors.blue
        ))
        for player in team2_pl:
            team2_pl_without = team2_pl.copy()  # Team2 player list without recipient of the message
            team2_pl_without.remove(player)
            await player.send(embed=Embed(
                title="Game started",
                description=f"**You're a member of the BLUE team**\n\nThe captain of your team is {team2_cap.mention}\n\nYour teammates are:\n" + "\n".join([p.mention for p in team2_pl_without]),
                color=Colors.blue
            ))

        team1_words, team2_words, endgame_word, other_words = gen.words(
            lang=language, dict_name=game_dict_name
        )
        opened_words = []
        order = list(team1_words + team2_words + (endgame_word,) + other_words)  # endgame_word is a single word
        random.shuffle(order)
        available_words = order.copy()  # Has to be a list
        order = tuple(order)

        if len(team1_words) > len(team2_words):
            first_color = "RED"
            first_cap = team1_cap
            first_pl = team1_pl
            first_words = team1_words
            second_color = "BLUE"
            second_cap = team2_cap
            second_pl = team2_pl
            second_words = team2_words
        else:
            first_color = "BLUE"
            first_cap = team2_cap
            first_pl = team2_pl
            first_words = team2_words
            second_color = "RED"
            second_cap = team1_cap
            second_pl = team1_pl
            second_words = team1_words

        # Mainloop
        game = True
        while game:
            gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)
            await util.send_fields(ctx, first_cap, second_cap)
            
            await ctx.send(embed=Embed(
                title="Waiting for move",
                description=f"Captain of **{first_color}** team",
                color=Colors.red if first_color == "RED" else Colors.blue
            ))
            await first_cap.send(embed=Embed(
                title="This is your move turn",
                description=f"Type a word and a number like {'**`animal 3`**' if language=='en' else '**`животное 3`**'} in response message",
                color=Colors.red if first_color == "RED" else Colors.blue
            ))
            move_msg = await self.bot.wait_for("message", check=lambda msg: msg.channel == first_cap.dm_channel and re.fullmatch(r"\w+ \d+", msg.content) and not msg.content.endswith(" 0"))
            move = move_msg.content
            word_count = int(move.split()[-1])
            await first_cap.send(embed=Embed(
                title="Move accepted",
                color=Colors.red if first_color == "RED" else Colors.blue
            ))
            await ctx.send(embed=Embed(
                title=f"Captain of **{first_color}** team moved",
                description=f"The move contains:\n**`{move}`**",
                color=Colors.red if first_color == "RED" else Colors.blue
            ))

            await ctx.send(embed=Embed(
                title="Waiting for move",
                description=f"Players of **{first_color}** team\n\nType words you want to open in response messages.\nIf you want to **BREAK THE MOVE** type **`0`**\nIf you want to **STOP THE GAME** type **`000`**",
                color=Colors.red if first_color == "RED" else Colors.blue
            ))
            while word_count >= 0:  # >= because of the rule that players can open one more word than their captain supposed them to
                move_msg = await self.bot.wait_for("message", check=lambda msg: msg.channel == ctx.channel and msg.author in first_pl and (msg.content.lower() in available_words or msg.content in ("0", "000")))
                move = move_msg.content.lower()
                if move == "0":
                    await move_msg.add_reaction("🆗")
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(embed=Embed(
                        title="Stopping the game",
                        description="**Do you really want to stop playing?**\n\nAll players have 15 seconds to vote",
                        color=Colors.red
                    ))
                    
                    upvotes, downvotes = await util.pros_and_cons(stop_msg, 15)
                    if upvotes > downvotes:
                        await ctx.send(embed=Embed(
                            title="GAME STOPPED",
                            description="Most players voted for game stopping",
                            color=Colors.purple
                        ))

                        game = False
                        break
                    else:
                        await ctx.send(embed=Embed(
                            title="GAME CONTINUED",
                            description="Most players voted against game stopping",
                            color=Colors.purple
                        ))
                        
                        continue  # No need to generate a new field or decrease word_count
                
                opened_words.append(move)
                available_words.remove(move)
                gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)

                if move in other_words:
                    await move_msg.reply(embed=Embed(
                        title="Miss",
                        description="Unfortunately, this word **doesn't belong to any team**",
                        color=Colors.white
                    ))
                    await first_cap.send(embed=Embed(
                        title="Miss",
                        description=f"Your team opened the word **`{move}`** that **doesn't belong to any team**",
                        color=Colors.white
                    ))
                    await second_cap.send(embed=Embed(
                        title="Lucky!",
                        description=f"The opponent team opened the word **`{move}`** that **doesn't belong to any team**",
                        color=Colors.white
                    ))

                    await util.send_fields(ctx, first_cap, second_cap)
                elif move in second_words:
                    await move_msg.reply(embed=Embed(
                        title="Miss",
                        description="Unfortunately, this word **belongs to the opponent team**",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title="Miss",
                        description=f"Your team opened the word **`{move}`** that **belongs to the opponent team**",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title="Lucky!",
                        description=f"The opponent team opened the word **`{move}`** that **belongs to your team**",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))

                    if set(second_words) <= set(opened_words):  # If all second_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title="Game over!",
                            description=f"**{second_color} team won!**\nThey opened all their team words",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))

                        await first_cap.send(embed=Embed(
                            title="Your team lost!",
                            description="Better luck in the next game!",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title="Your team lost!",
                                description="Better luck in the next game!",
                                color=Colors.red if second_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))
                        
                        await second_cap.send(embed=Embed(
                            title="Your team won!",
                            description="Keep it up!",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title="Your team won!",
                                description="Keep it up!",
                                color=Colors.red if second_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed=Embed(
                        title="Miss",
                        description="Unfortunately, this word **is an endgame one**",
                        color=Colors.black
                    ))
                    await first_cap.send(embed=Embed(
                        title="Miss",
                        description=f"Your team opened the word **`{move}`** that **is an endgame one**",
                        color=Colors.black
                    ))
                    await second_cap.send(embed=Embed(
                        title="Lucky!",
                        description=f"The opponent team opened the word **`{move}`** that **is an endgame one**",
                        color=Colors.black
                    ))

                    await util.send_fields(ctx, first_cap, second_cap)
                    
                    await ctx.send(embed=Embed(
                        title="Game over!",
                        description=f"**{second_color} team won!**\n{first_color} team opened an endgame word",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    
                    await first_cap.send(embed=Embed(
                        title="Your team lost!",
                        description="Better luck in the next game!",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    await self.db.increase_stats(first_cap.id, ("games", "games_cap"))
                    for player in first_pl:
                        await player.send(embed=Embed(
                            title="Your team lost!",
                            description="Better luck in the next game!",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games",))
                    
                    await second_cap.send(embed=Embed(
                        title="Your team won!",
                        description="Keep it up!",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    await self.db.increase_stats(second_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                    for player in second_pl:
                        await player.send(embed=Embed(
                            title="Your team won!",
                            description="Keep it up!",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games", "wins"))

                    game = False
                    break
                else:  # They guessed
                    await move_msg.reply(embed=Embed(
                        title="Success",
                        description="You guessed!",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title="Success",
                        description=f"Your team guessed the word **`{move}`** that **belongs to your team**!",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title="Opponent success",
                        description=f"The opponent team guessed the word **`{move}`** that **belongs to it**",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))

                    if set(first_words) <= set(opened_words):  # If all first_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title="Game over!",
                            description=f"**{first_color} team won!**\nThey opened all their team words",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        
                        await first_cap.send(embed=Embed(
                            title="Your team won!",
                            description="Keep it up!",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title="Your team won!",
                                description="Keep it up!",
                                color=Colors.red if first_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))
                        
                        await second_cap.send(embed=Embed(
                            title="Your team lost!",
                            description="Better luck in the next game!",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title="Your team lost!",
                                description="Better luck in the next game!",
                                color=Colors.red if first_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))

                        game = False
                        break

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await util.send_fields(ctx, first_cap, second_cap)

                word_count -= 1
            
            if not game:  # checking if the game is over after first team move (a crutch for loop check)
                break
            
            gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)
            await util.send_fields(ctx, first_cap, second_cap)
            
            await ctx.send(embed=Embed(
                title="Waiting for move",
                description=f"Captain of **{second_color}** team",
                color=Colors.red if second_color == "RED" else Colors.blue
            ))
            await second_cap.send(embed=Embed(
                title="This is your move turn",
                description=f"Type a word and a number like {'**`animal 3`**' if language=='en' else '**`животное 3`**'} in response message",
                color=Colors.red if second_color == "RED" else Colors.blue
            ))
            move_msg = await self.bot.wait_for("message", check=lambda msg: msg.channel == second_cap.dm_channel and re.fullmatch(r"\w+ \d+", msg.content) and not msg.content.endswith(" 0"))
            move = move_msg.content
            word_count = int(move.split()[-1])
            await second_cap.send(embed=Embed(
                title="Move accepted",
                color=Colors.red if second_color == "RED" else Colors.blue
            ))
            await ctx.send(embed=Embed(
                title=f"Captain of **{second_color}** team moved",
                description=f"The move contains:\n**`{move}`**",
                color=Colors.red if second_color == "RED" else Colors.blue
            ))

            await ctx.send(embed=Embed(
                title="Waiting for move",
                description=f"Players of **{second_color}** team\n\nType words you want to open in response messages.\nIf you want to **BREAK THE MOVE** type **`0`**\nIf you want to **STOP THE GAME** type **`000`**",
                color=Colors.red if second_color == "RED" else Colors.blue
            ))
            while word_count >= 0:  # >= because of the rule that players can open one more word than their captain said
                move_msg = await self.bot.wait_for("message", check=lambda msg: msg.channel == ctx.channel and msg.author in second_pl and (msg.content.lower() in available_words or msg.content in ("0", "000")))
                move = move_msg.content.lower()
                if move == "0":
                    await move_msg.add_reaction("🆗")
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(embed=Embed(
                        title="Stopping the game",
                        description="**Do you really want to stop playing?**\n\nAll players have 15 seconds to vote",
                        color=Colors.red
                    ))
                    
                    upvotes, downvotes = await util.pros_and_cons(stop_msg, 15)
                    if upvotes > downvotes:
                        await ctx.send(embed=Embed(
                            title="GAME STOPPED",
                            description="Most players voted for game stopping",
                            color=Colors.purple
                        ))

                        game = False
                        break
                    else:
                        await ctx.send(embed=Embed(
                            title="GAME CONTINUED",
                            description="Most players voted against game stopping",
                            color=Colors.purple
                        ))
                        
                        continue  # No need to generate a new field or decrease word_count

                opened_words.append(move)
                available_words.remove(move)
                gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)

                if move in other_words:
                    await move_msg.reply(embed=Embed(
                        title="Miss",
                        description="Unfortunately, this word **doesn't belong to any team**",
                        color=Colors.white
                    ))
                    await second_cap.send(embed=Embed(
                        title="Miss",
                        description=f"Your team opened the word **`{move}`** that **doesn't belong to any team**",
                        color=Colors.white
                    ))
                    await first_cap.send(embed=Embed(
                        title="Lucky!",
                        description=f"The opponent team opened the word **`{move}`** that **doesn't belong to any team**",
                        color=Colors.white
                    ))

                    await util.send_fields(ctx, first_cap, second_cap)
                elif move in first_words:
                    await move_msg.reply(embed=Embed(
                        title="Miss",
                        description="Unfortunately, this word **belongs to the opponent team**",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title="Miss",
                        description=f"Your team opened the word **`{move}`** that **belongs to the opponent team**",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title="Lucky!",
                        description=f"The opponent team opened the word **`{move}`** that **belongs to your team**",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))

                    if set(first_words) <= set(opened_words):  # If all first_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title="Game over!",
                            description=f"**{first_color} team won!**\nThey opened all their team words",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        
                        await first_cap.send(embed=Embed(
                            title="Your team won!",
                            description="Keep it up!",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title="Your team won!",
                                description="Keep it up!",
                                color=Colors.red if first_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))
                        
                        await second_cap.send(embed=Embed(
                            title="Your team lost!",
                            description="Better luck in the next game!",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title="Your team lost!",
                                description="Better luck in the next game!",
                                color=Colors.red if first_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed=Embed(
                        title="Miss",
                        description="Unfortunately, this word **is an endgame one**",
                        color=Colors.black
                    ))
                    await second_cap.send(embed=Embed(
                        title="Miss",
                        description=f"Your team opened the word **`{move}`** that **is an endgame one**",
                        color=Colors.black
                    ))
                    await first_cap.send(embed=Embed(
                        title="Lucky!",
                        description=f"The opponent team opened the word **`{move}`** that **is an endgame one**",
                        color=Colors.black
                    ))

                    await util.send_fields(ctx, first_cap, second_cap)
                    
                    await ctx.send(embed=Embed(
                        title="Game over!",
                        description=f"**{first_color} team won!**\n{second_color} team opened an endgame word",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    
                    await first_cap.send(embed=Embed(
                        title="Your team won!",
                        description="Keep it up!",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    await self.db.increase_stats(first_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                    for player in first_pl:
                        await player.send(embed=Embed(
                            title="Your team won!",
                            description="Keep it up!",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games", "wins"))
                    
                    await second_cap.send(embed=Embed(
                        title="Your team lost!",
                        description="Better luck in the next game!",
                        color=Colors.red if first_color == "RED" else Colors.blue
                    ))
                    await self.db.increase_stats(second_cap.id, ("games", "games_cap"))
                    for player in second_pl:
                        await player.send(embed=Embed(
                            title="Your team lost!",
                            description="Better luck in the next game!",
                            color=Colors.red if first_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games",))

                    game = False
                    break
                else:  # They guessed
                    await move_msg.reply(embed=Embed(
                        title="Success",
                        description="You guessed!",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title="Success",
                        description=f"Your team guessed the word **`{move}`** that **belongs to your team**!",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title="Opponent success",
                        description=f"The opponent team guessed the word **`{move}`** that **belongs to opponent's team**",
                        color=Colors.red if second_color == "RED" else Colors.blue
                    ))

                    if set(second_words) <= set(opened_words):  # If all second_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title="Game over!",
                            description=f"**{second_color} team won!**\nThey opened all their team words",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))

                        await first_cap.send(embed=Embed(
                            title="Your team lost!",
                            description="Better luck in the next game!",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title="Your team lost!",
                                description="Better luck in the next game!",
                                color=Colors.red if second_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))
                        
                        await second_cap.send(embed=Embed(
                            title="Your team won!",
                            description="Keep it up!",
                            color=Colors.red if second_color == "RED" else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title="Your team won!",
                                description="Keep it up!",
                                color=Colors.red if second_color == "RED" else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))

                        game = False
                        break

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await util.send_fields(ctx, first_cap, second_cap)

                word_count -= 1

        await self.db.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            ("", "", "", ctx.guild.id)
        )
        
        os.remove(os.path.join("images", f"{ctx.guild.id}-player.png"))
        os.remove(os.path.join("images", f"{ctx.guild.id}-captain.png"))

    @command(aliases=("st", "ss"), help="Shows player's statistics")
    async def stats(self, ctx: Context, member: Member = None) -> None:
        member = member if member else ctx.author
        
        info = await self.db.fetch("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (member.id,))
        if not info:
            await ctx.reply(embed=Embed(
                title="Error",
                description=f"**{member.nick if isinstance(ctx.channel, TextChannel) and member.nick else member.name}** has never played Codenames",
                color=Colors.red
            ))
            return
        games, games_cap, wins, wins_cap = map(int, info)
        games_tm = games - games_cap  # In the team
        wins_tm = wins - wins_cap
        winrate = f"{round((wins / games) * 100)}%" if games else "-"
        winrate_cap = f"{round((wins_cap / games_cap) * 100)}%" if games_cap else "-"
        winrate_tm = f"{round((wins_tm / games_tm) * 100)}%" if games_tm else "-"

        stats_embed = Embed(
            title=f"**{member.nick if isinstance(ctx.channel, TextChannel) and member.nick else member.name}**'s statistics",
            color=Colors.purple
        )
        stats_embed.add_field(name="Total", value=f"Games played: {games}\nGames won: {wins}\nWinrate: {winrate}")
        stats_embed.add_field(name="Captain", value=f"Games played: {games_cap}\nGames won: {wins_cap}\nWinrate: {winrate_cap}")
        stats_embed.add_field(name="Team", value=f"Games played: {games_tm}\nGames won: {wins_tm}\nWinrate: {winrate_tm}")
        stats_embed.add_field(
            name=EMPTY,
            value=f"Codenames is a **team game**, so the winrate statistics do **not** exactly show player's skill",
            inline=False
        )
        stats_embed.set_thumbnail(url=member.avatar_url)

        await ctx.reply(embed=stats_embed)


class SettingCommands(Cog, name="Settings"):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @command(aliases=("pre",), brief="Changes the bot's prefix. Empty prefix -> default", help='Changes the bot\'s prefix.\nIf you wand to set it to default ("cdn") do not input a new prefix')
    @is_moderator()
    async def prefix(self, ctx: Context, new_prefix: str = "cdn") -> None:
        new_prefix = "" if new_prefix == "cdn" else new_prefix
        
        if ctx.guild:
            await self.db.exec_and_commit("UPDATE guilds SET prefix=? WHERE id=?", (new_prefix, ctx.guild.id))
        else:
            await self.db.exec_and_commit("UPDATE players SET prefix=? WHERE id=?", (new_prefix, ctx.author.id))

        await ctx.send(embed=Embed(
            title="Prefix changed",
            description=(f"New prefix:\n**`{new_prefix}`**\n" if new_prefix else "Custom prefix deleted") + "\nDefault one **`cdn`** and bot ping are still valid",
            color=Colors.purple
        ))
    
    @command(aliases=("lang", "loc",), help="Changes the bot's messages language (**EN**/**RU**)")
    @is_moderator()
    async def language(self, ctx: Context) -> None:        
        curr_loc = await self.db.localization(ctx)
        
        msg: Message = await ctx.reply(embed=Embed(
            title="Language settings",
            description=f"**Current language: {curr_loc.upper()} {flags[curr_loc]}**\n\nSelect new language using reactions\n\n_You have 15 seconds_",
            color=Colors.purple
        ))
        for flag in flags.values():
            await msg.add_reaction(flag)
        
        try:
            new_loc: str = flags_rev[
                (await self.bot.wait_for(
                    "reaction_add",
                    timeout=15.0,
                    check=lambda reaction, user: reaction.message == msg and user.id == ctx.author.id and reaction.me
                ))[0].emoji
            ]
        except asyncio.TimeoutError:
            await msg.edit(embed=Embed(
                title="Language settings",
                description="Operation aborted",
                color=Colors.purple
            ))
            await msg.delete(delay=5)
            await ctx.message.delete(delay=5)
            return
        
        if ctx.guild:
            await self.db.exec_and_commit(
                "UPDATE guilds SET localization=? WHERE id=?",
                (new_loc, ctx.guild.id)
            )
        else:
            await self.db.exec_and_commit(
                "UPDATE players SET localization=? WHERE id=?",
                (new_loc, ctx.author.id)
            )
        
        await msg.edit(embed=Embed(
            title="Language settings",
            description=f"**New language: {new_loc.upper()} {flags[new_loc]}**",
            color=Colors.purple
        ))
        if ctx.guild:
            await msg.clear_reactions()


def add_cogs(bot: Bot, db: Database) -> None:
    bot.add_cog(Listeners(bot, db))
    bot.add_cog(GameCommands(bot, db))
    bot.add_cog(SettingCommands(bot, db))
