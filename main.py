import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timedelta


intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

for f in os.listdir("./cogs"):
    if f.endswith(".py"):
        bot.load_extension("cogs." + f[:-3])

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        error_embed = discord.Embed(title="Command Not Found", description="That command does not exits, please do `!cmds`", color=0xff0000, timestamp=datetime.utcnow())
        error_embed.set_footer(text="GoatX")
        await ctx.reply(embed=error_embed)

bot.run("TOKEN")
