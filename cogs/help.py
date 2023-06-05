import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter
import typing
from pymongo import MongoClient
from utils import embed_color

class Help(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(name = 'help')
    async def help(self,ctx):
        embed = discord.Embed(color= embed_color, title="Schwi Help")
        embed.description = """"""
        await ctx.send(embed=embed)
    
async def setup(client):
   await client.add_cog(Help(client))
