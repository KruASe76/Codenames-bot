import asyncio
import os
import random
import re
import shutil

from discord import Member, Embed, File
from discord.ext.commands import Context, Cog, hybrid_command, guild_only
from discord.app_commands import describe, locale_str

from bot import CodenamesBot
from handlers.checks import is_moderator
from misc.util import send_error, send_fields, most_count_reaction_emojis, pros_and_cons
import misc.generation as gen
from misc.constants import (
    EMPTY, ALPHABET, REACTION_ALPHABET, REACTION_R, REACTION_NUMBERS, flags_rev, dictionaries, Paths, Colors
)


class GameCog(Cog, name="game"):
    def __init__(self, bot: CodenamesBot) -> None:
        self.bot = bot

    @hybrid_command(aliases=("ready", "reg", "r"), description=locale_str("register"))
    @describe(team_number=locale_str("register_team_number_param"))
    @guild_only()
    async def register(self, ctx: Context, team_number: int = 0) -> None:
        loc = await self.bot.db.localization(ctx)

        if team_number == 34:  # easter egg
            r34_embed = Embed(
                title=loc.commands.register.egg_r34_title,
                description=loc.commands.register.egg_r34_desc,
                color=Colors.red
            )

            if ctx.interaction:
                await ctx.interaction.response.send_message(embed=r34_embed, ephemeral=True)
            else:
                await ctx.reply(embed=r34_embed, delete_after=7)
                await ctx.message.delete(delay=7)
            return

        if team_number not in range(3):
            await send_error(ctx, loc.errors.title, loc.errors.invalid_team)
            return
        
        no_team, team1, team2 = await self.bot.db.fetch_teams(ctx)

        if ctx.author in no_team + team1 + team2:
            if (ctx.author in no_team and team_number == 0) or \
                    (ctx.author in team1 and team_number == 1) or \
                    (ctx.author in team2 and team_number == 2):
                await send_error(ctx, loc.errors.title, loc.errors.already_in_team)
                return
            
            # Changes are not visible from this function running
            if ctx.author in no_team:  # Getting relevant player list again
                no_team.remove(ctx.author)
            elif ctx.author in team1:
                team1.remove(ctx.author)
            elif ctx.author in team2:
                team2.remove(ctx.author)
        
        if team_number == 0:
            no_team.append(ctx.author)
        elif team_number == 1:
            team1.append(ctx.author)
        elif team_number == 2:
            team2.append(ctx.author)

        if ctx.author.id not in map(
            lambda row: row[0],
            await self.bot.db.fetch("SELECT id FROM players", fetchall=True)
        ):
            await self.bot.db.exec_and_commit(
                "INSERT INTO players VALUES (?,strftime('%d/%m/%Y','now'),?,?,?,?,?,?)",
                (ctx.author.id, "", "en", 0, 0, 0, 0)
            )

        if ctx.interaction:
            await ctx.interaction.response.send_message("✅", ephemeral=True)
        else:
            await ctx.message.add_reaction("✅")
            await ctx.message.delete(delay=3)

        await self.bot.db.save_teams(ctx, no_team, team1, team2)

    @hybrid_command(aliases=("unregister", "unreg", "l"), description=locale_str("leave"))
    @guild_only()
    async def leave(self, ctx: Context) -> None:
        loc = await self.bot.db.localization(ctx)
        
        no_team, team1, team2 = await self.bot.db.fetch_teams(ctx)
        
        if ctx.author not in no_team + team1 + team2:
            await send_error(ctx, loc.errors.title, loc.errors.not_registered)
            return

        if ctx.author in no_team:
            no_team.remove(ctx.author)
        elif ctx.author in team1:
            team1.remove(ctx.author)
        elif ctx.author in team2:
            team2.remove(ctx.author)

        if ctx.interaction:
            await ctx.send("✅", ephemeral=True)
        else:
            await ctx.message.add_reaction("✅")
            await ctx.message.delete(delay=3)

        await self.bot.db.save_teams(ctx, no_team, team1, team2)

    @hybrid_command(aliases=("clr", "cl", "c"), description=locale_str("clear"))
    @guild_only()
    @is_moderator()
    async def clear(self, ctx: Context) -> None:
        await self.bot.db.save_teams(ctx, [], [], [])

        if ctx.interaction:
            await ctx.interaction.response.send_message("✅", ephemeral=True)
        else:
            await ctx.message.add_reaction("✅")
            await ctx.message.delete(delay=3)

    @hybrid_command(name="no_team", aliases=("ps", "p"), description=locale_str("no_team"))
    @guild_only()
    async def show_players(self, ctx: Context) -> None:
        final = ctx.command == self.start

        loc = await self.bot.db.localization(ctx)
        
        async with ctx.typing():
            no_team, team1, team2 = await self.bot.db.fetch_teams(ctx)

            if no_team or team1 or team2:
                players_embed = Embed(
                    title=loc.commands.players.final_player_list if final else loc.commands.players.player_list,
                    color=Colors.purple
                )

                if team1:
                    players_embed.add_field(
                        name=loc.commands.players.team1,
                        value="\n".join(map(lambda p: p.mention, team1))
                    )
                if no_team:
                    players_embed.add_field(
                        name=loc.commands.players.no_team,
                        value="\n".join(map(lambda p: p.mention, no_team))
                    )
                if team2:
                    players_embed.add_field(
                        name=loc.commands.players.team2,
                        value="\n".join(map(lambda p: p.mention, team2))
                    )

                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=players_embed)
                else:
                    await ctx.reply(embed=players_embed)
            else:
                nobody_ready_embed = Embed(
                    title=loc.commands.players.player_list,
                    description=loc.commands.players.empty_list,
                    color=Colors.purple
                )

                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=nobody_ready_embed)
                else:
                    await ctx.reply(embed=nobody_ready_embed)

    @hybrid_command(aliases=("s",), description=locale_str("start"))
    @guild_only()
    async def start(self, ctx: Context) -> None:
        loc = await self.bot.db.localization(ctx)
        
        # Final player list preparation and show
        no_team, team1, team2 = await self.bot.db.fetch_teams(ctx)

        random.shuffle(no_team)
        for member in no_team:  # Dividing no_team into two teams randomly
            if len(team1) <= len(team2):
                team1.append(member)
            else:
                team2.append(member)

        if len(team1) < 2 or len(team2) < 2:
            await send_error(ctx, loc.errors.title, loc.errors.not_enough_players)
            return

        if len(team1) > 25 or len(team2) > 25:
            await send_error(ctx, loc.errors.title, loc.errors.too_many_players)
            return

        await self.bot.db.save_teams(ctx, [], team1, team2)

        await self.show_players(ctx)

        await asyncio.sleep(1)

        # Dictionary selection
        language_msg = await ctx.send(embed=Embed(
            title=loc.commands.start.lang_selection_title,
            color=Colors.purple
        ))
        for flag in flags_rev.keys():
            await language_msg.add_reaction(flag)

        language: str = flags_rev[
            (await self.bot.wait_for(
                "reaction_add",
                check=lambda reaction, user: reaction.message == language_msg and
                                             user.id == ctx.author.id and
                                             reaction.me
            ))[0].emoji
        ]

        dict_msg_desc = map(lambda num, value: f"**{num}** - {value}", range(1, 10), dictionaries[language].values())
        dict_msg = await ctx.send(embed=Embed(
            title=loc.commands.start.dict_selection_title,
            description="{}\n\n{}".format("\n".join(dict_msg_desc), loc.commands.start.dict_selection_desc),
            color=Colors.purple
        ))
        for r_num in REACTION_NUMBERS[:len(dictionaries[language])]:
            await dict_msg.add_reaction(r_num)
        await asyncio.sleep(15)

        new_dict_msg = await ctx.fetch_message(dict_msg.id)
        emojis = await most_count_reaction_emojis(new_dict_msg, team1 + team2)

        potential_dicts = map(lambda e: tuple(dictionaries[language].keys())[REACTION_NUMBERS.index(e)], emojis)
        game_dict_name = random.choice(tuple(potential_dicts))
        await ctx.send(embed=Embed(
            title=loc.commands.start.dict_selected,
            description=dictionaries[language][game_dict_name],
            color=Colors.purple
        ))

        # Captains selection
        cap_selection_list = map(
            lambda letter, player: f"**{letter}** - {player.mention}",
            ALPHABET, team1
        )
        cap_msg = await ctx.send(embed=Embed(
            title=loc.commands.start.cap_selection_title.format(loc.game.red),
            description=loc.commands.start.cap_selection_desc.format("\n".join(cap_selection_list)),
            color=Colors.red
        ))
        await cap_msg.add_reaction(REACTION_R)
        for r_letter in REACTION_ALPHABET[:len(team1)]:
            await cap_msg.add_reaction(r_letter)
        await asyncio.sleep(15)

        # Have to get the message object again with reactions in it
        new_cap_msg = await ctx.fetch_message(cap_msg.id)
        emojis = await most_count_reaction_emojis(new_cap_msg, team1)
        
        if REACTION_R in emojis:
            team1_cap = random.choice(team1)
        else:
            potential_caps = map(lambda e: team1[REACTION_ALPHABET.index(e)], emojis)
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
            lambda letter, player: f"**{letter}** - {player.mention}",
            ALPHABET, team2
        )
        cap_msg = await ctx.send(embed=Embed(
            title=loc.commands.start.cap_selection_title.format(loc.game.blue),
            description=loc.commands.start.cap_selection_desc.format("\n".join(cap_selection_list)),
            color=Colors.blue
        ))
        await cap_msg.add_reaction(REACTION_R)
        for r_letter in REACTION_ALPHABET[:len(team2)]:
            await cap_msg.add_reaction(r_letter)
        await asyncio.sleep(15)

        # Have to get the message object again with reactions in it
        new_cap_msg = await ctx.fetch_message(cap_msg.id)
        emojis = await most_count_reaction_emojis(new_cap_msg, team2)
        
        if REACTION_R in emojis:
            team2_cap = random.choice(team2)
        else:
            potential_caps = map(lambda e: team2[REACTION_ALPHABET.index(e)], emojis)
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
                "\n".join(map(lambda p: p.mention, team1_pl))
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
                    "\n".join(map(lambda p: p.mention, team1_pl_without))
                ),
                color=Colors.red
            ))
        
        await team2_cap.send(embed=Embed(
            title=loc.game.start_notification_title,
            description=loc.game.start_notification_desc_cap.format(
                loc.game.blue,
                "\n".join(map(lambda p: p.mention, team2_pl))
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
                    "\n".join(map(lambda p: p.mention, team2_pl_without))
                ),
                color=Colors.blue
            ))

        team1_words, team2_words, endgame_word, no_team_words = gen.words(
            lang=language, dict_name=game_dict_name
        )
        opened_words = []
        available_words = list(team1_words + team2_words + (endgame_word,) + no_team_words)  # endgame_word is single
        order = available_words.copy()  # Has to be a list
        random.shuffle(order)
        order = tuple(order)

        if len(team1_words) > len(team2_words):
            current_color = loc.game.red
            current_cap = team1_cap
            current_pl = team1_pl
            current_words = team1_words
            other_color = loc.game.blue
            other_cap = team2_cap
            other_pl = team2_pl
            other_words = team2_words
        else:
            current_color = loc.game.blue
            current_cap = team2_cap
            current_pl = team2_pl
            current_words = team2_words
            other_color = loc.game.red
            other_cap = team1_cap
            other_pl = team1_pl
            other_words = team1_words

        # Mainloop
        game = True
        first_round = True
        while game:
            gen.field(team1_words, team2_words, endgame_word, no_team_words, opened_words, order, ctx.guild.id)
            await send_fields(ctx, current_cap, other_cap)

            if first_round:
                shutil.copy(
                    Paths.cap_img(ctx.guild.id),
                    Paths.cap_img_init(ctx.guild.id)
                )
                first_round = False
            
            await ctx.send(embed=Embed(
                title=loc.game.waiting_title,
                description=loc.game.waiting_desc_cap.format(current_color),
                color=Colors.red if current_color == loc.game.red else Colors.blue
            ))
            await current_cap.send(embed=Embed(
                title=loc.game.cap_move_request_title,
                description=loc.game.cap_move_request_desc.format("animal 3" if language == "en" else "животное 3"),
                color=Colors.red if current_color == loc.game.red else Colors.blue
            ))

            move_msg = await self.bot.wait_for(
                "message",
                check=lambda msg: msg.channel == current_cap.dm_channel and
                                  re.fullmatch(r"\w+ \d+", msg.content) and
                                  not msg.content.endswith(" 0")
            )
            move = move_msg.content
            word_count = int(move.split()[-1])

            await current_cap.send(embed=Embed(
                title=loc.game.cap_move_accepted,
                color=Colors.red if current_color == loc.game.red else Colors.blue
            ))
            await ctx.send(embed=Embed(
                title=loc.game.cap_move_notification_title.format(current_color),
                description=loc.game.cap_move_notification_desc.format(move),
                color=Colors.red if current_color == loc.game.red else Colors.blue
            ))

            await ctx.send(embed=Embed(
                title=loc.game.waiting_title,
                description=f"{loc.game.waiting_desc_pl.format(current_color)}\n\n{loc.game.pl_move_instructions}",
                color=Colors.red if current_color == loc.game.red else Colors.blue
            ))
            while word_count >= 0:
                # >= because of the rule that no_team can open one more word than their captain supposed them to
                move_msg = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel and
                                      msg.author in current_pl and
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
                    
                    pros, cons = await pros_and_cons(stop_msg, 15, team1 + team2)
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
                gen.field(team1_words, team2_words, endgame_word, no_team_words, opened_words, order, ctx.guild.id)

                if move in no_team_words:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_no_team_guild,
                        color=Colors.white
                    ))
                    await current_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_no_team_dm.format(move),
                        color=Colors.white
                    ))
                    await other_cap.send(embed=Embed(
                        title=loc.game.opponents_miss_title,
                        description=loc.game.opponents_miss_desc.format(move),
                        color=Colors.white
                    ))

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await send_fields(ctx, current_cap, other_cap)
                elif move in other_words:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_other_team_guild,
                        color=Colors.red if other_color == loc.game.red else Colors.blue
                    ))
                    await current_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_other_team_dm.format(move),
                        color=Colors.red if other_color == loc.game.red else Colors.blue
                    ))
                    await other_cap.send(embed=Embed(
                        title=loc.game.lucky_title,
                        description=loc.game.lucky_desc_your_team.format(move),
                        color=Colors.red if other_color == loc.game.red else Colors.blue
                    ))

                    if set(other_words) <= set(opened_words):  # If all second_words are opened
                        await send_fields(ctx, current_cap, other_cap)
                        
                        await ctx.send(embed=Embed(
                            title=loc.game.game_over_title,
                            description=loc.game.game_over_desc_all.format(other_color),
                            color=Colors.red if other_color == loc.game.red else Colors.blue
                        ))

                        await current_cap.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if other_color == loc.game.red else Colors.blue
                        ))
                        await self.bot.db.increase_stats(current_cap.id, ("games", "games_cap"))
                        for player in current_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_lost_title,
                                description=loc.game.your_team_lost_desc,
                                color=Colors.red if other_color == loc.game.red else Colors.blue
                            ))
                            await self.bot.db.increase_stats(player.id, ("games",))
                        
                        await other_cap.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if other_color == loc.game.red else Colors.blue
                        ))
                        await self.bot.db.increase_stats(other_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in other_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_won_title,
                                description=loc.game.your_team_won_desc,
                                color=Colors.red if other_color == loc.game.red else Colors.blue
                            ))
                            await self.bot.db.increase_stats(player.id, ("games", "wins"))

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_endgame_guild,
                        color=Colors.black
                    ))
                    await current_cap.send(embed=Embed(
                        title=loc.game.miss_title,
                        description=loc.game.miss_desc_endgame_dm.format(move),
                        color=Colors.black
                    ))
                    await other_cap.send(embed=Embed(
                        title=loc.game.lucky_title,
                        description=loc.game.lucky_desc_endgame.format(move),
                        color=Colors.black
                    ))

                    await send_fields(ctx, current_cap, other_cap)
                    
                    await ctx.send(embed=Embed(
                        title=loc.game.game_over_title,
                        description=loc.game.game_over_desc_endgame.format(other_color, current_color),
                        color=Colors.red if other_color == loc.game.red else Colors.blue
                    ))
                    
                    await current_cap.send(embed=Embed(
                        title=loc.game.your_team_lost_title,
                        description=loc.game.your_team_lost_desc,
                        color=Colors.red if other_color == loc.game.red else Colors.blue
                    ))
                    await self.bot.db.increase_stats(current_cap.id, ("games", "games_cap"))
                    for player in current_pl:
                        await player.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if other_color == loc.game.red else Colors.blue
                        ))
                        await self.bot.db.increase_stats(player.id, ("games",))
                    
                    await other_cap.send(embed=Embed(
                        title=loc.game.your_team_won_title,
                        description=loc.game.your_team_won_desc,
                        color=Colors.red if other_color == loc.game.red else Colors.blue
                    ))
                    await self.bot.db.increase_stats(other_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                    for player in other_pl:
                        await player.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if other_color == loc.game.red else Colors.blue
                        ))
                        await self.bot.db.increase_stats(player.id, ("games", "wins"))

                    game = False
                    break
                else:  # They guessed
                    await move_msg.reply(embed=Embed(
                        title=loc.game.success_title,
                        description=loc.game.success_desc_guild,
                        color=Colors.red if current_color == loc.game.red else Colors.blue
                    ))
                    await current_cap.send(embed=Embed(
                        title=loc.game.success_title,
                        description=loc.game.success_desc_dm.format(move),
                        color=Colors.red if current_color == loc.game.red else Colors.blue
                    ))
                    await other_cap.send(embed=Embed(
                        title=loc.game.opponents_success_title,
                        description=loc.game.opponents_success_desc.format(move),
                        color=Colors.red if current_color == loc.game.red else Colors.blue
                    ))

                    if set(current_words) <= set(opened_words):  # If all first_words are opened
                        await send_fields(ctx, current_cap, other_cap)
                        
                        await ctx.send(embed=Embed(
                            title=loc.game.game_over_title,
                            description=loc.game.game_over_desc_all.format(current_color),
                            color=Colors.red if current_color == loc.game.red else Colors.blue
                        ))
                        
                        await current_cap.send(embed=Embed(
                            title=loc.game.your_team_won_title,
                            description=loc.game.your_team_won_desc,
                            color=Colors.red if current_color == loc.game.red else Colors.blue
                        ))
                        await self.bot.db.increase_stats(current_cap.id, ("games", "games_cap", "wins", "wins_cap"))
                        for player in current_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_won_title,
                                description=loc.game.your_team_won_desc,
                                color=Colors.red if current_color == loc.game.red else Colors.blue
                            ))
                            await self.bot.db.increase_stats(player.id, ("games", "wins"))
                        
                        await other_cap.send(embed=Embed(
                            title=loc.game.your_team_lost_title,
                            description=loc.game.your_team_lost_desc,
                            color=Colors.red if current_color == loc.game.red else Colors.blue
                        ))
                        await self.bot.db.increase_stats(other_cap.id, ("games", "games_cap"))
                        for player in other_pl:
                            await player.send(embed=Embed(
                                title=loc.game.your_team_lost_title,
                                description=loc.game.your_team_lost_desc,
                                color=Colors.red if current_color == loc.game.red else Colors.blue
                            ))
                            await self.bot.db.increase_stats(player.id, ("games",))

                        game = False
                        break

                    if word_count > 0:  # If quitting after this move, field will be sent twice in a row
                        await send_fields(ctx, current_cap, other_cap)

                word_count -= 1
            
            current_color, other_color = other_color, current_color
            current_cap, other_cap = other_cap, current_cap
            current_pl, other_pl = other_pl, current_pl
            current_words, other_words = other_words, current_words

        # Sending initial captain filed to the guild text channel
        initial_cap_field = File(Paths.cap_img_init(ctx.guild.id), filename="initial_captain_field.png")
        await ctx.send(file=initial_cap_field)

        await self.bot.db.save_teams(ctx, [], [], [])
        
        os.remove(Paths.pl_img(ctx.guild.id))
        os.remove(Paths.cap_img(ctx.guild.id))
        os.remove(Paths.cap_img_init(ctx.guild.id))

    @hybrid_command(aliases=("stat", "ss", "st"), description=locale_str("stats"))
    @describe(member=locale_str("stats_member_param"), show=locale_str("stats_show_param"))
    async def stats(self, ctx: Context, member: Member | None = None, show: bool = False) -> None:
        member = member or ctx.author
        name = f"**{member.display_name}**"
        
        loc = await self.bot.db.localization(ctx)

        if member == self.bot.user:
            game_master_embed = Embed(
                title=loc.commands.stats.smbs_stats.format(name),
                description=loc.commands.stats.egg_game_master_desc,
                color=Colors.purple
            )

            if ctx.interaction:
                await ctx.interaction.response.send_message(embed=game_master_embed, ephemeral=not show)
            else:
                await ctx.reply(embed=game_master_embed)

            return
        
        info = await self.bot.db.fetch(
            "SELECT date, games, games_cap, wins, wins_cap FROM players WHERE id=?",
            (member.id,)
        )
        if not info:
            await send_error(ctx, loc.errors.title, loc.errors.never_played.format(name))
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
        stats_embed.set_thumbnail(url=member.display_avatar)

        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=stats_embed, ephemeral=not show)
        else:
            await ctx.reply(embed=stats_embed)


async def setup(bot: CodenamesBot) -> None:
    await bot.add_cog(GameCog(bot))
