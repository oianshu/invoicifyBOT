# mail_commands.py

import discord
from discord.ext import commands
import sqlite3

class MailCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = sqlite3.connect('users.db')
        self.cursor = self.db.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | mail_commands.py ✅')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx, user: discord.Member):
        discord_id = user.id
        self.cursor.execute('DELETE FROM users WHERE discord_id = ?', (discord_id,))
        self.db.commit()
        await ctx.send(f"{user.mention} **has been removed from the users database!** <:MHH_code:1167409853627650139>")

def setup(client):
    client.add_cog(MailCommands(client))
