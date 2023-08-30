import discord
from discord.ext import commands
import typing
from utils.database import resources_collection, units_collection, dead_collection
import utils.emoji


class Economy(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="inv")
    async def inv(self, ctx, member: typing.Optional[discord.Member] = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"{member.name}'s Inventory",
            color=discord.Color.from_rgb(201, 0, 118),
        )

        player_post = resources_collection.find_one(member.id)

        if not player_post:
            await ctx.send(f"Can't find profile for {member.name}.")
            return

        if member != ctx.author:
            author_post = units_collection.find_one(ctx.author.id)
            unit_post = units_collection.find_one(member.id)

            if not unit_post:
                unit_post = dead_collection.find_one(member.id)

            if not unit_post:
                await ctx.send("Unit not found.")
                return

            if not author_post and ctx.author != 660929334969761792:
                await ctx.send("You are not a part of the game system.")
                return

            if (
                unit_post.get("race") != author_post.get("race")
                and ctx.author.id != 660929334969761792
            ):
                await ctx.send(f"Can't view {member.name}'s profile.")
                return
        resources = ["wood", "stone", "iron", "gold", "coins"]
        d = ""
        for r in resources:
            d += f"{utils.emoji.resources.get(r)} {player_post.get(r)}\n"
        embed.description = d
        await ctx.send(embed=embed)

    @commands.command(name="give")
    async def give(
        self, ctx, member: typing.Optional[discord.Member] = None, *, args: str = ""
    ):
        if member == ctx.author:
            await ctx.send("Can't give resources to yourself you silly.")
            return
        arg, resources_type = args.split(" ")

        resources = ["wood", "stone", "iron", "gold", "coins"]
        if not (arg and member) or resources_type not in resources:
            embed = discord.Embed(
                title="Commands: .give", color=discord.Color.from_rgb(201, 0, 118)
            )
            embed.description = "**Description:**\nGives an amount of resources to another player.\n\n**Syntax:**\n.give [member] [amount] [wood/stone/iron/gold/coins]"
            await ctx.send(embed=embed)
            return

        try:
            amount = int(arg)
        except ValueError:
            await ctx.send("Amount entered must be an integer.")
            return

        if amount <= 0 and ctx.author.id != 660929334969761792:
            await ctx.send("Amount entered must be positive.")
            return

        player_post = resources_collection.find_one(ctx.author.id)
        member_post = resources_collection.find_one(member.id)

        if not player_post:
            await ctx.send("You are not a participant in the game system.")
            return
        if not member_post:
            await ctx.send(f"{member.name} is not a participant in the game system.")
            return

        coins = player_post.get(resources_type)

        if coins < amount:
            await ctx.send("Insufficient Funds.")
            return

        coins -= amount
        member_post[resources_type] += amount

        filter = {"_id": member.id}
        update = {"$set": {resources_type: member_post[resources_type]}}

        resources_collection.update_one(filter, update)

        filter = {"_id": ctx.author.id}
        update = {"$set": {resources_type: coins}}

        resources_collection.update_one(filter, update)
        emoji = utils.emoji.resources.get(resources_type)
        await ctx.send(f"Gave {amount} {emoji} to {member.name}")


async def setup(client):
    await client.add_cog(Economy(client))
