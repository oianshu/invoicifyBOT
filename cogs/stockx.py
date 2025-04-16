import discord
from discord.ext import commands
import sqlite3
import re
import requests
import datetime
import re
from datetime import datetime, timedelta
import time, json

#mail shit

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import ssl

#shutil

import shutil

class EmailSendError(Exception):
    pass


def send_email(file_path, mail, product_name, mail_title):
  from_email = 'goatxreceipts@gmail.com'
  from_name = 'StockX'
  password = "hkdklsfntvavlyux"
  to_email = mail
  cleaned_title = product_name.split('-', 1)[0].strip()
  msg = MIMEMultipart('alternative')
  msg['From'] = f'{from_name} <{from_email}>'
  msg['To'] = to_email
  msg['Subject'] = f'{mail_title}'

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


class StockX(commands.Cog):
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
        print(f'Bot Loaded | stockx.py ✅')

    @commands.command()
    async def stockx(self, ctx):

        
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

        # Step 1
        await ctx.reply("**[1]** StockX Ordered\n**[2]** StockX Verified & Shipped\n**[3]** StockX Delivered")
        try:
            receipt_msg = await self.client.wait_for('message', check=lambda message: message.author == ctx.author and message.content in ['1', '2', '3'] and message.channel == ctx.channel)
            receipt_id = ''
            if receipt_msg.content == '1':
                receipt_id = 'StockX Ordered'
            elif receipt_msg.content == '2':
                receipt_id = 'StockX Verified & Shipped'
            elif receipt_msg.content == '3':
                receipt_id = 'StockX Delivered'
            await ctx.send(f"<:MHH_on:1167409295495794728>  **Successfully set receipt ID:** {receipt_id}")
        except Exception as e:
            await ctx.send("Invalid choice. Please try again.")
            print(e)
            return

        # Step 2
        await ctx.send("<:ActiveDevBadge:1160081415745056798> ** - Please enter StockX product link:**")
        try:
            product_link_msg = await self.client.wait_for('message', check=lambda message: message.author == ctx.author and message.content.startswith('https://stockx.com/') and message.channel == ctx.channel)
            product_link = product_link_msg.content

            # Check if the URL is a valid StockX URL
            if re.match(r'https://stockx\.com/[^/]+$', product_link):
                payload = {'api_key': api_key, 'url': product_link}
                response = requests.get('http://api.scraperapi.com', params=payload)
                if response.status_code == 200:
                    await ctx.send("<:MHH_code:1167409853627650139>  ** - Valid URL received**")
                else:
                    await ctx.send("<:error:1158482168989888602> **- This is not a stockx.com link, please try again with the proper link!**")
            else:
                await ctx.send("<:error:1158482168989888602> **- This is not a stockx.com link, please try again with the proper link!**")
        except Exception as e:
            await ctx.send("<:error:1158482168989888602> **- This is not a stockx.com link, please try again with the proper link!***")
            return

        # Step 3
        split_url = product_link.replace('https://stockx.com/', '')

        cookies = {
            'stockx_device_id': '7ab17656-41cd-4481-b0cf-c54ef481fa48',
            'language_code': 'en',
            '_pxvid': 'b8ca5f5e-70fc-11ee-8422-2a296cb3c8de',
            '__pxvid': 'b8e2b3ad-70fc-11ee-bbf9-0242ac120003',
            'rbuid': 'rbos-ae3b7341-b8b7-4abf-9106-0c7318cb7839',
            'stockx_homepage': 'sneakers',
            'stockx_session': '9779d771-4dc3-4761-a989-c60f9d7b2f33',
            '__cf_bm': 'BP9_bm4VgpgTaMXKUVDjyGwwkJtd5AY.8yaKfxOmss0-1698040350-0-AU1Bm2BGrFh9xvAWuxiKEkpXAdHqJSo2gLYXTEZtsOwDhj4FejZEEZx3WmxA2UKtsxgM26bsFZnjTj2aqY4ROMM=',
            'stockx_session_id': '1d14fe55-d65e-4d4a-83c9-b6e855f42f19',
            'stockx_selected_region': 'DE',
            'display_location_selector': 'false',
            'stockx_preferred_market_activity': 'sales',
            '_com.auth0.auth.%7B%7D_compat': '{%22nonce%22:null%2C%22state%22:%22{}%22%2C%22lastUsedConnection%22:%22production%22}',
            'com.auth0.auth.%7B%7D': '{%22nonce%22:null%2C%22state%22:%22{}%22%2C%22lastUsedConnection%22:%22production%22}',
            'cf_clearance': '.h5LfmQ05dYu9v0ZCFX6UTI6NadMjFK2W_3LKMLUYHU-1698040355-0-1-c41d8bb2.3ea50020.1f92092a-0.2.1698040355',
            'pxcts': '5ded36ad-7168-11ee-ae97-b2eecd0d15f0',
            'stockx_product_visits': '4',
            'forterToken': 'bfbe201bf8574bd5a8902373f27cb27c_1698040943304_55_UDF9b_13ck',
            '_px3': 'f9bd9bf8c278bf4d914ed8d9de24d47bc29988bcadd0e9bdee25e396e89c99c6:TBLungWSpiBI4jQdkHBLg5No6UUa1ZU2xc1hl2JvQ/ZTC4rCKWkU9qfb53K28z/GqunltWTausiKizd1w2e6Hg==:1000:VG/tRSk6dOZqiXbKcZN3DXoWluVHOmQVhsS5sAl7BH0sRlFJ+ujrXFIV/CMZbQz7lr/yejJVOSTH/NZ9D41+hH6n6xRMtHf6vrC4x2pPQO3yfaP59QTJaxq0sFP55ppPLNQM2pWr5Y5aUK0tDzFkvxyaTBO5jKyzPHr/JPzQwaWD8T1OsRUo1disYFdjP/q4rHOMwkDn2o4gZb9PzEK+6p3x8vrqviPGXWRcGSh++29d/mZN8PIW8Ub2B0y6DebY',
            '_pxde': '42b31983874885dc31bcebf81cee122910d418bdb0705e7a1fe2cbb9c8b90552:eyJ0aW1lc3RhbXAiOjE2OTgwNDA5NTAzMDMsImZfa2IiOjB9',
            '_dd_s': 'rum=0&expire=1698041849912&logs=1&id=001b4b7e-121e-4276-967e-502b45adbe75&created=1698040353073',
        }

        headers = {
            'authority': 'stockx.com',
            'accept': 'application/json',
            'accept-language': 'en-US',
            'apollographql-client-name': 'Iron',
            'apollographql-client-version': '2023.10.15.00',
            'app-platform': 'Iron',
            'app-version': '2023.10.15.00',
            'content-type': 'application/json',
            # 'cookie': 'stockx_device_id=7ab17656-41cd-4481-b0cf-c54ef481fa48; language_code=en; _pxvid=b8ca5f5e-70fc-11ee-8422-2a296cb3c8de; __pxvid=b8e2b3ad-70fc-11ee-bbf9-0242ac120003; rbuid=rbos-ae3b7341-b8b7-4abf-9106-0c7318cb7839; stockx_homepage=sneakers; stockx_session=9779d771-4dc3-4761-a989-c60f9d7b2f33; __cf_bm=BP9_bm4VgpgTaMXKUVDjyGwwkJtd5AY.8yaKfxOmss0-1698040350-0-AU1Bm2BGrFh9xvAWuxiKEkpXAdHqJSo2gLYXTEZtsOwDhj4FejZEEZx3WmxA2UKtsxgM26bsFZnjTj2aqY4ROMM=; stockx_session_id=1d14fe55-d65e-4d4a-83c9-b6e855f42f19; stockx_selected_region=DE; display_location_selector=false; stockx_preferred_market_activity=sales; _com.auth0.auth.%7B%7D_compat={%22nonce%22:null%2C%22state%22:%22{}%22%2C%22lastUsedConnection%22:%22production%22}; com.auth0.auth.%7B%7D={%22nonce%22:null%2C%22state%22:%22{}%22%2C%22lastUsedConnection%22:%22production%22}; cf_clearance=.h5LfmQ05dYu9v0ZCFX6UTI6NadMjFK2W_3LKMLUYHU-1698040355-0-1-c41d8bb2.3ea50020.1f92092a-0.2.1698040355; pxcts=5ded36ad-7168-11ee-ae97-b2eecd0d15f0; stockx_product_visits=4; forterToken=bfbe201bf8574bd5a8902373f27cb27c_1698040943304_55_UDF9b_13ck; _px3=f9bd9bf8c278bf4d914ed8d9de24d47bc29988bcadd0e9bdee25e396e89c99c6:TBLungWSpiBI4jQdkHBLg5No6UUa1ZU2xc1hl2JvQ/ZTC4rCKWkU9qfb53K28z/GqunltWTausiKizd1w2e6Hg==:1000:VG/tRSk6dOZqiXbKcZN3DXoWluVHOmQVhsS5sAl7BH0sRlFJ+ujrXFIV/CMZbQz7lr/yejJVOSTH/NZ9D41+hH6n6xRMtHf6vrC4x2pPQO3yfaP59QTJaxq0sFP55ppPLNQM2pWr5Y5aUK0tDzFkvxyaTBO5jKyzPHr/JPzQwaWD8T1OsRUo1disYFdjP/q4rHOMwkDn2o4gZb9PzEK+6p3x8vrqviPGXWRcGSh++29d/mZN8PIW8Ub2B0y6DebY; _pxde=42b31983874885dc31bcebf81cee122910d418bdb0705e7a1fe2cbb9c8b90552:eyJ0aW1lc3RhbXAiOjE2OTgwNDA5NTAzMDMsImZfa2IiOjB9; _dd_s=rum=0&expire=1698041849912&logs=1&id=001b4b7e-121e-4276-967e-502b45adbe75&created=1698040353073',
            'origin': 'https://stockx.com',
            'referer': 'https://stockx.com/nike-air-max-270-white-black',
            'sec-ch-ua': '"Chromium";v="118", "Brave";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'selected-country': 'DE',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'x-operation-name': 'GetProduct',
            'x-stockx-device-id': '7ab17656-41cd-4481-b0cf-c54ef481fa48',
            'x-stockx-session-id': '1d14fe55-d65e-4d4a-83c9-b6e855f42f19',
        }
        json_data = {
            'query': 'query GetProduct($id: String!, $currencyCode: CurrencyCode, $countryCode: String!, $marketName: String, $skipBadges: Boolean!, $skipSeo: Boolean!) {\n  product(id: $id) {\n    id\n    listingType\n    deleted\n    gender\n    browseVerticals\n    ...ProductMerchandisingFragment\n    ...AffirmCalloutFragment\n    ...BreadcrumbsFragment\n    ...BreadcrumbSchemaFragment\n    ...HazmatWarningFragment\n    ...HeaderFragment\n    ...NFTHeaderFragment\n    ...UrgencyBadgeFragment\n    ...MarketActivityFragment\n    ...MediaFragment\n    ...MyPositionFragment\n    ...ProductDetailsFragment\n    ...ProductMetaTagsFragment\n    ...ProductSchemaFragment\n    ...ScreenTrackerFragment\n    ...SizeSelectorWrapperFragment\n    ...StatsForNerdsFragment\n    ...ThreeSixtyImageFragment\n    ...TrackingFragment\n    ...UtilityGroupFragment\n    ...FavoriteProductFragment\n    ...ProductBadgeFragment\n  }\n}\n\nfragment ProductMerchandisingFragment on Product {\n  id\n  merchandising {\n    title\n    subtitle\n    image {\n      alt\n      url\n    }\n    body\n    trackingEvent\n    link {\n      title\n      url\n      urlType\n    }\n  }\n}\n\nfragment AffirmCalloutFragment on Product {\n  productCategory\n  urlKey\n  market(currencyCode: $currencyCode) {\n    bidAskData(country: $countryCode, market: $marketName) {\n      lowestAsk\n    }\n  }\n  variants {\n    id\n    market(currencyCode: $currencyCode) {\n      bidAskData(country: $countryCode, market: $marketName) {\n        lowestAsk\n      }\n    }\n  }\n}\n\nfragment BreadcrumbsFragment on Product {\n  breadcrumbs {\n    name\n    url\n    level\n  }\n}\n\nfragment BreadcrumbSchemaFragment on Product {\n  breadcrumbs {\n    name\n    url\n  }\n}\n\nfragment HazmatWarningFragment on Product {\n  id\n  hazardousMaterial {\n    lithiumIonBucket\n  }\n}\n\nfragment HeaderFragment on Product {\n  primaryTitle\n  secondaryTitle\n  condition\n  productCategory\n  reciprocal {\n    id\n    urlKey\n    variants {\n      id\n      traits {\n        size\n      }\n    }\n  }\n}\n\nfragment NFTHeaderFragment on Product {\n  primaryTitle\n  secondaryTitle\n  productCategory\n  editionType\n}\n\nfragment UrgencyBadgeFragment on Product {\n  id\n  productCategory\n  primaryCategory\n  sizeDescriptor\n  listingType\n  market(currencyCode: $currencyCode) {\n    ...LowInventoryBannerMarket\n  }\n  variants {\n    id\n    market(currencyCode: $currencyCode) {\n      ...LowInventoryBannerMarket\n    }\n  }\n  traits {\n    name\n    value\n    visible\n  }\n}\n\nfragment LowInventoryBannerMarket on Market {\n  bidAskData(country: $countryCode, market: $marketName) {\n    numberOfAsks\n    lowestAsk\n  }\n  salesInformation {\n    lastSale\n    salesLast72Hours\n  }\n}\n\nfragment MarketActivityFragment on Product {\n  id\n  title\n  productCategory\n  primaryTitle\n  secondaryTitle\n  media {\n    smallImageUrl\n  }\n}\n\nfragment MediaFragment on Product {\n  id\n  productCategory\n  title\n  brand\n  urlKey\n  variants {\n    id\n    hidden\n    traits {\n      size\n    }\n  }\n  media {\n    gallery\n    imageUrl\n  }\n}\n\nfragment MyPositionFragment on Product {\n  id\n  urlKey\n}\n\nfragment ProductDetailsFragment on Product {\n  id\n  title\n  productCategory\n  contentGroup\n  browseVerticals\n  description\n  gender\n  traits {\n    name\n    value\n    visible\n    format\n  }\n}\n\nfragment ProductMetaTagsFragment on Product {\n  id\n  urlKey\n  productCategory\n  brand\n  model\n  title\n  description\n  condition\n  styleId\n  breadcrumbs {\n    name\n    url\n  }\n  traits {\n    name\n    value\n  }\n  media {\n    thumbUrl\n    imageUrl\n  }\n  market(currencyCode: $currencyCode) {\n    bidAskData(country: $countryCode, market: $marketName) {\n      lowestAsk\n      numberOfAsks\n    }\n  }\n  variants {\n    id\n    hidden\n    traits {\n      size\n    }\n    market(currencyCode: $currencyCode) {\n      bidAskData(country: $countryCode, market: $marketName) {\n        lowestAsk\n      }\n    }\n  }\n  seo @skip(if: $skipSeo) {\n    meta {\n      name\n      value\n    }\n  }\n}\n\nfragment ProductSchemaFragment on Product {\n  id\n  urlKey\n  productCategory\n  brand\n  model\n  title\n  description\n  condition\n  styleId\n  traits {\n    name\n    value\n  }\n  media {\n    thumbUrl\n    imageUrl\n  }\n  market(currencyCode: $currencyCode) {\n    bidAskData(country: $countryCode, market: $marketName) {\n      lowestAsk\n      numberOfAsks\n    }\n  }\n  variants {\n    id\n    hidden\n    traits {\n      size\n    }\n    market(currencyCode: $currencyCode) {\n      bidAskData(country: $countryCode, market: $marketName) {\n        lowestAsk\n      }\n    }\n    gtins {\n      type\n      identifier\n    }\n  }\n}\n\nfragment ScreenTrackerFragment on Product {\n  id\n  brand\n  productCategory\n  primaryCategory\n  title\n  market(currencyCode: $currencyCode) {\n    bidAskData(country: $countryCode, market: $marketName) {\n      highestBid\n      lowestAsk\n      numberOfAsks\n      numberOfBids\n    }\n    salesInformation {\n      lastSale\n    }\n  }\n  media {\n    imageUrl\n  }\n  traits {\n    name\n    value\n  }\n  variants {\n    id\n    traits {\n      size\n    }\n    market(currencyCode: $currencyCode) {\n      bidAskData(country: $countryCode, market: $marketName) {\n        highestBid\n        lowestAsk\n        numberOfAsks\n        numberOfBids\n      }\n      salesInformation {\n        lastSale\n      }\n    }\n  }\n  tags\n  reciprocal {\n    id\n    variants {\n      id\n    }\n  }\n}\n\nfragment SizeSelectorWrapperFragment on Product {\n  id\n  ...SizeSelectorFragment\n  ...SizeSelectorHeaderFragment\n  ...SizesFragment\n  ...SizesOptionsFragment\n  ...SizeChartFragment\n  ...SizeChartContentFragment\n  ...SizeConversionFragment\n  ...SizesAllButtonFragment\n}\n\nfragment SizeSelectorFragment on Product {\n  id\n  title\n  productCategory\n  browseVerticals\n  sizeDescriptor\n  availableSizeConversions {\n    name\n    type\n  }\n  defaultSizeConversion {\n    name\n    type\n  }\n  variants {\n    id\n    hidden\n    traits {\n      size\n    }\n    sizeChart {\n      baseSize\n      baseType\n      displayOptions {\n        size\n        type\n      }\n    }\n  }\n}\n\nfragment SizeSelectorHeaderFragment on Product {\n  sizeDescriptor\n  productCategory\n  availableSizeConversions {\n    name\n    type\n  }\n}\n\nfragment SizesFragment on Product {\n  id\n  productCategory\n  listingType\n  title\n}\n\nfragment SizesOptionsFragment on Product {\n  id\n  listingType\n  variants {\n    id\n    hidden\n    group {\n      shortCode\n    }\n    traits {\n      size\n    }\n    sizeChart {\n      baseSize\n      baseType\n      displayOptions {\n        size\n        type\n      }\n    }\n    market(currencyCode: $currencyCode) {\n      bidAskData(country: $countryCode, market: $marketName) {\n        lowestAsk\n      }\n      state(country: $countryCode) {\n        numberOfCustodialAsks\n        lowestCustodialAsk {\n          amount\n        }\n      }\n    }\n  }\n}\n\nfragment SizeChartFragment on Product {\n  availableSizeConversions {\n    name\n    type\n  }\n  defaultSizeConversion {\n    name\n    type\n  }\n}\n\nfragment SizeChartContentFragment on Product {\n  availableSizeConversions {\n    name\n    type\n  }\n  defaultSizeConversion {\n    name\n    type\n  }\n  variants {\n    id\n    sizeChart {\n      baseSize\n      baseType\n      displayOptions {\n        size\n        type\n      }\n    }\n  }\n}\n\nfragment SizeConversionFragment on Product {\n  productCategory\n  browseVerticals\n  sizeDescriptor\n  availableSizeConversions {\n    name\n    type\n  }\n  defaultSizeConversion {\n    name\n    type\n  }\n}\n\nfragment SizesAllButtonFragment on Product {\n  id\n  sizeAllDescriptor\n  market(currencyCode: $currencyCode) {\n    bidAskData(country: $countryCode, market: $marketName) {\n      lowestAsk\n    }\n    state(country: $countryCode) {\n      numberOfCustodialAsks\n      lowestCustodialAsk {\n        amount\n      }\n    }\n  }\n}\n\nfragment StatsForNerdsFragment on Product {\n  id\n  title\n  productCategory\n  sizeDescriptor\n  urlKey\n}\n\nfragment ThreeSixtyImageFragment on Product {\n  id\n  title\n  variants {\n    id\n  }\n  productCategory\n  media {\n    all360Images\n  }\n}\n\nfragment TrackingFragment on Product {\n  id\n  productCategory\n  primaryCategory\n  brand\n  title\n  market(currencyCode: $currencyCode) {\n    bidAskData(country: $countryCode, market: $marketName) {\n      highestBid\n      lowestAsk\n    }\n  }\n  variants {\n    id\n    market(currencyCode: $currencyCode) {\n      bidAskData(country: $countryCode, market: $marketName) {\n        highestBid\n        lowestAsk\n      }\n    }\n  }\n}\n\nfragment UtilityGroupFragment on Product {\n  id\n  ...PortfolioFragment\n  ...PortfolioContentFragment\n  ...ShareFragment\n}\n\nfragment PortfolioFragment on Product {\n  id\n  title\n  productCategory\n  variants {\n    id\n  }\n  traits {\n    name\n    value\n  }\n}\n\nfragment PortfolioContentFragment on Product {\n  id\n  productCategory\n  sizeDescriptor\n  variants {\n    id\n    traits {\n      size\n    }\n  }\n}\n\nfragment ShareFragment on Product {\n  id\n  productCategory\n  title\n  media {\n    imageUrl\n  }\n}\n\nfragment FavoriteProductFragment on Product {\n  favorite\n}\n\nfragment ProductBadgeFragment on Product {\n  badges(currencyCode: $currencyCode, market: $marketName, version: 2) @skip(if: $skipBadges) {\n    badgeID\n    title\n    subtitle\n    context {\n      key\n      value\n      format\n    }\n    backgroundColor\n    borderColor\n    icon {\n      url\n      alt\n    }\n    trackingEvent\n  }\n  variants {\n    badges(currencyCode: $currencyCode, market: $marketName, version: 2) @skip(if: $skipBadges) {\n      badgeID\n      title\n      subtitle\n      context {\n        key\n        value\n        format\n      }\n      backgroundColor\n      borderColor\n      icon {\n        url\n        alt\n      }\n      trackingEvent\n    }\n  }\n}',
            'variables': {
                'id': split_url,
                'currencyCode': 'EUR',
                'countryCode': 'DE',
                'marketName': 'DE',
                'skipBadges': True,
                'skipSeo': False,
            },
            'operationName': 'GetProduct',
        }
        response = requests.post('https://stockx.com/api/p/e', cookies=cookies, headers=headers, json=json_data)
        response_data = response.json()
        sizes = {}
        size_types = set()
        null = ""
        true = ""
        false = ""
        for variant in response_data["data"]["product"]["variants"]:
            for display_option in variant["sizeChart"]["displayOptions"]:
                size = display_option["size"]
                size_type = display_option["type"]
                size_types.add(size_type)
                if size_type not in sizes:
                    sizes[size_type] = []
                sizes[size_type].append(size)
        title = response_data['data']['product']['title']
        url_key = response_data['data']['product']['urlKey']
        style_id = response_data['data']['product']['styleId']
        condition = response_data['data']['product']['condition']
        small_image = response_data['data']['product']['media']['smallImageUrl']
        image_link_cut = small_image.split('?')[0]
        custom_type_names = {
            "eu": "**EU** 🇪🇺",
            "us w": "**United States** 🇺🇸 - Women",
            "us m": "**United States** 🇺🇸 - Men",
            "uk": "**UK** 🇬🇧",
            "kr": "**Korea** 🇰🇷",
            "cm": "**CM**",
        }

        def split_message(message):
            max_length = 2000
            message_parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
            return message_parts

        message = ""
        size_options = []
        size_counter = 1

        for size_type in size_types:
            if size_type == 'kr':
                continue
            if size_type == 'cm':
                continue
            new_message = f"{custom_type_names.get(size_type, size_type)}:\n"
            sizes_for_type = sizes[size_type]

            for size in sizes_for_type:
                if len(new_message) + len(f"**[{size_counter}] {size}\n") > 2000:
                    message_parts = split_message(new_message)
                    if len(message_parts) > 1:
                        # If the message was split, adjust the last part
                        last_part = message_parts[-1]
                        last_part += f"[{size_counter}] {size}\n"
                        message_parts[-1] = last_part

                    for part in message_parts:
                        await ctx.send(part)
                    new_message = ""
                new_message += f"**[{size_counter}]** {size}\n"
                size_options.append(size)
                size_counter += 1

            message += new_message

        # Send the message parts
        message_parts = split_message(message)
        if len(message_parts) > 1:
            # If the message was split, adjust the last part
            last_part = message_parts[-1]
            last_part += f"[{size_counter}] {size}\n"
            message_parts[-1] = last_part

        for part in message_parts:
            await ctx.send(part)
        await ctx.send("Please choose a size by responding with an integer, e.g., '1' or '2'.")



        def check(response):
            return response.author == ctx.author and response.content.isdigit() and 1 <= int(response.content) <= len(size_options) and response.channel == ctx.channel

        try:
            response = await self.client.wait_for('message', check=check, timeout=60)
            selected_size_index = int(response.content) - 1
            selected_size = size_options[selected_size_index]
            await ctx.send(f"Successfully set size: {selected_size}")
        except Exception as e:
            await ctx.send("Invalid size selection. Please try again.")

            
            
        if receipt_id == "StockX Delivered":
            await ctx.send("<:Timer:1167121901722804315> **- Please enter the delivery date (format: 28 September 2023):**")
        else:
            await ctx.send("<:Timer:1167121901722804315> **- Please enter the estimated arrival date (format: 28 September 2023):**")


        def check_date_format(message):
            return message.author == ctx.author and re.match(r'\d{1,2}\s\w+\s\d{4}', message.content) and message.channel == ctx.channel

        try:
            arrival_date_msg = await self.client.wait_for('message', check=check_date_format, timeout=60)
            arrival_date = arrival_date_msg.content
            print(arrival_date_msg.content)
            if receipt_id == "StockX Delivered":
                await ctx.send(f"Successfully set delivery date: {arrival_date}")
            else:
                await ctx.send(f"Successfully set estimated arrival date: {arrival_date}")
        except Exception as e:
            await ctx.send("<:MHH_DND:1153047517995487283> ** - Invalid date format. Please try again.**")
            print(e)
            return



        pattern = r'\d{1,2}\s\w+\s\d{4}'
        match = re.search(pattern, arrival_date)

        if match:
            date_str = match.group(0)
            month_dict = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
            }

            date_obj = datetime.strptime(date_str, "%d %B %Y")

            future_date = date_obj + timedelta(days=5)
            result_string = future_date.strftime("%d %B %Y")

            print(result_string)
        else:
            print("Date not found in the input string.")


        # Step 5: Enter Price
        await ctx.send("💶** - Please enter a price (no currency):**")

        def check_price(response):
            return response.author == ctx.author and response.content.replace(".", "", 1).isdigit() and response.channel == ctx.channel

        try:
            price_msg = await self.client.wait_for('message', check=check_price, timeout=60)
            price_final_string = price_msg.content
            await ctx.send(f"Successfully set price: {price_final_string}")
        except Exception as e:
            await ctx.send("Invalid price format. Please try again.")
            return

        # Step 6: Choose Currency
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

        confirmation_embed = discord.Embed(title="Confirmation", description="", color=0x42f56c, timestamp=datetime.utcnow())
        confirmation_embed.add_field(name="Email", value=email)
        confirmation_embed.add_field(name="Product Link", value=product_link, inline=False)
        confirmation_embed.add_field(name="Product Size", value=selected_size, inline=False)
        confirmation_embed.add_field(name="Currency", value=selected_currency, inline=False)
        confirmation_embed.set_footer(text="GoatX")
        
        class ConfirmationView(discord.ui.View):
            def __init__(self, onetime_cursor, new_uses, discord_id, mail_title):
                super().__init__()
                self.mail_title = mail_title
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


            
                    def random_string_func(length=8):
                        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        return ''.join(random.choice(letters) for _ in range(length))
                    #await interaction.response.send_message(f"<:MHH_icons_join:1167409237664735303> ** -  Successfully Sent Receipt to Email**")


                    import random
                    import string
                    first_part = ''.join(random.choice(string.digits) for _ in range(8))
                    second_part = ''.join(random.choice(string.digits) for _ in range(8))

                    random_string = first_part + '-' + second_part
                    if receipt_id == "StockX Ordered":
                        source_path = 'templates/stockx_ordered.html'
                        temp_path = f'temp/stockx_ordered_{random_string_func()}.html'
                    elif receipt_id == "StockX Verified & Shipped":
                        source_path = 'templates/stockx_verified_shipped.html'
                        temp_path = f'temp/stockx_verified_shipped_{random_string_func()}.html'
                    elif receipt_id == "StockX Delivered":
                        source_path = 'templates/stockx_delivered.html'
                        temp_path = f'temp/stockx_delivered_{random_string_func()}.html'
                    shutil.copy(source_path, temp_path)
                    replacements = {
                        'estimated_arrival': arrival_date + " - " + result_string,
                        'item_style_id': style_id,
                        'date_smth_kys': result_string,
                        'item_size': selected_size,
                        'order_number': random_string,
                        'price_1': currency_symbol + price_final_string,
                        'item_title': title,
                        'item_condition': condition,
                        'product_image_url_part': image_link_cut
                    }

                    if currency_symbol == '$':
                        price = 16.37
                        price_str = str(price)
                        price_shipping = 16.74
                        price_shipping_str = str(price_shipping)

                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str

                    elif currency_symbol == '£':
                        price = 17.37
                        price_str = str(price)
                        price_shipping = 17.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str
                    elif currency_symbol == '€':
                        price = 15.37
                        price_str = str(price)
                        price_shipping = 15.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str                    

                    elif currency_symbol == 'C$':
                        price = 16.37
                        price_str = str(price)
                        price_shipping = 16.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str                    

                    elif currency_symbol == 'A$':
                        price = 15.37
                        price_str = str(price)
                        price_shipping = 15.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str                    

                    with open(temp_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        for old_text, new_text in replacements.items():
                            content = re.sub(old_text, new_text, content)
                    with open(temp_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    email_sent_successfully = True

                    try:
                        send_email(temp_path, email, title, mail_title)
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
            def __init__(self, discord_id, mail_title):
                super().__init__()
                self.mail_title = mail_title
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



                    def random_string_func(length=8):
                        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
                        return ''.join(random.choice(letters) for _ in range(length))



                    import random
                    import string
                    first_part = ''.join(random.choice(string.digits) for _ in range(8))
                    second_part = ''.join(random.choice(string.digits) for _ in range(8))

                    random_string = first_part + '-' + second_part
                    if receipt_id == "StockX Ordered":
                        source_path = 'templates/stockx_ordered.html'
                        temp_path = f'temp/stockx_ordered_{random_string_func()}.html'
                    elif receipt_id == "StockX Verified & Shipped":
                        source_path = 'templates/stockx_verified_shipped.html'
                        temp_path = f'temp/stockx_verified_shipped_{random_string_func()}.html'
                    elif receipt_id == "StockX Delivered":
                        source_path = 'templates/stockx_delivered.html'
                        temp_path = f'temp/stockx_delivered_{random_string_func()}.html'
                    shutil.copy(source_path, temp_path)
                    replacements = {
                        'estimated_arrival': arrival_date + " - " + result_string,
                        'item_style_id': style_id,
                        'date_smth_kys': result_string,
                        'item_size': selected_size,
                        'order_number': random_string,
                        'price_1': currency_symbol + price_final_string,
                        'item_title': title,
                        'item_condition': condition,
                        'product_image_url_part': image_link_cut
                    }

                    if currency_symbol == '$':
                        price = 16.37
                        price_str = str(price)
                        price_shipping = 16.74
                        price_shipping_str = str(price_shipping)

                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str

                    elif currency_symbol == '£':
                        price = 17.37
                        price_str = str(price)
                        price_shipping = 17.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str
                    elif currency_symbol == '€':
                        price = 15.37
                        price_str = str(price)
                        price_shipping = 15.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str                    

                    elif currency_symbol == 'C$':
                        price = 16.37
                        price_str = str(price)
                        price_shipping = 16.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str                    

                    elif currency_symbol == 'A$':
                        price = 15.37
                        price_str = str(price)
                        price_shipping = 15.74
                        price_shipping_str = str(price_shipping)
                        replacements['price_2'] = currency_symbol + price_str
                        replacements['price_3'] = currency_symbol + price_shipping_str
                        price_item_int = int(float(price_final_string))
                        price_total = price_item_int + price + price_shipping
                        price_total_str = str(price_total)
                        replacements['price_total'] = currency_symbol + price_total_str                    

                    with open(temp_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        for old_text, new_text in replacements.items():
                            content = re.sub(old_text, new_text, content)
                    with open(temp_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    send_email(temp_path, email, title, mail_title)
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

        if receipt_id == "StockX Delivered":
            mail_title = f"🎉 Order Delivered: {title}"
        elif receipt_id == "StockX Ordered":
            mail_title = f"👍 Order Confirmed: {title}"
        elif receipt_id == "StockX Verified & Shipped":
            mail_title = f" ✅ Order Verified & Shipped: {title}"
        if not subscription_result:
            action_row = ConfirmationView(self.onetime_cursor, onetime_uses, discord_id, mail_title)
        else:
            action_row = ConfirmationView2(discord_id, mail_title)
        # Send Embed with Buttons
        confirmation_message  = await ctx.reply(embed=confirmation_embed, view=action_row)



def setup(client):
    client.add_cog(StockX(client))
