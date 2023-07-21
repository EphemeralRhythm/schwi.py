import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter
import typing
from pymongo import MongoClient
from utils import embed_color


class World(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="map", aliases=["m"])
    async def map(self, ctx):
        await ctx.send("Map Command!")


async def setup(client):
    await client.add_cog(World(client))
