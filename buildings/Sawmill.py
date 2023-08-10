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


color = discord.Color.from_rgb(201, 0, 118)


class Sawmill(discord.ui.View):
    def __init__(self, author, unit, building, *, timeout: Optional[float] = 40):
        super().__init__(timeout=timeout)
        self.author = author
        self.unit = unit
        self.building = building

        embed = discord.Embed(color=color, title="Sawmill")
        stock = building.get("wood", 0)
        description = (
            "<:Sawmill:1136661542583160852> "
            + info["Sawmill"]["Description"]
            + f"\n** * Currently Stored:** {stock} {resources['wood']}"
        )

        embed.description = description
        self.embed = embed

    @discord.ui.button(label="store")
    async def store(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        await interaction.response.send_message(
            "Enter the amount that you want to store."
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

        message = await interaction.channel.send(f"Store {amount} {resources['wood']}?")

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
            if self.unit["name"] != "Player":
                unit_stock = self.unit.get("wood", 0)
            else:
                inv = resources_collection.find_one({"_id": self.unit["_id"]})
                if not inv:
                    await interaction.channel.send("Profile not found.")
                    return
                unit_stock = inv["wood"]

            if amount > unit_stock:
                await interaction.channel.send("Insufficient resources.")
                return

            if self.unit["name"] != "Player":
                units_collection.update_one(
                    {"_id": self.unit["_id"]}, {"$inc": {"wood": -amount}}
                )
            else:
                resources_collection.update_one(
                    {"_id": self.unit["_id"]}, {"$inc": {"wood": -amount}}
                )
            stock = self.building.get("wood", 0)
            stock += amount

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {"wood": stock}}
            )
            self.building["wood"] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(
                f"Successfully stored {amount} {resources['wood']}."
            )

    @discord.ui.button(label="Withdraw")
    async def withdraw(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()

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

        message = await interaction.channel.send(
            f"Withdraw {amount} {resources['wood']}?"
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
            stock = self.building.get("wood", 0)

            if amount > stock:
                await interaction.channel.send("Insufficient resources.")
                return
            if self.unit["name"] != "Player":
                units_collection.update_one(
                    {"_id": self.unit["_id"]}, {"$inc": {"wood": amount}}
                )
            else:
                resources_collection.update_one(
                    {"_id": self.unit["_id"]}, {"$inc": {"wood": amount}}
                )
            stock = self.building.get("wood", 0)
            stock -= amount

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {"wood": stock}}
            )
            self.building["wood"] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(
                f"Successfully withdrew {amount} {resources['wood']}."
            )
