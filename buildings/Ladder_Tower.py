import discord
import utils.units_info
from typing import Optional
from utils.buildings_info import info
from utils.database import (
    units_collection,
)
import utils.data


color = discord.Color.from_rgb(201, 0, 118)


class Ladder_Tower(discord.ui.View):
    def __init__(self, author, unit, building, *, timeout: Optional[float] = 40):
        super().__init__(timeout=timeout)
        self.author = author
        self.unit = unit
        self.building = building

        embed = discord.Embed(color=color, title="Ladder Tower")
        description = (
            "<:ladder_tower:1137460753834713241> " + info["Ladder Tower"]["Description"]
        )
        embed.description = description
        self.embed = embed

    @discord.ui.button(label="Climb Up")
    async def Climb(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()

        x, y = self.unit["x"] // 16, self.unit["y"] // 16
        node = utils.data.map_arr[x][y]
        if node == -1:
            await interaction.response.send_message("Already Up!")
        else:
            f_x, f_y = self.building["_id"].split("-")
            f_x, f_y = int(f_x), int(f_y)

            units_collection.update_one(
                {"_id": self.unit["_id"]},
                {"$set": {"x": f_x * 16, "y": f_y * 16}},
            )

            await interaction.response.send_message("Climbed Up!")

    @discord.ui.button(label="Go Down")
    async def descend(self, interaction: discord.Interaction, item):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return

        self.stop()
        u_x, u_y = self.unit["x"] // 16, self.unit["y"] // 16

        node = utils.data.map_arr[u_x][u_y]
        if node == 1:
            await interaction.response.send_message("Already down!")

        x, y = self.building["_id"].split("-")
        x, y = int(x), int(y)

        node = utils.data.map_arr[x][y + 1]
        f_x, f_y = x, y + 1
        if node != 1:
            await interaction.response.send_message("Unable to go down!")
        else:
            units_collection.update_one(
                {"_id": self.unit["_id"]},
                {"$set": {"x": f_x * 16, "y": f_y * 16}},
            )

            await interaction.response.send_message("Went down!")
