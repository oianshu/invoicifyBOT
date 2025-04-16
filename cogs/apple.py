import discord
from discord.ext import commands
import sqlite3
import re
import requests
import datetime
import re
from datetime import datetime, timedelta
import time, json
from bs4 import BeautifulSoup
#mail shit

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import ssl

#shutil

import shutil

class EmailSendError(Exception):
    pass


def send_email(file_path, mail, product_name):
  from_email = 'goatxreceipts@gmail.com'
  from_name = 'Apple'
  password = "hkdklsfntvavlyux"
  to_email = mail
  cleaned_title = product_name.split('-', 1)[0].strip()
  msg = MIMEMultipart('alternative')
  msg['From'] = f'{from_name} <{from_email}>'
  msg['To'] = to_email
  msg['Subject'] = f"We're processing your order {product_name}"

  with open(file_path, 'rb') as attachment:
    # Read the bytes and decode to a string
    file_content = attachment.read().decode('utf-8')

    part = MIMEText(file_content, 'html')
    msg.attach(part)

  try:
    simple_email_context = ssl.create_default_context()
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls(context=simple_email_context)
    server.login(from_email, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()
  except Exception as e:
      error_message = str(e)
      raise EmailSendError(error_message)
  return True

class Apple(commands.Cog):
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

        self.subscription_db = sqlite3.connect('subscriptions.db')
        self.subscription_cursor = self.subscription_db.cursor()
        self.subscription_cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                                        discord_id INTEGER PRIMARY KEY,
                                        subscription_expiry INTEGER
                                    )''')
        self.subscription_db.commit()

        self.onetime_db = sqlite3.connect('onetime_uses.db')
        self.onetime_cursor = self.onetime_db.cursor()
        self.onetime_cursor.execute('''CREATE TABLE IF NOT EXISTS onetime_uses (
                                        discord_id INTEGER PRIMARY KEY,
                                        uses INTEGER
                                    )''')
        self.onetime_db.commit()



    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | apple.py ✅')


    @commands.command()
    async def apple(self, ctx):
        
        with open('scrape_api.json', 'r') as file:
                    scrape_api_data = json.load(file)
                    api_key = scrape_api_data.get('api_key')



        discord_id = ctx.author.id
        self.subscription_cursor.execute('SELECT subscription_expiry FROM subscriptions WHERE discord_id = ?', (discord_id,))
        subscription_result = self.subscription_cursor.fetchone()
        self.onetime_cursor.execute('SELECT uses FROM onetime_uses WHERE discord_id = ?', (discord_id,))
        onetime_result = self.onetime_cursor.fetchone()

        if subscription_result:
            subscription_expiry = subscription_result[0]
            current_timestamp = int(time.time())
            if subscription_expiry < current_timestamp:
                await ctx.send("You don't have a valid subscription or one-time use. Please buy gen access by running !prices")
                return
        elif onetime_result:
            onetime_uses = onetime_result[0]
            if onetime_uses > 0:
                await ctx.send(f"<:MHH_on:1167409295495794728>  *You have {onetime_uses} receipts currently. As soon as the Email gets send. One of your onetime-Receipts will be removed*")
            else:
                await ctx.send("You don't have a valid subscription or one-time use. Please buy gen access by running !prices")
                return
        else:
            await ctx.send("You don't have a valid subscription or one-time use. Please buy gen access by running !prices")
            return
            


        self.cursor.execute('SELECT email, address FROM users WHERE discord_id = ?', (discord_id,))
        result = self.cursor.fetchone()
        if result:
            email, address = result
        else:
            await ctx.send("<:MHH_folder:1167409764414791691> **- It appears you haven't setup your account for the generator yet, please run !setup to start using the generator**")
            return
        await ctx.send("Make sure you click the Buy Button on the apple website, choose the colourway and then copy the product link")
        await ctx.send("place holder :3")
        await ctx.reply("`Please enter Apple Product Link:`")
        try:
            product_link_msg = await self.client.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
            product_link = product_link_msg.content

            if product_link.startswith('https://www.apple.com/uk/shop/'):
                payload = {'api_key': api_key, 'url': product_link}
                response = requests.get('http://api.scraperapi.com', params=payload)

                if response.status_code == 200:
                    await ctx.send("<:MHH_code:1167409853627650139>  ** - Valid URL received**")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    og_image_tag = soup.find('meta', attrs={'property': 'og:image'})
                    og_title_tag = soup.find('meta', attrs={'property': 'og:title'})

                    if og_image_tag and 'content' in og_image_tag.attrs:
                        image_url = og_image_tag['content']

                    if og_title_tag and 'content' in og_title_tag.attrs:
                        title = og_title_tag['content']
                else:
                    await ctx.send("<:error:1158482168989888602> **- This is not an apple.com/uk link, please try again with the proper link!**")
            else:
                await ctx.send("<:error:1158482168989888602> **- The link you entered does not start with 'https://www.apple.com/uk/shop/', please try again with the proper link!**")
        except Exception as e:
            await ctx.send("<:error:1158482168989888602> **- This is not a valid Apple link, please try again with the proper link!**")
            return

        def check_date_format(message):
            return (message.author == ctx.author and re.match(r'\d{2}/\d{2}/\d{2}', message.content) and message.channel == ctx.channel)

        try:
            await ctx.send("`Please enter order date (eg. 20/06/23):`")
            arrival_date_msg = await self.client.wait_for('message', check=check_date_format, timeout=60)
            arrival_date = arrival_date_msg.content
            print(arrival_date_msg.content)
        except Exception as e:
            await ctx.send("<:MHH_DND:1153047517995487283> ** - Invalid date format. Please try again.**")
            print(e)


        def check_price(response):
            try:
                price = float(response.content)
                return response.author == ctx.author and price >= 0 and response.channel == ctx.channel
            except ValueError:
                return False

        try:
            await ctx.send("Please enter a price (no currency symbol):")
            price_msg = await self.client.wait_for('message', check=check_price, timeout=60)
            price = float(price_msg.content)
            await ctx.send(f"Successfully set the price to {price}")
        except Exception as e:
            await ctx.send("Invalid price format. Please try again.")

        await ctx.send("**[1]** USD :dollar:\n**[2]** GBP :pound:\n**[3]** EUR :euro:\n**[4]** CAD :flag_ca:\n**[5]** AUD :flag_au:")
        await ctx.send("Please enter currency ID (1-5):")

        def check_currency(response):
            return response.author == ctx.author and response.content.isdigit() and 1 <= int(response.content) <= 5 and response.channel == ctx.channel

        currency_symbols = ["USD", "GBP", "EUR", "CAD", "AUD"]

        try:
            currency_msg = await self.client.wait_for('message', check=check_currency, timeout=60)
            currency_id = int(currency_msg.content) - 1
            selected_currency = currency_symbols[currency_id]
            await ctx.send(f"Successfully set currency to {selected_currency}")
        except Exception as e:
            await ctx.send("Invalid currency selection. Please try again.")
            return
        
        currency_symbols = {
            "USD": "$",
            "GBP": "£",
            "EUR": "€",
            "CAD": "C$",
            "AUD": "A$"
        }

        def code_to_symbol(code):
            return currency_symbols.get(code, code)
        currency_symbol = code_to_symbol(selected_currency)
        print(f"{selected_currency} is represented as {currency_symbol}")

        
        import random
        import string

        random_uppercase_letter = random.choice(string.ascii_uppercase)
        random_digits = ''.join(random.choices(string.digits, k=10))
        random_string_apple = random_uppercase_letter + random_digits


        def check_name(response):
            # Check if the message content contains two or more words (first name and last name)
            names = response.content.split()
            return (
                response.author == ctx.author
                and len(names) >= 2
                and all(word.isalpha() for word in names)
                and response.channel == ctx.channel
            )

        try:
            await ctx.send("`Please enter full name (forename and surname):`")
            name_msg = await self.client.wait_for('message', check=check_name, timeout=60)
            user_name = name_msg.content
            await ctx.send(f"Successfully set your name to {user_name}")
        except Exception as e:
            await ctx.send("Invalid name format. Please try again.")


        class ConfirmationView(discord.ui.View):
            def __init__(self, onetime_cursor, new_uses, discord_id):
                super().__init__()
                self.onetime_cursor = onetime_cursor
                self.new_uses = new_uses
                self.discord_id = discord_id
                self.used_selects = set()

            async def interaction_check(self,interaction: discord.MessageInteraction) -> bool:
                if interaction.user.id != self.discord_id:
                    await interaction.response.send_message(content="You don't have permission to press this button.",ephemeral=True)
                    return False
                else:
                    return True
                
            @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
            async def yes_button_callback(self, button, interaction):
                if interaction.user.id not in self.used_selects:
                    self.used_selects.add(interaction.user.id)
                    button.disabled = True
                    # Modify the original message to display the "Confirmed" embed
                    confirmed_embed = discord.Embed(
                        title="Confirmed", description="Information confirmed!", color=0x42f56c
                    )
                    
                    await interaction.response.edit_message(embed=confirmed_embed,view=self)


                    price_gay = float(price)
                    price_str = str(price)
                    price_gay_2 = price_gay + 8
                    price_gay_2_str = str(price_gay_2)
                    def random_string_func(length=8):
                        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        return ''.join(random.choice(letters) for _ in range(length))

                    source_path = 'templates/apple.html'
                    temp_path = f'temp/apple_{random_string_func()}.html'
                    shutil.copy(source_path, temp_path)
                    replacements = {
                        'product_title': title,
                        'product_price': currency_symbol + price_str,
                        'customer_name': user_name,
                        'customer_street': street_ady,
                        'customer_city': city,
                        'customer_zip': zip_code,
                        'customer_country': country,
                        'customer_email': email,
                        'price_tax': currency_symbol + "8.00",
                        'price_total': currency_symbol + price_gay_2_str,
                        'product_image': image_url,
                        'order_number': random_string_apple,
                        'arrival_date': arrival_date
                    }                 

                    with open(temp_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        for old_text, new_text in replacements.items():
                            content = re.sub(old_text, new_text, content)
                    with open(temp_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    email_sent_successfully = True

                    try:
                        send_email(temp_path, email, random_string_apple)
                    except EmailSendError as e:
                        email_sent_successfully = False
                        await ctx.send(f"Failed to send the email: {str(e)}")

                    # Deduct one-time use only if the email was sent successfully
                    if email_sent_successfully:
                        if onetime_result:
                            onetime_uses = onetime_result[0]
                            if onetime_uses > 0:
                                new_uses = onetime_uses - 1
                                self.onetime_cursor.execute('UPDATE onetime_uses SET uses = ? WHERE discord_id = ?', (new_uses, discord_id))
                                self.onetime_cursor.connection.commit()

                    if email_sent_successfully:
                        await ctx.send(f"<:MHH_icons_join:1167409237664735303> ** -  Successfully Sent Receipt to Email**")
                    else:
                        await ctx.send("Email was not sent due to an error. Please try again.")
                else:
                    await interaction.response.send_message("This button can only be used once.", ephemeral=True)


            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def no_button_callback(self, button, interaction):
                self.disable_all_items()
                cancel = discord.Embed(
                    title="Cancelled!", description="**Generating Canceled Succesfuly** <:MHH_DND:1153047517995487283>", color=0xff0000
                )
                    
                await interaction.response.edit_message(embed=cancel,view=self)
                return


        class ConfirmationView2(discord.ui.View):
            def __init__(self, discord_id):
                super().__init__()
                self.used_selects = set()
                self.discord_id = discord_id

            async def interaction_check(self,interaction: discord.MessageInteraction) -> bool:
                if interaction.user.id != self.discord_id:
                    await interaction.response.send_message(content="You don't have permission to press this button.",ephemeral=True)
                    return False
                else:
                    return True
                
            @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
            async def yes_button_callback(self, button, interaction):
                if interaction.user.id not in self.used_selects:
                    self.used_selects.add(interaction.user.id)
                    button.disabled = True
                    confirmed_embed = discord.Embed(
                        title="Confirmed", description="Information confirmed!", color=0x42f56c
                    )
                    await interaction.response.edit_message(embed=confirmed_embed,view=self)


                    price_gay = float(price)
                    price_gay_2 = price_gay + 8
                    price_gay_2_str = str(price_gay_2)
                    price_str = str(price)
                    def random_string_func(length=8):
                        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        return ''.join(random.choice(letters) for _ in range(length))

                    source_path = 'templates/apple.html'
                    temp_path = f'temp/apple_{random_string_func()}.html'
                    shutil.copy(source_path, temp_path)
                    replacements = {
                        'product_title': title,
                        'product_price': currency_symbol + price_str,
                        'customer_name': user_name,
                        'customer_street': street_ady,
                        'customer_city': city,
                        'customer_zip': zip_code,
                        'customer_country': country,
                        'customer_email': email,
                        'price_tax': currency_symbol + "8.00",
                        'price_total': currency_symbol + price_gay_2_str,
                        'product_image': image_url,
                        'order_number': random_string_apple,
                        'arrival_date': arrival_date
                    }           

                    with open(temp_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        for old_text, new_text in replacements.items():
                            content = re.sub(old_text, new_text, content)
                    with open(temp_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    send_email(temp_path, email, random_string_apple)
                    await ctx.send(f"<:MHH_icons_join:1167409237664735303> ** -  Successfully Sent Receipt to Email**")
                
                else:
                    await interaction.response.send_message("This button can only be used once.", ephemeral=True)


            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def no_button_callback(self, button, interaction):
                self.disable_all_items()
                cancel = discord.Embed(
                    title="Cancelled!", description="**Generating Canceled Succesfuly** <:MHH_DND:1153047517995487283>", color=0xff0000
                )
                    
                await interaction.response.edit_message(embed=cancel,view=self)
                return
            
        confirmation_embed = discord.Embed(title="Confirmation", description="s", color=0x42f56c, timestamp=datetime.utcnow())
        confirmation_embed.add_field(name="Email", value=email)
        confirmation_embed.add_field(name="Product Link", value=product_link, inline=False)
        confirmation_embed.add_field(name="Price", value=price, inline=False)
        confirmation_embed.add_field(name="Order Number", value=random_string_apple, inline=False)
        confirmation_embed.add_field(name="Currency", value=currency_symbol, inline=False)
        confirmation_embed.set_footer(text="GoatX")
        
        self.cursor.execute('SELECT address FROM users WHERE discord_id = ?', (discord_id,))
        resultasdas = self.cursor.fetchone()
        if resultasdas:
            address = resultasdas[0] 
            address_parts = address.split(',')
            if len(address_parts) == 4:
                street_ady, city, zip_code, country = map(str.strip, address_parts)
                print(f"Street: {street_ady}, City: {city}, Zip Code: {zip_code}, Country: {country}")
            else:
                print("Address format is incorrect. Expected 4 parts separated by commas.")
        if not subscription_result:
            action_row = ConfirmationView(self.onetime_cursor, onetime_uses, discord_id)
        else:
            action_row = ConfirmationView2(discord_id)
        confirmation_message = await ctx.reply(embed=confirmation_embed, view=action_row)
        
def setup(client):
    client.add_cog(Apple(client))
