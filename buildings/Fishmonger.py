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
cod = "<:cod:1136730585272955021>"
salmon = "<:salmon:1136730583586848849>"
tropical_fish = "<:tropicalFish:1136730580340441208>"


class Fishmonger(discord.ui.View):
    def __init__(self, author, unit, building, *, timeout: Optional[float] = 40):
        super().__init__(timeout=timeout)
        self.author = author
        self.unit = unit
        self.building = building

        embed = discord.Embed(color=color, title="Fishmonger")

        cod_amount = building.get("cod", 0)
        salmon_amount = building.get("salmon", 0)
        tropical_fish_amount = building.get("tropical_fish", 0)

        description = (
            "<:Fishmonger:1136661561172303953> "
            + info["Fishmonger"]["Description"]
            + "\n\n** * Selling Prices:**"
            + f"10 {cod} -> 1 {resources['gold']}\n"
            + f"5 {salmon} -> 1 {resources['gold']}\n"
            + f"1 {tropical_fish} -> 1 {resources['gold']}\n"
            + "\n** * Currently Stored:**"
            + f"{cod} {cod_amount} "
            + f"{salmon} {salmon_amount} {tropical_fish} {tropical_fish_amount}"
        )

        embed.description = description
        self.embed = embed

    @discord.ui.button(label="Sell")
    async def sell(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        await interaction.response.send_message(
            "What type of fish do you want to store?"
            + f"\n(c) {cod} (s) {salmon} (t) {tropical_fish}"
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

        if arg.content not in ["c", "C", "t", "T", "s", "S"]:
            await interaction.channel.send("Invalid input.")
            return

        await interaction.channel.send("Enter the amount that you want to sell.")

        fish_type = arg.content.lower()
        fish_dict = {"c": "cod", "s": "salmon", "t": "tropical_fish"}
        fish_amounts = {"cod": 10, "salmon": 5, "tropical_fish": 1}
        fish = fish_dict[fish_type]
        fish_amount = fish_amounts[fish]
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
            f"Sell {amount} * {fish_amount} {eval(fish)}"
            + f" for {amount} {resources['gold']}?"
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
            stock = self.building.get(fish, 0)

            if amount * fish_amount > stock:
                await interaction.channel.send("Insufficient resources.")
                return

            stock -= fish_amount * amount
            resources_collection.update_one(
                {"_id": self.author.id}, {"$inc": {"gold": amount}}
            )

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {fish: stock}}
            )
            self.building[fish] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(
                f"Successfully sold {amount} * {fish_amount} {eval(fish)}."
            )

    @discord.ui.button(label="Store")
    async def store(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        if self.unit["name"] != "Worker" and self.unit["name"] != "Player":
            await interaction.response.send_message(
                "Only workers can players withdraw and store fish."
            )
            return
        await interaction.response.send_message(
            "What type of fish do you want to store?"
            + f"\n(c) {cod} (s) {salmon} (t) {tropical_fish}"
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

        if arg.content not in ["c", "C", "t", "T", "s", "S"]:
            await interaction.channel.send("Invalid input.")
            return

        await interaction.channel.send("Enter the amount that you want to store.")

        fish_type = arg.content.lower()
        fish_dict = {"c": "cod", "s": "salmon", "t": "tropical_fish"}

        fish = fish_dict[fish_type]
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

        message = await interaction.channel.send(f"Store {amount} {eval(fish)}?")

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
            unit_stock = self.unit.get(fish, 0)

            if amount > unit_stock:
                await interaction.channel.send("Insufficient resources.")
                return
            units_collection.update_one(
                {"_id": self.unit["_id"]}, {"$inc": {fish: -amount}}
            )

            stock = self.building.get(fish, 0)
            stock += amount

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {fish: stock}}
            )
            self.building[fish] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(f"Successfully stored {amount} fish.")

    @discord.ui.button(label="Withdraw")
    async def withdraw(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        if self.unit["name"] != "Worker" and self.unit["name"] != "Player":
            await interaction.response.send_message(
                "Only workers can players withdraw and store fish."
            )
            return
        await interaction.response.send_message(
            "What type of fish do you want to withdraw?"
            + f"\n(c) {cod} (s) {salmon} (t) {tropical_fish}"
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

        if arg.content not in ["c", "C", "t", "T", "s", "S"]:
            await interaction.channel.send("Invalid input.")
            return

        await interaction.channel.send("Enter the amount that you want to withdraw.")

        fish_type = arg.content.lower()
        fish_dict = {"c": "cod", "s": "salmon", "t": "tropical_fish"}

        fish = fish_dict[fish_type]
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
        message = await interaction.channel.send(f"Withdraw {amount} {eval(fish)}?")

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
            stock = self.building.get(fish, 0)

            if amount > stock:
                await interaction.channel.send("Insufficient resources.")
                return

            units_collection.update_one(
                {"_id": self.unit["_id"]}, {"$inc": {fish: amount}}
            )

            stock = self.building.get(fish, 0)
            stock -= amount

            buildings_collection.update_one(
                {"_id": self.building["_id"]}, {"$set": {fish: stock}}
            )
            self.building[fish] = stock
            x, y = self.building["_id"].split("-")
            x, y = int(x), int(y)

            utils.data.map_objects[(x, y)] = self.building

            await interaction.channel.send(
                f"Successfully withdrew {amount} {eval(fish)}."
            )
