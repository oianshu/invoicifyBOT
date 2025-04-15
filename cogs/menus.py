import discord
from discord.ext import commands
from datetime import datetime

class Menus(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | menus.py✅')
        
    @commands.command()
    async def prices(self, ctx):
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        embed = discord.Embed(
            title="<:Premium_Bot:1166682050011598868>  **Generator Prices** <:Premium_Bot:1166682050011598868>",
            description="**Note: Every subscription includes unlimited receipts with all generator commands available to use.**\n\n"
                        "**Generator Prices**\n"
                        "1 time use - $5.00\n"
                        "1 Day - $15.00\n"
                        "1 Week - $30.00\n"
                        "Lifetime - $80.00\n"
                        "Lifetime **+** Vendor Access - $120.00",
            color=0x016b2d
        )

        embed.set_footer(text=f"GoatX | {current_time}")
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(
            title="<:Discover:1160083455481233459>  **VENDOR BUNDLE** <:Discover:1160083455481233459>",
            description="Vendor bundle offers the user access to all the generator, a custom private channel for you to run commands in, access to private channels.. **AND ABILITY TO USE SPOOFED EMAILS**",
            color=0xe67e22
        )

        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Menus(client))
