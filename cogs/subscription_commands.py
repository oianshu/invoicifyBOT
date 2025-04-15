import discord
from discord.ext import commands
import sqlite3
import re
import requests
import datetime
import re
from datetime import datetime, timedelta
import time


class SubscriptionCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.subscription_db = sqlite3.connect('subscriptions.db')
        self.subscription_cursor = self.subscription_db.cursor()
        self.subscription_cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                                        discord_id INTEGER PRIMARY KEY,
                                        subscription_expiry INTEGER
                                    )''')
        self.subscription_db.commit()


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | subscription_commands.py✅')

        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def day(self, ctx, user: discord.Member):
        discord_id = user.id
        current_timestamp = int(time.time())
        one_day = 86400  # 24 hours * 60 minutes * 60 seconds
        subscription_expiry = current_timestamp + one_day
        self.subscription_cursor.execute('INSERT OR REPLACE INTO subscriptions (discord_id, subscription_expiry) VALUES (?, ?)', (discord_id, subscription_expiry))
        self.subscription_db.commit()
        await ctx.send(f"{user.mention} **has received a 1-day subscription!** <:Timer:1167121901722804315>")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def week(self, ctx, user: discord.Member):
        discord_id = user.id
        current_timestamp = int(time.time())
        one_week = 604800  # 7 days * 24 hours * 60 minutes * 60 seconds
        subscription_expiry = current_timestamp + one_week
        self.subscription_cursor.execute('INSERT OR REPLACE INTO subscriptions (discord_id, subscription_expiry) VALUES (?, ?)', (discord_id, subscription_expiry))
        self.subscription_db.commit()
        await ctx.send(f"{user.mention} **has received a 1-week subscription!** <:Timer:1151665788474904677> ")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def access(self, ctx, user: discord.Member):
        discord_id = user.id
        current_timestamp = int(time.time())
        # You can set the subscription expiry based on your needs
        # For example, you can set it to one month (30 days)
        one_month = 2592000  # 30 days * 24 hours * 60 minutes * 60 seconds
        subscription_expiry = current_timestamp + one_month
        self.subscription_cursor.execute('INSERT OR REPLACE INTO subscriptions (discord_id, subscription_expiry) VALUES (?, ?)', (discord_id, subscription_expiry))
        self.subscription_db.commit()
        await ctx.send(f"{user.mention} **has received an extended subscription!** <:PremiumBot:1166682050011598868> ")
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, user: discord.Member):
        discord_id = user.id
        self.subscription_cursor.execute('SELECT subscription_expiry FROM subscriptions WHERE discord_id = ?', (discord_id,))
        subscription_result = self.subscription_cursor.fetchone()

        if subscription_result:
            self.subscription_cursor.execute('DELETE FROM subscriptions WHERE discord_id = ?', (discord_id,))
            self.subscription_db.commit()
            await ctx.send(f"<:MHH_DND:1153047517995487283> **Subscription removed for **{user.mention}!")
        else:
            await ctx.send(f"{user.mention} **does not have an active subscription to remove.** <:error:1158482168989888602>")



def setup(client):
    client.add_cog(SubscriptionCommands(client))