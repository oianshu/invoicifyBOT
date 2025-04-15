import discord
from discord.ext import commands
import sqlite3
import json
import re
import datetime
from datetime import datetime, timedelta

class Setup(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = sqlite3.connect('users.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                discord_id INTEGER PRIMARY KEY,
                                email TEXT,
                                address TEXT,
                                subscription TEXT,
                                subscription_expiry TEXT
                            )''')
        self.db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | setup.py✅')



    @commands.command()
    async def setup(self, ctx):
        class ConfirmationView(discord.ui.View):
            def __init__(self, discord_id, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.discord_id = discord_id
                self.email = email
                self.address = address
                self.save_count = 0


                self.db = sqlite3.connect('users.db')
                self.cursor = self.db.cursor()
                self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                        discord_id INTEGER PRIMARY KEY,
                                        email TEXT,
                                        address TEXT,
                                        subscription TEXT,
                                        subscription_expiry TEXT
                                    )''')
                self.db.commit()

            async def interaction_check(self,interaction: discord.MessageInteraction) -> bool:
                if interaction.user.id != self.discord_id:
                    await interaction.response.send_message(content="You don't have permission to press this button.",ephemeral=True)
                    return False
                else:
                    return True
            
            @discord.ui.button(label="Email", style=discord.ButtonStyle.red, emoji="<:google:1167414367575343165>")
            async def email_button_callback(self, button, interaction):
                modal = Email(title="Email Set")
                await interaction.response.send_modal(modal)
                await modal.wait()
                self.email = modal.val
                print(modal.val)


            @discord.ui.button(label="Address", style=discord.ButtonStyle.secondary, emoji="🏠")
            async def address_button_callback(self, button, interaction):
                modal = AddressSetup(title="Address Set")
                await interaction.response.send_modal(modal)
                await modal.wait()
                self.address = modal.addy
                print(self.address)
                
            @discord.ui.button(label="Save", style=discord.ButtonStyle.primary)
            async def save_button_callback(self, button, interaction):
                if not self.email or not self.address:
                    await interaction.response.send_message("<:error:1158482168989888602> **- Please fill out both email and address before saving.**")
                elif self.save_count == 0:
                    embed = discord.Embed(
                        title="Final Values - If correct, press Save a second time",
                        color=0xfafbff,
                    )
                    embed.add_field(name="Email", value=self.email, inline=False)
                    embed.add_field(name="Address", value=self.address, inline=False)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    self.save_count += 1
                elif self.save_count == 1:
                    # Save email and address to the database here
                    discord_id = interaction.user.id
                    self.cursor.execute(
                        'INSERT INTO users (discord_id, email, address) VALUES (?, ?, ?)',
                        (discord_id, self.email, self.address),
                    )
                    self.db.commit()
                    await interaction.response.send_message("<:MHH_clouddown:1167415796411146300> **Email and Address saved!.. your ready to start using the generator**")
                    self.stop()


        class Email(discord.ui.Modal):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.val = None

                self.add_item(discord.ui.InputText(label="Email"))
            async def callback(self, interaction: discord.Interaction):
                string = self.children[0].value
                self.val = self.children[0].value
                await interaction.response.send_message(f"<:checkmark:1151164474083000411> - **Email  set to:** {string}", ephemeral=True)
                #self.cursor.execute('INSERT INTO users (discord_id, email, address) VALUES (?, ?, ?)', (discord_id, email, address))
                #self.db.commit()
                self.stop()
        class AddressSetup(discord.ui.Modal):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.addy = None
                self.add_item(discord.ui.InputText(label="Street"))
                self.add_item(discord.ui.InputText(label="City"))
                self.add_item(discord.ui.InputText(label="Zip Code"))
                self.add_item(discord.ui.InputText(label="Country"))

            async def callback(self, interaction: discord.Interaction):
                string = self.children[0].value + "," +self.children[1].value + ","+ self.children[2].value + "," + self.children[3].value
                self.addy = string
                await interaction.response.send_message(f"<:checkmark:1151164474083000411> - **Address set to:** {string}", ephemeral=True)
                #self.cursor.execute('INSERT INTO users (discord_id, email, address) VALUES (?, ?, ?)', (discord_id, email, address))
                #self.db.commit()


        discord_id = ctx.author.id
        self.cursor.execute('SELECT email, address FROM users WHERE discord_id = ?', (discord_id,))
        result = self.cursor.fetchone()
        if result:
            email, address = result
            await ctx.reply("<:MHH_folder:1167409764414791691> - **It appears you have already setup your account for the generator. to reset your email or address please contact an Admin.**")
        else:


            address_embed = discord.Embed(title="<:MHH_folder:1167409764414791691> **GoatX Information Setup!** <:MHH_folder:1167409764414791691>", description="please click on both email and address buttons and fill out your info, keep in mind this is permanent and you cannot change this in the future so be careful and watch for any mistakes!", color=0xfafbff, timestamp=datetime.utcnow())
            address_embed.set_footer(text="GoatX")
            email = ""
            address = ""
            discord_id = ctx.author.id
            action_row = ConfirmationView(discord_id)
            confirmation_message  = await ctx.reply(embed=address_embed, view=action_row)

            #await ctx.send("<:error:1158482168989888602> **- It appears you haven't added an email, this will be your permanent email for the bot:**")




def setup(client):
    client.add_cog(Setup(client))
    
