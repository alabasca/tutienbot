import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import random
import logging
from typing import Dict, List

from database.mongo_handler import get_user_or_create, update_user, add_user_exp
from config import (
    CULTIVATION_REALMS, EXP_PER_MESSAGE, EXP_PER_MINUTE_VOICE,
    VOICE_CHECK_INTERVAL, EMBED_COLOR, EMOJI_EXP, EMOJI_LEVEL_UP
)

# Cấu hình logging
logger = logging.getLogger("tutien-bot.cultivation")

# Theo dõi người dùng đang trong voice chat
voice_users = {}  # {user_id: {"channel_id": channel_id, "start_time": datetime, "last_check": datetime}}


class CultivationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_check.start()

    def cog_unload(self):
        self.voice_check.cancel()

    @tasks.loop(seconds=VOICE_CHECK_INTERVAL)
    async def voice_check(self):
        """Kiểm tra và cộng kinh nghiệm cho người dùng trong voice chat"""
        now = datetime.datetime.now()
        users_to_remove = []

        for user_id, data in voice_users.items():
            # Tính toán thời gian từ lần check cuối
            last_check = data["last_check"]
            time_diff = (now - last_check).total_seconds() / 60  # Đổi sang phút

            # Nếu đã trôi qua ít nhất 1 phút
            if time_diff >= 1:
                # Tính toán kinh nghiệm
                exp_gain = int(time_diff * EXP_PER_MINUTE_VOICE)

                # Cộng kinh nghiệm
                await self.add_exp(user_id, exp_gain, f"tu luyện Voice Chat ({int(time_diff)} phút)")

                # Cập nhật thời gian kiểm tra
                voice_users[user_id]["last_check"] = now

                # Kiểm tra xem người dùng còn trong voice chat không
                member = self.bot.get_user(user_id)
                if not member:
                    # Bot không thể tìm thấy thành viên, có thể đã offline
                    users_to_remove.append(user_id)

        # Xóa các người dùng đã rời voice
        for user_id in users_to_remove:
            del voice_users[user_id]

    @voice_check.before_loop
    async def before_voice_check(self):
        await self.bot.wait_until_ready()

    @commands.command(name="canhgioi", aliases=["cg", "realm"])
    async def check_realm(self, ctx, member: discord.Member = None):
        """Kiểm tra cảnh giới tu luyện của bản thân hoặc người khác"""
        # Nếu không chỉ định member, lấy người gọi lệnh
        if member is None:
            member = ctx.author

        # Lấy dữ liệu người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lấy thông tin cảnh giới
        realm_id = user["realm_id"]
        realm = next((r for r in CULTIVATION_REALMS if r["id"] == realm_id), CULTIVATION_REALMS[0])

        # Tính toán thông tin kinh nghiệm
        current_exp = user["experience"]

        # Xác định cảnh giới tiếp theo
        next_realm = None
        exp_to_next = 0
        if realm_id < len(CULTIVATION_REALMS) - 1:
            next_realm = next((r for r in CULTIVATION_REALMS if r["id"] == realm_id + 1), None)
            if next_realm:
                exp_to_next = next_realm["exp_required"] - current_exp

        # Tạo embed
        embed = discord.Embed(
            title=f"Cảnh Giới Tu Luyện - {member.display_name}",
            description=f"Tu vi hiện tại: **{realm['name']}**",
            color=EMBED_COLOR
        )

        # Thêm thông tin kinh nghiệm
        embed.add_field(
            name="Linh lực",
            value=f"{EMOJI_EXP} Kinh nghiệm hiện tại: **{current_exp:,}**",
            inline=False
        )

        # Thêm thông tin cảnh giới tiếp theo
        if next_realm:
            embed.add_field(
                name="Đột phá",
                value=(
                    f"Cảnh giới tiếp theo: **{next_realm['name']}**\n"
                    f"Cần thêm: **{exp_to_next:,}** kinh nghiệm"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="Đột phá",
                value="Đã đạt đến cảnh giới tối cao!",
                inline=False
            )

        # Thêm avatar
        embed.set_thumbnail(url=member.display_avatar.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="xephang", aliases=["xh", "rank", "ranking"])
    async def show_ranking(self, ctx):
        """Hiển thị bảng xếp hạng tu luyện"""
        # Lấy dữ liệu từ database
        from database.mongo_handler import users_collection
        cursor = users_collection.find().sort("experience", -1).limit(10)
        users = await cursor.to_list(length=10)

        # Tạo embed
        embed = discord.Embed(
            title="Bảng Xếp Hạng Tu Luyện",
            description="Top 10 cao thủ có tu vi cao nhất",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng người
        for i, user in enumerate(users, 1):
            # Lấy thông tin cảnh giới
            realm_id = user["realm_id"]
            realm = next((r for r in CULTIVATION_REALMS if r["id"] == realm_id), CULTIVATION_REALMS[0])

            # Lấy thông tin thành viên
            member = ctx.guild.get_member(user["user_id"])
            name = member.display_name if member else user["username"]

            # Thêm vào embed
            embed.add_field(
                name=f"{i}. {name}",
                value=f"Cảnh giới: **{realm['name']}**\nKinh nghiệm: **{user['experience']:,}**",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    async def add_exp(self, user_id, exp_amount, source=""):
        """Thêm kinh nghiệm cho người dùng và xử lý đột phá cảnh giới"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(user_id, str(user_id))

        # Cộng kinh nghiệm
        old_exp = user["experience"]
        old_realm_id = user["realm_id"]
        await add_user_exp(user_id, exp_amount)

        # Lấy thông tin người dùng sau khi cập nhật
        user = await get_user_or_create(user_id, str(user_id))
        new_exp = user["experience"]

        # Kiểm tra xem có đột phá cảnh giới không
        new_realm_id = old_realm_id
        for realm in CULTIVATION_REALMS:
            if realm["id"] > old_realm_id and new_exp >= realm["exp_required"]:
                new_realm_id = realm["id"]

        # Nếu có đột phá
        if new_realm_id > old_realm_id:
            # Cập nhật cảnh giới
            await update_user(user_id, {"realm_id": new_realm_id})

            # Lấy thông tin cảnh giới mới
            new_realm = next((r for r in CULTIVATION_REALMS if r["id"] == new_realm_id), None)

            # Lấy người dùng để thông báo
            member = self.bot.get_user(user_id)
            if member:
                # Tạo embed thông báo
                embed = discord.Embed(
                    title=f"{EMOJI_LEVEL_UP} Đột Phá Thành Công!",
                    description=f"Chúc mừng {member.mention} đã đột phá lên **{new_realm['name']}**!",
                    color=discord.Color.gold()
                )

                # Gửi thông báo đến kênh chung
                for guild in self.bot.guilds:
                    member_in_guild = guild.get_member(user_id)
                    if member_in_guild:
                        # Tìm kênh general
                        general_channel = discord.utils.get(guild.text_channels, name="general")
                        if general_channel:
                            await general_channel.send(embed=embed)
                            break

                # Gửi tin nhắn riêng
                try:
                    await member.send(embed=embed)
                except:
                    pass  # Bỏ qua nếu không gửi được DM

            logger.info(f"{member.name} đã đột phá lên {new_realm['name']}")

            return True, new_realm["name"]

        return False, None


# Hàm để thêm kinh nghiệm từ chat
async def add_chat_exp(bot, message):
    """Thêm kinh nghiệm khi chat"""
    # Lấy thông tin người dùng
    user_id = message.author.id

    # Thêm kinh nghiệm
    cog = bot.get_cog("CultivationCog")
    if cog:
        await cog.add_exp(user_id, EXP_PER_MESSAGE, "chat")


# Hàm để bắt đầu theo dõi voice chat
async def start_voice_tracking(bot, member, voice_channel):
    """Bắt đầu theo dõi người dùng trong voice chat"""
    # Thêm vào danh sách theo dõi
    now = datetime.datetime.now()
    voice_users[member.id] = {
        "channel_id": voice_channel.id,
        "start_time": now,
        "last_check": now
    }

    logger.info(f"{member.name} đã tham gia voice chat {voice_channel.name}")


# Hàm để kết thúc theo dõi voice chat
async def end_voice_tracking(bot, member, voice_channel):
    """Kết thúc theo dõi người dùng trong voice chat"""
    # Kiểm tra xem người dùng có trong danh sách không
    if member.id in voice_users:
        # Lấy thông tin
        data = voice_users[member.id]
        start_time = data["start_time"]
        now = datetime.datetime.now()

        # Tính toán thời gian
        time_diff = (now - start_time).total_seconds() / 60  # Đổi sang phút

        # Tính toán kinh nghiệm
        exp_gain = int(time_diff * EXP_PER_MINUTE_VOICE)

        # Cộng kinh nghiệm
        cog = bot.get_cog("CultivationCog")
        if cog:
            await cog.add_exp(member.id, exp_gain, f"tu luyện Voice Chat ({int(time_diff)} phút)")

        # Xóa khỏi danh sách theo dõi
        del voice_users[member.id]

        logger.info(f"{member.name} đã rời voice chat {voice_channel.name} sau {int(time_diff)} phút")


async def setup(bot):
    await bot.add_cog(CultivationCog(bot))