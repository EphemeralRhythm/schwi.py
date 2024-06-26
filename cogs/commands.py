import discord
from discord.ext import commands
import typing
import utils.database as db
import utils.data
from utils.pings import get_pings
import utils.ui
from models.views import Select_View, PingsView
import utils.emoji


class Commands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="map")
    async def map(self, ctx, arg=None):
        player_post = db.units_collection.find_one({"_id": ctx.author.id})

        if player_post is None:
            player_post = db.dead_collection.find_one({"_id": ctx.author.id})

        if player_post is None:
            await ctx.send("You are not a participant in the game system.")
            return

        if arg:
            if arg == "-a":
                unit_post = player_post
            else:
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
        if x < new_size[0] // 2:
            x = new_size[0] // 2
        if x > size[0] - new_size[0] // 2:
            x = size[0] - new_size[0] // 2
        if y < new_size[1] // 2:
            y = new_size[1] // 2
        if y > size[1] - new_size[1] // 2:
            y = size[1] - new_size[1] // 2
        if arg != "-a":
            map_image = utils.ui.draw_map(player_post, unit_post)
        else:
            map_image = utils.ui.full_map(player_post, unit_post)

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

    @commands.command(name="units")
    async def units(self, ctx, arg=None):
        if arg and arg != "all":
            await ctx.send("Invalid argument")
            return
        player_post = db.units_collection.find_one(
            {"_id": ctx.author.id}
        ) or db.dead_collection.find_one({"_id": ctx.author.id})

        if not player_post:
            await ctx.send("You are not a participant in the game system.")
            return

        if arg == "all":
            units = db.units_collection.find({"race": player_post.get("race")})
        else:
            units = db.units_collection.find({"owner": ctx.author.id})

        embed = discord.Embed(
            title="Available Units", color=discord.Color.from_rgb(201, 0, 118)
        )
        description = ""
        for unit in units:
            description += f'{unit.get("name")}: {unit.get("_id")}\n'
        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="command", aliases=["c"])
    async def command(self, ctx, arg=None):
        dead = False
        player_post = db.units_collection.find_one({"_id": ctx.author.id})

        if not player_post:
            player_post = db.dead_collection.find_one({"_id": ctx.author.id})
            dead = True

        if not player_post:
            await ctx.send("You are not a participant in the game system.")
            return

        if dead and not arg:
            await ctx.send("You are dead. L bozo")
            return

        if arg:
            unit = db.units_collection.find_one(
                {"_id": int(arg), "race": player_post.get("race")}
            )
            if not unit:
                await ctx.send("Unit not found")
                return
            if not unit.get("owner") == ctx.author.id:
                await ctx.send("You don't have permission to control this unit.")
                return
        else:
            unit = player_post

        filter = {"unit": unit["_id"]}

        if command := db.commands_collection.find_one(filter):
            if command.get("command") == "build":
                await ctx.send(
                    f"""{unit.get('name')} is building {command.get('name')}.
                    Time Left: {command.get('time')}"""
                )
                return

            db.commands_collection.delete_many(filter)

        view = Select_View(author=ctx.author, unit=unit)
        await ctx.send(f"{unit.get('name')} {unit.get('_id')}", view=view)

    @commands.command(name="move")
    async def move(self, ctx, *, args: str):
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

        # if ctx.author.id == 660929334969761792:
        #     i_x += x
        #     i_y += y
        #     update = {"$set": {"x": i_x, "y": i_y}}
        #
        #     db.units_collection.find_one_and_update({"_id": ctx.author.id}, update)
        #     await ctx.send("✅")
        #     return
        if player_post.get("boat"):
            await ctx.send("Cannot move while in boat.")
            return

        db.commands_collection.delete_many({"unit": ctx.author.id})

        i_x += x
        i_y += y
        command = {
            "author": ctx.author.id,
            "unit": ctx.author.id,
            "command": "move",
            "x": i_x,
            "y": i_y,
        }
        db.commands_collection.insert_one(command)

        await ctx.channel.send("Command added to queue!")

    @commands.command(name="status", aliases=["s"])
    async def status(self, ctx, arg=None):
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

        embed = discord.Embed(
            color=discord.Color.from_rgb(201, 0, 118),
        )
        _id = (
            unit_post["_id"]
            if unit_post["name"] != "player"
            else f"<@{unit_post['_id']}>"
        )
        description = f"**{unit_post['name']} {_id}**\n\n"
        if cl := unit_post.get("class"):
            description += f"* **Class:** {cl}\n\n"

        description += f"* **HP**: {unit_post.get('hp')}\n\n"
        inv = False
        if inv := unit_post.get("inv"):
            description += "* **Inventory:** \n"

            for item in inv:
                description += " * " + item + "\n"
            inv = True

        items = [
            "seeds",
            "wheat",
            "cod",
            "salmon",
            "tropical_fish",
            "wood",
            "stone",
            "raw_iron",
            "raw_gold",
            "haybale",
        ]
        for item in items:
            if amount := unit_post.get(item):
                if not inv:
                    description += "* **Inventory:** \n"
                    inv = True
                emoji = utils.emoji.items.get(item) or utils.emoji.resources.get(item)
                description += f" * {amount} {emoji}\n"

        description += "\n"
        command = db.commands_collection.find_one({"unit": unit_post["_id"]})
        if command:
            description += "* **Command:** \n"
            match command["command"]:
                case "move":
                    f_x, f_y = command.get("x"), command.get("y")
                    x, y = unit_post.get("x"), unit_post.get("y")
                    description += f"Move: ({f_x - x}, {f_y - y})"
                case "attack":
                    target = db.units_collection.find_one({"_id": command["target"]})
                    description += f"Attack: {target['name']}"
                case "battack":
                    target = db.buildings_collection.find_one(
                        {"_id": command["target"]}
                    )
                    description += f"Attack: {target['name']}"

                case "gather":
                    resources_type = command.get("type")
                    raw_type = "raw_" + str(resources_type)
                    amount = unit_post.get(raw_type)
                    emoji = utils.emoji.resources.get(resources_type)
                    description += f"Gather: {amount} {emoji}"
                case "build":
                    time = command.get("time")
                    name = command.get("name")

                    description += f"Build: {name} ({time} minutes left)"
                case other:
                    description += str(other)

        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="statusAll")
    async def status_all(self, ctx):
        player_post = db.units_collection.find_one(
            {"_id": ctx.author.id}
        ) or db.dead_collection.find_one({"_id": ctx.author.id})

        if not player_post:
            await ctx.send("Invalid syntax. Use `.help reassign` for more info.")
            return
        race = player_post.get("race")
        description = ""

        query = {"race": race}
        for unit in db.units_collection.find(query):
            command = db.commands_collection.find_one({"unit": unit["_id"]})

            if command:
                description += f"* {unit.get('name')} {unit['_id']}:\n"
                match command["command"]:
                    case "move":
                        f_x, f_y = command.get("x"), command.get("y")
                        x, y = unit.get("x"), unit.get("y")
                        description += f"Move: ({f_x - x}, {f_y - y})"
                    case "attack":
                        target = db.units_collection.find_one(
                            {"_id": command["target"]}
                        )
                        description += f"Attack: {target['name']}"
                    case "battack":
                        target = db.buildings_collection.find_one(
                            {"_id": command["target"]}
                        )
                        description += f"Attack: {target['name']}"

                    case "gather":
                        resources_type = command.get("type")
                        raw_type = "raw_" + str(resources_type)
                        amount = unit.get(raw_type)
                        emoji = utils.emoji.resources.get(resources_type)
                        description += f"Gather: {amount} {emoji}"
                    case "build":
                        time = command.get("time")
                        name = command.get("name")

                        description += f"Build: {name} ({time} minutes left)"
                    case other:
                        description += str(other)
                description += "\n"

        color = discord.Color.from_rgb(201, 0, 118)
        embed = discord.Embed(
            color=color, title="All Units Status", description=description
        )
        await ctx.send(embed=embed)

    @commands.command(name="reassign")
    async def reassign(
        self, ctx, arg=None, member: typing.Optional[discord.Member] = None
    ):
        player_post = db.units_collection.find_one(
            {"_id": ctx.author.id}
        ) or db.dead_collection.find_one({"_id": ctx.author.id})

        if not member:
            await ctx.send("Invalid syntax. Use `.help reassign` for more info.")
            return

        member_post = db.units_collection.find_one(
            {"_id": member.id}
        ) or db.dead_collection.find_one({"_id": member.id})

        if not member_post:
            await ctx.send(f"{member.name} is not a part of the game system.")
            return

        if not player_post:
            await ctx.send("You are not a participant in the game system.")
            return

        if member_post.get("race") != player_post.get("race"):
            await ctx.send(
                "You can't give units to a player of a different race you silly."
            )
            return

        if not arg:
            await ctx.send(
                "Please provide the unit id that you want to reassign."
                + "Use `.help reassign` for more info on this command."
            )
            return

        unit = db.units_collection.find_one(
            {"_id": int(arg), "race": player_post.get("race")}
        )
        if not unit:
            await ctx.send("Unit not found")
            return

        isLeader = False
        role = discord.utils.get(ctx.guild.roles, name="Team Leader")
        if ctx.author in role.members:
            isLeader = True

        if not unit.get("owner") == ctx.author.id and not isLeader:
            await ctx.send("You don't have permission to command this unit.")
            return

        filter = {"_id": unit["_id"]}
        update = {"$set": {"owner": member.id}}

        db.units_collection.update_one(filter, update)

        await ctx.send(
            f"Reassigned {unit.get('name')} {unit.get('_id')} to {member.name}."
        )

    @commands.command(name="pings")
    async def pings(self, ctx):
        player_post = db.units_collection.find_one(
            {"_id": ctx.author.id}
        ) or db.dead_collection.find_one({"_id": ctx.author.id})

        if not player_post:
            await ctx.send("You are not a participant in the game system.")
            return

        view = PingsView(author=ctx.author)
        await ctx.send("Edit your pings configuration: ", view=view)

    @commands.command(name="getpings")
    async def getpings(self, ctx):
        ping_configs = get_pings(ctx.author.id)
        ping_configs.pop("_id")
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Ping Settings: ",
            color=discord.Color.from_rgb(201, 0, 118),
        )
        description = ""

        for value in ping_configs:
            description += f"* {value}: {ping_configs.get(value)}\n"
        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name="wood")
    async def wood(self, ctx, arg=None):
        dead = False
        player_post = db.units_collection.find_one({"_id": ctx.author.id})

        if not player_post:
            player_post = db.dead_collection.find_one({"_id": ctx.author.id})
            dead = True

        if not player_post:
            await ctx.send("You are not a participant in the game system.")
            return

        if dead and not arg:
            await ctx.send("You are dead. L bozo")
            return

        if arg:
            unit = db.units_collection.find_one(
                {"_id": int(arg), "race": player_post.get("race")}
            )
            if not unit:
                await ctx.send("Unit not found")
                return
            if not unit.get("owner") == ctx.author.id:
                await ctx.send("You don't have permission to control this unit.")
                return
        else:
            unit = player_post

        if not unit.get("wood"):
            await ctx.send(f"{unit['name']} {unit['_id']} doesn't have any wood.")
            return
        db.resources_collection.update_one(
            {"_id": ctx.author.id}, {"$inc": {"wood": unit.get("wood")}}
        )
        db.units_collection.update_one({"_id": unit["_id"]}, {"$set": {"wood": 0}})

        await ctx.send("✅")


async def setup(client):
    await client.add_cog(Commands(client))
