import discord
from discord.ext import commands
from PIL import Image
import utils.database as db
from utils.data import map_objects
import time
import utils.images


class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="map", aliases=["m"])
    async def map(self, ctx, arg=None):
        start_time = time.time()
        player_post = db.units_collection.find_one({"_id": ctx.author.id})

        if player_post is None:
            player_post = db.dead_collection.find_one({"_id": ctx.author.id})

        if player_post is None:
            await ctx.send("You are not a participant in the game system.")
            return

        if arg:
            try:
                unit_id = int(arg)
            except ValueError:
                await ctx.send("Invalid parameter.")
                return

            unit_post = db.units_collection.find_one(
                {"_id": unit_id, "race": player_post.get("race")}
            )

            if unit_post is None:
                await ctx.send("Unit not found.")
                return
        else:
            if player_post.get("dead"):
                await ctx.send("You are dead. L Bozo.")
                return

        unit_post = player_post

        map_image = Image.open("images/NCNL/map.png")

        size = (6000, 6000)
        new_size = (800, 800)
        x, y = unit_post.get("x"), unit_post.get("y")

        # set constraint for x and y boundaries
        if x < new_size[0] / 2:
            x = new_size[0] / 2
        if x > size[0] - new_size[0] / 2:
            x = size[0] - new_size[0] / 2
        if y < new_size[1] / 2:
            y = new_size[1] / 2
        if y > size[1] - new_size[1] / 2:
            y = size[1] - new_size[1] / 2
        end_time_0 = time.time()
        # draw all map objects
        for object in map_objects:
            b_x, b_y = object[0], object[1]

            object = map_objects[object]
            size = object.get("size", (16, 16))
            if (
                b_x * 16 < x - new_size[0] // 2 - size[0]
                or b_x * 16 > x + new_size[0] // 2 + size[0]
                or b_y * 16 < y - new_size[1] // 2 - size[1]
                or b_y * 16 > y + new_size[1] // 2 + size[1]
            ):
                continue
            object_type = object.get("type")

            if object_type == "building":
                race = object.get("race", "NPC")

                path = f"images/NCNL/{race}/{object.get('image')}.png"

            elif object_type == "nature":
                path = f"images/NCNL/Nature/{object.get('image')}.png"
            else:
                path = f"images/NCNL/Other/{object.get('image')}.png"

            image = Image.open(path)
            map_image.paste(
                image,
                (b_x * 16, b_y * 16, b_x * 16 + size[0], b_y * 16 + size[1]),
                mask=image,
            )
        end_time_1 = time.time()

        # draw units
        for unit in db.units_collection.find():
            u_x, u_y = unit.get("x"), unit.get("y")
            if (
                u_x < x - new_size[0] // 2 - 32
                or u_x > x + new_size[0] // 2 + 32
                or u_y < y - new_size[1] // 2 - 32
                or u_y > y + new_size[1] // 2 + 32
            ):
                continue

            states = {-1: "attack", 0: "idle", 1: "move"}
            race = unit.get("race")
            name = unit.get("name")
            if name == "Player":
                name = unit.get("class")
            state = states.get(unit.get("state"))
            direction = unit.get("direction")

            s = 32 if name == "Knight" else 16
            path = f"images/NCNL/Units/{race}/{name}/{state}/{direction}.png"

            unit_image = Image.open(path)
            map_image.paste(
                unit_image,
                (
                    u_x - s // 2,
                    u_y - s // 2,
                    u_x + s // 2,
                    u_y + s // 2,
                ),
                mask=unit_image,
            )

            if name == "Lancer" and state == "attack":
                dir = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
                offset = dir.get(direction, (0, 0))
                u_x += 16 * offset[0]
                u_y += 16 * offset[1]

                path = f"images/NCNL/Units/{race}/{name}/{state}/{direction}2.png"

                unit_image = Image.open(path)
                map_image.paste(
                    unit_image,
                    (
                        u_x - s // 2,
                        u_y - s // 2,
                        u_x + s // 2,
                        u_y + s // 2,
                    ),
                    mask=unit_image,
                )
        end_time_2 = time.time()
        cropped = map_image.crop(
            (
                x - new_size[0] // 2,
                y - new_size[1] // 2,
                x + new_size[0] // 2,
                y + new_size[1] // 2,
            )
        )
        cropped.save("images/NCNL/cropped.png")
        end_time_3 = time.time()

        execution_time_0 = end_time_0 - start_time
        execution_time_1 = end_time_1 - end_time_0
        execution_time_2 = end_time_2 - end_time_1
        execution_time_3 = end_time_3 - end_time_2

        # Print the execution time of each block
        print(f"Image.open() Time: {execution_time_0:.6f} seconds")
        print(f"Map Time: {execution_time_1:.6f} seconds")
        print(f"Units Time: {execution_time_2:.6f} seconds")
        print(f"Crop Time: {execution_time_3:.6f} seconds")
        print(f"Total Time: {(start_time - end_time_3):.6f} seconds\n")
        await ctx.send(file=discord.File("images/NCNL/cropped.png"))

    @commands.command(name="test")
    async def test(self, ctx, arg=None):
        player_post = db.units_collection.find_one({"_id": ctx.author.id})

        if player_post is None:
            player_post = db.dead_collection.find_one({"_id": ctx.author.id})

        if player_post is None:
            await ctx.send("You are not a participant in the game system.")
            return

        if arg:
            try:
                unit_id = int(arg)
            except ValueError:
                await ctx.send("Invalid parameter.")
                return

            unit_post = db.units_collection.find_one(
                {"_id": unit_id, "race": player_post.get("race")}
            )

            if unit_post is None:
                await ctx.send("Unit not found.")
                return
        else:
            if player_post.get("dead"):
                await ctx.send("You are dead. L Bozo.")
                return

        unit_post = player_post

        size = (6000, 6000)
        new_size = (800, 800)
        x, y = unit_post.get("x"), unit_post.get("y")

        # set constraint for x and y boundaries
        if x < new_size[0] / 2:
            x = new_size[0] / 2
        if x > size[0] - new_size[0] / 2:
            x = size[0] - new_size[0] / 2
        if y < new_size[1] / 2:
            y = new_size[1] / 2
        if y > size[1] - new_size[1] / 2:
            y = size[1] - new_size[1] / 2

        if player_post.get("race") == "Cyan":
            map_image = utils.images.map_cyan
        elif player_post.get("race") == "Red":
            map_image = utils.images.map_red
        elif player_post.get("race") == "Lime":
            map_image = utils.images.map_lime
        elif player_post.get("race") == "Admin":
            map_image = utils.images.map_image
        else:
            await ctx.send("An error occured! Please contact <@660929334969761792>.")
            return

        if player_post.get("race") != "Admin":
            cropped = map_image.crop(
                (
                    x - new_size[0] // 2,
                    y - new_size[1] // 2,
                    x + new_size[0] // 2,
                    y + new_size[1] // 2,
                )
            )
            cropped.save("images/NCNL/cropped.png")
            await ctx.send(file=discord.File("images/NCNL/cropped.png"))
        else:
            map_image.save("images/NCNL/admin.png")
            await ctx.send(file=discord.File("images/NCNL/admin.png"))


async def setup(client):
    await client.add_cog(Commands(client))
