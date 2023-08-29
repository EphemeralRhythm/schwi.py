import time
import discord
import utils.data
import utils.database as db
import asyncio
from utils.pings import get_pings
from utils.buildings_info import info
from PIL import Image
from utils.ui import draw_map
from utils.buttons import building_classes
from utils.units_info import units as units_info


def overlap(rect1, rect2):
    if rect1 == rect2:
        return True
    if rect1[2] <= rect2[0] or rect2[2] <= rect1[0]:
        return False
    if rect1[3] <= rect2[1] or rect2[3] <= rect1[1]:
        return False
    return True


class Unit_Select(discord.ui.Select):
    def __init__(self, author, unit):
        self.author = author
        self.unit = unit
        options = [
            discord.SelectOption(
                label="Move",
                emoji="<:location:1065283234834940044>",
                description="Move this unit on the map.",
            ),
            discord.SelectOption(
                label="Turn",
                emoji="<:turn:1135328996159131708>",
                description="Choose the direction that your unit is facing.",
            ),
        ]

        if self.unit["name"] != "Boat":
            options.extend(
                [
                    discord.SelectOption(
                        label="Action",
                        emoji="<:pickaxe:1101437961414905898>",
                        description="Interact with nearby objects on the map.",
                    ),
                    discord.SelectOption(
                        label="Attack (Unit)",
                        emoji="<:crosshair:1065283238618214410>",
                        description="Attack an enemy unit.",
                    ),
                    discord.SelectOption(
                        label="Attack (Building)",
                        emoji="<:crosshair:1065283238618214410>",
                        description="Attack an enemy building.",
                    ),
                    discord.SelectOption(
                        label="Structure",
                        emoji="<:gears:1068824355687112756>",
                        description="Interact with near buildings.",
                    ),
                    discord.SelectOption(
                        label="Guard",
                        emoji="⚔️",
                        description="Attack any enemy units within field of view.",
                    ),
                ]
            )

        if self.unit["name"] == "Worker":
            options.append(
                discord.SelectOption(
                    label="Build",
                    emoji="<:tool:1070299017587732501>",
                    description="Construct new buildings.",
                )
            )

            options.append(
                discord.SelectOption(
                    label="Plant",
                    emoji="<:seeds:1139516070869352499>",
                    description="Plant seeds.",
                )
            )

            options.append(
                discord.SelectOption(
                    label="Gather",
                    emoji="<:pickaxe:1101437961414905898>",
                    description="Gather resources from a mine.",
                )
            )
        super().__init__(
            placeholder="Select your command",
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

        x, y = self.unit.get("x"), self.unit.get("y")
        if self.values[0] == "Guard":
            command = {
                "author": self.author.id,
                "unit": self.unit.get("_id"),
                "command": "guard",
                "direction": self.unit.get("direction"),
                "x": x,
                "y": y,
            }
            db.commands_collection.insert_one(command)
            await interaction.response.send_message("Command added to queue!")

        if self.values[0] == "Turn":
            await interaction.response.send_message("Enter the direction:")

            def check(m):
                return m.channel == interaction.channel and m.author == self.author

            try:
                direction = await interaction.client.wait_for(
                    "message", check=check, timeout=20
                )
            except asyncio.TimeoutError:
                return

            if direction.content not in ["U", "D", "R", "L"]:
                await interaction.channel.send("Invalid input.")
                return

            command = {
                "author": self.author.id,
                "unit": self.unit.get("_id"),
                "command": "turn",
                "direction": direction.content,
            }
            db.commands_collection.insert_one(command)
            await interaction.channel.send("Command added to queue!")

        if (
            self.values[0] == "Move"
            or self.values[0] == "Attack (Unit)"
            or self.values[0] == "Attack (Building)"
        ):
            if self.values[0] == "Move":
                if self.unit.get("boat"):
                    await interaction.response.send_message(
                        "Cannot move while in a boat."
                    )
                    return
                await interaction.response.send_message("Enter the distance vector x y")
            elif self.values[0] == "Attack (Unit)" or "Attack (Building)":
                u_info = units_info.get(self.unit["name"], {})
                u_range = self.unit.get("range") or u_info.get("range") or 8

                if self.unit.get("boat") and u_range <= 16:
                    await interaction.response.send_message(
                        "Melee units can't attack while in boat."
                    )
                    return
                await interaction.response.send_message(
                    "Enter the distance vector x y for the target."
                )

            def check(m):
                return m.channel == interaction.channel and m.author == self.author

            try:
                vector = await interaction.client.wait_for(
                    "message", check=check, timeout=20
                )
            except asyncio.TimeoutError:
                return

            if len(vector.content.split(" ")) != 2:
                await interaction.channel.send("Invalid Vector Format")
                return
            x, y = vector.content.split(" ")
            try:
                x, y = int(x), int(y)
            except ValueError:
                await interaction.channel.send("Invalid Vector Format")
                return

            i_x, i_y = self.unit.get("x"), self.unit.get("y")

            if self.values[0] == "Attack (Unit)":
                if abs(x) + abs(y) > 500:
                    await interaction.channel.send("Target is too far.")
                    return
            if self.values[0] == "Move":
                command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "move",
                    "x": i_x + x,
                    "y": i_y + y,
                }
                db.commands_collection.insert_one(command)

                await interaction.channel.send("Command added to queue!")

            elif self.values[0] == "Attack (Unit)":
                query = {"race": {"$ne": self.unit.get("race")}}
                players = db.units_collection.find(query)

                def locate_unit(unit):
                    offset = 0
                    if u := utils.data.dynamic_fog.get(
                        (unit.get("x") // 16, unit.get("y") // 16)
                    ):
                        if not u.get(self.unit.get("race")):
                            offset += 300

                    loc_x, loc_y = unit.get("x"), unit.get("y")
                    return abs(i_x + x - loc_x) + abs(i_y + y - loc_y) + offset

                players = sorted(players, key=lambda enemy: locate_unit(enemy))

                if locate_unit(players[0]) > 200:
                    await interaction.channel.send(
                        "No target found in the specified location."
                    )
                    return
                message = await interaction.channel.send(
                    f"Found {players[0].get('name')}. "
                    + "React with ✅ to confirm the command"
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
                    command = {
                        "author": self.author.id,
                        "unit": self.unit.get("_id"),
                        "command": "attack",
                        "target": players[0]["_id"],
                    }
                    db.commands_collection.insert_one(command)
                    await interaction.channel.send("Command added to queue!")

            elif self.values[0] == "Attack (Building)":
                query = {"race": {"$ne": self.unit.get("race")}}
                buildings = db.buildings_collection.find(query)

                def locate(building):
                    loc_x, loc_y = building["_id"].split("-")
                    loc_x, loc_y = int(loc_x) * 16, int(loc_y) * 16
                    print(f"loc: {loc_x}, {loc_y}")
                    print(f"i_x: {i_x}, i_y: {i_y}")
                    return abs(i_x + x - loc_x) + abs(i_y + y - loc_y)

                sorted_arr = sorted(buildings, key=lambda enemy: locate(enemy))
                if not sorted_arr:
                    await interaction.channel.send(
                        "No target found in the specified location."
                    )
                    return
                if locate(sorted_arr[0]) > 200:
                    await interaction.channel.send(
                        "No target found in the specified location."
                    )
                    return
                message = await interaction.channel.send(
                    f"Found {sorted_arr[0].get('name')}."
                    + "React with ✅ to confirm the command"
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
                    command = {
                        "author": self.author.id,
                        "unit": self.unit.get("_id"),
                        "command": "battack",
                        "target": sorted_arr[0]["_id"],
                    }
                    db.commands_collection.insert_one(command)
                    await interaction.channel.send("Command added to queue!")

        elif self.values[0] == "Structure":
            building = utils.data.map_objects.get((x // 16, y // 16), {})

            dir_map = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
            dir = self.unit.get("direction")

            d_x, d_y = dir_map[dir]
            if not (
                building.get("type") == "building"
                or building.get("name") == "Ladder Tower"
            ):
                building = utils.data.map_objects.get(
                    (x // 16 + d_x, y // 16 + d_y), {}
                )
            for d_x in [-1, 0, 1]:
                for d_y in [-1, 0, 1]:
                    if not (
                        building.get("type") == "building"
                        or building.get("name") == "Ladder Tower"
                    ):
                        building = utils.data.map_objects.get(
                            (x // 16 + d_x, y // 16 + d_y), {}
                        )

            if not (
                building.get("type") == "building"
                or building.get("name") == "Ladder Tower"
            ):
                await interaction.response.send_message("No nearby buildings found.")
                return
            if (
                building.get("race") != self.unit.get("race")
                and building.get("race") != "NPC"
            ):
                await interaction.response.send_message(
                    "Can't interact with enemy buildings."
                )

            elif building.get("race") != "NPC":
                await interaction.response.send_message(f"Found {building.get('name')}")

                building_class = building_classes[building["name"]]

                view = building_class(self.author, self.unit, building)
                await interaction.channel.send(view=view, embed=view.embed)

        elif self.values[0] == "Build":
            view = Construct_View(author=self.author, unit=self.unit)
            await interaction.response.send_message(view=view)

        elif self.values[0] == "Action":
            dir = self.unit.get("direction", "U")
            dir_map = {"U": (0, -1), "D": (0, 1), "R": (1, 0), "L": (-1, 0)}

            dir_int = dir_map[dir]
            o_x = x + dir_int[0] * 16
            o_y = y + dir_int[1] * 16

            if self.unit.get("boat"):
                node = utils.data.map_arr[o_x // 16][o_y // 16]

                if not node == 1:
                    await interaction.response.send_message(
                        "The unit needs to be facing a land node"
                        + "before attempting to leave boat."
                    )
                    return

                db.units_collection.update_one(
                    {"_id": self.unit["_id"]}, {"$set": {"x": o_x, "y": o_y, "boat": 0}}
                )
                db.units_collection.update_one(
                    {"_id": self.unit["boat"]}, {"$unset": {"unit": ""}}
                )

                await interaction.response.send_message("Hopped off!")
                return
            object = utils.data.map_objects.get((o_x // 16, o_y // 16))

            if not object:

                def locate_unit(unit):
                    offset = 0
                    loc_x, loc_y = unit.get("x"), unit.get("y")
                    if unit.get("unit"):
                        offset += 32
                    return abs(o_x - loc_x) + abs(o_y - loc_y)

                query = {"race": self.unit.get("race"), "name": "Boat"}
                boats = db.units_collection.find(query)

                sorted_units = sorted(boats, key=lambda x: locate_unit(x))
                if sorted_units:
                    if locate_unit(sorted_units[0]) > 32:
                        await interaction.response.send_message(
                            "No nearby objects found."
                        )
                        return

                    await interaction.response.send_message(
                        f"Found {sorted_units[0]['name']}. "
                        + "React with ✅ to hop on board!"
                    )
                    message = await interaction.original_response()
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
                        db.units_collection.update_one(
                            {"_id": self.unit["_id"]},
                            {
                                "$set": {
                                    "boat": sorted_units[0]["_id"],
                                    "x": sorted_units[0]["x"],
                                    "y": sorted_units[0]["y"] - 8,
                                }
                            },
                        )
                        db.units_collection.update_one(
                            {"_id": sorted_units[0]["_id"]},
                            {"$set": {"unit": self.unit["_id"]}},
                        )
                        await interaction.channel.send("Hopped on!")
                    return
            if not object:
                await interaction.response.send_message("No nearby objects found.")
                return
            if object.get("name") == "wheatfield":
                if object.get("state") != 4:
                    await interaction.response.send_message("Cannot harvest now!")
                    return

                await interaction.response.send_message(
                    "Found wheat field."
                    + "React with <:pickaxe:1101437961414905898> to harvest."
                )

                message = await interaction.original_response()
                await message.add_reaction("<:pickaxe:1101437961414905898>")

                def check_reaction(reaction, user):
                    return (
                        str(reaction.emoji) == "<:pickaxe:1101437961414905898>"
                        and user == self.author
                    )

                timed_out = False
                try:
                    await interaction.client.wait_for(
                        "reaction_add", check=check_reaction, timeout=10
                    )
                except asyncio.TimeoutError:
                    timed_out = True
                if not timed_out:
                    index = utils.data.wheat_fields.index(object)

                    if index != -1:
                        utils.data.wheat_fields.pop(index)
                    utils.data.map_objects.pop((o_x // 16, o_y // 16))
                    db.map_collection.delete_one({"_id": object["_id"]})

                    db.units_collection.update_one(
                        {"_id": self.unit["_id"]}, {"$inc": {"wheat": 20 * 20}}
                    )

                    await interaction.channel.send(
                        "Successfully harversted from the wheatfield!"
                    )

                    return
            if "Tree" in object.get("name"):
                await interaction.response.send_message(
                    f"Found {object.get('name')}. "
                    + "React with <:pickaxe:1101437961414905898> to chop the tree."
                )
                message = await interaction.original_response()
                await message.add_reaction("<:pickaxe:1101437961414905898>")

                def check_reaction(reaction, user):
                    return (
                        str(reaction.emoji) == "<:pickaxe:1101437961414905898>"
                        and user == self.author
                    )

                timed_out = False
                try:
                    await interaction.client.wait_for(
                        "reaction_add", check=check_reaction, timeout=10
                    )
                except asyncio.TimeoutError:
                    timed_out = True
                if not timed_out:
                    command = {
                        "author": self.author.id,
                        "unit": self.unit.get("_id"),
                        "command": "chop",
                        "name": object.get("name"),
                        "x": o_x,
                        "y": o_y,
                    }

                    db.commands_collection.insert_one(command)
                    await interaction.channel.send("Command added to queue!")

        elif self.values[0] == "Plant":
            if self.unit.get("seeds", 0) < 20:
                await interaction.response.send_message("Insufficient resources.")
                return
            if self.unit.get("boat"):
                await interaction.response.send_message("Can't plant while in water.")
                return
            dir = self.unit.get("direction", "U")
            dir_map = {"U": (0, -1), "D": (0, 1), "R": (1, 0), "L": (-1, 0)}

            dir_int = dir_map[dir]
            o_x = (x + dir_int[0] * 16) // 16
            o_y = (y + dir_int[1] * 16) // 16

            node = utils.data.map_arr[o_x][o_y]

            if node != 1:
                await interaction.response.send_message(
                    "Can't plant seeds in a water node."
                )
                return

            if utils.data.map_objects.get((o_x, o_y)):
                await interaction.response.send_message("Can't plant here.")
                return
            await interaction.response.send_message("Planted!")
            post = {
                "_id": f"{o_x}-{o_y}",
                "name": "wheatfield",
                "type": "nature",
                "state": 1,
            }

            db.map_collection.insert_one(post)
            utils.data.wheat_fields.append(post)
            utils.data.map_objects[(o_x, o_y)] = post
            db.units_collection.update_one(
                {"_id": self.unit["_id"]}, {"$inc": {"seeds": -20}}
            )

        elif self.values[0] == "Gather":
            mine = utils.data.map_objects.get((x // 16, y // 16), {})

            dir_map = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
            dir = self.unit.get("direction")

            d_x, d_y = dir_map[dir]
            if mine.get("type") != "Mine":
                mine = utils.data.map_objects.get((x // 16 + d_x, y // 16 + d_y), {})
            for d_x in [-1, 0, 1]:
                for d_y in [-1, 0, 1]:
                    if mine.get("type") != "Mine":
                        mine = utils.data.map_objects.get(
                            (x // 16 + d_x, y // 16 + d_y), {}
                        )

            if mine.get("type") != "Mine":
                await interaction.response.send_message("No nearby mines found.")
                return

            else:
                await interaction.response.send_message(
                    f"Found {mine.get('name')}.\nCapacity: {mine.get('cap')}\nCommand added to queue!"
                )
                if mine.get("name") == "Iron Mine":
                    resources_type = "iron"
                else:
                    resources_type = "gold"
                command = {
                    "author": self.author.id,
                    "unit": self.unit.get("_id"),
                    "command": "gather",
                    "name": mine.get("name"),
                    "x": mine["x"],
                    "y": mine["y"],
                    "state": "collect",
                    "type": resources_type,
                    "ore": mine["_id"],
                }
                db.commands_collection.insert_one(command)


class Pings_Select(discord.ui.Select):
    def __init__(self, author):
        self.author = author
        options = [
            discord.SelectOption(
                label="Reaching destination",
                description="Moving units reach their destination.",
            ),
            discord.SelectOption(
                label="Hitting an obstacle",
                description="Moving units fail to reach their destination.",
            ),
            discord.SelectOption(
                label="Attacking an enemy",
                description="Units successfully attack target unit.",
            ),
            discord.SelectOption(
                label="Failing to attack",
                description="Units fail to attack target unit.",
            ),
            discord.SelectOption(
                label="Getting attacked",
                description="Units get attacked by enemy units.",
            ),
        ]

        super().__init__(
            placeholder="Edit your notification settings.",
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
        get_pings(self.author.id).get(self.values[0])

        await interaction.response.send_message(
            f"Editing settings for: {self.values[0]}"
            + "\nSend (y) to set the value to true or (n) to set the value to false."
        )

        def check(m):
            return m.channel == interaction.channel and m.author == self.author

        try:
            choice = await interaction.client.wait_for(
                "message", check=check, timeout=20
            )
        except asyncio.TimeoutError:
            return
        choice = choice.content
        if choice not in ["y", "Y", "n", "N"]:
            await interaction.channel.send("Invalid parameter.")
            return
        if choice == "Y" or choice == "y":
            value = True
        else:
            value = False
        db.pings_collection.update_one(
            {"_id": self.author.id}, {"$set": {self.values[0]: value}}
        )
        await interaction.channel.send("Updated notification settings!")


class PingsView(discord.ui.View):
    def __init__(self, author, *, timeout=40):
        super().__init__(timeout=timeout)
        self.add_item(Pings_Select(author=author))


class construct_Select(discord.ui.Select):
    def __init__(self, author, unit):
        self.author = author
        self.unit = unit
        options = []

        for building in info:
            wood, stone, gold, iron = info[building].get("Cost", (0, 0, 0, 0))
            cost_string = ""

            cost_string += f"Wood: {wood} "
            cost_string += f",Stone: {stone} "
            cost_string += f",Gold: {gold} "
            cost_string += f",Iron: {iron} "

            options.append(
                discord.SelectOption(label=building, description=cost_string)
            )

        super().__init__(
            placeholder="Select the building",
            max_values=1,
            min_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
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
        cost = info[self.values[0]].get("Cost", ())
        player_post = db.resources_collection.find_one({"_id": self.author.id}) or {}
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

        x, y = self.unit.get("x"), self.unit.get("y")

        s = info.get(self.values[0], {}).get("Size", (16, 16))

        dir = self.unit.get("direction", "U")
        dir_map = {"U": (0, -1), "D": (0, 1), "R": (1, 0), "L": (-1, 0)}

        dir_int = dir_map[dir]
        x, y = (x // 16) * 16 + dir_int[0] * 16, (y // 16) * 16 + dir_int[1] * 16
        draw_box = (x, y, x + s[0], y + s[1])

        node = utils.data.map_arr[x // 16][y // 16]
        if not node:
            await interaction.response.send_message("Cannot build here.")
            return

        # Docks need to be next to a water body
        direction_array = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        adjacent_node = utils.data.map_arr[x // 16][y // 16]
        nx, ny = x, y
        if self.values[0] == "Docks":
            for d in direction_array:
                if adjacent_node != 0:
                    nx, ny = d[0], d[1]
                    adjacent_node = utils.data.map_arr[(x // 16) + d[0]][
                        (y // 16) + d[1]
                    ]

            if adjacent_node != 0:
                await interaction.response.send_message(
                    "Docks can only be built next to a water body."
                )
                return

        # Checking if the building overlaps with another object or building on the map
        rect1 = (x // 16, y // 16, (x + s[0]) // 16, (y + s[1]) // 16)
        start = time.time()
        for object in utils.data.map_objects:
            value = utils.data.map_objects[object]
            o_x, o_y = object
            size = value.get("size", (16, 16))

            rect2 = (o_x, o_y, o_x + size[0] // 16, o_y + size[1] // 16)

            if overlap(rect1, rect2):
                await interaction.response.send_message(
                    "Cannot build here." + "Too close to another building."
                )
                await interaction.channel.send(f"{rect1} \n{rect2}")
                print(size)
                print(value)
                return
        end = time.time()
        print(f"iterated through all map objects in {end - start :.3f}")

        author_post = db.units_collection.find_one({"_id": self.author.id})
        unit_post = self.unit
        size = (6000, 6000)
        new_size = (800, 800)
        u_x, u_y = unit_post.get("x"), unit_post.get("y")

        # set constraint for x and y boundaries
        if u_x < new_size[0] // 2:
            u_x = new_size[0] // 2
        if u_x > size[0] - new_size[0] // 2:
            u_x = size[0] - new_size[0] // 2
        if u_y < new_size[1] // 2:
            u_y = new_size[1] // 2
        if u_y > size[1] - new_size[1] // 2:
            u_y = size[1] - new_size[1] // 2

        map_image, fog_image = draw_map(author_post, unit_post, transparent=True)

        building_image_name = self.values[0].replace(" ", "_")
        race = self.unit.get("race")

        t = info[self.values[0]].get("Time")

        # Determine the box coordinates based on direction
        if self.values[0] == "Docks":
            for d in dir_map:
                if dir_map[d] == (nx, ny):
                    building_image_name = f"Docks_{d}"
                    s = (16 + abs(nx) * 16, 16 + abs(ny) * 16)

                    start = min((x, y), (x + 16 * nx, y + 16 * ny))
                    end = max((x, y), (x + 16 * nx, y + 16 * ny))
                    draw_box = (x, y, x + s[0], y + s[1])
                    break

        if self.values[0] in [
            "Horizontal Wall",
            "Vertical Wall",
            "Tower",
            "Ladder Tower",
        ]:
            hp = 200
            building_type = "wall"
            t = 1 / 6
            building_image_name = info[self.values[0]].get("Image")
            path = f"images/NCNL/Walls/{building_image_name}.png"
        else:
            building_type = "building"
            path = f"images/NCNL/{race}/{building_image_name}.png"
            hp = 400

        if not t:
            print(f"Invalid time for {self.values[0]}")
            return
        building_image = Image.open(path)
        building_image.putalpha(200)
        fog_image.paste(building_image, draw_box, mask=building_image)
        map_image = Image.alpha_composite(map_image, fog_image)
        cropped = map_image.crop(
            (
                u_x - new_size[0] // 2,
                u_y - new_size[1] // 2,
                u_x + new_size[0] // 2,
                u_y + new_size[1] // 2,
            )
        )
        cropped.save("images/NCNL/cropped-build.png")
        await interaction.response.send_message(
            file=discord.File("images/NCNL/cropped-build.png")
        )

        message = await interaction.channel.send("React with ✅ to build.")
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
            filter = {"_id": self.author.id}

            resources = ["wood", "stone", "gold", "iron"]

            for index, currency in enumerate(inventory):
                currency -= cost[index]

                update = {"$set": {resources[index]: currency}}
                db.resources_collection.update_one(filter, update)

            command = {
                "author": self.author.id,
                "unit": self.unit.get("_id"),
                "command": "build",
                "name": self.values[0],
                "hp": hp,
                "race": self.unit.get("race"),
                "x": x,
                "y": y,
                "image": building_image_name,
                "type": building_type,
                "time": int(t * 60),
            }
            if s != (16, 16):
                command["size"] = s
            db.commands_collection.insert_one(command)
            await interaction.channel.send("Command added to queue!")


class Select_View(discord.ui.View):
    def __init__(self, author, unit, *, timeout=40):
        super().__init__(timeout=timeout)
        self.add_item(Unit_Select(author=author, unit=unit))


class Construct_View(discord.ui.View):
    def __init__(self, author, unit, *, timeout=40):
        super().__init__(timeout=timeout)
        self.add_item(construct_Select(author=author, unit=unit))
