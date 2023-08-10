import discord
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if not message.guild:
                logs = self.client.get_channel(1103882731890425887)

                embed = discord.Embed(title="DM recieved")
                description = f"Author: {message.author.name}\n\n"
                description += message.content
                embed.description = description

                await logs.send(embed=embed)

    @commands.command(name="say")
    async def help(self, ctx, *, args):
        if ctx.author.id != 660929334969761792:
            return
        await ctx.message.delete()
        await ctx.send(args)

    @commands.command(name="dm")
    async def dm(self, ctx, member: discord.Member, *, args):
        if ctx.author.id != 660929334969761792:
            return
        await member.send(args)


async def setup(client):
    await client.add_cog(Admin(client))
