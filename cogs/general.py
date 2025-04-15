import discord
from discord.ext import commands
import json
import re
import datetime
from datetime import datetime, timedelta

class General(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | general.py✅')



    @commands.command()
    async def cmds(self, ctx):
        class MyView(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
            @discord.ui.button(label="Generator Commands", style=discord.ButtonStyle.secondary) # Create a button with the label "😎 Click me!" with color Blurple
            async def button_callback1(self, button, interaction):
                button.disabled = True
                general = discord.Embed(title="1 Generator Command", description="**Receipt Generators (1)**\n[StockX](https://stockx.com/) - `!stockx`", color=0x38761d, timestamp=datetime.utcnow())
                general.set_footer(text="GoatX")
                await interaction.response.edit_message(embed=general,view=self)

            @discord.ui.button(label="General Commands", style=discord.ButtonStyle.secondary) 
            async def button_callback2(self, button, interaction):
                button.disabled = True
                general = discord.Embed(title="General Commands", description="Help - `!cmds`\nPrices - `!prices`\nVendor - `!vendor`", color=0x38761d, timestamp=datetime.utcnow())
                general.set_footer(text="GoatX")
                await interaction.response.edit_message(embed=general,view=self)

            @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="❌")
            async def button_callback3(self, button, interaction):
                self.disable_all_items()
                cancel = discord.Embed(title="Cancelled", description="Interaction cancelled", color=0xff0000, timestamp=datetime.utcnow())
                cancel.set_footer(text="GoatX")
                await interaction.response.edit_message(embed=cancel, view=self)


        cmds_embed = discord.Embed(title="Help Command", description="Please choose a button below.", color=0xfafbff, timestamp=datetime.utcnow())
        cmds_embed.set_footer(text="GoatX")
        action_row = MyView()
        await ctx.reply(embed=cmds_embed, view=action_row)

def setup(client):
    client.add_cog(General(client))
