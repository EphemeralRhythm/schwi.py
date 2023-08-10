import discord
from typing import Optional
from utils.buildings_info import info
from utils.units_info import units as units_info
from utils.database import (
    resources_collection,
    info_collection,
    unit_queues,
)
from utils.emoji import troops_emoji
import utils.data

color = discord.Color.from_rgb(201, 0, 118)

units_array = ["Boat", "Battleship"]


class Docks_Select(discord.ui.Select):
    def __init__(self, author, unit, building):
        self.author = author
        self.unit = unit
        self.building = building
        options = []

        for i in range(2):
            name = units_array[i]
            emoji = troops_emoji[name]

            wood, stone, gold, iron = units_info[name].get("cost", (0, 0, 0, 0))
            cost_string = ""

            cost_string += f"Wood: {wood} "
            cost_string += f",Stone: {stone} "
            cost_string += f",Gold: {gold} "
            cost_string += f",Iron: {iron} "
            options.append(
                discord.SelectOption(
                    label=name,
                    emoji=emoji,
                    description=cost_string,
                )
            )

        super().__init__(
            placeholder="Train units.",
            max_values=1,
            min_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.channel:
            return

        if not isinstance(interaction.channel, discord.TextChannel) and not isinstance(
            interaction.channel, discord.threads.Thread
        ):
            print("Failed to send, channel type: ", type(interaction.channel))
            return

        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "Interaction failed."
                + "The command author is not the same as the interaction author."
            )
            return
        filter = {"building": self.building["_id"]}
        unit_in_queue = unit_queues.find_one(filter)

        if unit_in_queue:
            await interaction.response.send_message(
                "This building already has a unit in queue."
            )
            return

        cost = units_info[self.values[0]].get("cost")
        if not cost:
            await interaction.response.send_message("An error has occured! Code: 01")
            return

        player_post = resources_collection.find_one({"_id": self.author.id}) or {}
        inventory = [
            player_post.get("wood"),
            player_post.get("stone"),
            player_post.get("gold"),
            player_post.get("iron"),
        ]

        for index, building_cost in enumerate(cost):
            if building_cost > inventory[index]:
                await interaction.response.send_message("Insufficient resources.")
                return

        count = info_collection.find_one({"_id": "unit_count"})
        if not count:
            await interaction.channel.send("An error has occured. Code: 02")
            return

        name = self.values[0]
        info_post = units_info[name]

        hp = info_post["hitpoints"]
        x, y = self.building["_id"].split("-")
        x, y = int(x) * 16, int(y) * 16

        direction = self.building["image"][-1]
        dir_map = {"U": (0, -1), "D": (0, 1), "R": (1, 0), "L": (-1, 0)}

        f_x = x + dir_map[direction][0] * 32
        f_y = y + dir_map[direction][1] * 32

        value = count["value"] + 1
        training_time = info_post.get("time")

        if not training_time:
            await interaction.response.send_message("An error has occured. Code: 03")
            return

        resources_arr = ["wood", "stone", "gold", "iron"]
        filter = {"_id": self.author.id}
        for index, currency in enumerate(inventory):
            currency -= cost[index]

            update = {"$set": {resources_arr[index]: currency}}
            resources_collection.update_one(filter, update)

        unit = {
            "_id": value,
            "name": name,
            "type": "naval",
            "hp": hp,
            "race": self.unit["race"],
            "x": f_x,
            "y": f_y,
            "owner": self.author.id,
            "time": training_time * 60,
            "direction": "D",
            "state": 0,
            "building": self.building["_id"],
        }
        info_collection.update_one({"_id": "unit_count"}, {"$inc": {"value": 1}})
        unit_queues.insert_one(unit)
        await interaction.response.send_message("Unit added to queue!")


class Docks(discord.ui.View):
    def __init__(self, author, unit, building, *, timeout: Optional[float] = 40):
        super().__init__(timeout=timeout)
        self.author = author
        self.unit = unit
        self.building = building

        embed = discord.Embed(color=color, title="Barracks")

        description = (
            "<:Barracks:1136661534387470457> "
            + info["Barracks"]["Description"]
            + "\n\n* Unlocked Units:"
        )

        for i in range(0, 2):
            name = units_array[i]
            emoji = troops_emoji[name]
            description += f"\n * {emoji} {name}"

        filter = {"building": self.building["_id"]}
        unit_in_queue = unit_queues.find_one(filter)

        if unit_in_queue:
            name = unit_in_queue.get("name")
            emoji = troops_emoji.get(name)
            time_left = unit_in_queue.get("time")
            description += (
                "\n\n** * Currently training: **"
                + f"{emoji} {name}: {time_left} minutes left"
            )
            embed.description = description
            self.embed = embed
            return

        self.embed = embed
        embed.description = description

        self.add_item(Docks_Select(self.author, self.unit, self.building))
