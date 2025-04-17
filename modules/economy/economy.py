# modules/economy/economy.py
import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
from typing import Dict, List, Optional, Union, Any

from database.mongo_handler import MongoHandler
from database.models.user_model import User
from utils.embed_utils import create_embed, create_success_embed, create_error_embed
from utils.text_utils import format_number, progress_bar

# Cấu hình logging
logger = logging.getLogger("tutien-bot.economy")


class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_handler = MongoHandler()
        self.daily_rewards = {
            1: {"spirit_stones": 100, "exp": 50},
            2: {"spirit_stones": 120, "exp": 60},
            3: {"spirit_stones": 140, "exp": 70},
            4: {"spirit_stones": 160, "exp": 80},
            5: {"spirit_stones": 180, "exp": 90},
            6: {"spirit_stones": 200, "exp": 100},
            7: {"spirit_stones": 300, "exp": 150, "special": "weekly_chest"},
            14: {"spirit_stones": 500, "exp": 250, "special": "biweekly_chest"},
            30: {"spirit_stones": 1000, "exp": 500, "special": "monthly_chest"},
            60: {"spirit_stones": 2000, "exp": 1000, "special": "bimonthly_chest"},
            100: {"spirit_stones": 5000, "exp": 2500, "special": "cultivation_manual"},
            365: {"spirit_stones": 20000, "exp": 10000, "special": "legendary_pet_egg"}
        }

    async def get_user_data(self, user_id: int) -> Optional[User]:
        """Lấy dữ liệu người dùng từ database"""
        user_data = await self.mongo_handler.find_one_async("users", {"user_id": user_id})
        if user_data:
            return User.from_dict(user_data)
        return None

    async def save_user_data(self, user: User) -> bool:
        """Lưu dữ liệu người dùng vào database"""
        result = await self.mongo_handler.update_one_async(
            "users",
            {"user_id": user.user_id},
            {"$set": user.to_dict()},
            upsert=True
        )
        return result.acknowledged

    @commands.command(name="balance", aliases=["bal", "money", "linhthach"])
    async def balance(self, ctx, member: discord.Member = None):
        """Xem số linh thạch của bạn hoặc người khác"""
        # Nếu không chỉ định thành viên, mặc định là người gọi lệnh
        target = member or ctx.author

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(target.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"{'Bạn' if target == ctx.author else target.display_name} chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Tạo embed hiển thị số linh thạch
        embed = create_embed(
            title=f"💰 Linh Thạch của {target.display_name}",
            description="Tài nguyên tu luyện hiện có"
        )

        # Thêm thông tin linh thạch
        embed.add_field(
            name="Linh thạch",
            value=f"{format_number(user.resources['spirit_stones'])} 💎",
            inline=False
        )

        # Thêm thông tin linh thạch khác nếu có
        if user.resources.get("low_stones", 0) > 0:
            embed.add_field(
                name="Linh thạch hạ phẩm",
                value=f"{format_number(user.resources['low_stones'])} 🟢",
                inline=True
            )

        if user.resources.get("mid_stones", 0) > 0:
            embed.add_field(
                name="Linh thạch trung phẩm",
                value=f"{format_number(user.resources['mid_stones'])} 🔵",
                inline=True
            )

        if user.resources.get("high_stones", 0) > 0:
            embed.add_field(
                name="Linh thạch thượng phẩm",
                value=f"{format_number(user.resources['high_stones'])} 🟣",
                inline=True
            )

        # Thêm thông tin linh thạch khóa nếu có
        if user.resources.get("bound_spirit_stones", 0) > 0:
            embed.add_field(
                name="Linh thạch khóa",
                value=f"{format_number(user.resources['bound_spirit_stones'])} 🔒",
                inline=True
            )

        # Thêm thông tin tài nguyên khác
        if user.resources.get("spiritual_energy", 0) > 0:
            embed.add_field(
                name="Linh khí",
                value=f"{format_number(user.resources['spiritual_energy'])} ✨",
                inline=True
            )

        if user.resources.get("contribution", 0) > 0:
            embed.add_field(
                name="Điểm cống hiến",
                value=f"{format_number(user.resources['contribution'])} 🏆",
                inline=True
            )

        if user.resources.get("reputation", 0) > 0:
            embed.add_field(
                name="Danh vọng",
                value=f"{format_number(user.resources['reputation'])} 🌟",
                inline=True
            )

        # Thêm avatar người dùng
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="daily", aliases=["diemdanh"])
    async def daily(self, ctx):
        """Nhận phần thưởng điểm danh hàng ngày"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem đã điểm danh hôm nay chưa
        now = datetime.datetime.utcnow()
        last_daily = user.activities.get("last_daily")

        if last_daily and (now - last_daily).total_seconds() < 86400:  # 24 giờ = 86400 giây
            # Tính thời gian còn lại
            next_daily = last_daily + datetime.timedelta(days=1)
            time_left = next_daily - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            embed = create_error_embed(
                title="⏰ Chưa đến thời gian",
                description=f"Bạn đã điểm danh hôm nay rồi. Vui lòng quay lại sau {hours} giờ {minutes} phút {seconds} giây."
            )
            return await ctx.send(embed=embed)

        # Cập nhật thời gian điểm danh
        if last_daily and (now - last_daily).days == 1:
            # Điểm danh liên tiếp
            user.activities["daily_streak"] += 1
        else:
            # Bắt đầu chuỗi điểm danh mới
            user.activities["daily_streak"] = 1

        user.activities["last_daily"] = now

        # Xác định phần thưởng
        streak = user.activities["daily_streak"]
        reward = None

        # Tìm phần thưởng phù hợp với chuỗi điểm danh
        for milestone in sorted(self.daily_rewards.keys(), reverse=True):
            if streak >= milestone:
                reward = self.daily_rewards[milestone]
                break

        if not reward:
            reward = self.daily_rewards[1]  # Phần thưởng mặc định

        # Cộng phần thưởng
        spirit_stones = reward.get("spirit_stones", 100)
        exp = reward.get("exp", 50)

        user.add_spirit_stones(spirit_stones)
        exp_result = user.gain_exp(exp)

        # Thêm vật phẩm đặc biệt nếu có
        special_item = reward.get("special")
        if special_item:
            user.add_item(special_item, 1)

        # Lưu dữ liệu người dùng
        await self.save_user_data(user)

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Điểm Danh Thành Công",
            description=f"Bạn đã điểm danh thành công! Chuỗi điểm danh hiện tại: **{streak}** ngày."
        )

        # Thêm thông tin phần thưởng
        embed.add_field(
            name="Phần thưởng",
            value=f"💰 {format_number(spirit_stones)} linh thạch\n✨ {format_number(exp_result['exp_gained'])} kinh nghiệm",
            inline=False
        )

        # Thêm thông tin vật phẩm đặc biệt nếu có
        if special_item:
            special_item_names = {
                "weekly_chest": "Rương Tuần",
                "biweekly_chest": "Rương Nửa Tháng",
                "monthly_chest": "Rương Tháng",
                "bimonthly_chest": "Rương Hai Tháng",
                "cultivation_manual": "Bí Kíp Tu Luyện",
                "legendary_pet_egg": "Trứng Linh Thú Huyền Thoại"
            }

            embed.add_field(
                name="Phần thưởng đặc biệt",
                value=f"🎁 {special_item_names.get(special_item, special_item)}",
                inline=False
            )

        # Thêm thông tin về đột phá nếu có
        if exp_result.get("breakthrough", False):
            if exp_result.get("realm_advancement", False):
                embed.add_field(
                    name="🌟 Đột phá cảnh giới",
                    value=f"Chúc mừng! Bạn đã đột phá lên {exp_result['new_realm']} cảnh {exp_result['new_level']}!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🌟 Đột phá tiểu cảnh",
                    value=f"Chúc mừng! Bạn đã đột phá lên {user.cultivation['realm']} cảnh {user.cultivation['realm_level']}!",
                    inline=False
                )

        # Thêm thông tin về chuỗi điểm danh tiếp theo
        next_milestone = None
        for milestone in sorted(self.daily_rewards.keys()):
            if milestone > streak:
                next_milestone = milestone
                break

        if next_milestone:
            days_left = next_milestone - streak
            embed.add_field(
                name="Chuỗi điểm danh tiếp theo",
                value=f"Còn {days_left} ngày nữa để đạt chuỗi {next_milestone} ngày và nhận phần thưởng lớn hơn!",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="convert", aliases=["doilinhthach", "exchange"])
    async def convert_spirit_stones(self, ctx, amount: int, from_type: str, to_type: str):
        """Chuyển đổi giữa các loại linh thạch"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra số lượng
        if amount <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Số lượng phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Ánh xạ tên loại linh thạch
        type_mapping = {
            "normal": "spirit_stones",
            "thuong": "spirit_stones",
            "thường": "spirit_stones",
            "spirit_stones": "spirit_stones",
            "linh_thach": "spirit_stones",
            "linhthach": "spirit_stones",

            "low": "low_stones",
            "ha": "low_stones",
            "hạ": "low_stones",
            "low_stones": "low_stones",
            "ha_pham": "low_stones",
            "hapham": "low_stones",

            "mid": "mid_stones",
            "trung": "mid_stones",
            "mid_stones": "mid_stones",
            "trung_pham": "mid_stones",
            "trungpham": "mid_stones",

            "high": "high_stones",
            "thuong_pham": "high_stones",
            "thuongpham": "high_stones",
            "thượng": "high_stones",
            "high_stones": "high_stones",

            "bound": "bound_spirit_stones",
            "khoa": "bound_spirit_stones",
            "khóa": "bound_spirit_stones",
            "bound_spirit_stones": "bound_spirit_stones"
        }

        # Chuyển đổi tên loại
        from_type_key = type_mapping.get(from_type.lower())
        to_type_key = type_mapping.get(to_type.lower())

        if not from_type_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Loại linh thạch nguồn không hợp lệ. Các loại hợp lệ: normal/thường, low/hạ, mid/trung, high/thượng, bound/khóa."
            )
            return await ctx.send(embed=embed)

        if not to_type_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Loại linh thạch đích không hợp lệ. Các loại hợp lệ: normal/thường, low/hạ, mid/trung, high/thượng, bound/khóa."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có đủ linh thạch không
        if user.resources.get(from_type_key, 0) < amount:
            embed = create_error_embed(
                title="❌ Không đủ linh thạch",
                description=f"Bạn không có đủ linh thạch loại {from_type}."
            )
            return await ctx.send(embed=embed)

        # Thực hiện chuyển đổi
        result = user.convert_spirit_stones(from_type_key, to_type_key, amount)

        if not result:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Không thể chuyển đổi giữa hai loại linh thạch này."
            )
            return await ctx.send(embed=embed)

        # Lưu dữ liệu người dùng
        await self.save_user_data(user)

        # Tạo embed thông báo
        # Tên hiển thị cho các loại linh thạch
        type_display = {
            "spirit_stones": "Linh thạch thường",
            "low_stones": "Linh thạch hạ phẩm",
            "mid_stones": "Linh thạch trung phẩm",
            "high_stones": "Linh thạch thượng phẩm",
            "bound_spirit_stones": "Linh thạch khóa"
        }

        # Biểu tượng cho các loại linh thạch
        type_emoji = {
            "spirit_stones": "💎",
            "low_stones": "🟢",
            "mid_stones": "🔵",
            "high_stones": "🟣",
            "bound_spirit_stones": "🔒"
        }

        # Tỷ lệ chuyển đổi
        conversion_rates = {
            "low_stones": {"spirit_stones": 10},
            "spirit_stones": {"low_stones": 0.1, "mid_stones": 100},
            "mid_stones": {"spirit_stones": 0.01, "high_stones": 100},
            "high_stones": {"mid_stones": 0.01}
        }

        # Tính số lượng nhận được
        rate = conversion_rates[from_type_key][to_type_key]
        converted_amount = int(amount * rate)

        embed = create_success_embed(
            title="✅ Chuyển Đổi Thành Công",
            description=f"Đã chuyển đổi {format_number(amount)} {type_display[from_type_key]} thành {format_number(converted_amount)} {type_display[to_type_key]}."
        )

        # Thêm thông tin số dư hiện tại
        embed.add_field(
            name="Số dư hiện tại",
            value=f"{type_emoji[from_type_key]} {type_display[from_type_key]}: {format_number(user.resources[from_type_key])}\n"
                  f"{type_emoji[to_type_key]} {type_display[to_type_key]}: {format_number(user.resources[to_type_key])}",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="give", aliases=["transfer", "chuyen"])
    async def give_spirit_stones(self, ctx, member: discord.Member, amount: int):
        """Chuyển linh thạch cho người khác"""
        # Kiểm tra xem có phải tự chuyển cho mình không
        if member.id == ctx.author.id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn không thể chuyển linh thạch cho chính mình."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra số lượng
        if amount <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Số lượng phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người gửi
        sender = await self.get_user_data(ctx.author.id)
        if not sender:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người nhận
        receiver = await self.get_user_data(member.id)
        if not receiver:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"{member.display_name} chưa bắt đầu tu tiên."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có đủ linh thạch không
        if sender.resources["spirit_stones"] < amount:
            embed = create_error_embed(
                title="❌ Không đủ linh thạch",
                description=f"Bạn không có đủ linh thạch. Hiện tại bạn có {format_number(sender.resources['spirit_stones'])} linh thạch."
            )
            return await ctx.send(embed=embed)

        # Tính phí giao dịch (5%)
        fee = int(amount * 0.05)
        transfer_amount = amount - fee

        # Tạo embed xác nhận
        embed = create_embed(
            title="💰 Xác Nhận Chuyển Linh Thạch",
            description=f"Bạn sắp chuyển {format_number(amount)} linh thạch cho {member.mention}.\n"
                        f"Phí giao dịch (5%): {format_number(fee)} linh thạch\n"
                        f"Số linh thạch {member.display_name} sẽ nhận được: {format_number(transfer_amount)} linh thạch"
        )

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Xác nhận", style=discord.ButtonStyle.primary)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Kiểm tra lại xem có đủ linh thạch không
            if sender.resources["spirit_stones"] < amount:
                await interaction.response.send_message(
                    "Không đủ linh thạch để thực hiện giao dịch!",
                    ephemeral=True
                )
                return

            # Trừ linh thạch của người gửi
            sender.resources["spirit_stones"] -= amount

            # Cộng linh thạch cho người nhận
            receiver.resources["spirit_stones"] += transfer_amount

            # Lưu dữ liệu người dùng
            await self.save_user_data(sender)
            await self.save_user_data(receiver)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Chuyển Linh Thạch Thành Công",
                description=f"Đã chuyển {format_number(transfer_amount)} linh thạch cho {member.mention}.\n"
                            f"Phí giao dịch: {format_number(fee)} linh thạch"
            )

            # Thêm thông tin số dư hiện tại
            embed.add_field(
                name="Số dư của bạn",
                value=f"💰 {format_number(sender.resources['spirit_stones'])} linh thạch",
                inline=True
            )

            embed.add_field(
                name=f"Số dư của {member.display_name}",
                value=f"💰 {format_number(receiver.resources['spirit_stones'])} linh thạch",
                inline=True
            )

            await interaction.response.send_message(embed=embed)

            # Gửi thông báo cho người nhận
            try:
                receiver_embed = create_success_embed(
                    title="💰 Nhận Được Linh Thạch",
                    description=f"Bạn đã nhận được {format_number(transfer_amount)} linh thạch từ {ctx.author.display_name}."
                )

                receiver_embed.add_field(
                    name="Số dư hiện tại",
                    value=f"💰 {format_number(receiver.resources['spirit_stones'])} linh thạch",
                    inline=False
                )

                await member.send(embed=receiver_embed)
            except:
                pass  # Bỏ qua nếu không gửi được DM

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy giao dịch.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    @commands.command(name="leaderboard", aliases=["lb", "top", "bangxephang"])
    async def leaderboard(self, ctx, category: str = "cultivation"):
        """Xem bảng xếp hạng"""
        valid_categories = ["cultivation", "spirit_stones", "contribution", "reputation", "pvp"]
        category_aliases = {
            "tu_luyen": "cultivation",
            "tuluyen": "cultivation",
            "tu": "cultivation",
            "level": "cultivation",
            "cap": "cultivation",
            "cấp": "cultivation",

            "linh_thach": "spirit_stones",
            "linhthach": "spirit_stones",
            "money": "spirit_stones",
            "tien": "spirit_stones",
            "tiền": "spirit_stones",

            "cong_hien": "contribution",
            "conghien": "contribution",
            "cống_hiến": "contribution",
            "cốnghiến": "contribution",

            "danh_vong": "reputation",
            "danhvong": "reputation",

            "pvp": "pvp",
            "pk": "pvp",
            "chien_dau": "pvp",
            "chiendau": "pvp"
        }

        # Chuyển đổi category
        category = category_aliases.get(category.lower(), category.lower())

        if category not in valid_categories:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Danh mục không hợp lệ. Các danh mục hợp lệ: {', '.join(valid_categories)}"
            )
            return await ctx.send(embed=embed)

        # Tên hiển thị cho các danh mục
        category_display = {
            "cultivation": "Tu Luyện",
            "spirit_stones": "Linh Thạch",
            "contribution": "Cống Hiến",
            "reputation": "Danh Vọng",
            "pvp": "PvP"
        }

        # Biểu tượng cho các danh mục
        category_emoji = {
            "cultivation": "✨",
            "spirit_stones": "💰",
            "contribution": "🏆",
            "reputation": "🌟",
            "pvp": "⚔️"
        }

        # Truy vấn dữ liệu từ database
        if category == "cultivation":
            # Sắp xếp theo cảnh giới và tiểu cảnh giới
            pipeline = [
                {
                    "$addFields": {
                        "realm_index": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$cultivation.realm", "Luyện Khí"]}, "then": 1},
                                    {"case": {"$eq": ["$cultivation.realm", "Trúc Cơ"]}, "then": 2},
                                    {"case": {"$eq": ["$cultivation.realm", "Kim Đan"]}, "then": 3},
                                    {"case": {"$eq": ["$cultivation.realm", "Nguyên Anh"]}, "then": 4},
                                    {"case": {"$eq": ["$cultivation.realm", "Hóa Thần"]}, "then": 5},
                                    {"case": {"$eq": ["$cultivation.realm", "Luyện Hư"]}, "then": 6},
                                    {"case": {"$eq": ["$cultivation.realm", "Hợp Thể"]}, "then": 7},
                                    {"case": {"$eq": ["$cultivation.realm", "Đại Thừa"]}, "then": 8},
                                    {"case": {"$eq": ["$cultivation.realm", "Độ Kiếp"]}, "then": 9},
                                    {"case": {"$eq": ["$cultivation.realm", "Tiên Nhân"]}, "then": 10}
                                ],
                                "default": 0
                            }
                        }
                    }
                },
                {"$sort": {"realm_index": -1, "cultivation.realm_level": -1}},
                {"$limit": 10},
                {"$project": {"user_id": 1, "username": 1, "cultivation.realm": 1, "cultivation.realm_level": 1}}
            ]

            users = await self.mongo_handler.aggregate_async("users", pipeline)

        elif category == "spirit_stones":
            # Sắp xếp theo số linh thạch
            users = await self.mongo_handler.find_async(
                "users",
                {},
                {"user_id": 1, "username": 1, "resources.spirit_stones": 1},
                sort=[("resources.spirit_stones", -1)],
                limit=10
            )

        elif category == "contribution":
            # Sắp xếp theo điểm cống hiến
            users = await self.mongo_handler.find_async(
                "users",
                {},
                {"user_id": 1, "username": 1, "resources.contribution": 1},
                sort=[("resources.contribution", -1)],
                limit=10
            )

        elif category == "reputation":
            # Sắp xếp theo danh vọng
            users = await self.mongo_handler.find_async(
                "users",
                {},
                {"user_id": 1, "username": 1, "resources.reputation": 1},
                sort=[("resources.reputation", -1)],
                limit=10
            )

        elif category == "pvp":
            # Sắp xếp theo điểm PvP
            users = await self.mongo_handler.find_async(
                "users",
                {},
                {"user_id": 1, "username": 1, "social.pvp.points": 1, "social.pvp.wins": 1, "social.pvp.losses": 1},
                sort=[("social.pvp.points", -1)],
                limit=10
            )

        # Chuyển đổi kết quả thành list
        users_list = await users.to_list(length=10)

        # Tạo embed bảng xếp hạng
        embed = create_embed(
            title=f"{category_emoji[category]} Bảng Xếp Hạng {category_display[category]}",
            description=f"Top 10 người chơi theo {category_display[category].lower()}"
        )

        # Thêm thông tin từng người chơi
        if not users_list:
            embed.add_field(name="Không có dữ liệu", value="Chưa có người chơi nào trong bảng xếp hạng này.",
                            inline=False)
        else:
            for i, user_data in enumerate(users_list, 1):
                # Lấy tên người chơi
                username = user_data.get("username", "Không xác định")

                # Tạo chuỗi hiển thị thông tin
                if category == "cultivation":
                    realm = user_data.get("cultivation", {}).get("realm", "Không xác định")
                    realm_level = user_data.get("cultivation", {}).get("realm_level", 0)
                    value = f"{realm} cảnh {realm_level}"

                elif category == "spirit_stones":
                    spirit_stones = user_data.get("resources", {}).get("spirit_stones", 0)
                    value = f"{format_number(spirit_stones)} linh thạch"

                elif category == "contribution":
                    contribution = user_data.get("resources", {}).get("contribution", 0)
                    value = f"{format_number(contribution)} điểm cống hiến"

                elif category == "reputation":
                    reputation = user_data.get("resources", {}).get("reputation", 0)
                    value = f"{format_number(reputation)} danh vọng"

                elif category == "pvp":
                    points = user_data.get("social", {}).get("pvp", {}).get("points", 0)
                    wins = user_data.get("social", {}).get("pvp", {}).get("wins", 0)
                    losses = user_data.get("social", {}).get("pvp", {}).get("losses", 0)
                    value = f"{format_number(points)} điểm | {wins}W/{losses}L"

                # Thêm biểu tượng xếp hạng
                if i == 1:
                    rank_icon = "🥇"
                elif i == 2:
                    rank_icon = "🥈"
                elif i == 3:
                    rank_icon = "🥉"
                else:
                    rank_icon = f"#{i}"

                # Đánh dấu người gọi lệnh
                if user_data.get("user_id") == ctx.author.id:
                    username = f"**{username}** (Bạn)"

                embed.add_field(
                    name=f"{rank_icon} {username}",
                    value=value,
                    inline=False
                )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="mine", aliases=["daolinhthach", "dao"])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 lần mỗi giờ
    async def mine_spirit_stones(self, ctx):
        """Đào linh thạch để kiếm tài nguyên"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            ctx.command.reset_cooldown(ctx)
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Tạo embed thông báo đang đào
        embed = create_embed(
            title="⛏️ Đang Đào Linh Thạch",
            description="Bạn đang tìm kiếm mạch linh thạch...\nVui lòng đợi trong giây lát."
        )

        message = await ctx.send(embed=embed)

        # Giả lập thời gian đào
        await asyncio.sleep(3)

        # Tính toán kết quả đào
        # Cơ bản: 50-200 linh thạch
        base_stones = random.randint(50, 200)

        # Điều chỉnh theo cảnh giới
        realm_multipliers = {
            "Luyện Khí": 1,
            "Trúc Cơ": 2,
            "Kim Đan": 5,
            "Nguyên Anh": 10,
            "Hóa Thần": 20,
            "Luyện Hư": 50,
            "Hợp Thể": 100,
            "Đại Thừa": 200,
            "Độ Kiếp": 500,
            "Tiên Nhân": 1000
        }

        realm_multiplier = realm_multipliers.get(user.cultivation["realm"], 1)

        # Điều chỉnh theo tiểu cảnh giới
        level_multiplier = 1 + (user.cultivation["realm_level"] - 1) * 0.1

        # Tính tổng linh thạch
        spirit_stones = int(base_stones * realm_multiplier * level_multiplier)

        # Cơ hội nhận được linh thạch đặc biệt
        special_chance = min(0.5, 0.1 + (realm_multipliers.get(user.cultivation["realm"], 1) / 20))

        # Kết quả đặc biệt
        special_results = []

        # Linh thạch hạ phẩm (10% cơ bản)
        if random.random() < special_chance:
            low_stones = random.randint(1, 5) * realm_multiplier
            user.resources["low_stones"] = user.resources.get("low_stones", 0) + low_stones
            special_results.append(f"🟢 {low_stones} linh thạch hạ phẩm")

        # Linh thạch trung phẩm (5% cơ bản, chỉ từ Trúc Cơ trở lên)
        if user.cultivation["realm"] != "Luyện Khí" and random.random() < special_chance / 2:
            mid_stones = random.randint(1, 3)
            user.resources["mid_stones"] = user.resources.get("mid_stones", 0) + mid_stones
            special_results.append(f"🔵 {mid_stones} linh thạch trung phẩm")

        # Linh thạch thượng phẩm (1% cơ bản, chỉ từ Kim Đan trở lên)
        if user.cultivation["realm"] not in ["Luyện Khí", "Trúc Cơ"] and random.random() < special_chance / 10:
            high_stones = 1
            user.resources["high_stones"] = user.resources.get("high_stones", 0) + high_stones
            special_results.append(f"🟣 {high_stones} linh thạch thượng phẩm")

        # Cơ hội tìm thấy vật phẩm đặc biệt (5% cơ bản)
        if random.random() < special_chance / 2:
            # Danh sách vật phẩm có thể tìm thấy theo cảnh giới
            items_by_realm = {
                "Luyện Khí": ["minor_herb", "stone_fragment", "qi_gathering_stone"],
                "Trúc Cơ": ["common_herb", "foundation_stone", "minor_elixir"],
                "Kim Đan": ["uncommon_herb", "golden_essence", "spirit_fruit"],
                "Nguyên Anh": ["rare_herb", "nascent_crystal", "spirit_beast_blood"],
                "Hóa Thần": ["very_rare_herb", "divine_fragment", "transformation_pill"],
                "Luyện Hư": ["extremely_rare_herb", "void_essence", "immortal_grass"],
                "Hợp Thể": ["legendary_herb", "fusion_core", "heavenly_material"],
                "Đại Thừa": ["mythic_herb", "dao_fragment", "celestial_essence"],
                "Độ Kiếp": ["divine_herb", "tribulation_crystal", "immortal_spring_water"],
                "Tiên Nhân": ["immortal_herb", "immortal_essence", "primordial_stone"]
            }

            # Lấy danh sách vật phẩm phù hợp với cảnh giới
            available_items = items_by_realm.get(user.cultivation["realm"], ["minor_herb"])

            # Chọn ngẫu nhiên một vật phẩm
            item_id = random.choice(available_items)
            user.add_item(item_id, 1)

            # Tên hiển thị cho vật phẩm
            item_names = {
                "minor_herb": "Linh Thảo Phàm Cấp",
                "stone_fragment": "Mảnh Linh Thạch",
                "qi_gathering_stone": "Tụ Khí Thạch",
                "common_herb": "Linh Thảo Thường Gặp",
                "foundation_stone": "Trúc Cơ Thạch",
                "minor_elixir": "Tiểu Đan",
                "uncommon_herb": "Linh Thảo Hiếm",
                "golden_essence": "Kim Đan Tinh Túy",
                "spirit_fruit": "Linh Quả",
                "rare_herb": "Linh Thảo Quý Hiếm",
                "nascent_crystal": "Nguyên Anh Tinh Thể",
                "spirit_beast_blood": "Huyết Linh Thú",
                "very_rare_herb": "Linh Thảo Cực Hiếm",
                "divine_fragment": "Thần Tính Mảnh Vỡ",
                "transformation_pill": "Hóa Thần Đan",
                "extremely_rare_herb": "Linh Thảo Tuyệt Thế",
                "void_essence": "Hư Không Tinh Túy",
                "immortal_grass": "Tiên Thảo",
                "legendary_herb": "Linh Thảo Huyền Thoại",
                "fusion_core": "Hợp Thể Hạch",
                "heavenly_material": "Thiên Cấp Tài Liệu",
                "mythic_herb": "Linh Thảo Thần Thoại",
                "dao_fragment": "Đại Đạo Mảnh Vỡ",
                "celestial_essence": "Thiên Đạo Tinh Túy",
                "divine_herb": "Linh Thảo Thần Thánh",
                "tribulation_crystal": "Kiếp Lôi Tinh Thể",
                "immortal_spring_water": "Tiên Tuyền Chi Thủy",
                "immortal_herb": "Tiên Dược",
                "immortal_essence": "Tiên Đạo Tinh Túy",
                "primordial_stone": "Hỗn Độn Thạch"
            }

            special_results.append(f"🎁 1 {item_names.get(item_id, item_id)}")

        # Cộng linh thạch cho người dùng
        user.add_spirit_stones(spirit_stones)

        # Cộng kinh nghiệm (10% số linh thạch)
        exp = int(spirit_stones * 0.1)
        exp_result = user.gain_exp(exp)

        # Lưu dữ liệu người dùng
        await self.save_user_data(user)

        # Tạo embed kết quả
        embed = create_success_embed(
            title="⛏️ Đào Linh Thạch Thành Công",
            description=f"Bạn đã tìm thấy một mạch linh thạch và thu hoạch được:"
        )

        # Thêm thông tin phần thưởng
        embed.add_field(
            name="Linh thạch",
            value=f"💰 {format_number(spirit_stones)} linh thạch",
            inline=False
        )

        # Thêm thông tin kinh nghiệm
        embed.add_field(
            name="Kinh nghiệm",
            value=f"✨ {format_number(exp_result['exp_gained'])} kinh nghiệm",
            inline=False
        )

        # Thêm thông tin phần thưởng đặc biệt
        if special_results:
            embed.add_field(
                name="Phần thưởng đặc biệt",
                value="\n".join(special_results),
                inline=False
            )

        # Thêm thông tin về đột phá nếu có
        if exp_result.get("breakthrough", False):
            if exp_result.get("realm_advancement", False):
                embed.add_field(
                    name="🌟 Đột phá cảnh giới",
                    value=f"Chúc mừng! Bạn đã đột phá lên {exp_result['new_realm']} cảnh {exp_result['new_level']}!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🌟 Đột phá tiểu cảnh",
                    value=f"Chúc mừng! Bạn đã đột phá lên {user.cultivation['realm']} cảnh {user.cultivation['realm_level']}!",
                    inline=False
                )

        # Cập nhật tin nhắn
        await message.edit(embed=embed)

    @mine_spirit_stones.error
    async def mine_spirit_stones_error(self, ctx, error):
        """Xử lý lỗi lệnh đào linh thạch"""
        if isinstance(error, commands.CommandOnCooldown):
            # Tính thời gian còn lại
            minutes, seconds = divmod(int(error.retry_after), 60)

            embed = create_error_embed(
                title="⏰ Đang Hồi Cooldown",
                description=f"Bạn cần nghỉ ngơi trước khi tiếp tục đào linh thạch.\nVui lòng thử lại sau {minutes} phút {seconds} giây."
            )

            await ctx.send(embed=embed)
        else:
            # Xử lý các lỗi khác
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Đã xảy ra lỗi: {str(error)}"
            )

            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(EconomyCog(bot))
