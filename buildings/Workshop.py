import discord
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


class Workshop(discord.ui.View):
    def __init__(self, author, unit, building, *, timeout: Optional[float] = 40):
        super().__init__(timeout=timeout)
        self.author = author
        self.unit = unit
        self.building = building

        embed = discord.Embed(color=color, title="Workshop")

        minerals = ["raw_iron", "raw_gold", "iron", "gold"]
        description = (
            "<:Workshop:1136661568583635027> "
            + info["Workshop"]["Description"]
            + "\n\n* Resources Present:"
        )

        for m in minerals:
            amount = building.get(m, 0)
            description += f"\n * {resources[m]} {amount}"

        embed.description = description
        self.embed = embed

    @discord.ui.button(label="Process")
    async def store(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        if self.unit["name"] != "Worker":
            await interaction.response.send_message(
                "Only workers can enter raw minerals."
            )
            return
        if not isinstance(interaction.channel, discord.TextChannel) and not isinstance(
            interaction.channel, discord.threads.Thread
        ):
            print("Failed to send, channel type: ", type(interaction.channel))
            return

        raw_iron = self.unit.get("raw_iron", 0)
        raw_gold = self.unit.get("raw_gold", 0)

        if raw_iron == 0 and raw_gold == 0:
            await interaction.response.send_message(
                f"Worker {self.unit['_id']} is not carrying any raw resources."
            )
            return

        units_collection.update_one(
            {"_id": self.unit["_id"]}, {"$set": {"raw_iron": 0, "raw_gold": 0}}
        )

        building_iron = self.building.get("iron", 0) + raw_iron
        building_gold = self.building.get("gold", 0) + raw_gold

        buildings_collection.update_one(
            {"_id": self.building["_id"]},
            {"$set": {"iron": building_iron, "gold": building_gold}},
        )
        self.building["iron"] = building_iron
        self.building["gold"] = building_gold

        x, y = self.building["_id"].split("-")
        x, y = int(x), int(y)

        utils.data.map_objects[(x, y)] = self.building

        await interaction.response.send_message(
            f"Successfully entered {resources['raw_iron']} {raw_iron}"
            + f" {resources['raw_gold']} {raw_gold}."
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
        if not isinstance(interaction.channel, discord.TextChannel) and not isinstance(
            interaction.channel, discord.threads.Thread
        ):
            print("Failed to send, channel type: ", type(interaction.channel))
            return

        iron = self.building.get("iron", 0)
        gold = self.building.get("gold", 0)

        if not (iron or gold):
            await interaction.response.send_message("No resources to withdraw.")
            return
        owner_id = self.unit.get("owner") or self.unit["_id"]
        resources_collection.update_one(
            {"_id": owner_id},
            {"$inc": {"iron": iron, "gold": gold}},
        )

        buildings_collection.update_one(
            {"_id": self.building["_id"]}, {"$set": {"gold": 0, "iron": 0}}
        )
        self.building["gold"] = 0
        self.building["iron"] = 0

        x, y = self.building["_id"].split("-")
        x, y = int(x), int(y)

        utils.data.map_objects[(x, y)] = self.building

        await interaction.response.send_message(
            f"Successfully withdrew {resources['iron']} {iron}"
            + f"{resources['gold']} {gold}."
        )
