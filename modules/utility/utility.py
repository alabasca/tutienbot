import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
import sys
import os
import psutil
from typing import List, Dict, Any, Optional, Union

from database.mongo_handler import get_user_or_create, users_collection
from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR, EMOJI_LINH_THACH, EMOJI_EXP
)
from utils.text_utils import format_number, generate_random_quote, realm_description
from utils.time_utils import get_vietnamese_date_string, format_seconds
from utils.embed_utils import create_embed, create_success_embed, create_error_embed

# Cấu hình logging
logger = logging.getLogger("tutien-bot.utility")


class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="profile", aliases=["p", "me", "thongtin"])
    async def profile(self, ctx, member: discord.Member = None):
        """Hiển thị thông tin nhân vật của bạn hoặc người khác"""
        # Nếu không chỉ định member, lấy người gọi lệnh
        if member is None:
            member = ctx.author

        # Lấy thông tin người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lấy thông tin cảnh giới
        realm_id = user.get("realm_id", 0)
        realm_info = CULTIVATION_REALMS[realm_id] if realm_id < len(CULTIVATION_REALMS) else {"name": "Không xác định",
                                                                                              "exp_required": 0}
        realm_name = realm_info["name"]

        # Tạo embed
        embed = discord.Embed(
            title=f"Thông Tin Tu Luyện - {member.display_name}",
            description=f"Tu vi hiện tại: **{realm_name}**\n\n{realm_description(realm_id, realm_name)}",
            color=EMBED_COLOR
        )

        # Thêm thông tin kinh nghiệm
        current_exp = user.get("experience", 0)

        # Xác định cảnh giới tiếp theo
        next_realm = None
        exp_to_next = 0

        if realm_id < len(CULTIVATION_REALMS) - 1:
            next_realm = CULTIVATION_REALMS[realm_id + 1]
            exp_to_next = next_realm["exp_required"] - current_exp

        # Hiển thị thông tin kinh nghiệm và cảnh giới
        exp_text = f"{EMOJI_EXP} Kinh nghiệm: **{format_number(current_exp)}**"

        if next_realm:
            progress = (current_exp - realm_info["exp_required"]) / (
                        next_realm["exp_required"] - realm_info["exp_required"]) * 100
            exp_text += f"\n➡️ Cảnh giới tiếp theo: **{next_realm['name']}**"
            exp_text += f"\n⏳ Tiến độ: **{progress:.1f}%** ({format_number(exp_to_next)} exp còn thiếu)"
        else:
            exp_text += "\n🏆 Đã đạt đến cảnh giới tối cao!"

        embed.add_field(
            name="Linh Lực",
            value=exp_text,
            inline=False
        )

        # Thêm thông tin tài nguyên
        linh_thach = user.get("linh_thach", 0)
        embed.add_field(
            name="Tài Nguyên",
            value=f"{EMOJI_LINH_THACH} Linh thạch: **{format_number(linh_thach)}**",
            inline=True
        )

        # Thêm thông tin chiến đấu
        health = user.get("health", 100)
        attack = user.get("attack", 10)
        defense = user.get("defense", 5)

        embed.add_field(
            name="Thông Số Chiến Đấu",
            value=(
                f"❤️ HP: **{health}**\n"
                f"⚔️ Tấn công: **{attack}**\n"
                f"🛡️ Phòng thủ: **{defense}**"
            ),
            inline=True
        )

        # Thêm thông tin môn phái
        sect_id = user.get("sect_id")
        if sect_id:
            # Lấy thông tin môn phái
            from database.mongo_handler import get_sect
            sect = await get_sect(sect_id)

            if sect:
                embed.add_field(
                    name="Môn Phái",
                    value=f"🏯 **{sect['name']}**",
                    inline=True
                )

        # Thêm thông tin điểm danh
        daily_streak = user.get("daily_streak", 0)
        if daily_streak > 0:
            embed.add_field(
                name="Điểm Danh",
                value=f"🔄 Chuỗi điểm danh: **{daily_streak}** ngày",
                inline=True
            )

        # Thêm avatar
        embed.set_thumbnail(url=member.display_avatar.url)

        # Thêm footer
        embed.set_footer(text=f"ID: {member.id} • {get_vietnamese_date_string()}")

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="roll", aliases=["r", "dice", "xucxac"])
    async def roll_dice(self, ctx, dice_str: str = "1d6"):
        """Tung xúc xắc theo định dạng NdM (N viên xúc xắc M mặt)"""
        try:
            # Phân tích cú pháp
            if "d" not in dice_str:
                # Nếu chỉ là một số, ném một viên xúc xắc với số mặt đó
                num_dice = 1
                num_sides = int(dice_str)
            else:
                # Phân tích NdM
                num_dice, num_sides = map(int, dice_str.lower().split("d"))

            # Kiểm tra giới hạn
            if num_dice < 1 or num_dice > 100:
                return await ctx.send("Số lượng xúc xắc phải từ 1 đến 100!")

            if num_sides < 1 or num_sides > 1000:
                return await ctx.send("Số mặt xúc xắc phải từ 1 đến 1000!")

            # Tung xúc xắc
            results = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(results)

            # Tạo embed
            embed = discord.Embed(
                title=f"🎲 Kết Quả Tung Xúc Xắc: {dice_str}",
                color=EMBED_COLOR
            )

            # Thêm thông tin kết quả
            if num_dice > 1:
                embed.add_field(
                    name="Chi Tiết",
                    value=", ".join(str(r) for r in results),
                    inline=False
                )

            embed.add_field(
                name="Tổng",
                value=str(total),
                inline=False
            )

            # Thêm người tung
            embed.set_footer(text=f"Được tung bởi {ctx.author.display_name}")

            # Gửi embed
            await ctx.send(embed=embed)

        except ValueError:
            # Nếu cú pháp không hợp lệ
            embed = create_error_embed(
                title="❌ Lỗi Cú Pháp",
                description="Cú pháp hợp lệ: `!roll NdM` hoặc `!roll M`\nVí dụ: `!roll 2d6` để tung 2 viên xúc xắc 6 mặt, hoặc `!roll 20` để tung 1 viên xúc xắc 20 mặt."
            )
            await ctx.send(embed=embed)

    @commands.command(name="choose", aliases=["c", "chon", "pick"])
    async def choose(self, ctx, *, choices: str):
        """Chọn ngẫu nhiên một lựa chọn từ danh sách"""
        # Tách các lựa chọn
        options = [option.strip() for option in choices.split(",")]

        # Loại bỏ các tùy chọn trống
        options = [option for option in options if option]

        # Kiểm tra có đủ lựa chọn không
        if len(options) < 2:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vui lòng cung cấp ít nhất 2 lựa chọn, phân cách bởi dấu phẩy.",
            )
            return await ctx.send(embed=embed)

        # Chọn ngẫu nhiên
        chosen = random.choice(options)

        # Tạo embed
        embed = create_embed(
            title="🎯 Lựa Chọn Ngẫu Nhiên",
            description=f"Tôi chọn: **{chosen}**",
        )

        # Thêm danh sách các lựa chọn
        embed.add_field(
            name="Các Lựa Chọn",
            value="\n".join(f"• {option}" for option in options),
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="poll", aliases=["binhchon", "vote"])
    async def create_poll(self, ctx, question: str, *options):
        """Tạo một cuộc bình chọn"""
        # Kiểm tra số lượng lựa chọn
        if len(options) < 2:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vui lòng cung cấp ít nhất 2 lựa chọn cho cuộc bình chọn.\nVí dụ: `!poll \"Môn phái nào mạnh nhất?\" \"Thiên Kiếm Tông\" \"Đoạn Tình Cốc\" \"Huyết Ma Giáo\"`",
            )
            return await ctx.send(embed=embed)

        if len(options) > 10:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Cuộc bình chọn chỉ hỗ trợ tối đa 10 lựa chọn.",
            )
            return await ctx.send(embed=embed)

        # Các emoji số từ 1 đến 10
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        # Tạo embed
        embed = create_embed(
            title=f"📊 Bình Chọn: {question}",
            description="Bấm vào các emoji bên dưới để bình chọn!",
        )

        # Thêm các lựa chọn
        for i, option in enumerate(options):
            embed.add_field(
                name=f"Lựa chọn {i + 1}",
                value=f"{emoji_numbers[i]} {option}",
                inline=False
            )

        # Thêm người tạo
        embed.set_footer(text=f"Được tạo bởi {ctx.author.display_name}")

        # Gửi embed
        message = await ctx.send(embed=embed)

        # Thêm các emoji để bình chọn
        for i in range(len(options)):
            await message.add_reaction(emoji_numbers[i])

    @commands.command(name="weather", aliases=["thoitiet", "tt"])
    async def weather(self, ctx, *, location: str = "Phàm Trần"):
        """Hiển thị thời tiết tại một địa điểm trong thế giới tu tiên"""
        # Danh sách các địa điểm tưởng tượng
        locations = {
            "pham tran": {
                "name": "Phàm Trần",
                "description": "Nơi sinh sống của phàm nhân, thế giới phồn hoa đô hội.",
                "weather": ["nắng nhẹ", "mưa rào", "mây che phủ", "sương mù", "nắng gắt"]
            },
            "thien kiem phong": {
                "name": "Thiên Kiếm Phong",
                "description": "Đỉnh núi nơi tọa lạc của Thiên Kiếm Tông, cao vút trên mây.",
                "weather": ["mây lành", "sương mù nhẹ", "nắng cao nguyên", "gió nhẹ", "mưa tinh khiết"]
            },
            "doan tinh coc": {
                "name": "Đoạn Tình Cốc",
                "description": "Thung lũng u ám, nơi ẩn tu của các nữ tu không màng tình cảm.",
                "weather": ["sương độc", "gió lạnh", "mây hồng", "trăng sáng", "hoa rơi"]
            },
            "huyet ma cung": {
                "name": "Huyết Ma Cung",
                "description": "Cung điện đỏ tươi của Huyết Ma Giáo, nhuốm đầy máu tươi và sát khí.",
                "weather": ["mưa máu", "sương đỏ", "mây đen", "sấm chớp", "tối tăm"]
            },
            "tuyet nguyet phong": {
                "name": "Tuyết Nguyệt Phong",
                "description": "Đỉnh núi tuyết trắng, nơi ánh trăng luôn rọi sáng dù ngày hay đêm.",
                "weather": ["tuyết rơi", "trăng sáng", "băng giá", "gió lạnh", "sương trắng"]
            },
            "phieu dieu cac": {
                "name": "Phiêu Diêu Các",
                "description": "Nơi tụ họp của Hồng Trần Lữ Khách, tọa lạc trên đỉnh núi mây mù.",
                "weather": ["gió nhẹ", "mây trôi", "nắng ấm", "sương sớm", "trăng thanh"]
            }
        }

        # Chuẩn hóa địa điểm
        location_key = location.lower().replace(" ", "")

        # Tìm địa điểm phù hợp nhất
        matched_location = None
        for key, loc_data in locations.items():
            if key.replace(" ", "") in location_key or location_key in key.replace(" ", ""):
                matched_location = loc_data
                break

        # Nếu không tìm thấy, sử dụng Phàm Trần
        if not matched_location:
            matched_location = locations["pham tran"]

        # Chọn ngẫu nhiên thời tiết
        weather = random.choice(matched_location["weather"])

        # Chọn ngẫu nhiên nhiệt độ dựa trên thời tiết
        if "tuyết" in weather or "băng" in weather:
            temp = random.randint(-10, 5)
        elif "lạnh" in weather:
            temp = random.randint(5, 15)
        elif "nắng gắt" in weather:
            temp = random.randint(30, 40)
        elif "nắng" in weather:
            temp = random.randint(25, 30)
        else:
            temp = random.randint(15, 25)

        # Chọn ngẫu nhiên độ ẩm
        humidity = random.randint(30, 90)

        # Chọn ngẫu nhiên tốc độ gió
        wind_speed = random.randint(0, 30)

        # Tạo embed
        embed = create_embed(
            title=f"🌤️ Thời Tiết: {matched_location['name']}",
            description=matched_location["description"],
        )

        # Thêm thông tin thời tiết
        embed.add_field(
            name="Thời Tiết",
            value=weather.capitalize(),
            inline=True
        )

        embed.add_field(
            name="Nhiệt Độ",
            value=f"{temp}°C",
            inline=True
        )

        embed.add_field(
            name="Độ Ẩm",
            value=f"{humidity}%",
            inline=True
        )

        embed.add_field(
            name="Gió",
            value=f"{wind_speed} km/h",
            inline=True
        )

        # Thêm thông tin linh khí
        linh_khi_level = random.randint(1, 10)
        linh_khi_desc = {
            1: "Cực kỳ thấp, khó tu luyện",
            2: "Rất thấp, tiến độ tu luyện chậm",
            3: "Thấp, không thích hợp tu luyện",
            4: "Hơi thấp, tu luyện không hiệu quả",
            5: "Trung bình, tu luyện bình thường",
            6: "Khá tốt, thích hợp tu luyện",
            7: "Cao, rất thích hợp tu luyện",
            8: "Rất cao, tu luyện tiến triển nhanh",
            9: "Cực cao, tuyệt vời cho tu luyện",
            10: "Đỉnh cao, đột phá dễ dàng"
        }

        embed.add_field(
            name="Nồng Độ Linh Khí",
            value=f"Cấp độ {linh_khi_level}/10 - {linh_khi_desc[linh_khi_level]}",
            inline=False
        )

        # Thêm thời gian dự báo
        embed.set_footer(text=f"Dự báo vào: {get_vietnamese_date_string()}")

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="quote", aliases=["q", "daochan", "caungon"])
    async def random_quote(self, ctx):
        """Hiển thị một câu nói ngẫu nhiên về tu tiên"""
        # Lấy câu nói ngẫu nhiên
        quote = generate_random_quote()

        # Tạo embed
        embed = create_embed(
            title="📜 Đạo Châm Tu Tiên",
            description=f"*\"{quote}\"*",
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="timeleft", aliases=["cooldown", "cd", "thoigian"])
    async def check_cooldowns(self, ctx):
        """Kiểm tra thời gian hồi của các hoạt động"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Lấy thời gian hiện tại
        now = datetime.datetime.now()

        # Tạo embed
        embed = create_embed(
            title=f"⏳ Thời Gian Hồi - {ctx.author.display_name}",
            description="Thời gian còn lại cho các hoạt động:",
        )

        # Kiểm tra thời gian điểm danh
        last_daily = user.get("last_daily")
        if last_daily:
            last_daily = datetime.datetime.fromisoformat(last_daily)
            # Kiểm tra xem đã qua ngày mới chưa
            next_day = datetime.datetime.combine(last_daily.date() + datetime.timedelta(days=1), datetime.time.min)
            if now < next_day:
                time_diff = (next_day - now).total_seconds()
                embed.add_field(
                    name="Điểm Danh",
                    value=format_seconds(time_diff),
                    inline=True
                )
            else:
                embed.add_field(
                    name="Điểm Danh",
                    value="✅ Sẵn sàng",
                    inline=True
                )
        else:
            embed.add_field(
                name="Điểm Danh",
                value="✅ Sẵn sàng",
                inline=True
            )

        # Kiểm tra thời gian đánh quái
        last_danhquai = user.get("last_danhquai")
        if last_danhquai:
            last_danhquai = datetime.datetime.fromisoformat(last_danhquai)
            time_diff = (now - last_danhquai).total_seconds()
            cooldown = 600  # 10 phút

            if time_diff < cooldown:
                remaining = cooldown - time_diff
                embed.add_field(
                    name="Đánh Quái",
                    value=format_seconds(remaining),
                    inline=True
                )
            else:
                embed.add_field(
                    name="Đánh Quái",
                    value="✅ Sẵn sàng",
                    inline=True
                )
        else:
            embed.add_field(
                name="Đánh Quái",
                value="✅ Sẵn sàng",
                inline=True
            )

        # Kiểm tra thời gian đánh boss
        last_danhboss = user.get("last_danhboss")
        if last_danhboss:
            last_danhboss = datetime.datetime.fromisoformat(last_danhboss)
            time_diff = (now - last_danhboss).total_seconds()
            cooldown = 900  # 15 phút

            if time_diff < cooldown:
                remaining = cooldown - time_diff
                embed.add_field(
                    name="Đánh Boss",
                    value=format_seconds(remaining),
                    inline=True
                )
            else:
                embed.add_field(
                    name="Đánh Boss",
                    value="✅ Sẵn sàng",
                    inline=True
                )
        else:
            embed.add_field(
                name="Đánh Boss",
                value="✅ Sẵn sàng",
                inline=True
            )

        # Kiểm tra thời gian PvP
        last_combat = user.get("last_combat")
        if last_combat:
            last_combat = datetime.datetime.fromisoformat(last_combat)
            time_diff = (now - last_combat).total_seconds()
            cooldown = 1800  # 30 phút

            if time_diff < cooldown:
                remaining = cooldown - time_diff
                embed.add_field(
                    name="PvP",
                    value=format_seconds(remaining),
                    inline=True
                )
            else:
                embed.add_field(
                    name="PvP",
                    value="✅ Sẵn sàng",
                    inline=True
                )
        else:
            embed.add_field(
                name="PvP",
                value="✅ Sẵn sàng",
                inline=True
            )

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))