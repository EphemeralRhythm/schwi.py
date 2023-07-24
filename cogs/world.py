import discord
from discord.ext import commands, tasks
from PIL import Image, ImageDraw
import utils.database as db
from utils.data import map_objects, map_fog
import time
import utils.images

ROWS = 375
COLS = 375
GAME_SPEED = 1

with open("map.txt", "r") as f:
    map_array = eval(f.read())


def drawMap():
    start_time = time.time()
    map_image = Image.open("images/NCNL/map.png")

    size = (6000, 6000)
    end_time_0 = time.time()
    # draw all map objects
    for object in map_objects:
        b_x, b_y = object[0], object[1]

        object = map_objects[object]
        size = object.get("size", (16, 16))
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
        image.close()

    end_time_1 = time.time()

    # draw units
    for unit in db.units_collection.find():
        u_x, u_y = unit.get("x"), unit.get("y")

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

            unit_image.close()

    end_time_2 = time.time()

    print("Started")
    red_image = Image.new("RGBA", (6000, 6000), (0, 0, 0, 0))
    red_fog = ImageDraw.Draw(red_image)

    cyan_image = Image.new("RGBA", (6000, 6000), (0, 0, 0, 0))
    cyan_fog = ImageDraw.Draw(cyan_image)

    lime_image = Image.new("RGBA", (6000, 6000), (0, 0, 0, 0))
    lime_fog = ImageDraw.Draw(lime_image)

    for spot in map_fog:
        x, y = spot

        post = map_fog[spot]
        if not post.get("cyan"):
            cyan_fog.rounded_rectangle(
                (
                    x * 16,
                    y * 16,
                    x * 16 + 16,
                    y * 16 + 16,
                ),
                fill=(0, 0, 0),
            )

        if not post.get("red"):
            red_fog.rounded_rectangle(
                (
                    x * 16,
                    y * 16,
                    x * 16 + 16,
                    y * 16 + 16,
                ),
                fill=(0, 0, 0),
            )

        if not post.get("lime"):
            lime_fog.rounded_rectangle(
                (
                    x * 16,
                    y * 16,
                    x * 16 + 16,
                    y * 16 + 16,
                ),
                fill=(0, 0, 0),
            )
    end_time_3 = time.time()

    utils.images.map_cyan = Image.alpha_composite(map_image, cyan_image)
    utils.images.map_red = Image.alpha_composite(map_image, red_image)
    utils.images.map_lime = Image.alpha_composite(map_image, lime_image)
    utils.images.map_image = map_image

    end_time_4 = time.time()

    execution_time_0 = end_time_0 - start_time
    execution_time_1 = end_time_1 - end_time_0
    execution_time_2 = end_time_2 - end_time_1
    execution_time_3 = end_time_3 - end_time_2
    execution_time_4 = end_time_4 - end_time_3

    # Print the execution time of each block
    print(f"Image.open() Time: {execution_time_0:.6f} seconds")
    print(f"Map Time: {execution_time_1:.6f} seconds")
    print(f"Units Time: {execution_time_2:.6f} seconds")
    print(f"Fog Draw Time: {execution_time_3:.6f} seconds")
    print(f"Alpha Time: {execution_time_4:.6f} seconds")
    print(f"Total Time: {(start_time - end_time_4):.6f} seconds\n")


class World(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.index = 0
        self.game.start()

    def cog_unload(self):
        self.game.cancel()

    @tasks.loop(minutes=GAME_SPEED)
    async def game(self):
        print("tick: ", self.index)
        drawMap()
        self.index += 1


async def setup(client):
    await client.add_cog(World(client))
