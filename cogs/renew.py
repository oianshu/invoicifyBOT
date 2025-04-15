import discord
from discord.ext import commands
import json

class RenewCog(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Bot Loaded | renew.py✅')



    @commands.command()
    @commands.has_permissions(administrator=True)
    async def renew(self, ctx, api_key):
        # Load the existing JSON data
        try:
            with open('scrape_api.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}

        # Update the API key
        data['api_key'] = api_key

        # Save the updated JSON data
        with open('scrape_api.json', 'w') as file:
            json.dump(data, file, indent=4)

        await ctx.send(f"API key has been renewed to: {api_key}")

def setup(client):
    client.add_cog(RenewCog(client))
