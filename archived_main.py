# https://discord.com/api/oauth2/authorize?client_id=841776986246348851&permissions=4311104&scope=bot

import discord
from discord.ext import commands
import os, json, random, sqlite3

# Getting settings and base
with open(os.path.join(os.getcwd(), 'settings.json'), 'r') as settings_file:
    settings = json.load(settings_file)

base = sqlite3.connect(os.path.join(os.getcwd(), 'base.db'))
cursor = base.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS guilds (id int primary key, prefix text, players text, team1 text, team2 text)')
cursor.execute('CREATE TABLE IF NOT EXISTS players (id int primary key, games int, wins int, wins_cap int)')

# cursor.execute('INSERT INTO guilds VALUES (?,?,?,?,?)', (795556636748021770, '-', '', '', ''))

# Creating bot
def get_prefix(bot, message):
    cursor.execute('SELECT prefix FROM guilds WHERE id=?', [(message.guild.id)])
    return cursor.fetchone()[0]

bot = commands.Bot(command_prefix=get_prefix, help_command=None)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Activity(type=discord.ActivityType.watching, name='codenames.me'))

@bot.event
async def on_guild_join(guild):
    cursor.execute('INSERT INTO guilds VALUES (?,?,?,?,?)', (guild.id, '!', '', '', ''))


# Temprorary commands
@bot.command()
async def kill(ctx):
    if ctx.message.author.id != settings['chief_id']:
        await ctx.reply(embed=discord.Embed(
            title = 'Forbidden :no_entry_sign:',
            colour = discord.Colour(int('8d08d2', 16))
        ))
        return
    
    with open('settings.json', 'w') as settings_file:
        json.dump(settings, settings_file, indent=4)
    base.commit()
    base.close()
    await ctx.message.add_reaction('✅')
    exit()


# Tool commands
@bot.command()
async def help(ctx):
    await ctx.reply(embed=discord.Embed(
        title = 'CodenamesBot Help',
        description = 'Help will be here soon...',
        colour = discord.Colour(int('8d08d2', 16))
    ))

@bot.command()
async def prefix(ctx, new_prefix = ''):
    cursor.execute('UPDATE guilds SET prefix=? WHERE id=?', (new_prefix, ctx.guild.id))
    await ctx.message.add_reaction('✅')


# Game commands
@bot.command(aliases=['r'])
async def ready(ctx, team:int = 0):
    cursor.execute('SELECT players, team1, team2 FROM guilds WHERE id=?', [(ctx.guild.id)])
    players, team1, team2 = map(lambda s: list(map(int, s.split())), cursor.fetchone())
    players = [await bot.fetch_user(id) for id in players]
    team1 = [await bot.fetch_user(id) for id in team1]
    team2 = [await bot.fetch_user(id) for id in team2]
    print(players, team1, team2)

    if ctx.author not in players+team1+team2:
        if not team:
            players.append(ctx.author)
        elif team == 1:
            team1.append(ctx.author)
        elif team == 2:
            team2.append(ctx.author)
        else:
            await ctx.reply(embed = discord.Embed(
                title = 'Invalid team number',
                description = "There are only 2 teams in the game.\nChoose one of them or don't type the number to shuffle randomly",
                colour = discord.Colour(int('8d08d2', 16))
            ))
        cursor.execute('SELECT id FROM players')
        if ctx.author.id not in [tup[0] for tup in cursor.fetchall()]:
            cursor.execute('INSERT INTO players VALUES (?,?,?,?)', (ctx.author.id, 0, 0, 0))
        
        await ctx.message.add_reaction('✅')
    else:
        await ctx.reply(embed = discord.Embed(
            title = 'You\'re already ready',
            description = 'Do you want to quit the game? (y/n)',
            colour = discord.Colour(int('8d08d2', 16))
        ))

        reply = await bot.wait_for('message', check=lambda msg: msg.content.lower() in ['y', 'n'] and msg.author == ctx.author and msg.channel == ctx.channel)
        if reply.content.lower() == 'y':
            if reply.author in players: players.remove(reply.author)
            elif reply.author in team1: team1.remove(reply.author)
            elif reply.author in team2: team2.remove(reply.author)
            await reply.add_reaction('✅')
        else:
            await reply.add_reaction('🆗')
    
    players = [str(p.id) for p in players]
    team1 = [str(p.id) for p in team1]
    team2 = [str(p.id) for p in team2]
    cursor.execute('UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?', (' '.join(players), ' '.join(team1), ' '.join(team2), ctx.guild.id))

@bot.command(name='players', aliases=['ps'])
async def show_players(ctx):
    cursor.execute('SELECT players, team1, team2 FROM guilds WHERE id=?', [(ctx.guild.id)])
    players, team1, team2 = map(lambda s: list(map(int, s.split())), cursor.fetchone())
    players = [await bot.fetch_user(id) for id in players]
    team1 = [await bot.fetch_user(id) for id in team1]
    team2 = [await bot.fetch_user(id) for id in team2]
    print(players, team1, team2)

    players_embed = discord.Embed(title='Player list', colour=discord.Colour(int('8d08d2', 16)))
    if players: players_embed.add_field(name='No Team', value='\n'.join([p.mention for p in players]))
    if team1: players_embed.add_field(name='Team 1', value='\n'.join([p.mention for p in team1]))
    if team2: players_embed.add_field(name='Team 2', value='\n'.join([p.mention for p in team2]))

    if players+team1+team2:
        await ctx.reply(embed = players_embed)
    else:
        await ctx.reply(embed = discord.Embed(
            title = 'Player list',
            description = 'Nobody is ready to play :no_good:',
            colour = discord.Colour(int('8d08d2', 16))
        ))
    
    players = [str(p.id) for p in players]
    team1 = [str(p.id) for p in team1]
    team2 = [str(p.id) for p in team2]
    cursor.execute('UPDATE guilds SET players=?, team1=?, team2=? WHERE id=?', (' '.join(players), ' '.join(team1), ' '.join(team2), ctx.guild.id))

@bot.command(aliases=['s'])
async def start(ctx):
    pass

bot.run(settings['token'])