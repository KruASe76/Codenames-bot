import discord
from discord.ext import commands
import os, sqlite3, dotenv, inspect, asyncio, re, random
import generation as gen

# Setting defaults
LOGO_LINK = "https://cdn.discordapp.com/attachments/797224818763104317/845081822329176114/codenames_logo.jpg"

ALPHABET = "ABCDEFGHIJKLMNOPQSTUVWXYZ" # Without letter R
REACTION_ALPHABET = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇸🇹🇺🇻🇼🇽🇾🇿" # Without R too
REACTION_NUMBERS = "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣"

# Getting the database
base = sqlite3.connect(os.path.join(os.getcwd(), "base.db"))
cursor = base.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS guilds (id int primary key, prefix text, players text, team1 text, team2 text, dark null)")
cursor.execute("CREATE TABLE IF NOT EXISTS players (id int primary key, games int, games_cap int, wins int, wins_cap int)")
base.commit()

# Creating bot
def get_prefix(bot, message):
    if message.guild:
        cursor.execute("SELECT prefix FROM guilds WHERE id=?", (message.guild.id,))
        prefix = cursor.fetchone()[0]
        res = (prefix, "cdn") if prefix else ("cdn",)
    else:
        res = ("cdn", "!", "/", "-")
    
    return commands.when_mentioned_or(*res)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, help_command=None, strip_after_prefix=True, owner_ids=(689766059712315414, 790535470870298642))

# Checks
is_moderator = commands.check(lambda ctx: ctx.message.author.permissions_in(ctx.channel).manage_messages or bot.is_owner(ctx.message.author))

# Some useful functions
def get_most_count_reaction_emojis(msg):
    filt_reactions = tuple(filter(lambda r: r.me, msg.reactions))
    max_count = max(filt_reactions, key=lambda r: r.count).count
    max_reactions = tuple(filter(lambda r: r.count == max_count, filt_reactions))
    return tuple(map(lambda r: r.emoji, max_reactions))

async def pros_and_cons(msg, delay):
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await asyncio.sleep(delay)

    new_msg = await msg.channel.fetch_message(msg.id) # Have to get the message object again with reactions in it
    reactions = filter(lambda r: r.emoji in "👍👎", new_msg.reactions)
    for reaction in reactions:
        if reaction.emoji == "👍":
            upvotes = reaction.count
        else:
            downvotes = reaction.count
    
    return upvotes, downvotes

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Activity(type=discord.ActivityType.watching, name="codenames.me"))

@bot.event
async def on_message(message):
    if message.content.strip() == f"<@!{bot.user.id}>":
        help_comm = bot.get_command("help")
        await help_comm.__call__(await bot.get_context(message))
    
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.add_reaction("❔")
        await ctx.message.delete(delay=3)
    elif isinstance(error, commands.CheckFailure):
        await ctx.reply(embed = discord.Embed(
            title = "You have no permission to call this command",
            colour = discord.Colour(int("ff6450", 16))
        ))
    else:
        raise error

@bot.event
async def on_guild_join(guild):
    cursor.execute("INSERT INTO guilds VALUES (?,?,?,?,?,?)", (guild.id, "", "", "", "", False))
    base.commit()

@bot.event
async def on_guild_remove(guild):
    cursor.execute("DELETE FROM guilds WHERE id=?", (guild.id,))
    base.commit()

# Help
@bot.command()
async def help(ctx, command=None):
    prefix = ctx.message.content.split("help")[0] # Getting a prefix used when calling
    prefix = "cdn " if prefix.strip() == f"<@!{bot.user.id}>" else prefix

    if command:
        comm = bot.get_command(command)
        if not comm:
            title = "Error"
            desc = "Command not found"
            col = discord.Colour(int("ff6450", 16))
        else:
            title = comm.cog_name[:-1] # Removing "..s" to get not plural, but singular
            col = discord.Colour(int("8d08d2", 16))

            comm_info = inspect.getfullargspec(comm._callback)
            arg_list = comm_info.args[2:] # Removing "self" and "ctx"
            default_args = comm_info.defaults if comm_info.defaults else ()
            names = (comm.name,) + comm.aliases
            name = "{" + "|".join(names) + "}"
            args = []
            while len(arg_list) > len(default_args):
                args.append(f"<{arg_list[0]}>")
                arg_list.pop(0)
            for ind, arg in enumerate(arg_list):
                if arg == "final":
                    continue
                def_arg = default_args[ind]
                if def_arg:
                    if not def_arg.isdigit():
                        def_arg = f'"{def_arg}"' # String type defaults stylization
                else:
                    def_arg = None
                args.append(f"[{arg}={def_arg}]")
            allowed1 = "**[Moderator]**\n" if is_moderator.predicate.__wrapped__ in comm.checks else ""
            allowed2 = "\n\n_**Note:**\nModerator is the member who can manage messages in the channel where the command was called_"
            desc = f"**`{prefix}{name}{' ' if args else ''}{' '.join(args)}`**\n\n{allowed1}{comm.help}{allowed2}"

        help_embed = discord.Embed(
            title = title,
            description = desc,
            colour = col
        )
    else:
        help_embed = discord.Embed(
            title = "Command list",
            colour = discord.Colour(int("8d08d2", 16))
        )
        help_embed.set_thumbnail(url = LOGO_LINK)

        for cog_name, cog in bot.cogs.items():
            allowed = lambda comm: "**[Mod]** " if is_moderator.predicate.__wrapped__ in comm.checks else ""
            cog_comms = map(lambda comm: f"**`{prefix}{comm.name}`** - {allowed(comm)}{comm.brief if comm.brief else comm.help}", cog.get_commands())
            help_embed.add_field(name=cog_name, value="\n".join(cog_comms), inline=False)
        
        help_embed.add_field(
            name = chr(int("2063", 16)),
            value = f"**To learn a more detailed description of the command, type**\n**`{prefix}help [command]`**",
            inline = False
        )

    await ctx.reply(embed = help_embed)

# Cogs
class GameCommands(commands.Cog, name = "Game Commands"):
    """They are used to play (wow, so unpredictable)"""
    def __init__(self, bot:commands.Bot):
        self.bot = bot
    
    @commands.command(aliases=("register", "reg", "r"), brief="Registers the user for the game",
        help="Registers the user for the game.\nIf you won't enter the team number it will be selected randomly when the game starts.\nTo change the team call the commang again with another argument; to reset team, do not input the argument"
    )
    async def ready(self, ctx, team_number:int = 0):
        cursor.execute("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        players, team1, team2 = map(lambda var: map(int, var.split()), cursor.fetchone())
        players = [await self.bot.fetch_user(id) for id in players]
        team1 = [await self.bot.fetch_user(id) for id in team1]
        team2 = [await self.bot.fetch_user(id) for id in team2]

        if ctx.author in players + team1 + team2:
            if (ctx.author in players and team_number == 0) or (ctx.author in team1 and team_number == 1) or (ctx.author in team2 and team_number == 2):
                await ctx.reply(embed = discord.Embed(
                    title = "Error",
                    description = "You're already in that team!",
                    colour = discord.Colour(int("ff6450", 16)),
                ))
                return

            leave_comm = bot.get_command("leave") # Removing author from any team, then processing main code
            await leave_comm.__call__(ctx) # Changes are not visible from this function running
            
            if ctx.author in players: # Getting again needed player list
                cursor.execute("SELECT players FROM guilds WHERE id=?", (ctx.guild.id,))
                players = map(int, cursor.fetchone()[0].split())
                players = [await self.bot.fetch_user(id) for id in players]
            if ctx.author in team1:
                cursor.execute("SELECT team1 FROM guilds WHERE id=?", (ctx.guild.id,))
                team1 = map(int, cursor.fetchone()[0].split())
                team1 = [await self.bot.fetch_user(id) for id in team1]
            if ctx.author in team2:
                cursor.execute("SELECT team2 FROM guilds WHERE id=?", (ctx.guild.id,))
                team2 = map(int, cursor.fetchone()[0].split())
                team2 = [await self.bot.fetch_user(id) for id in team2]
        
        if team_number == 0:
            players.append(ctx.author)
        elif team_number == 1:
            team1.append(ctx.author)
        elif team_number == 2:
            team2.append(ctx.author)
        else:
            await ctx.reply(embed = discord.Embed(
                title = "Invalid team number",
                description = "There are only 2 teams in the game.\nSelect one of them or don't type the number to select randomly",
                colour = discord.Colour(int("8d08d2", 16))
            ))
            return
        cursor.execute("SELECT id FROM players")
        if ctx.author.id not in map(lambda row: row[0], cursor.fetchall()):
            cursor.execute("INSERT INTO players VALUES (?,?,?,?,?)", (ctx.author.id, 0, 0, 0, 0))
            base.commit()

        await ctx.message.add_reaction("✅")
        
        players_id = map(lambda p: str(p.id), players)
        team1_id = map(lambda p: str(p.id), team1)
        team2_id = map(lambda p: str(p.id), team2)
        cursor.execute(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            (" ".join(players_id), " ".join(team1_id), " ".join(team2_id), ctx.guild.id)
        )

        await ctx.message.delete(delay=3)
    

    @commands.command(aliases=("l", "unreg"), help="Unregisters the user from the game")
    async def leave(self, ctx):
        cursor.execute("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
        players, team1, team2 = map(lambda var: map(int, var.split()), cursor.fetchone())
        players = [await self.bot.fetch_user(id) for id in players]
        team1 = [await self.bot.fetch_user(id) for id in team1]
        team2 = [await self.bot.fetch_user(id) for id in team2]
        
        if ctx.author not in players + team1 + team2:
            await ctx.reply(embed = discord.Embed(
                title = "Error",
                description = "You're not registered to the game",
                colour = discord.Colour(int("ff6450", 16)),
            ))
            return

        if ctx.author in players:
            players.remove(ctx.author)
        elif ctx.author in team1:
            team1.remove(ctx.author)
        elif ctx.author in team2:
            team2.remove(ctx.author)
        
        await ctx.message.add_reaction("✅")

        players_id = map(lambda p: str(p.id), players)
        team1_id = map(lambda p: str(p.id), team1)
        team2_id = map(lambda p: str(p.id), team2)
        cursor.execute(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            (" ".join(players_id), " ".join(team1_id), " ".join(team2_id), ctx.guild.id)
        )

        await ctx.message.delete(delay=3)


    @commands.command(name="players", aliases=("ps",), help="Shows registered players")
    async def show_players(self, ctx, final=False):
        async with ctx.typing():
            cursor.execute("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
            players, team1, team2 = map(lambda var: map(int, var.split()), cursor.fetchone())
            players = [await self.bot.fetch_user(id) for id in players]
            team1 = [await self.bot.fetch_user(id) for id in team1]
            team2 = [await self.bot.fetch_user(id) for id in team2]

            players_embed = discord.Embed(
                title = "Final player list" if final else "Player list",
                colour = discord.Colour(int("8d08d2", 16))
            )
            if team1:
                players_embed.add_field(name="Team 1", value="\n".join(map(lambda p: p.mention, team1)))
            if players:
                players_embed.add_field(name="No Team", value="\n".join(map(lambda p: p.mention, players)))
            if team2:
                players_embed.add_field(name="Team 2", value="\n".join(map(lambda p: p.mention, team2)))

            if players or team1 or team2:
                await ctx.reply(embed = players_embed)
            else:
                await ctx.reply(embed = discord.Embed(
                    title = "Player list",
                    description = "Nobody is ready to play",
                    colour = discord.Colour(int("8d08d2", 16))
                ))


    @commands.command(aliases=("s",), brief="Starts the game",
        help="Starts the game.\nIf there are players without a team they will be evenly distributed among the teams."
    )
    async def start(self, ctx):
        async with ctx.typing(): # Final player list preparation and show
            cursor.execute("SELECT players, team1, team2 FROM guilds WHERE id=?", (ctx.guild.id,))
            players, team1, team2 = map(lambda var: map(int, var.split()), cursor.fetchone())
            players = [await self.bot.fetch_user(id) for id in players]
            team1 = [await self.bot.fetch_user(id) for id in team1]
            team2 = [await self.bot.fetch_user(id) for id in team2]

            if players: # Dividing players into two teams randomly
                random.shuffle(players)
                for member in players:
                    if len(team1) <= len(team2):
                        team1.append(member)
                    else:
                        team2.append(member)
            
            if len(team1) < 2 or len(team2) < 2:
                await ctx.reply(embed = discord.Embed(
                    title = "Error",
                    description = "There are not enough players.\nIt has to be at least 2 players in each team.",
                    colour = discord.Colour(int("ff6450", 16))
                ))
                return
            
            if len(team1) > 25 or len(team2) > 25:
                await ctx.reply(embed = discord.Embed(
                    title = "Error",
                    description = "There are too much players.\nIt has **not** to be more than 25 players in each team.",
                    colour = discord.Colour(int("ff6450", 16))
                ))
                return

            team1_id = map(lambda p: str(p.id), team1)
            team2_id = map(lambda p: str(p.id), team2)
            cursor.execute(
                "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
                ("", " ".join(team1_id), " ".join(team2_id), ctx.guild.id) # There are no players without team left
            )
            
            final_show = self.bot.get_command("players")
            await final_show.__call__(ctx, final=True)
        await asyncio.sleep(1)

        # Dictionary selecting
        selecting_dict = {
            "en": {
                "std":      "**Original** English dictionary (400 words)",
                "duet":     "**Original Duet** dictionary (400 words)",
                "deep":     "**Original Deep Undercover** dictionary (**18+**, 390 words)",
                "denull":   "**deNULL's** dictionary (763 words)",
                "denull18": "**deNULL's** dictionary (**18+**, 1081 words)",
                "all":      "**All** English dictionaries (18+, 1139 words)",
                "esp":      "**Esperanto**"
            },
            "ru": {
                "std":      "**Стандартный** словарь из локализации GaGa Games (400 слов)",
                "deep":     "Словарь версии **Deep Undercover**, GaGa Games (**18+**, 390 слов)",
                "pard":     "Словарь от **Pard** (302 слова)",
                "vpupkin":  "Словарь от **vpupkin** (396 слов, много топонимов)",
                "zav":      "Словарь от **Ивана Заворина** (2272 частых слов)",
                "denull":   "Словарь от **deNULL** (636 слов, немного топонимса)",
                "denull18": "Словарь от **deNULL** (**18+**, 1014 слов)",
                "all":      "**Все** словари **вместе** (1058 слов)",
                "esp":      "**Esperanto**"
            }
        }

        await ctx.send(embed = discord.Embed(
            title = "Select language",
            description = "**en** - English\n**ru** - Russian\n\nType answer in the following message",
            colour = discord.Colour(int("8d08d2", 16))
        ))
        language = await self.bot.wait_for("message", check=lambda msg: msg.content.lower() in selecting_dict.keys() and msg.channel == ctx.channel)
        language = language.content.lower()

        dict_msg_desc = map(lambda num, value: f"**{num}** - {value}", range(1, 10), selecting_dict[language].values())
        dict_msg = await ctx.send(embed = discord.Embed(
            title = "Select dictionary",
            description = "\n".join(dict_msg_desc) + "\n\nYou have 15 seconds to vote",
            colour = discord.Colour(int("8d08d2", 16))
        ))
        for ind, _ in enumerate(selecting_dict[language]):
            await dict_msg.add_reaction(REACTION_NUMBERS[ind*3 : ind*3 + 3])
        await asyncio.sleep(15)

        new_dict_msg = await ctx.channel.fetch_message(dict_msg.id)
        emojis = get_most_count_reaction_emojis(new_dict_msg)

        potential_dicts = map(lambda em: tuple(selecting_dict[language].keys())[REACTION_NUMBERS.index(em) // 3], emojis)
        game_dict_name = random.choice(tuple(potential_dicts))
        await ctx.send(embed = discord.Embed(
            title = "Dictionary selected",
            description = selecting_dict[language][game_dict_name],
            colour = discord.Colour(int("8d08d2", 16))
        ))

        # Captains selecting
        cap_selecting_list = map(lambda ind, player: f"**{ALPHABET[ind]}** - {player.mention}", range(len(team1)), team1)
        cap_msg = await ctx.send(embed = discord.Embed(
            title = "RED team: Captain selecting",
            description = "**R** - Random captain\n\n" + "\n".join(cap_selecting_list) + "\n\nYou have 15 seconds to vote",
            colour = discord.Colour(int("ff6450", 16))
        ))
        await cap_msg.add_reaction("🇷")
        for ind, _ in enumerate(team1):
            await cap_msg.add_reaction(REACTION_ALPHABET[ind])
        await asyncio.sleep(15)

        new_cap_msg = await ctx.channel.fetch_message(cap_msg.id) # Have to get the message object again with reactions in it
        emojis = get_most_count_reaction_emojis(new_cap_msg)
        
        if "🇷" in emojis:
            team1_cap = random.choice(team1)
        else:
            potential_caps = map(lambda em: team1[REACTION_ALPHABET.index(em)], emojis)
            team1_cap = random.choice(tuple(potential_caps))
        team1_pl = team1.copy()
        team1_pl.remove(team1_cap)

        await ctx.send(embed = discord.Embed(
            title = "RED team: Captain selected",
            description = f"Your captain is {team1_cap.mention}!",
            colour = discord.Colour(int("ff6450", 16))
        ))

        # The same code for team2_cap
        cap_selecting_list = map(lambda ind, player: f"**{ALPHABET[ind]}** - {player.mention}", range(len(team1)), team2)
        msg = await ctx.send(embed = discord.Embed(
            title = "BLUE team: Captain selecting",
            description = "**R** - Random captain\n\n" + "\n".join(cap_selecting_list) + "\n\nYou have 15 seconds to vote",
            colour = discord.Colour(int("50bbff", 16))
        ))
        await msg.add_reaction("🇷")
        for ind, _ in enumerate(team2):
            await msg.add_reaction(REACTION_ALPHABET[ind])
        await asyncio.sleep(15)

        new_cap_msg = await ctx.channel.fetch_message(cap_msg.id) # Have to get the message object again with reactions in it
        emojis = get_most_count_reaction_emojis(new_cap_msg)
        
        if "🇷" in emojis:
            team2_cap = random.choice(team2)
        else:
            potential_caps = map(lambda em: team2[REACTION_ALPHABET.index(em)], emojis)
            team2_cap = random.choice(tuple(potential_caps))
        team2_pl = team2.copy()
        team2_pl.remove(team2_cap)

        await ctx.send(embed = discord.Embed(
            title = "BLUE team: Captain selected",
            description = f"Your captain is {team2_cap.mention}!",
            colour = discord.Colour(int("50bbff", 16))
        ))


        await ctx.send(embed = discord.Embed(
            title = "GAME STARTED!",
            colour = discord.Colour(int("8d08d2", 16))
        ))
        
        # Notifying everyone in direct messages
        await team1_cap.send(embed = discord.Embed(
            title = "Game started",
            description = "**You're the captain of the RED team**\n\nYour teammates are:\n" + "\n".join([p.mention for p in team1_pl]),
            colour = discord.Colour(int("ff6450", 16))
        ))
        for player in team1_pl:
            team1_pl_without = team1_pl.copy() # Team1 player list without recipient of the message
            team1_pl_without.remove(player)
            await player.send(embed = discord.Embed(
                title = "Game started",
                description = f"**You're a member of the RED team**\n\nThe captain of your team is {team1_cap.mention}\n\nYour teammates are:\n" + "\n".join([p.mention for p in team1_pl_without]),
                colour = discord.Colour(int("ff6450", 16))
            ))
        
        await team2_cap.send(embed = discord.Embed(
            title = "Game started",
            description = "**You're the captain of the BLUE team**\n\nYour teammates are:\n" + "\n".join([p.mention for p in team2_pl]),
            colour = discord.Colour(int("50bbff", 16))
        ))
        for player in team2_pl:
            team2_pl_without = team2_pl.copy() # Team2 player list without recipient of the message
            team2_pl_without.remove(player)
            await player.send(embed = discord.Embed(
                title = "Game started",
                description = f"**You're a member of the BLUE team**\n\nThe captain of your team is {team2_cap.mention}\n\nYour teammates are:\n" + "\n".join([p.mention for p in team2_pl_without]),
                colour = discord.Colour(int("50bbff", 16))
            ))

        uhd = gen.UltraHD()
        cursor.execute("SELECT dark FROM guilds WHERE id=?", (ctx.guild.id,))
        col = gen.Colors(cursor.fetchone()[0])

        team1_words, team2_words, endgame_word, other_words = gen.words(
            lang=language, dict_name=game_dict_name
        )
        opened_words = []
        order = list(team1_words + team2_words + (endgame_word,) + other_words) # endgame_word is a single word
        random.shuffle(order)
        available_words = order.copy() # Has to be a list
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

        game = True
        while game: # Mainloop
            gen.field(uhd, col, team1_words, team2_words, endgame_word, other_words, opened_words, order)
            
            with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                pl_field = discord.File(pl_field_bin, filename="player_field.png")
                await ctx.send(file = pl_field)
            with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                await first_cap.send(file = cap_field)
            with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                await second_cap.send(file = cap_field)
            
            await ctx.send(embed = discord.Embed(
                title = "Waiting for move",
                description = f"Captain of **{first_color}** team",
                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
            ))
            await first_cap.send(embed = discord.Embed(
                title = "This is your move turn",
                description = f"Type a word and a number like {'**`cow 3`**' if language=='en' else '**`корова 3`**'} in the following message",
                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
            ))
            move_msg = await self.bot.wait_for("message", check=lambda msg: re.fullmatch(r".+ \d+", msg.content) and not msg.content.endswith(" 0") and msg.channel == first_cap.dm_channel)
            move = move_msg.content
            word_count = int(move.split()[1])
            await first_cap.send(embed = discord.Embed(
                title = "Move accepted",
                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
            ))
            await ctx.send(embed = discord.Embed(
                title = f"Captain of **{first_color}** team moved",
                description = f"The move contains:\n**`{move}`**",
                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
            ))

            await ctx.send(embed = discord.Embed(
                title = "Waiting for move",
                description = f"Players of **{first_color}** team\n\nType words you want to open in the following messages.\nIf you want to **BREAK THE MOVE** type **`0`**\nIf you want to **STOP THE GAME** type **`000`**",
                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
            ))
            while word_count >= 0: # >= because of the rule that players can open one more word than their captain supposed to
                move_msg = await self.bot.wait_for("message", check=lambda msg: (msg.content.lower() in available_words or msg.content in ("0", "000")) and msg.channel == ctx.channel and msg.author in first_pl)
                move = move_msg.content.lower()
                if move == "0":
                    await move_msg.add_reaction("🆗")
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(embed = discord.Embed(
                        title = "Stopping the game",
                        description = "**Do you really want to stop playing?**\n\nAll players have 15 seconds to vote",
                        colour = discord.Colour(int("ff6450", 16))
                    ))
                    
                    upvotes, downvotes = await pros_and_cons(stop_msg, 15)
                    if upvotes > downvotes:
                        await ctx.send(embed = discord.Embed(
                            title = "GAME STOPPED",
                            description = "Most players voted for game stopping",
                            colour = discord.Colour(int("8d08d2", 16))
                        ))

                        game = False
                        break
                    else:
                        await ctx.send(embed = discord.Embed(
                            title = "GAME CONTINUED",
                            description = "Most players voted against game stopping",
                            colour = discord.Colour(int("8d08d2", 16))
                        ))
                        
                        continue # No need to generate a new field or decrease word_count
                
                opened_words.append(move)
                available_words.remove(move)
                gen.field(uhd, col, team1_words, team2_words, endgame_word, other_words, opened_words, order)\

                if move in other_words:
                    await move_msg.reply(embed = discord.Embed(
                        title = "Miss",
                        description = "Unfortunately, this word **doesn't belong to any team**",
                        colour = discord.Colour(int("dddddd", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Miss",
                        description = f"Your team opened the word **`{move}`** that **doesn't belong to any team**",
                        colour = discord.Colour(int("dddddd", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Lucky!",
                        description = f"The opponent team opened the word **`{move}`** that **doesn't belong to any team**",
                        colour = discord.Colour(int("dddddd", 16))
                    ))

                    with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                        pl_field = discord.File(pl_field_bin, filename="player_field.png")
                        await ctx.send(file = pl_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await first_cap.send(file = cap_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await second_cap.send(file = cap_field)
                elif move in second_words:
                    await move_msg.reply(embed = discord.Embed(
                        title = "Miss",
                        description = "Unfortunately, this word **belongs to the opponent team**",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Miss",
                        description = f"Your team opened the word **`{move}`** that **belongs to the opponent team**",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Lucky!",
                        description = f"The opponent team opened the word **`{move}`** that **belongs to your team**",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))

                    if set(second_words) <= set(opened_words): # If all second_words are opened
                        with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                            pl_field = discord.File(pl_field_bin, filename="player_field.png")
                            await ctx.send(file = pl_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await first_cap.send(file = cap_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await second_cap.send(file = cap_field)
                        
                        await ctx.send(embed = discord.Embed(
                            title = "Game over!",
                            description = f"**{second_color} team won!**\nThey opened all their team words",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))

                        await first_cap.send(embed = discord.Embed(
                            title = "Your team lost!",
                            description = "Better luck in the next game!",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap FROM players WHERE id=?", (first_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), first_cap.id)
                        )
                        for player in first_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team lost!",
                                description = "Better luck in the next game!",
                                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )
                        
                        await second_cap.send(embed = discord.Embed(
                            title = "Your team won!",
                            description = "Keep it up!",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (second_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=?, wins=?, wins_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), second_cap.id)
                        )
                        for player in second_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team won!",
                                description = "Keep it up!",
                                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games, wins FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=?, wins=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed = discord.Embed(
                        title = "Miss",
                        description = "Unfortunately, this word **is an endgame one**",
                        colour = discord.Colour(int("222222", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Miss",
                        description = f"Your team opened the word **`{move}`** that **is an endgame one**",
                        colour = discord.Colour(int("222222", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Lucky!",
                        description = f"The opponent team opened the word **`{move}`** that **is an endgame one**",
                        colour = discord.Colour(int("222222", 16))
                    ))

                    with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                        pl_field = discord.File(pl_field_bin, filename="player_field.png")
                        await ctx.send(file = pl_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await first_cap.send(file = cap_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await second_cap.send(file = cap_field)
                    
                    await ctx.send(embed = discord.Embed(
                        title = "Game over!",
                        description = f"**{second_color} team won!**\n{first_color} team opened an endgame word",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    
                    await first_cap.send(embed = discord.Embed(
                        title = "Your team lost!",
                        description = "Better luck in the next game!",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    cursor.execute("SELECT games, games_cap FROM players WHERE id=?", (first_cap.id,))
                    cursor.execute(
                        "UPDATE players SET games=?, games_cap=? WHERE id=?",
                        (*map(lambda stat: stat+1, cursor.fetchone()), first_cap.id)
                    )
                    for player in first_pl:
                        await player.send(embed = discord.Embed(
                            title = "Your team lost!",
                            description = "Better luck in the next game!",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games FROM players WHERE id=?", (player.id,))
                        cursor.execute(
                            "UPDATE players SET games=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                        )
                    
                    await second_cap.send(embed = discord.Embed(
                        title = "Your team won!",
                        description = "Keep it up!",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (second_cap.id,))
                    cursor.execute(
                        "UPDATE players SET games=?, games_cap=?, wins=?, wins_cap=? WHERE id=?",
                        (*map(lambda stat: stat+1, cursor.fetchone()), second_cap.id)
                    )
                    for player in second_pl:
                        await player.send(embed = discord.Embed(
                            title = "Your team won!",
                            description = "Keep it up!",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, wins FROM players WHERE id=?", (player.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, wins=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                        )

                    game = False
                    break
                else: # They guessed
                    await move_msg.reply(embed = discord.Embed(
                        title = "Success",
                        description = "You guessed!",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Success",
                        description = f"Your team guessed the word **`{move}`** that **belongs to your team**!",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Opponent success",
                        description = f"The opponent team guessed the word **`{move}`** that **belongs to it**",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))

                    if set(first_words) <= set(opened_words): # If all first_words are opened
                        with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                            pl_field = discord.File(pl_field_bin, filename="player_field.png")
                            await ctx.send(file = pl_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await first_cap.send(file = cap_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await second_cap.send(file = cap_field)
                        
                        await ctx.send(embed = discord.Embed(
                            title = "Game over!",
                            description = f"**{first_color} team won!**\nThey opened all their team words",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        
                        await first_cap.send(embed = discord.Embed(
                            title = "Your team won!",
                            description = "Keep it up!",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (first_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=?, wins=?, wins_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), first_cap.id)
                        )
                        for player in first_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team won!",
                                description = "Keep it up!",
                                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games, wins FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=?, wins=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )
                        
                        await second_cap.send(embed = discord.Embed(
                            title = "Your team lost!",
                            description = "Better luck in the next game!",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap FROM players WHERE id=?", (second_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), second_cap.id)
                        )
                        for player in second_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team lost!",
                                description = "Better luck in the next game!",
                                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )

                        game = False
                        break

                    if word_count > 0: # If quitting after this move, field will be sent twice in a row
                        with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                            pl_field = discord.File(pl_field_bin, filename="player_field.png")
                            await ctx.send(file = pl_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await first_cap.send(file = cap_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await second_cap.send(file = cap_field)

                word_count -= 1
            
            if not game: # checking if the game is over after first team move (a crutch for loop check)
                break
            
            gen.field(uhd, col, team1_words, team2_words, endgame_word, other_words, opened_words, order)
            
            with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                pl_field = discord.File(pl_field_bin, filename="player_field.png")
                await ctx.send(file = pl_field)
            with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                await first_cap.send(file = cap_field)
            with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                await second_cap.send(file = cap_field)
            
            await ctx.send(embed = discord.Embed(
                title = "Waiting for move",
                description = f"Captain of **{second_color}** team",
                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
            ))
            await second_cap.send(embed = discord.Embed(
                title = "This is your move turn",
                description = f"Type a word and a number like {'**`cow 3`**' if language=='en' else '**`корова 3`**'} in the following message",
                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
            ))
            move_msg = await self.bot.wait_for("message", check=lambda msg: re.fullmatch(r".+ \d+", msg.content) and not msg.content.endswith(" 0") and msg.channel == second_cap.dm_channel)
            move = move_msg.content
            word_count = int(move.split()[1])
            await second_cap.send(embed = discord.Embed(
                title = "Move accepted",
                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
            ))
            await ctx.send(embed = discord.Embed(
                title = f"Captain of **{second_color}** team moved",
                description = f"The move contains:\n**`{move}`**",
                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
            ))

            await ctx.send(embed = discord.Embed(
                title = "Waiting for move",
                description = f"Players of **{second_color}** team\n\nType words you want to open in the following messages.\nIf you want to **BREAK THE MOVE** type **`0`**\nIf you want to **STOP THE GAME** type **`000`**",
                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
            ))
            while word_count >= 0: # >= because of the rule that players can open one more word than their captain said
                move_msg = await self.bot.wait_for("message", check=lambda msg: (msg.content.lower() in available_words or msg.content in ("0", "000")) and msg.channel == ctx.channel and msg.author in second_pl)
                move = move_msg.content.lower()
                if move == "0":
                    await move_msg.add_reaction("🆗")
                    break
                if move == "000":
                    stop_msg = await move_msg.reply(embed = discord.Embed(
                        title = "Stopping the game",
                        description = "**Do you really want to stop playing?**\n\nAll players have 15 seconds to vote",
                        colour = discord.Colour(int("ff6450", 16))
                    ))
                    
                    upvotes, downvotes = await pros_and_cons(stop_msg, 15)
                    if upvotes > downvotes:
                        await ctx.send(embed = discord.Embed(
                            title = "GAME STOPPED",
                            description = "Most players voted for game stopping",
                            colour = discord.Colour(int("8d08d2", 16))
                        ))

                        game = False
                        break
                    else:
                        await ctx.send(embed = discord.Embed(
                            title = "GAME CONTINUED",
                            description = "Most players voted against game stopping",
                            colour = discord.Colour(int("8d08d2", 16))
                        ))
                        
                        continue # No need to generate a new field or decrease word_count

                opened_words.append(move)
                available_words.remove(move)
                gen.field(uhd, col, team1_words, team2_words, endgame_word, other_words, opened_words, order)

                if move in other_words:
                    await move_msg.reply(embed = discord.Embed(
                        title = "Miss",
                        description = "Unfortunately, this word **doesn't belong to any team**",
                        colour = discord.Colour(int("dddddd", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Miss",
                        description = f"Your team opened the word **`{move}`** that **doesn't belong to any team**",
                        colour = discord.Colour(int("dddddd", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Lucky!",
                        description = f"The opponent team opened the word **`{move}`** that **doesn't belong to any team**",
                        colour = discord.Colour(int("dddddd", 16))
                    ))

                    with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                        pl_field = discord.File(pl_field_bin, filename="player_field.png")
                        await ctx.send(file = pl_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await first_cap.send(file = cap_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await second_cap.send(file = cap_field)
                elif move in first_words:
                    await move_msg.reply(embed = discord.Embed(
                        title = "Miss",
                        description = "Unfortunately, this word **belongs to the opponent team**",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Miss",
                        description = f"Your team opened the word **`{move}`** that **belongs to the opponent team**",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Lucky!",
                        description = f"The opponent team opened the word **`{move}`** that **belongs to your team**",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))

                    if set(first_words) <= set(opened_words): # If all first_words are opened
                        with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                            pl_field = discord.File(pl_field_bin, filename="player_field.png")
                            await ctx.send(file = pl_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await first_cap.send(file = cap_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await second_cap.send(file = cap_field)
                        
                        await ctx.send(embed = discord.Embed(
                            title = "Game over!",
                            description = f"**{first_color} team won!**\nThey opened all their team words",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        
                        await first_cap.send(embed = discord.Embed(
                            title = "Your team won!",
                            description = "Keep it up!",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (first_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=?, wins=?, wins_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), first_cap.id)
                        )
                        for player in first_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team won!",
                                description = "Keep it up!",
                                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games, wins FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=?, wins=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )
                        
                        await second_cap.send(embed = discord.Embed(
                            title = "Your team lost!",
                            description = "Better luck in the next game!",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap FROM players WHERE id=?", (second_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), second_cap.id)
                        )
                        for player in second_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team lost!",
                                description = "Better luck in the next game!",
                                colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )

                        game = False
                        break
                    
                    break
                elif move == endgame_word:
                    await move_msg.reply(embed = discord.Embed(
                        title = "Miss",
                        description = "Unfortunately, this word **is an endgame one**",
                        colour = discord.Colour(int("222222", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Miss",
                        description = f"Your team opened the word **`{move}`** that **is an endgame one**",
                        colour = discord.Colour(int("222222", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Lucky!",
                        description = f"The opponent team opened the word **`{move}`** that **is an endgame one**",
                        colour = discord.Colour(int("222222", 16))
                    ))

                    with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                        pl_field = discord.File(pl_field_bin, filename="player_field.png")
                        await ctx.send(file = pl_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await first_cap.send(file = cap_field)
                    with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                        cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                        await second_cap.send(file = cap_field)
                    
                    await ctx.send(embed = discord.Embed(
                        title = "Game over!",
                        description = f"**{first_color} team won!**\n{second_color} team opened an endgame word",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    
                    await first_cap.send(embed = discord.Embed(
                        title = "Your team won!",
                        description = "Keep it up!",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (first_cap.id,))
                    cursor.execute(
                        "UPDATE players SET games=?, games_cap=?, wins=?, wins_cap=? WHERE id=?",
                        (*map(lambda stat: stat+1, cursor.fetchone()), first_cap.id)
                    )
                    for player in first_pl:
                        await player.send(embed = discord.Embed(
                            title = "Your team won!",
                            description = "Keep it up!",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, wins FROM players WHERE id=?", (player.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, wins=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                        )
                    
                    await second_cap.send(embed = discord.Embed(
                        title = "Your team lost!",
                        description = "Better luck in the next game!",
                        colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                    ))
                    cursor.execute("SELECT games, games_cap FROM players WHERE id=?", (second_cap.id,))
                    cursor.execute(
                        "UPDATE players SET games=?, games_cap=? WHERE id=?",
                        (*map(lambda stat: stat+1, cursor.fetchone()), second_cap.id)
                    )
                    for player in second_pl:
                        await player.send(embed = discord.Embed(
                            title = "Your team lost!",
                            description = "Better luck in the next game!",
                            colour = discord.Colour(int("ff6450" if first_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games FROM players WHERE id=?", (player.id,))
                        cursor.execute(
                            "UPDATE players SET games=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                        )

                    game = False
                    break
                else: # They guessed
                    await move_msg.reply(embed = discord.Embed(
                        title = "Success",
                        description = "You guessed!",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    await second_cap.send(embed = discord.Embed(
                        title = "Success",
                        description = f"Your team guessed the word **`{move}`** that **belongs to your team**!",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))
                    await first_cap.send(embed = discord.Embed(
                        title = "Opponent success",
                        description = f"The opponent team guessed the word **`{move}`** that **belongs to opponent's team**",
                        colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                    ))

                    if set(second_words) <= set(opened_words): # If all second_words are opened
                        with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                            pl_field = discord.File(pl_field_bin, filename="player_field.png")
                            await ctx.send(file = pl_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await first_cap.send(file = cap_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await second_cap.send(file = cap_field)
                        
                        await ctx.send(embed = discord.Embed(
                            title = "Game over!",
                            description = f"**{second_color} team won!**\nThey opened all their team words",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))

                        await first_cap.send(embed = discord.Embed(
                            title = "Your team lost!",
                            description = "Better luck in the next game!",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap FROM players WHERE id=?", (first_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), first_cap.id)
                        )
                        for player in first_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team lost!",
                                description = "Better luck in the next game!",
                                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )
                        
                        await second_cap.send(embed = discord.Embed(
                            title = "Your team won!",
                            description = "Keep it up!",
                            colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                        ))
                        cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (second_cap.id,))
                        cursor.execute(
                            "UPDATE players SET games=?, games_cap=?, wins=?, wins_cap=? WHERE id=?",
                            (*map(lambda stat: stat+1, cursor.fetchone()), second_cap.id)
                        )
                        for player in second_pl:
                            await player.send(embed = discord.Embed(
                                title = "Your team won!",
                                description = "Keep it up!",
                                colour = discord.Colour(int("ff6450" if second_color=="RED" else "50bbff", 16))
                            ))
                            cursor.execute("SELECT games, wins FROM players WHERE id=?", (player.id,))
                            cursor.execute(
                                "UPDATE players SET games=?, wins=? WHERE id=?",
                                (*map(lambda stat: stat+1, cursor.fetchone()), player.id)
                            )

                        game = False
                        break

                    if word_count > 0: # If quitting after this move, field will be sent twice in a row
                        with open(os.path.join("images", "pl_field.png"), "rb") as pl_field_bin:
                            pl_field = discord.File(pl_field_bin, filename="player_field.png")
                            await ctx.send(file = pl_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await first_cap.send(file = cap_field)
                        with open(os.path.join("images", "cap_field.png"), "rb") as cap_field_bin:
                            cap_field = discord.File(cap_field_bin, filename="captain_field.png")
                            await second_cap.send(file = cap_field)

                word_count -= 1

        cursor.execute(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            ("", "", "", ctx.guild.id)
        )
        base.commit()


    @commands.command(aliases=("st", "ss"), help="Shows player's statistics")
    async def stats(self, ctx, member:discord.Member=None):
        if not member:
            member = ctx.author
        
        cursor.execute("SELECT games, games_cap, wins, wins_cap FROM players WHERE id=?", (member.id,))
        info = cursor.fetchone()
        if not info:
            await ctx.reply(embed = discord.Embed(
                title = "Error",
                description = f"**{member.nick if member.nick else member.name}** has never played Codenames",
                colour = discord.Colour(int("ff6450", 16))
            ))
            return
        games, games_cap, wins, wins_cap = map(int, info)
        games_tm = games - games_cap # In the team
        wins_tm = wins - wins_cap
        winrate = f"{round((wins / games) * 100)}%" if games else "-"
        winrate_cap = f"{round((wins_cap / games_cap) * 100)}%" if games_cap else "-"
        winrate_tm = f"{round((wins_tm / games_tm) * 100)}%" if games_tm else "-"

        stats_embed = discord.Embed(
            title = f"**{member.nick if member.nick else member.name}**'s statistics",
            colour = discord.Colour(int("8d08d2", 16))
        )
        stats_embed.add_field(name="Total", value=f"Games played: {games}\nGames won: {wins}\nWinrate: {winrate}")
        stats_embed.add_field(name="Captain", value=f"Games played: {games_cap}\nGames won: {wins_cap}\nWinrate: {winrate_cap}")
        stats_embed.add_field(name="Team", value=f"Games played: {games_tm}\nGames won: {wins_tm}\nWinrate: {winrate_tm}")
        stats_embed.add_field(
            name = chr(int("2063", 16)),
            value = f"Codenames is a **team game**, so the winrate statistics do **not** exactly show player's skill",
            inline = False
        )
        stats_embed.set_thumbnail(url = member.avatar_url)

        await ctx.reply(embed = stats_embed)
    

    @commands.command(aliases=("c", "cl", "clr"), help="Clears registered players list")
    @is_moderator
    async def clear(self, ctx):
        cursor.execute(
            "UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?",
            ("", "", "", ctx.guild.id)
        )
        await ctx.message.add_reaction("✅")
        await ctx.message.delete(delay=3)


class SettingCommands(commands.Cog, name = "Setting Commands"):
    """Changes the bot's defaults"""
    def __init__(self, bot:commands.Bot):
        self.bot = bot
    
    @commands.command(aliases=("pre",), brief="Changes the bot's prefix. Empty prefix -> default", help='Changes the bot\'s prefix.\nIf you wand to set it to default ("cdn") do not input a new prefix')
    @is_moderator
    async def prefix(self, ctx, new_prefix="cdn"):
        prefix = "" if new_prefix == "cdn" else new_prefix
        cursor.execute("UPDATE guilds SET prefix=? WHERE id=?", (prefix, ctx.guild.id))
        base.commit()

        await ctx.send(embed=discord.Embed(
            title = "Prefix changed",
            description = (f"New prefix for this server:\n**`{prefix}`**\n" if prefix else "Custom prefix for this server deleted") + "\nDefault one **`cdn`** and bot ping are still valid",
            colour = discord.Colour(int("8d08d2", 16))
        ))


# Last setting
bot.add_cog(GameCommands(bot))
bot.add_cog(SettingCommands(bot))

# Getting the token and starting
dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
