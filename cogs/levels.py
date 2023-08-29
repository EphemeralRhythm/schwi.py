import discord
from discord import File
from discord.ext import commands
import typing
from easy_pil import Editor, load_image_async, Font, Canvas
import time
from models.ranks import ranks
from utils.database import xp_collection as profiles


def get_post(id) -> dict:
    player_post = profiles.find_one({"_id": id})
    if not player_post:
        player_post = {"_id": id, "xp": -5, "timeout": 0}
        profiles.insert_one(player_post)
    return player_post


class Levels(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            # if message.author.id == 532902276021485589:
            #     await message.add_reaction("<:L_onion:1109189732337975387>")

            player_post = get_post(message.author.id)
            diff = int(time.time() - player_post.get("timeout", 0))
            if diff < 60:
                return
            xp = player_post.get("xp", 0)

            current_rank = "Novice"
            for r in ranks:
                if xp >= ranks[r]:
                    current_rank = r

            xp += 5

            next_rank = "Novice"
            for r in ranks:
                if xp >= ranks[r]:
                    next_rank = r

            if next_rank != current_rank:
                ncnl = await self.client.fetch_guild(899204296275550249)

                prev_role = discord.utils.get(ncnl.roles, name=current_rank)
                await message.author.remove_roles(prev_role)
                await message.channel.send(
                    f"Congrats {message.author.mention}! You've leveled up to {next_rank}!"
                )

                role = discord.utils.get(ncnl.roles, name=next_rank)
                await message.author.add_roles(role)

            filter = {"_id": player_post["_id"]}
            update = {"$set": {"timeout": int(time.time()), "xp": xp}}

            profiles.update_one(filter, update)

    @commands.command(name="rank", aliases=["r"])
    async def rank(self, ctx, member: typing.Optional[discord.Member] = None):
        member = member or ctx.author

        player_post = get_post(member.id)

        xp = player_post.get("xp") or 0

        rank = "Novice"
        for r in ranks:
            if xp >= ranks[r]:
                rank = r

        index = list(ranks.keys()).index(rank)

        if rank == "Hero":
            r_above = None
            xp_above = 750_000

        else:
            r_above = list(ranks.keys())[index + 1]
            xp_above = ranks[r_above]

        players = profiles.find()
        players = sorted(players, key=lambda x: x["xp"], reverse=True)
        rank_index = 1 + players.index(player_post)

        if rank != "Hero":
            percentage = int((xp - ranks[rank]) * 100 / (xp_above - ranks[rank]))

        else:
            percentage = 100

        xpcard = "images/xpcards/zIMAGE.png"

        background = Editor(xpcard).resize((900, 300))

        profile = await load_image_async(str(member.display_avatar).split("?")[0])
        profile = Editor(profile).resize((150, 150)).circle_image()
        poppins = Font(path="fonts/arial-unicode.ttf", size=40)
        poppins_small = Font(path="fonts/arial-unicode.ttf", size=30)

        # add black tint to make text more readable
        ima = Editor("images/xpcards/zBLACK.png")
        background.blend(image=ima, alpha=0.6, on_top=False)

        background.paste(profile.image, (30, 30))

        background.rectangle((30, 220), width=780, height=40, fill="#fff", radius=20)
        if percentage > 2:
            background.bar(
                (30, 220),
                max_width=780,
                height=40,
                percentage=percentage,
                color="#00ffe4",
                radius=20,
            )
        background.text((200, 40), str(member.name), font=poppins, color="#ffffff")
        background.text((790, 40), f"#{rank_index}", font=poppins, color="#ffffff")
        background.rectangle((200, 100), width=620, height=2, fill="#ffffff")
        background.text(
            (200, 130),
            f"Level : {rank}   " + f" XP : {xp} / {(xp_above)}",
            font=poppins_small,
            color="#ffffff",
        )

        card = File(fp=background.image_bytes, filename="images/xpcards/zCARD.png")
        await ctx.send(file=card)

    @commands.command(name="top", aliases=["t"])
    async def top(self, ctx, arg: int = 1):
        arg -= 1
        if arg < 1:
            arg = 0

        uploads_channel = self.client.get_channel(1014864807243038792)

        canvas = Canvas(size=(650, 650))
        editor = Editor(canvas)
        background = Editor("images/xpcards/top.png").resize((650, 650))

        player_post = get_post(ctx.author.id)
        players = profiles.find()
        players = sorted(players, key=lambda x: x["xp"], reverse=True)
        rank_index = 1 + players.index(player_post)

        font = Font(path="fonts/arial-unicode-bold.ttf", size=25)
        efont = Font(path="fonts/NotoEmoji.ttf", size=25)

        box_height = 50
        box_width = 650

        start = arg * 10
        end = len(players)

        if end - start > 10:
            end = start + 10
        iterations = end - start
        for i in range(iterations):
            user = await self.client.fetch_user(players[i + arg * 10]["_id"])
            editor.rectangle(
                (0, i * box_height + 14 * i),
                width=box_width,
                height=box_height,
                fill="#000",
                radius=20,
            )
            editor.text(
                (20, 20 + box_height * i + 14 * i),
                f"#{ i + 1 + arg* 10} • {user.name}",
                font=font,
                color="#ffffff",
            )

            editor.text(
                (450, 20 + box_height * i + 14 * i),
                f"💬",
                font=efont,
                color="#ffffff",
            )

            editor.text(
                (500, 20 + box_height * i + 14 * i),
                f"{players[i + arg* 10]['xp']}",
                font=font,
                color="#ffffff",
            )

        background.blend(image=editor, alpha=0.4, on_top=False)

        card = File(fp=background.image_bytes, filename="images/ranks.png")
        message = await uploads_channel.send(file=card)

        embed = discord.Embed(
            title="No Chess No Life All Time Rankings",
            color=discord.Color.from_rgb(201, 0, 118),
        )
        embed.description = f"""<:chat_bubble:1076148573718196294> **Your Rank**
You are rank `#{rank_index}` on this server\nwith a total of `{player_post.get('xp')}` <:chat_bubble:1076148573718196294>"""

        if arg * 10 > len(players):
            embed.set_image(
                url="https://media.discordapp.net/attachments/1073538985529446511/1076152373736640673/top.png"
            )
        else:
            url = message.attachments[0].url
            embed.set_image(url=url)
            embed.set_footer(
                text=f"Page {arg + 1} • Type .top  {arg + 2} to go to page {arg + 2} of the leaderboard"
            )
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Levels(client))
