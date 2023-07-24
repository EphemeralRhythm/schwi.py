import discord
from discord import File
from discord.ext import commands
import typing
from models.ranks import ranks
from easy_pil import Editor, load_image_async, Font, Canvas
from utils.database import units_collection as profiles, xp_collection as xp_profiles


def get_post(id):
    player_post = xp_profiles.find_one({"_id": id})
    if not player_post:
        player_post = {"_id": id, "xp": -5, "timeout": 0}
        post = xp_profiles.insert_one(player_post)
    return player_post


class Profile(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="profile", aliases=["p"])
    async def profile(self, ctx, member: typing.Optional[discord.Member] = None):
        member = member or ctx.author

        player_post = get_post(member.id)

        xp = player_post.get("xp") or 0

        rank = "Novice"
        for r in ranks:
            if xp >= ranks[r]:
                rank = r

        guild = member.guild
        race = player_post.get("race")

        description = ""
        profile_post = profiles.find_one({"_id": member.id})
        if not player_post:
            await ctx.send(f"Profile not found.")
            return

        if profile_post:
            race = profile_post.get("race")
            description += f"Race: {race}\n"

        description += f"Level: {player_post.get('xp')}\n"

        pcard = f"images/profile.jpg"

        background = Editor(pcard).resize((900, 300))

        profile = await load_image_async(str(member.display_avatar).split("?")[0])
        profile = Editor(profile).resize((150, 150)).circle_image()
        poppins = Font(path="fonts/arial-unicode-bold.ttf", size=40)
        poppins_small = Font(path="fonts/arial-unicode.ttf", size=26)
        emoji_font = Font(path="fonts/NotoEmoji.ttf", size=28)

        ima = Editor("images/xpcards/zBLACK.png")
        background.blend(image=ima, alpha=0.6, on_top=False)

        background.paste(profile.image, (30, 30))

        background.text((200, 40), str(member.name), font=poppins, color="#ffffff")
        background.rectangle((200, 90), width=680, height=2, fill="#ffffff")

        # line break
        # background.text(
        #     (260, 130),
        #     f"Level :",
        #     font=poppins_small,
        #     color="#ffffff",
        # )
        # background.text(
        #     (440, 130),
        #     f"{rank}",
        #     font=poppins_small,
        #     color="#ffffff",
        #     align= 'right'
        # )
        # background.text(
        #     (260, 160),
        #     f"Quests:",
        #     font=poppins_small,
        #     color="#ffffff",
        # )
        # background.text(
        #     (440, 160),
        #     f"0",
        #     font=poppins_small,
        #     color="#ffffff",
        #     align='right'
        # )
        # background.text(
        #     (260, 190),
        #     f"Kills:",
        #     font=poppins_small,
        #     color="#ffffff",
        # )
        # background.text(
        #     (440, 190),
        #     f"0",
        #     font=poppins_small,
        #     color="#ffffff",
        #     align='right'
        # )

        check = False
        roles = [
            "Einzig",
            "Elven High Council Plenipotentiary",
            "Dwarven Master Craftsman",
        ]
        for name in roles:
            role = discord.utils.get(guild.roles, name=name)
            if role in member.roles:
                check = True
                break

        if race:
            background.text(
                (30 + 150 / 2, 210),
                f"{race}",
                font=poppins_small,
                color="#ffffff",
                align="center",
            )

        if check:
            background.text(
                (830, 40), f"👑", font=emoji_font, color="#ffffff", align="center"
            )

        card = File(fp=background.image_bytes, filename="images/xpcards/profile.png")
        await ctx.send(file=card)


async def setup(client):
    await client.add_cog(Profile(client))
