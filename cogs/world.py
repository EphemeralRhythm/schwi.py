from discord.ext import commands, tasks
import utils.database as db
import time
import random
import utils.data
from utils.command_utils import update_command, astar, log, attack
from utils.fog_of_war import diverge_search
from utils.units_info import units as units_info
from pymongo import UpdateOne

ROWS = 375
COLS = 375
GAME_SPEED = 10

with open("map.txt", "r") as f:
    map_array = eval(f.read())


class World(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.index = 1
        self.game.start()

    def cog_unload(self):
        self.game.cancel()

    @tasks.loop(seconds=GAME_SPEED)
    async def game(self):
        print("tick: ", self.index)

        utils.data.game_time = self.index

        start_time = time.time()

        command_list = list(db.commands_collection.find())
        command_hash = {}
        for c in command_list:
            command_hash[c.get("unit")] = c.get("command")

        for unit in db.units_collection.find():
            if target_id := utils.data.attacked_from.get(unit["_id"]):
                if command_hash.get(unit["_id"]) == "attack":
                    continue
                utils.data.has_attacked.add(unit["_id"])
                await attack(unit, target_id[0], client=self.client)

        utils.data.attacked_from.clear()

        random.shuffle(command_list)
        for c in command_list:
            if c.get("unit") in utils.data.has_attacked:
                continue
            await update_command(c, client=self.client)

        utils.data.has_attacked.clear()

        end_time_1 = time.time()
        utils.data.dynamic_fog = {}
        fog_updates = []

        night_debuff = 0 if self.index < 180 else 2
        for unit in db.units_collection.find():
            x, y = unit.get("x"), unit.get("y")

            tower_buff = 0
            node_type = utils.data.map_arr[x // 16][y // 16]
            if node_type == -1:
                tower_buff = 2

            info = units_info.get(unit["name"], {})
            sight = unit.get("sight", info.get("sight")) + tower_buff - night_debuff
            race = unit.get("race")

            # create the dynamic fog of war
            local_update = diverge_search(
                (x // 16, y // 16),
                sight,
                race,
                unit.get("direction"),
                utils.data.dynamic_fog,
                utils.data.map_fog,
            )

            fog_updates.extend(local_update)

            # update units
            update_map = {}
            query = {"_id": unit["_id"]}
            info_post = units_info.get(unit["name"])
            if unit.get("recharge", 0) > 0:
                update_map["recharge"] = 1

            if not info_post:
                max_hp = unit.get("max_hp", 0)
            else:
                max_hp = info_post["hitpoints"]
            if unit.get("heal", 0) > 0:
                update_map["heal"] = -1
            elif unit.get("hp") < max_hp:
                update_map["hp"] = 1
            if update_map:
                update = {"$inc": update_map, "$set": {"state": 0}}
            else:
                update = {"$set": {"state": 0}}
            db.units_collection.update_one(query, update)

        db.fog_collection.bulk_write(fog_updates)
        end_time_2 = time.time()

        for q in db.unit_queues.find():
            db.unit_queues.update_one(
                {"_id": q["_id"]}, {"$set": {"time": q["time"] - 1}}
            )
            if q.get("time") == 0:
                db.unit_queues.delete_one({"_id": q["_id"]})

                keys = ["time", "building"]
                for k in keys:
                    q.pop(k)

                db.units_collection.insert_one(q)

                await log(
                    q.get("race"),
                    "Unit Ready!",
                    f"{q['name']} {q['_id']} is ready!",
                    client=self.client,
                    content=None,
                )
        self.index += 1
        if self.index >= 360:
            updates = []
            for field in utils.data.wheat_fields:
                if field["state"] < 4:
                    field["state"] += 1
                    query = {"_id": field["_id"]}
                    update = {"state": field["state"]}

                    updates.append(UpdateOne(query, update))

            db.map_collection.bulk_write(fog_updates)
            self.index = 0
        execution_time_1 = end_time_1 - start_time
        execution_time_2 = end_time_2 - end_time_1
        # print(f"Handling commands:{execution_time_1:.6f} seconds")
        # print(f"World Fog Time: {execution_time_2:.6f} seconds")

    @commands.command(name="set_time")
    async def set_time(self, ctx, arg=0):
        if ctx.author.id != 660929334969761792:
            return

        self.index = int(arg)

        await ctx.send("✅")

    @commands.command(name="set_tick_speed")
    async def set_tick_speed(self, ctx, arg=0):
        if ctx.author.id != 660929334969761792:
            return
        global GAME_SPEED
        GAME_SPEED = int(arg)

        await ctx.send("✅")

    @commands.command(name="pathfind")
    async def pathfind(self, ctx, *, args):
        if not ctx.author.id == 660929334969761792:
            return
        player_post = db.units_collection.find_one({"_id": ctx.author.id})

        if not player_post:
            await ctx.send("Unit not found.")
            return

        if len(args.split(" ")) != 2:
            await ctx.send("Invalid Vector Format")
            return

        i_x, i_y = player_post.get("x"), player_post.get("y")
        x, y = args.split(" ")
        try:
            x, y = int(x), int(y)
        except ValueError:
            await ctx.send("Invalid Vector Format")
            return
        node_x = (i_x + x) // 16
        node_y = (i_y + y) // 16
        path = astar(node_x, node_y, player_post)

        await ctx.send(path)


async def setup(client):
    await client.add_cog(World(client))
