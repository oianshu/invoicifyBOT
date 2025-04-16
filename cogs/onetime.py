import discord
from discord.ext import commands
import sqlite3
import re
import requests
import datetime
import re
from datetime import datetime, timedelta
import time

class OnetimeCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.onetime_db = sqlite3.connect('onetime_uses.db')
        self.onetime_cursor = self.onetime_db.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | onetime.py✅')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def onetime(self, ctx, amount: int, user: discord.Member):
        discord_id = user.id
        self.onetime_cursor.execute('SELECT uses FROM onetime_uses WHERE discord_id = ?', (discord_id,))
        result = self.onetime_cursor.fetchone()
        if not result:
            self.onetime_cursor.execute('INSERT INTO onetime_uses (discord_id, uses) VALUES (?, ?)', (discord_id, amount))
        else:
            current_uses = result[0]
            new_uses = current_uses + amount
            self.onetime_cursor.execute('UPDATE onetime_uses SET uses = ? WHERE discord_id = ?', (new_uses, discord_id))
        self.onetime_db.commit()
        await ctx.send(f"{user.mention} has received {amount} one-time use(s) for the `!stockx` command!")

def setup(client):
    client.add_cog(OnetimeCommands(client))
