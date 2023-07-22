import discord
from discord.ext import commands, tasks
from utils import embed_color
import database as db

GAME_SPEED = 1
with open("map.txt", "r") as f:
    map_array = eval(f.read())


class World(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.index = 0
        self.game.start()

    def cog_unload(self):
        self.game.cancel()

    @tasks.loop(minutes=GAME_SPEED)
    async def game(self):
        # print("tick: " , self.index)
        self.index += 1


async def setup(client):
    await client.add_cog(World(client))
