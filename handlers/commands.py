from discord import Message, TextChannel, Member, Embed, File
from discord.ext.commands import Bot, Context, Cog, command, guild_only
import asyncio
import random
import os
import shutil
import re
from typing import Optional

from handlers.checks import is_moderator
from misc.database import Database
from misc.constants import EMPTY, ALPHABET, REACTION_ALPHABET, REACTION_NUMBERS, dictionaries, flags, flags_rev, Colors
import misc.generation as gen
from misc import util


class GameCog(Cog, name="game"):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @command(aliases=("ready", "reg", "r"))
    @guild_only()
    async def register(self, ctx: Context, team_number: int = 0) -> None:
        loc = await self.db.localization(ctx)
        
        players, team1, team2 = map(
            lambda result: map(int, result.split()),
            await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        )
        players = [await self.bot.fetch_user(id) for id in players]
        team1 = [await self.bot.fetch_user(id) for id in team1]
        team2 = [await self.bot.fetch_user(id) for id in team2]

        if ctx.author in players + team1 + team2:
            if (ctx.author in players and team_number == 0) or \
                    (ctx.author in team1 and team_number == 1) or \
                    (ctx.author in team2 and team_number == 2):
                await util.send_error(ctx, loc.errors.title, loc.errors.already_in_team)
                return
            
            await self.leave(ctx)  # Removing author from any team, then processing main code
            
            # Changes are not visible from this function running
            if ctx.author in players:  # Getting relevant player list again
                players.remove(ctx.author)
            elif ctx.author in team1:
                team1.remove(ctx.author)
            elif ctx.author in team2:
                team2.remove(ctx.author)
        
        if team_number == 0:
            players.append(ctx.author)
        elif team_number == 1:
            team1.append(ctx.author)
        elif team_number == 2:
            team2.append(ctx.author)
        else:
            await util.send_error(ctx, loc.errors.title, loc.errors.invalid_team)
            return

        if ctx.author.id not in map(lambda row: row[0], await self.db.fetch("SELECT id FROM players", fetchall=True)):
            await self.db.exec_and_commit(
                "INSERT INTO players VALUES (?,strftime('%d/%m/%Y','now'),?,?,?,?,?,?)",
                (ctx.author.id, "", "en", 0, 0, 0, 0)
            )

        await ctx.message.add_reaction("✅")
        
        players_id = map(lambda player: str(player.id), players)
        team1_id = map(lambda player: str(player.id), team1)
        team2_id = map(lambda player: str(player.id), team2)
        await self.db.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            (" ".join(players_id), " ".join(team1_id), " ".join(team2_id), ctx.guild.id)
        )

        await ctx.message.delete(delay=3)

    @command(aliases=("unregister", "unreg", "l"))
    @guild_only()
    async def leave(self, ctx: Context) -> None:
        loc = await self.db.localization(ctx)
        
        players, team1, team2 = map(
            lambda result: map(int, result.split()),
            await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        )
        players = [await self.bot.fetch_user(id) for id in players]
        team1 = [await self.bot.fetch_user(id) for id in team1]
        team2 = [await self.bot.fetch_user(id) for id in team2]
        
        if ctx.author not in players + team1 + team2:
            await util.send_error(ctx, loc.errors.title, loc.errors.not_registered)
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

    @command(aliases=("clr", "cl", "c"))
    @guild_only()
    @is_moderator()
    async def clear(self, ctx: Context) -> None:
        await self.db.exec_and_commit(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            ("", "", "", ctx.guild.id)
        )
        
        await ctx.message.add_reaction("✅")
        await ctx.message.delete(delay=3)

    @command(name="players", aliases=("ps", "p"))
    @guild_only()
    async def show_players(self, ctx: Context, final: bool = False) -> None:
        loc = await self.db.localization(ctx)
        
        async with ctx.typing():
            players, team1, team2 = map(
                lambda result: map(int, result.split()),
                await self.db.fetch("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
            )
            players = [await self.bot.fetch_user(id) for id in players]
            team1 = [await self.bot.fetch_user(id) for id in team1]
            team2 = [await self.bot.fetch_user(id) for id in team2]

            players_embed = Embed(
                title=loc.commands.players.final_player_list if final else loc.commands.players.player_list,
                color=Colors.purple
            )
            if team1:
                players_embed.add_field(
                    name=loc.commands.players.team1,
                    value="\n".join(map(lambda p: p.mention, team1))
                )
            if players:
                players_embed.add_field(
                    name=loc.commands.players.no_team,
                    value="\n".join(map(lambda p: p.mention, players))
                )
            if team2:
                players_embed.add_field(
                    name=loc.commands.players.team2,
                    value="\n".join(map(lambda p: p.mention, team2))
                )

            if players or team1 or team2:
                await ctx.reply(embed=players_embed)
            else:
                await ctx.reply(embed=Embed(
                    title=loc.commands.players.player_list,
                    description=loc.commands.players.empty_list,
                    color=Colors.purple
                ))

    @command(aliases=("s",))
    @guild_only()
    async def start(self, ctx: Context) -> None:
        loc = await self.db.localization(ctx)
        
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
                await util.send_error(ctx, loc.errors.title, loc.errors.not_enough_players)
                return
            
            if len(team1) > 25 or len(team2) > 25:
                await util.send_error(ctx, loc.errors.title, loc.errors.too_many_players)
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

        # Dictionary selection
        await ctx.send(embed=Embed(
            title=loc.commands.start.lang_selection_title,
            description=loc.commands.start.lang_selection_desc,
            color=Colors.purple
        ))
        language = await self.bot.wait_for(
            "message",
            check=lambda msg: msg.channel == ctx.channel and
                              msg.author in (team1 + team2) and
                              msg.content.lower() in dictionaries.keys()
        )
        language = language.content.lower()

        dict_msg_desc = map(lambda num, value: f"**{num}** - {value}", range(1, 10), dictionaries[language].values())
        dict_msg = await ctx.send(embed=Embed(
            title=loc.commands.start.dict_selection_title,
            description="{}\n\n{}".format("\n".join(dict_msg_desc), loc.commands.start.dict_selection_desc),
            color=Colors.purple
        ))
        for ind, _ in enumerate(dictionaries[language]):
            await dict_msg.add_reaction(REACTION_NUMBERS[ind])
        await asyncio.sleep(15)

        new_dict_msg = await ctx.channel.fetch_message(dict_msg.id)
        emojis = await util.most_count_reaction_emojis(new_dict_msg, team1 + team2)

        potential_dicts = map(lambda em: tuple(dictionaries[language].keys())[REACTION_NUMBERS.index(em)], emojis)
        game_dict_name = random.choice(tuple(potential_dicts))
        await ctx.send(embed=Embed(
            title=loc.commands.start.dict_selected,
            description=dictionaries[language][game_dict_name],
            color=Colors.purple
        ))

        # Captains selection
        cap_selection_list = map(
            lambda ind, player: f"**{ALPHABET[ind]}** - {player.mention}",
            range(len(team1)), team1
        )
        cap_msg = await ctx.send(embed=Embed(
            title=loc.commands.start.cap_selection_title.format(loc.game.red),
            description=loc.commands.start.cap_selection_desc.format("\n".join(cap_selection_list)),
            color=Colors.red
        ))
        await cap_msg.add_reaction("🇷")
        for ind, _ in enumerate(team1):
            await cap_msg.add_reaction(REACTION_ALPHABET[ind])
        await asyncio.sleep(15)

        # Have to get the message object again with reactions in it
        new_cap_msg = await ctx.channel.fetch_message(cap_msg.id)
        emojis = await util.most_count_reaction_emojis(new_cap_msg, team1)
        
        if "🇷" in emojis:
            team1_cap = random.choice(team1)
        else:
            potential_caps = map(lambda em: team1[REACTION_ALPHABET.index(em)], emojis)
            team1_cap = random.choice(tuple(potential_caps))
        team1_pl = team1.copy()
        team1_pl.remove(team1_cap)

        await ctx.send(embed=Embed(
            title=loc.commands.start.cap_selected_title.format(loc.game.red),
            description=loc.commands.start.cap_selected_desc.format(team1_cap.mention),
            color=Colors.red
        ))

        # The same code for team2_cap
        cap_selection_list = map(
            lambda ind, player: f"**{ALPHABET[ind]}** - {player.mention}",
            range(len(team2)), team2
        )
        msg = await ctx.send(embed=Embed(
            title=loc.commands.start.cap_selection_title.format(loc.game.blue),
            description=loc.commands.start.cap_selection_desc.format("\n".join(cap_selection_list)),
            color=Colors.blue
        ))
        await msg.add_reaction("🇷")
        for ind, _ in enumerate(team2):
            await msg.add_reaction(REACTION_ALPHABET[ind])
        await asyncio.sleep(15)

        # Have to get the message object again with reactions in it
        new_cap_msg = await ctx.channel.fetch_message(cap_msg.id)
        emojis = await util.most_count_reaction_emojis(new_cap_msg, team2)
        
        if "🇷" in emojis:
            team2_cap = random.choice(team2)
        else:
            potential_caps = map(lambda em: team2[REACTION_ALPHABET.index(em)], emojis)
            team2_cap = random.choice(tuple(potential_caps))
        team2_pl = team2.copy()
        team2_pl.remove(team2_cap)

        await ctx.send(embed=Embed(
            title=loc.commands.start.cap_selected_title.format(loc.game.blue),
            description=loc.commands.start.cap_selected_desc.format(team2_cap.mention),
            color=Colors.blue
        ))


        await ctx.send(embed=Embed(
            title=loc.game.start_announcement,
            color=Colors.purple
        ))
        
        # Notifying everyone in direct messages
        await team1_cap.send(embed=Embed(
            title=loc.game.start_notification_title,
            description=loc.game.start_notification_desc_cap.format(
                loc.game.red,
                "\n".join([p.mention for p in team1_pl])
            ),
            color=Colors.red
        ))
        for player in team1_pl:
            team1_pl_without = team1_pl.copy()
            team1_pl_without.remove(player)  # Team1 player list without recipient of the message
            await player.send(embed=Embed(
                title=loc.game.start_notification_title,
                description=loc.game.start_notification_desc_pl.format(
                    loc.game.red,
                    team1_cap.mention,
                    "\n".join([p.mention for p in team1_pl_without])
                ),
                color=Colors.red
            ))
        
        await team2_cap.send(embed=Embed(
            title=loc.game.start_notification_title,
            description=loc.game.start_notification_desc_cap.format(
                loc.game.blue,
                "\n".join([p.mention for p in team2_pl])
            ),
            color=Colors.blue
        ))
        for player in team2_pl:
            team2_pl_without = team2_pl.copy()
            team2_pl_without.remove(player)  # Team2 player list without recipient of the message
            await player.send(embed=Embed(
                title=loc.game.start_notification_title,
                description=loc.game.start_notification_desc_pl.format(
                    loc.game.blue,
                    team2_cap.mention,
                    "\n".join([p.mention for p in team2_pl_without])
                ),
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
            first_color = loc.game.red
            first_cap = team1_cap
            first_pl = team1_pl
            first_words = team1_words
            second_color = loc.game.blue
            second_cap = team2_cap
            second_pl = team2_pl
            second_words = team2_words
        else:
            first_color = loc.game.blue
            first_cap = team2_cap
            first_pl = team2_pl
            first_words = team2_words
            second_color = loc.game.red
            second_cap = team1_cap
            second_pl = team1_pl
            second_words = team1_words

        # Mainloop
        game = True
        first_round = True
        while game:
            gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)
            await util.send_fields(ctx, first_cap, second_cap)

            if first_round:
                shutil.copy(
                    os.path.join("images", f"{ctx.guild.id}-captain.png"),
                    os.path.join("images", f"{ctx.guild.id}-captain-initial.png")
                )
                first_round = False
            
            await ctx.send(embed=Embed(
                title=loc.game.waiting_title,
                description=loc.game.waiting_desc_cap.format(first_color),
                color=Colors.red if first_color == loc.game.red else Colors.blue
            ))
            await first_cap.send(embed=Embed(
                title=loc.game.cap_move_request_title,
                description=loc.game.cap_move_request_desc.format("animal 3" if language == "en" else "животное 3"),
                color=Colors.red if first_color == loc.game.red else Colors.blue
            ))

            move_msg = await self.bot.wait_for(
                "message",
                check=lambda msg: msg.channel == first_cap.dm_channel and
                                  re.fullmatch(r"\w+ \d+", msg.content) and
                                  not msg.content.endswith(" 0")
            )
            move = move_msg.content
            word_count = int(move.split()[-1])

            await first_cap.send(embed=Embed(
                title=loc.game.cap_move_accepted,
                color=Colors.red if first_color == loc.game.red else Colors.blue
            ))
            await ctx.send(embed=Embed(
                title=loc.game.cap_move_notification_title.format(first_color),
                description=loc.game.cap_move_notification_desc.format(move),
                color=Colors.red if first_color == loc.game.red else Colors.blue
            ))

            await ctx.send(embed=Embed(
                title=loc.game.waiting_title,
                description=f"{loc.game.waiting_desc_pl.format(first_color)}\n\n{loc.game.pl_move_instructions}",
                color=Colors.red if first_color == loc.game.red else Colors.blue
            ))
            while word_count >= 0:
                # >= because of the rule that players can open one more word than their captain supposed them to
                move_msg = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel and
                                      msg.author in first_pl and
                                      (msg.content.lower() in available_words or msg.content in ("0", "000"))
                )
                move = move_msg.content.lower()

                if move == "0":
                    await move_msg.add_reaction("🆗")
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(embed=Embed(
                        title=loc.game.voting_for_stopping_title,
                        description=loc.game.voting_for_stopping_desc,
                        color=Colors.purple
                    ))
                    
                    pros, cons = await util.pros_and_cons(stop_msg, 15, team1 + team2)
                    if pros > cons:
                        await ctx.send(embed=Embed(
                            title=loc.game.game_stopped_title,
                            description=loc.game.game_stopped_desc,
                            color=Colors.purple
                        ))

                        game = False
                        break
                    else:
                        await ctx.send(embed=Embed(
                            title=loc.game.game_continued_title,
                            description=loc.game.game_continued_desc,
                            color=Colors.purple
                        ))
                        
                        continue  # No need to generate a new field or decrease word_count
                
                opened_words.append(move)
                available_words.remove(move)
                gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)

                if move in other_words:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_no_team_guild,
                        color=Colors.white
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_no_team_dm.format(move),
                        color=Colors.white
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.opponents_miss_title,
                        description=loc.game.opponents_miss_desc.format(move),
                        color=Colors.white
                    ))

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await util.send_fields(ctx, first_cap, second_cap)
                elif move in second_words:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_other_team_guild,
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_other_team_dm.format(move),
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.lucky_title,
                        description=loc.game.lucky_desc_your_team.format(move),
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))

                    if set(second_words) <= set(opened_words):  # If all second_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title=loc.game.game_over_title,
                            description=loc.game.game_over_desc_all.format(second_color),
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))

                        await first_cap.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_lost_title,
                                description=loc.game.your_team_lost_desc,
                                color=Colors.red if second_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))
                        
                        await second_cap.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_won_title,
                                description=loc.game.your_team_won_desc,
                                color=Colors.red if second_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_endgame_guild,
                        color=Colors.black
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_endgame_dm.format(move),
                        color=Colors.black
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.lucky_title,
                        description=loc.game.lucky_desc_endgame.format(move),
                        color=Colors.black
                    ))

                    await util.send_fields(ctx, first_cap, second_cap)
                    
                    await ctx.send(embed=Embed(
                        title=loc.game.game_over_title,
                        description=loc.game.game_over_desc_endgame.format(second_color, first_color),
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    
                    await first_cap.send(embed=Embed(
                        title=loc.game.your_team_lost_title,
                        description=loc.game.your_team_lost_desc,
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    await self.db.increase_stats(first_cap.id, ("games", "games_cap"))
                    for player in first_pl:
                        await player.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games",))
                    
                    await second_cap.send(embed=Embed(
                        title=loc.game.your_team_won_title,
                        description=loc.game.your_team_won_desc,
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    await self.db.increase_stats(second_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                    for player in second_pl:
                        await player.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games", "wins"))

                    game = False
                    break
                else:  # They guessed
                    await move_msg.reply(embed=Embed(
                        title=loc.game.success_title,
                        description=loc.game.success_desc_guild,
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.success_title,
                        description=loc.game.success_desc_dm.format(move),
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.opponents_success_title,
                        description=loc.game.opponents_success_desc.format(move),
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))

                    if set(first_words) <= set(opened_words):  # If all first_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title=loc.game.game_over_title,
                            description=loc.game.game_over_desc_all.format(first_color),
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        
                        await first_cap.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_won_title,
                                description=loc.game.your_team_won_desc,
                                color=Colors.red if first_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))
                        
                        await second_cap.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_lost_title,
                                description=loc.game.your_team_lost_desc,
                                color=Colors.red if first_color == loc.game.red else Colors.blue
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
                title=loc.game.waiting_title,
                description=loc.game.waiting_desc_cap.format(second_color),
                color=Colors.red if second_color == loc.game.red else Colors.blue
            ))
            await second_cap.send(embed=Embed(
                title=loc.game.cap_move_request_title,
                description=loc.game.cap_move_request_desc.format("animal 3" if language == "en" else "животное 3"),
                color=Colors.red if second_color == loc.game.red else Colors.blue
            ))

            move_msg = await self.bot.wait_for(
                "message",
                check=lambda msg: msg.channel == second_cap.dm_channel and
                                  re.fullmatch(r"\w+ \d+", msg.content) and
                                  not msg.content.endswith(" 0")
            )
            move = move_msg.content
            word_count = int(move.split()[-1])

            await second_cap.send(embed=Embed(
                title=loc.game.cap_move_accepted,
                color=Colors.red if second_color == loc.game.red else Colors.blue
            ))
            await ctx.send(embed=Embed(
                title=loc.game.cap_move_notification_title.format(second_color),
                description=loc.game.cap_move_notification_desc.format(move),
                color=Colors.red if second_color == loc.game.red else Colors.blue
            ))

            await ctx.send(embed=Embed(
                title=loc.game.waiting_title,
                description=f"{loc.game.waiting_desc_pl.format(second_color)}\n\n{loc.game.pl_move_instructions}",
                color=Colors.red if second_color == loc.game.red else Colors.blue
            ))
            while word_count >= 0:
                # >= because of the rule that players can open one more word than their captain said
                move_msg = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel and
                                      msg.author in second_pl and
                                      (msg.content.lower() in available_words or msg.content in ("0", "000"))
                )
                move = move_msg.content.lower()

                if move == "0":
                    await move_msg.add_reaction("🆗")
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(embed=Embed(
                        title=loc.game.voting_for_stopping_title,
                        description=loc.game.voting_for_stopping_desc,
                        color=Colors.purple
                    ))
                    
                    pros, cons = await util.pros_and_cons(stop_msg, 15, team1 + team2)
                    if pros > cons:
                        await ctx.send(embed=Embed(
                            title=loc.game.game_stopped_title,
                            description=loc.game.game_stopped_desc,
                            color=Colors.purple
                        ))

                        game = False
                        break
                    else:
                        await ctx.send(embed=Embed(
                            title=loc.game.game_continued_title,
                            description=loc.game.game_continued_desc,
                            color=Colors.purple
                        ))
                        
                        continue  # No need to generate a new field or decrease word_count

                opened_words.append(move)
                available_words.remove(move)
                gen.field(team1_words, team2_words, endgame_word, other_words, opened_words, order, ctx.guild.id)

                if move in other_words:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_no_team_guild,
                        color=Colors.white
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_no_team_dm.format(move),
                        color=Colors.white
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.opponents_miss_title,
                        description=loc.game.opponents_miss_desc.format(move),
                        color=Colors.white
                    ))

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await util.send_fields(ctx, first_cap, second_cap)
                elif move in first_words:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_other_team_guild,
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_other_team_dm.format(move),
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.lucky_title,
                        description=loc.game.lucky_desc_your_team.format(move),
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))

                    if set(first_words) <= set(opened_words):  # If all first_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title=loc.game.game_over_title,
                            description=loc.game.game_over_desc_all.format(first_color),
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        
                        await first_cap.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_won_title,
                                description=loc.game.your_team_won_desc,
                                color=Colors.red if first_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))
                        
                        await second_cap.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_lost_title,
                                description=loc.game.your_team_lost_desc,
                                color=Colors.red if first_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_endgame_guild,
                        color=Colors.black
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_endgame_dm.format(move),
                        color=Colors.black
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.lucky_title,
                        description=loc.game.lucky_desc_endgame.format(move),
                        color=Colors.black
                    ))

                    await util.send_fields(ctx, first_cap, second_cap)
                    
                    await ctx.send(embed=Embed(
                        title=loc.game.game_over_title,
                        description=loc.game.game_over_desc_endgame.format(first_color, second_color),
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    
                    await first_cap.send(embed=Embed(
                        title=loc.game.your_team_won_title,
                        description=loc.game.your_team_won_desc,
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    await self.db.increase_stats(first_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                    for player in first_pl:
                        await player.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games", "wins"))
                    
                    await second_cap.send(embed=Embed(
                        title=loc.game.your_team_lost_title,
                        description=loc.game.your_team_lost_desc,
                        color=Colors.red if first_color == loc.game.red else Colors.blue
                    ))
                    await self.db.increase_stats(second_cap.id, ("games", "games_cap"))
                    for player in second_pl:
                        await player.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if first_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(player.id, ("games",))

                    game = False
                    break
                else:  # They guessed
                    await move_msg.reply(embed=Embed(
                        title=loc.game.success_title,
                        description=loc.game.success_desc_guild,
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    await second_cap.send(embed=Embed(
                        title=loc.game.success_title,
                        description=loc.game.success_desc_dm.format(move),
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))
                    await first_cap.send(embed=Embed(
                        title=loc.game.opponents_success_title,
                        description=loc.game.opponents_success_desc.format(move),
                        color=Colors.red if second_color == loc.game.red else Colors.blue
                    ))

                    if set(second_words) <= set(opened_words):  # If all second_words are opened
                        await util.send_fields(ctx, first_cap, second_cap)
                        
                        await ctx.send(embed=Embed(
                            title=loc.game.game_over_title,
                            description=loc.game.game_over_desc_all.format(second_color),
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))

                        await first_cap.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(first_cap.id, ("games", "games_cap"))
                        for player in first_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_lost_title,
                                description=loc.game.your_team_lost_desc,
                                color=Colors.red if second_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games",))
                        
                        await second_cap.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if second_color == loc.game.red else Colors.blue
                        ))
                        await self.db.increase_stats(second_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in second_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_won_title,
                                description=loc.game.your_team_won_desc,
                                color=Colors.red if second_color == loc.game.red else Colors.blue
                            ))
                            await self.db.increase_stats(player.id, ("games", "wins"))

                        game = False
                        break

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await util.send_fields(ctx, first_cap, second_cap)

                word_count -= 1

        # Sending initial captain filed to the guild text channel
        with open(os.path.join("images", f"{ctx.guild.id}-captain-initial.png"), "rb") as init_cap_field_bin:
            init_cap_field = File(init_cap_field_bin, filename="initial_captain_field.png")
            await ctx.send(file=init_cap_field)

        await self.db.exec_and_commit(
            "UPDATE guilds SET team1=?, team2=? WHERE id=?",
            ("", "", ctx.guild.id)
        )
        
        os.remove(os.path.join("images", f"{ctx.guild.id}-player.png"))
        os.remove(os.path.join("images", f"{ctx.guild.id}-captain.png"))
        os.remove(os.path.join("images", f"{ctx.guild.id}-captain-initial.png"))

    @command(aliases=("stat", "ss", "st"))
    async def stats(self, ctx: Context, member: Optional[Member] = None) -> None:
        member = member or ctx.author
        name = f"**{member.nick if isinstance(ctx.channel, TextChannel) and member.nick else member.name}**"
        
        loc = await self.db.localization(ctx)
        
        info = await self.db.fetch(
            "SELECT date, games, games_cap, wins, wins_cap FROM players WHERE id=?",
            (member.id,)
        )
        if not info:
            await util.send_error(ctx, loc.errors.title, loc.errors.never_played.format(name))
            return

        # noinspection PyTupleAssignmentBalance
        date, games, games_cap, wins, wins_cap = info[0], *map(int, info[1:])
        games_tm = games - games_cap  # In the team
        wins_team = wins - wins_cap
        winrate = f"{round((wins / games) * 100)}%" if games else "-"
        winrate_cap = f"{round((wins_cap / games_cap) * 100)}%" if games_cap else "-"
        winrate_team = f"{round((wins_team / games_tm) * 100)}%" if games_tm else "-"

        stats_embed = Embed(
            title=loc.commands.stats.smbs_stats.format(name),
            description=loc.commands.stats.playing_since.format(f"**{date}**"),
            color=Colors.purple
        )
        stats_embed.add_field(
            name=loc.commands.stats.total,
            value=f"{loc.commands.stats.games_played}: **{games}**\n{loc.commands.stats.games_won}: **{wins}**"
                  f"\n{loc.commands.stats.winrate}: **{winrate}**"
        )
        stats_embed.add_field(
            name=loc.commands.stats.team,
            value=f"{loc.commands.stats.games_played}: **{games_tm}**\n{loc.commands.stats.games_won}: **{wins_team}**"
                  f"\n{loc.commands.stats.winrate}: **{winrate_team}**"
        )
        stats_embed.add_field(
            name=loc.commands.stats.captain,
            value=f"{loc.commands.stats.games_played}: **{games_cap}**\n{loc.commands.stats.games_won}: **{wins_cap}**"
                  f"\n{loc.commands.stats.winrate}: **{winrate_cap}**"
        )
        
        stats_embed.add_field(
            name=EMPTY,
            value=loc.commands.stats.note,
            inline=False
        )
        stats_embed.set_thumbnail(url=member.avatar_url)

        await ctx.reply(embed=stats_embed)


class SettingCog(Cog, name="settings"):
    def __init__(self, bot: Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    @command(aliases=("pre",))
    @is_moderator()
    async def prefix(self, ctx: Context, new_prefix: str = "cdn") -> None:
        new_prefix = "" if new_prefix == "cdn" else new_prefix

        loc = await self.db.localization(ctx)
        
        if ctx.guild:
            await self.db.exec_and_commit("UPDATE guilds SET prefix=? WHERE id=?", (new_prefix, ctx.guild.id))
        else:
            await self.db.exec_and_commit("UPDATE players SET prefix=? WHERE id=?", (new_prefix, ctx.author.id))

        await ctx.send(embed=Embed(
            title=loc.commands.prefix.prefix_changed_title,
            description=loc.commands.prefix.prefix_changed_desc.format(
                loc.commands.prefix.new_prefix.format(new_prefix) if new_prefix else loc.commands.prefix.prefix_deleted
            ),
            color=Colors.purple
        ))
    
    @command(aliases=("lang",))
    @is_moderator()
    async def language(self, ctx: Context) -> None:
        loc = await self.db.localization(ctx)

        if ctx.guild:
            current_loc = (await self.db.fetch("SELECT localization FROM guilds WHERE id=?", (ctx.guild.id,)))[0]
        else:
            current_loc = (await self.db.fetch("SELECT localization FROM players WHERE id=?", (ctx.author.id,)))[0]
        
        msg: Message = await ctx.reply(embed=Embed(
            title=loc.commands.language.title,
            description=loc.commands.language.desc_current.format(current_loc.upper(), flags[current_loc]),
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
                title=loc.commands.language.title,
                description=loc.commands.language.desc_aborted,
                color=Colors.red
            ))
            await msg.delete(delay=7)
            await ctx.message.delete(delay=7)
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

        loc = await self.db.localization(ctx)
        
        await msg.edit(embed=Embed(
            title=loc.commands.language.title,
            description=loc.commands.language.desc_new.format(new_loc.upper(), flags[new_loc]),
            color=Colors.purple
        ))
        if ctx.guild:
            await msg.clear_reactions()


def add_commands(bot: Bot, db: Database) -> None:
    bot.add_cog(GameCog(bot, db))
    bot.add_cog(SettingCog(bot, db))
