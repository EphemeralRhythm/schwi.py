import random
import typing
import discord
from discord import File
from discord.ext import commands
from easy_pil import Editor, load_image_async, Font
from io import BytesIO


class Events(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"{member} just joined the server!")

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

    @commands.command(name="testgreet")
    async def rank(self, ctx, member: typing.Optional[discord.Member] = None):
        member = member or ctx.author

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
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f"{member} has left the server.")
        if member.guild.id == 899204296275550249:
            channel = self.client.get_channel(899204296829194282)
            await channel.send(f"{member} has left the server")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        messageID = 1056568346520334377
        print(f"reaction added")

        if payload.message_id == messageID:
            member = payload.member
            guild = member.guild
            emoji = payload.emoji.name
            print(emoji)
            if emoji == "🎖️":
                role = discord.utils.get(guild.roles, name="Chess")
            elif emoji == "🎯":
                role = discord.utils.get(guild.roles, name="Server Announcements")
            elif emoji == "❔":
                role = discord.utils.get(guild.roles, name="QOTD")
            elif emoji == "schwi":
                role = discord.utils.get(guild.roles, name="Exceed")
            await member.add_roles(role)

            if emoji == "schwi":
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

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        messageID = 1056568346520334377
        if messageID == payload.message_id:
            guild = await self.client.fetch_guild(payload.guild_id)
            emoji = payload.emoji.name

            if emoji == "🎖️":
                role = discord.utils.get(guild.roles, name="Chess")
            elif emoji == "🎯":
                role = discord.utils.get(guild.roles, name="Server Announcements")
            elif emoji == "❔":
                role = discord.utils.get(guild.roles, name="QOTD")
            elif emoji == "schwi":
                role = discord.utils.get(guild.roles, name="Exceed")
            member = await guild.fetch_member(payload.user_id)

            if member is not None:
                await member.remove_roles(role)
            else:
                print("Member not found: reaction remove error")


async def setup(client):
    await client.add_cog(Events(client))
