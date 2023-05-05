import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter
import typing
from pymongo import MongoClient

class Help(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(name = 'help')
    async def help(self,ctx):
        await ctx.send("No.")
        
async def setup(client):
   await client.add_cog(Help(client))
