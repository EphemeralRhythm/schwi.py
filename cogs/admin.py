import discord
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
from discord import File
import random
import utils.database as db


class Admin(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if not message.guild:
                logs = self.client.get_channel(1103882731890425887)

                embed = discord.Embed(title="DM recieved")
                description = f"Author: {message.author.name}\n\n"
                description += message.content
                embed.description = description

                await logs.send(embed=embed)

    @commands.command(name="say")
    async def help(self, ctx, *, args):
        if ctx.author.id != 660929334969761792:
            return
        await ctx.message.delete()
        await ctx.send(args)

    @commands.command(name="welcome")
    async def welcome(self, ctx, member: discord.Member):
        if ctx.author.id != 660929334969761792:
            return

        entrance_channel = self.client.get_channel(899204296829194282)
        uploads_channel = self.client.get_channel(1014864807243038792)

        embed = discord.Embed(
            title=f"Welcome to No Chess No Life",
            color=discord.Color.from_rgb(201, 0, 118),
        )

        embed.description = f"""Welcome {member.mention}!"""
        embed.set_footer(text=f"Member count: {member.guild.member_count}")

        font = Font(path="fonts/arial-unicode.ttf", size=40)
        choice = random.randint(0, 3) + 1
        diameter = 240
        offset = 10

        x, y = (752 // 2 - diameter // 2, 16)

        background = Editor(f"images/welcome/ngnl_bg{choice}.jpg").resize((752, 419))

        # add black tint to the bg
        ima = Editor("images/xpcards/zBLACK.png").resize((752, 422))
        background.blend(image=ima, alpha=0.6, on_top=False)

        profile = await load_image_async(str(member.display_avatar).split("?")[0])
        profile = Editor(profile).resize((diameter, diameter)).circle_image()

        background.ellipse(
            (x - offset, y - offset),
            width=diameter + 2 * offset,
            height=diameter + 2 * offset,
            fill=None,
            outline="#fff",
            stroke_width=7,
        )
        background.paste(profile.image, (x, y))

        background.text(
            (x + diameter // 2, 300),
            str(member.name),
            font=font,
            color="#fff",
            align="center",
        )

        card = File(fp=background.image_bytes, filename="images/xpcards/zCARD.png")
        message = await uploads_channel.send(file=card)
        url = message.attachments[0].url

        embed.set_image(url=url)
        await entrance_channel.send(embed=embed)

    @commands.command(name="dm")
    async def dm(self, ctx, member: discord.Member, *, args):
        if ctx.author.id != 660929334969761792:
            return
        await member.send(args)

    @commands.command(name="updateRoles")
    async def update_roles(self, ctx):
        guild = ctx.author.guild

        disboard_channel = self.client.get_channel(1026908349020770324)
        embed_mess = await disboard_channel.fetch_message(1056567118960791652)

        color = discord.Color.from_rgb(201, 0, 118)
        embed = discord.Embed(title="Disboard", color=color)

        description = ""
        role = guild.get_role(992490411425792201)

        for member in role.members:
            description += f"• <@{member.id}>\n"

        embed.description = description
        await embed_mess.edit(embed=embed)

    @commands.command(name="logs")
    async def logs(self, ctx):
        if ctx.author.id != 660929334969761792:
            return
        file_path = "logs/infos.log"

        with open(file_path, "rb") as file:
            file_data = discord.File(file)

        await ctx.send(file=file_data)

    @commands.command(name="create")
    async def create(self, ctx):
        if ctx.author.id != 660929334969761792:
            return
        guild = ctx.guild
        red = discord.utils.get(guild.roles, name="Red")
        cyan = discord.utils.get(guild.roles, name="Cyan")
        lime = discord.utils.get(guild.roles, name="Lime 🤓")
        locations = [(5, 92), (310, 369), (303, 3)]
        races = ["cyan", "red", "lime"]
        roles = [cyan, red, lime]

        for i in range(3):
            role = roles[i]
            for member in role.members:
                race = races[i]
                print(member, races[i])
                loc = locations[i]
                x_offset = random.randint(-60, +60)
                y_offset = random.randint(-60, +60)
                x = loc[0] * 16 + x_offset
                y = loc[1] * 16 + y_offset

                if x <= 0:
                    x = 1
                if x >= 6000:
                    x = 6000 - 1
                if y <= 0:
                    y = 1
                if y >= 6000:
                    y = 6000 - 1

                player = {
                    "_id": member.id,
                    "race": race,
                    "name": "Player",
                    "class": "Swordsman",
                    "hp": 50,
                    "max_hp": 50,
                    "direction": random.choice(["U", "D", "R", "L"]),
                    "x": x,
                    "y": y,
                    "attack": 10,
                    "state": 0,
                    "recharge": 0,
                }
                resources = {
                    "_id": member.id,
                    "gold": 0,
                    "iron": 0,
                    "wood": 0,
                    "stone": 0,
                }
                db.resources_collection.insert_one(resources)
                # db.units_collection.insert_one(player)


async def setup(client):
    await client.add_cog(Admin(client))
