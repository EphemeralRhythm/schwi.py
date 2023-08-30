import discord
import asyncio
import utils.units_info
from typing import Optional
from utils.buildings_info import info
from utils.emoji import resources
from utils.database import (
    resources_collection,
    buildings_collection,
    units_collection,
)
import utils.data

hay_bale = "<:hay:1136684958346399775>"
seeds = "<:seeds:1139516070869352499>"
color = discord.Color.from_rgb(201, 0, 118)


class Grain_Stall(discord.ui.View):
    def __init__(self, author, unit, building, *, timeout: Optional[float] = 40):
        super().__init__(timeout=timeout)
        self.author = author
        self.unit = unit
        self.building = building

        embed = discord.Embed(color=color, title="Grain Stall")
        stock = building.get("stock", 0)
        seeds_amount = building.get("seeds", 0)

        description = (
            "<:Grain_Stall:1136661559708483615> "
            + info["Grain Stall"]["Description"]
            + f"\n\n** * Selling Price:** 20 {hay_bale} -> 5 {resources['gold']}"
            + f"\n** * Buying Price:** 1 {resources['gold']} -> 100 {seeds}"
            + f"\n** * Currently Stored:** {stock} {hay_bale} {seeds_amount} {seeds}"
        )

        embed.description = description
        self.embed = embed

    @discord.ui.button(label="Buy Seeds")
    async def buy(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        await interaction.response.send_message(
            "Enter the amount that you want to buy."
        )
        if not isinstance(interaction.channel, discord.TextChannel) and not isinstance(
            interaction.channel, discord.threads.Thread
        ):
            print("Failed to send, channel type: ", type(interaction.channel))
            return

        def check(m):
            return m.channel == interaction.channel and m.author == self.author

        try:
            arg = await interaction.client.wait_for("message", check=check, timeout=20)
        except asyncio.TimeoutError:
            return
        try:
            amount = int(arg.content)
        except ValueError:
            await interaction.channel.send("Amount entered must be an integer.")
            return

        if amount <= 0:
            await interaction.channel.send("Amount entered must be positive.")
            return

        message = await interaction.channel.send(
            f"Purchase {amount} * 100 {seeds} for {amount} {resources['gold']}?"
        )

        await message.add_reaction("✅")

        def check_reaction(reaction, user):
            return str(reaction.emoji) == "✅" and user == self.author

        timed_out = False
        try:
            await interaction.client.wait_for(
                "reaction_add", check=check_reaction, timeout=20
            )
        except asyncio.TimeoutError:
            timed_out = True
        if not timed_out:
            player_post = resources_collection.find_one(self.author.id)

            if not player_post:
                await interaction.channel.send("Profile not found.")
                return

            coins = player_post.get("gold", 0)

            if coins < amount:
                await interaction.channel.send("Insufficient Funds.")
                return

            coins -= amount

            filter = {"_id": self.author.id}
            update = {"$set": {"gold": coins}}

            resources_collection.update_one(filter, update)

            stock = self.building.get("seeds", 0)
            stock += amount * 100

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {"seeds": stock}}
            )
            self.building["seeds"] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building
            await interaction.channel.send(
                f"Successfully purchased {amount} * 100 {seeds}."
            )

    @discord.ui.button(label="Sell Wheat")
    async def sell(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        await interaction.response.send_message(
            "Enter the amount that you want to sell."
        )
        if not isinstance(interaction.channel, discord.TextChannel) and not isinstance(
            interaction.channel, discord.threads.Thread
        ):
            print("Failed to send, channel type: ", type(interaction.channel))
            return

        def check(m):
            return m.channel == interaction.channel and m.author == self.author

        try:
            arg = await interaction.client.wait_for("message", check=check, timeout=10)
        except asyncio.TimeoutError:
            return
        try:
            amount = int(arg.content)
        except ValueError:
            await interaction.channel.send("Amount entered must be an integer.")
            return

        if amount <= 0:
            await interaction.channel.send("Amount entered must be positive.")
            return

        message = await interaction.channel.send(
            f"Sell {amount} * 20 {hay_bale} for {amount * 5} {resources['gold']}?"
        )

        await message.add_reaction("✅")

        def check_reaction(reaction, user):
            return str(reaction.emoji) == "✅" and user == self.author

        timed_out = False
        try:
            await interaction.client.wait_for(
                "reaction_add", check=check_reaction, timeout=10
            )
        except asyncio.TimeoutError:
            timed_out = True
        if not timed_out:
            stock = self.building.get("stock", 0)

            if amount * 20 > stock:
                await interaction.channel.send(
                    "Haybales must be placed in the grain stall in order to sell them."
                )
                return

            stock -= 20 * amount
            resources_collection.update_one(
                {"_id": self.author.id}, {"$inc": {"gold": amount * 5}}
            )

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {"stock": stock}}
            )
            self.building["stock"] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(f"Successfully sold {amount} {hay_bale}")

    @discord.ui.button(label="Store")
    async def store(self, interaction: discord.Interaction, item):
        amount = self.unit.get("haybale")
        if not amount:
            await interaction.response.send_message(
                "This units doesn't have anything to store."
            )
            return

        self.building["stock"] += amount

        x, y = self.building["_id"].split("-")
        x, y = int(x), int(y)

        utils.data.map_objects[(x, y)] = self.building
        buildings_collection.update_one(
            {"_id", self.building["_id"]}, {"$inc": {"stock": amount}}
        )
        units_collection.update_one({"_id": self.unit["_id"]}, {"$set": {"haybale": 0}})

    @discord.ui.button(label="Withdraw")
    async def withdraw(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        if self.unit["name"] != "Worker":
            await interaction.response.send_message("Only workers can withdraw seeds.")
            return
        await interaction.response.send_message(
            "Enter the amount that you want to withdraw."
        )
        if not isinstance(interaction.channel, discord.TextChannel) and not isinstance(
            interaction.channel, discord.threads.Thread
        ):
            print("Failed to send, channel type: ", type(interaction.channel))
            return

        def check(m):
            return m.channel == interaction.channel and m.author == self.author

        try:
            arg = await interaction.client.wait_for("message", check=check, timeout=20)
        except asyncio.TimeoutError:
            return
        try:
            amount = int(arg.content)
        except ValueError:
            await interaction.channel.send("Amount entered must be an integer.")
            return

        if amount <= 0:
            await interaction.channel.send("Amount entered must be positive.")
            return

        message = await interaction.channel.send(f"Withdraw {amount} * 100 {seeds}?")

        await message.add_reaction("✅")

        def check_reaction(reaction, user):
            return str(reaction.emoji) == "✅" and user == self.author

        timed_out = False
        try:
            await interaction.client.wait_for(
                "reaction_add", check=check_reaction, timeout=20
            )
        except asyncio.TimeoutError:
            timed_out = True
        if not timed_out:
            stock = self.building.get("seeds", 0)

            if amount * 100 > stock:
                await interaction.channel.send("Insufficient resources.")
                return

            units_collection.update_one(
                {"_id": self.unit["_id"]}, {"$inc": {"seeds": 100 * amount}}
            )

            stock = self.building.get("seeds", 0)
            stock -= amount * 100

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {"seeds": stock}}
            )
            self.building["seeds"] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(
                f"Successfully withdrew {amount} * 100 {seeds}."
            )
