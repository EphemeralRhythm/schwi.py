import discord
from discord.ext import commands

color = (discord.Color.from_rgb(201, 0, 118),)


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(title="Schwi Help")
        description = "The detailed list of commands can be viewed [here](https://discord.com/channels/899204296275550249/998967114314559498/1137757084650315856)"

        description += (
            "\n\nList of Commands: "
            + "**Levels:**\n`rank` `top`\n\n"
            + "**Disboard:**\n`map` `command` `pings` `getpings` `units` `give` "
            + "`inv` `status` `statusall` `reassign`"
        )
        embed.description = description
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Help(client))
