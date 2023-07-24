import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(title="Schwi Help")
        embed.description = """"""
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Help(client))
