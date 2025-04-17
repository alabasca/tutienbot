import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
from typing import Dict, List

from database.mongo_handler import get_user_or_create, update_user, add_user_linh_thach, add_user_exp
from config import (
    CULTIVATION_REALMS, DAILY_REWARD, EMBED_COLOR, EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR, EMOJI_LINH_THACH, EMOJI_EXP, EMOJI_LEVEL_UP
)

# Cấu hình logging
logger = logging.getLogger("tutien-bot.daily")


class DailyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="diemdanh", aliases=["daily", "nhandiemdanh", "dd"])
    async def daily_reward(self, ctx):
        """Nhận phần thưởng điểm danh hàng ngày"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra thời gian điểm danh gần nhất
        now = datetime.datetime.now()
        last_daily = user.get("last_daily")

        if last_daily:
            last_daily = datetime.datetime.fromisoformat(last_daily)

            # Kiểm tra xem đã qua ngày mới chưa
            if last_daily.date() == now.date():
                # Tính thời gian còn lại đến ngày tiếp theo
                tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
                time_left = tomorrow - now
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)

                embed = discord.Embed(
                    title="❌ Đã Điểm Danh",
                    description=(
                        f"Bạn đã điểm danh hôm nay rồi!\n"
                        f"Vui lòng quay lại sau: **{hours} giờ {minutes} phút {seconds} giây**"
                    ),
                    color=EMBED_COLOR_ERROR
                )

                return await ctx.send(embed=embed)

        # Tính phần thưởng điểm danh
        linh_thach_reward = DAILY_REWARD
        exp_reward = 20

        # Thêm phần thưởng
        await add_user_linh_thach(ctx.author.id, linh_thach_reward)

        # Cộng kinh nghiệm và kiểm tra đột phá
        cultivation_cog = self.bot.get_cog("CultivationCog")
        if cultivation_cog:
            success, new_realm = await cultivation_cog.add_exp(ctx.author.id, exp_reward, "điểm danh hàng ngày")
            breakthrough_text = f"\n{EMOJI_LEVEL_UP} Chúc mừng! Bạn đã đột phá lên **{new_realm}**!" if success else ""
        else:
            await add_user_exp(ctx.author.id, exp_reward)
            breakthrough_text = ""

        # Tính chuỗi điểm danh
        daily_streak = user.get("daily_streak", 0) + 1

        # Phần thưởng cho chuỗi điểm danh
        streak_bonus = 0
        if daily_streak % 7 == 0:  # Thưởng cho mỗi 7 ngày liên tiếp
            streak_bonus = 50
            await add_user_linh_thach(ctx.author.id, streak_bonus)

        # Cập nhật thông tin điểm danh
        await update_user(ctx.author.id, {
            "last_daily": now.isoformat(),
            "daily_streak": daily_streak
        })

        # Tạo embed thông báo
        embed = discord.Embed(
            title="✅ Điểm Danh Thành Công",
            description=f"Bạn đã điểm danh thành công ngày hôm nay!",
            color=EMBED_COLOR_SUCCESS
        )

        # Thêm thông tin phần thưởng
        embed.add_field(
            name="Phần Thưởng",
            value=(
                f"{EMOJI_LINH_THACH} **+{linh_thach_reward}** linh thạch\n"
                f"{EMOJI_EXP} **+{exp_reward}** kinh nghiệm{breakthrough_text}"
            ),
            inline=False
        )

        # Thêm thông tin chuỗi điểm danh
        embed.add_field(
            name="Chuỗi Điểm Danh",
            value=(
                    f"**{daily_streak}** ngày liên tiếp"
                    + (f"\n🎁 Bonus: **+{streak_bonus}** linh thạch" if streak_bonus > 0 else "")
            ),
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="chuoidiemdanh", aliases=["streak", "chuoi"])
    async def check_streak(self, ctx, member: discord.Member = None):
        """Kiểm tra chuỗi điểm danh của bản thân hoặc người khác"""
        # Nếu không chỉ định member, lấy người gọi lệnh
        if member is None:
            member = ctx.author

        # Lấy dữ liệu người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lấy thông tin chuỗi điểm danh
        daily_streak = user.get("daily_streak", 0)
        last_daily = user.get("last_daily")

        # Kiểm tra xem chuỗi có đang tiếp tục không
        streak_status = "Đang tiếp tục"

        if last_daily:
            last_daily = datetime.datetime.fromisoformat(last_daily)
            now = datetime.datetime.now()

            # Nếu đã qua ngày mà chưa điểm danh
            if (now - last_daily).days > 1:
                streak_status = "Đã đứt gãy"

        # Tạo embed thông báo
        embed = discord.Embed(
            title=f"Chuỗi Điểm Danh - {member.display_name}",
            description=f"**{daily_streak}** ngày liên tiếp ({streak_status})",
            color=EMBED_COLOR
        )

        # Thêm thông tin ngày điểm danh gần nhất
        if last_daily:
            embed.add_field(
                name="Điểm Danh Gần Nhất",
                value=last_daily.strftime("%d/%m/%Y %H:%M:%S"),
                inline=False
            )

        # Thêm thông tin phần thưởng chuỗi
        next_milestone = ((daily_streak // 7) + 1) * 7
        days_to_milestone = next_milestone - daily_streak

        embed.add_field(
            name="Phần Thưởng Chuỗi",
            value=f"Điểm danh thêm **{days_to_milestone}** ngày để nhận thưởng đặc biệt!",
            inline=False
        )

        # Thêm avatar
        embed.set_thumbnail(url=member.display_avatar.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="bangdiemdanh", aliases=["topdaily", "topdd"])
    async def daily_leaderboard(self, ctx):
        """Hiển thị bảng xếp hạng điểm danh"""
        # Lấy dữ liệu từ database
        from database.mongo_handler import users_collection
        cursor = users_collection.find().sort("daily_streak", -1).limit(10)
        users = await cursor.to_list(length=10)

        # Tạo embed
        embed = discord.Embed(
            title="Bảng Xếp Hạng Điểm Danh",
            description="Top 10 người chơi có chuỗi điểm danh cao nhất",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng người
        for i, user in enumerate(users, 1):
            # Lấy thông tin thành viên
            member = ctx.guild.get_member(user["user_id"])
            name = member.display_name if member else user["username"]

            # Lấy thông tin chuỗi điểm danh
            daily_streak = user.get("daily_streak", 0)

            # Thêm vào embed
            embed.add_field(
                name=f"{i}. {name}",
                value=f"Chuỗi: **{daily_streak}** ngày liên tiếp",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="thuongngay", aliases=["reward", "bonus"])
    async def show_daily_rewards(self, ctx):
        """Hiển thị thông tin phần thưởng điểm danh"""
        # Tạo embed
        embed = discord.Embed(
            title="Phần Thưởng Điểm Danh Hàng Ngày",
            description="Điểm danh mỗi ngày để nhận các phần thưởng hấp dẫn!",
            color=EMBED_COLOR
        )

        # Thêm thông tin phần thưởng điểm danh thường
        embed.add_field(
            name="Phần Thưởng Hàng Ngày",
            value=(
                f"{EMOJI_LINH_THACH} **+{DAILY_REWARD}** linh thạch\n"
                f"{EMOJI_EXP} **+20** kinh nghiệm"
            ),
            inline=False
        )

        # Thêm thông tin phần thưởng chuỗi
        embed.add_field(
            name="Phần Thưởng Chuỗi (Mỗi 7 ngày)",
            value=f"{EMOJI_LINH_THACH} **+50** linh thạch",
            inline=False
        )

        # Thêm lưu ý
        embed.add_field(
            name="Lưu Ý",
            value="Bạn cần điểm danh mỗi ngày để duy trì chuỗi. Nếu bỏ lỡ một ngày, chuỗi sẽ bị đặt lại!",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DailyCog(bot))


class DailyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="diemdanh", aliases=["daily", "nhandiemdanh", "dd"])
    async def daily_reward(self, ctx):
        """Nhận phần thưởng điểm danh hàng ngày"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra thời gian điểm danh gần nhất
        now = datetime.datetime.now()
        last_daily = user.get("last_daily")

        if last_daily:
            last_daily = datetime.datetime.fromisoformat(last_daily)

            # Kiểm tra xem đã qua ngày mới chưa
            if last_daily.date() == now.date():
                # Tính thời gian còn lại đến ngày tiếp theo
                tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
                time_left = tomorrow - now
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)

                embed = discord.Embed(
                    title="❌ Đã Điểm Danh",
                    description=(
                        f"Bạn đã điểm danh hôm nay rồi!\n"
                        f"Vui lòng quay lại sau: **{hours} giờ {minutes} phút {seconds} giây**"
                    ),
                    color=EMBED_COLOR_ERROR
                )

                return await ctx.send(embed=embed)

        # Tính phần thưởng điểm danh
        linh_thach_reward = DAILY_REWARD
        exp_reward = 20

        # Thêm phần thưởng
        await add_user_linh_thach(ctx.author.id, linh_thach_reward)

        # Cộng kinh nghiệm và kiểm tra đột phá
        cultivation_cog = self.bot.get_cog("CultivationCog")
        if cultivation_cog:
            success, new_realm = await cultivation_cog.add_exp(ctx.author.id, exp_reward, "điểm danh hàng ngày")
            breakthrough_text = f"\n{EMOJI_LEVEL_UP} Chúc mừng! Bạn đã đột phá lên **{new_realm}**!" if success else ""
        else:
            await add_user_exp(ctx.author.id, exp_reward)
            breakthrough_text = ""

        # Tính chuỗi điểm danh
        daily_streak = user.get("daily_streak", 0) + 1

        # Phần thưởng cho chuỗi điểm danh
        streak_bonus = 0
        if daily_streak % 7 == 0:  # Thưởng cho mỗi 7 ngày liên tiếp
            streak_bonus = 50
            await add_user_linh_thach(ctx.author.id, streak_bonus)

        # Cập nhật thông tin điểm danh
        await update_user(ctx.author.id, {
            "last_daily": now.isoformat(),
            "daily_streak": daily_streak
        })

        # Tạo embed thông báo
        embed = discord.Embed(
            title="✅ Điểm Danh Thành Công",
            description=f"Bạn đã điểm danh thành công ngày hôm nay!",
            color=EMBED_COLOR_SUCCESS
        )

        # Thêm thông tin phần thưởng
        embed.add_field(
            name="Phần Thưởng",
            value=(
                f"{EMOJI_LINH_THACH} **+{linh_thach_reward}** linh thạch\n"
                f"{EMOJI_EXP} **+{exp_reward}** kinh nghiệm{breakthrough_text}"
            ),
            inline=False
        )

        # Thêm thông tin chuỗi điểm danh
        embed.add_field(
            name="Chuỗi Điểm Danh",
            value=(
                    f"**{daily_streak}** ngày liên tiếp"
                    + (f"\n🎁 Bonus: **+{streak_bonus}** linh thạch" if streak_bonus > 0 else "")
            ),
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="chuoidiemdanh", aliases=["streak", "chuoi"])
    async def check_streak(self, ctx, member: discord.Member = None):
        """Kiểm tra chuỗi điểm danh của bản thân hoặc người khác"""
        # Nếu không chỉ định member, lấy người gọi lệnh
        if member is None:
            member = ctx.author

        # Lấy dữ liệu người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lấy thông tin chuỗi điểm danh
        daily_streak = user.get("daily_streak", 0)
        last_daily = user.get("last_daily")

        # Kiểm tra xem chuỗi có đang tiếp tục không
        streak_status = "Đang tiếp tục"

        if last_daily:
            last_daily = datetime.datetime.fromisoformat(last_daily)
            now = datetime.datetime.now()

            # Nếu đã qua ngày mà chưa điểm danh
            if (now - last_daily).days > 1:
                streak_status = "Đã đứt gãy"

        # Tạo embed thông báo
        embed = discord.Embed(
            title=f"Chuỗi Điểm Danh - {member.display_name}",
            description=f"**{daily_streak}** ngày liên tiếp ({streak_status})",
            color=EMBED_COLOR
        )

        # Thêm thông tin ngày điểm danh gần nhất
        if last_daily:
            embed.add_field(
                name="Điểm Danh Gần Nhất",
                value=last_daily.strftime("%d/%m/%Y %H:%M:%S"),
                inline=False
            )

        # Thêm thông tin phần thưởng chuỗi
        next_milestone = ((daily_streak // 7) + 1) * 7
        days_to_milestone = next_milestone - daily_streak

        embed.add_field(
            name="Phần Thưởng Chuỗi",
            value=f"Điểm danh thêm **{days_to_milestone}** ngày để nhận thưởng đặc biệt!",
            inline=False
        )

        # Thêm avatar
        embed.set_thumbnail(url=member.display_avatar.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="bangdiemdanh", aliases=["topdaily", "topdd"])
    async def daily_leaderboard(self, ctx):
        """Hiển thị bảng xếp hạng điểm danh"""
        # Lấy dữ liệu từ database
        from database.mongo_handler import users_collection
        cursor = users_collection.find().sort("daily_streak", -1).limit(10)
        users = await cursor.to_list(length=10)

        # Tạo embed
        embed = discord.Embed(
            title="Bảng Xếp Hạng Điểm Danh",
            description="Top 10 người chơi có chuỗi điểm danh cao nhất",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng người
        for i, user in enumerate(users, 1):
            # Lấy thông tin thành viên
            member = ctx.guild.get_member(user["user_id"])
            name = member.display_name if member else user["username"]

            # Lấy thông tin chuỗi điểm danh
            daily_streak = user.get("daily_streak", 0)

            # Thêm vào embed
            embed.add_field(
                name=f"{i}. {name}",
                value=f"Chuỗi: **{daily_streak}** ngày liên tiếp",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="thuongngay", aliases=["reward", "bonus"])
    async def show_daily_rewards(self, ctx):
        """Hiển thị thông tin phần thưởng điểm danh"""
        # Tạo embed
        embed = discord.Embed(
            title="Phần Thưởng Điểm Danh Hàng Ngày",
            description="Điểm danh mỗi ngày để nhận các phần thưởng hấp dẫn!",
            color=EMBED_COLOR
        )

        # Thêm thông tin phần thưởng điểm danh thường
        embed.add_field(
            name="Phần Thưởng Hàng Ngày",
            value=(
                f"{EMOJI_LINH_THACH} **+{DAILY_REWARD}** linh thạch\n"
                f"{EMOJI_EXP} **+20** kinh nghiệm"
            ),
            inline=False
        )

        # Thêm thông tin phần thưởng chuỗi
        embed.add_field(
            name="Phần Thưởng Chuỗi (Mỗi 7 ngày)",
            value=f"{EMOJI_LINH_THACH} **+50** linh thạch",
            inline=False
        )

        # Thêm lưu ý
        embed.add_field(
            name="Lưu Ý",
            value="Bạn cần điểm danh mỗi ngày để duy trì chuỗi. Nếu bỏ lỡ một ngày, chuỗi sẽ bị đặt lại!",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DailyCog(bot))