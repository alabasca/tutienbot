# modules/economy/auction.py
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
logger = logging.getLogger("tutien-bot.auction")


class AuctionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_handler = MongoHandler()
        self.items_cache = {}
        self.load_items_data()

        # Danh sách đấu giá hiện tại
        self.active_auctions = {}

        # Tải các đấu giá từ database
        self.bot.loop.create_task(self.load_auctions())

        # Tạo task kiểm tra đấu giá đã kết thúc
        self.bot.loop.create_task(self.check_ended_auctions())

    def load_items_data(self):
        """Tải dữ liệu vật phẩm từ file JSON"""
        import json
        import os

        try:
            with open(os.path.join("data", "items.json"), "r", encoding="utf-8") as f:
                self.items_cache = json.load(f)
            logger.info(f"Đã tải {len(self.items_cache)} vật phẩm từ file JSON")
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu vật phẩm: {e}")

    async def load_auctions(self):
        """Tải các đấu giá từ database"""
        try:
            auctions = await self.mongo_handler.find_async(
                "auctions",
                {"end_time": {"$gt": datetime.datetime.utcnow()}}
            )

            async for auction in auctions:
                self.active_auctions[auction["auction_id"]] = auction

            logger.info(f"Đã tải {len(self.active_auctions)} đấu giá từ database")
        except Exception as e:
            logger.error(f"Lỗi khi tải đấu giá: {e}")

    async def check_ended_auctions(self):
        """Kiểm tra và xử lý các đấu giá đã kết thúc"""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                now = datetime.datetime.utcnow()
                ended_auctions = []

                # Tìm các đấu giá đã kết thúc
                for auction_id, auction in self.active_auctions.items():
                    if auction["end_time"] <= now:
                        ended_auctions.append(auction)

                # Xử lý từng đấu giá đã kết thúc
                for auction in ended_auctions:
                    await self.process_ended_auction(auction)
                    self.active_auctions.pop(auction["auction_id"], None)

                # Kiểm tra mỗi 60 giây
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Lỗi khi kiểm tra đấu giá đã kết thúc: {e}")
                await asyncio.sleep(60)

    async def process_ended_auction(self, auction):
        """Xử lý đấu giá đã kết thúc"""
        try:
            # Kiểm tra xem có người đặt giá không
            if not auction["bids"]:
                # Không có ai đặt giá, trả lại vật phẩm cho người bán
                seller_id = auction["seller_id"]
                item_id = auction["item_id"]
                quantity = auction["quantity"]

                # Lấy dữ liệu người bán
                seller = await self.get_user_data(seller_id)
                if seller:
                    # Trả lại vật phẩm
                    seller.add_item(item_id, quantity)
                    await self.save_user_data(seller)

                    # Gửi thông báo cho người bán
                    try:
                        seller_user = self.bot.get_user(seller_id)
                        if seller_user:
                            item_data = self.items_cache.get(item_id, {"name": f"Vật phẩm #{item_id}"})

                            embed = create_embed(
                                title="📦 Đấu Giá Kết Thúc",
                                description=f"Đấu giá của bạn đã kết thúc mà không có ai đặt giá.\n"
                                            f"Vật phẩm {item_data['name']} (x{quantity}) đã được trả lại vào kho đồ của bạn."
                            )

                            await seller_user.send(embed=embed)
                    except:
                        pass
            else:
                # Có người đặt giá, xử lý kết quả
                # Sắp xếp các lượt đặt giá theo giá giảm dần
                sorted_bids = sorted(auction["bids"], key=lambda x: x["amount"], reverse=True)
                highest_bid = sorted_bids[0]

                winner_id = highest_bid["bidder_id"]
                bid_amount = highest_bid["amount"]

                # Lấy dữ liệu người thắng
                winner = await self.get_user_data(winner_id)
                if winner:
                    # Thêm vật phẩm vào kho đồ người thắng
                    winner.add_item(auction["item_id"], auction["quantity"])
                    await self.save_user_data(winner)

                    # Gửi thông báo cho người thắng
                    try:
                        winner_user = self.bot.get_user(winner_id)
                        if winner_user:
                            item_data = self.items_cache.get(auction["item_id"],
                                                             {"name": f"Vật phẩm #{auction['item_id']}"})

                            embed = create_success_embed(
                                title="🎉 Chúc Mừng! Bạn Đã Thắng Đấu Giá",
                                description=f"Bạn đã thắng đấu giá với giá {format_number(bid_amount)} linh thạch.\n"
                                            f"Vật phẩm {item_data['name']} (x{auction['quantity']}) đã được thêm vào kho đồ của bạn."
                            )

                            await winner_user.send(embed=embed)
                    except:
                        pass

                # Trả tiền cho người bán
                seller_id = auction["seller_id"]
                seller = await self.get_user_data(seller_id)

                if seller:
                    # Tính phí giao dịch (5%)
                    fee = int(bid_amount * 0.05)
                    seller_amount = bid_amount - fee

                    # Cộng tiền cho người bán
                    seller.add_spirit_stones(seller_amount)
                    await self.save_user_data(seller)

                    # Gửi thông báo cho người bán
                    try:
                        seller_user = self.bot.get_user(seller_id)
                        if seller_user:
                            item_data = self.items_cache.get(auction["item_id"],
                                                             {"name": f"Vật phẩm #{auction['item_id']}"})

                            embed = create_success_embed(
                                title="💰 Đấu Giá Thành Công",
                                description=f"Vật phẩm {item_data['name']} (x{auction['quantity']}) của bạn đã được bán với giá {format_number(bid_amount)} linh thạch.\n"
                                            f"Phí giao dịch (5%): {format_number(fee)} linh thạch\n"
                                            f"Số tiền bạn nhận được: {format_number(seller_amount)} linh thạch"
                            )

                            await seller_user.send(embed=embed)
                    except:
                        pass

            # Cập nhật trạng thái đấu giá trong database
            await self.mongo_handler.update_one_async(
                "auctions",
                {"auction_id": auction["auction_id"]},
                {"$set": {"status": "ended"}}
            )

        except Exception as e:
            logger.error(f"Lỗi khi xử lý đấu giá đã kết thúc: {e}")

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

    @commands.group(name="auction", aliases=["daugia"], invoke_without_command=True)
    async def auction(self, ctx, page: int = 1):
        """Xem danh sách đấu giá hiện tại"""
        # Kiểm tra trang hợp lệ
        if page < 1:
            page = 1

        # Số đấu giá mỗi trang
        auctions_per_page = 5

        # Lấy danh sách đấu giá hiện tại từ database
        auctions = await self.mongo_handler.find_async(
            "auctions",
            {"end_time": {"$gt": datetime.datetime.utcnow()}, "status": "active"},
            sort=[("end_time", 1)]  # Sắp xếp theo thời gian kết thúc tăng dần
        )

        # Chuyển đổi kết quả thành list
        auctions_list = await auctions.to_list(length=None)

        # Tính toán số trang
        total_auctions = len(auctions_list)
        total_pages = max(1, (total_auctions + auctions_per_page - 1) // auctions_per_page)

        if page > total_pages:
            page = total_pages

        # Tính chỉ số bắt đầu và kết thúc
        start_idx = (page - 1) * auctions_per_page
        end_idx = min(start_idx + auctions_per_page, total_auctions)

        # Tạo embed hiển thị danh sách đấu giá
        embed = create_embed(
            title="🔨 Phòng Đấu Giá",
            description=f"Danh sách các đấu giá đang diễn ra\nTrang {page}/{total_pages}"
        )

        # Thêm thông tin từng đấu giá
        if not auctions_list:
            embed.add_field(name="Không có đấu giá", value="Hiện tại không có đấu giá nào đang diễn ra.", inline=False)
        else:
            current_auctions = auctions_list[start_idx:end_idx]

            for i, auction in enumerate(current_auctions, start=start_idx + 1):
                # Lấy thông tin vật phẩm
                item_id = auction["item_id"]
                item_data = self.items_cache.get(item_id, {"name": f"Vật phẩm #{item_id}"})

                # Định dạng tên vật phẩm theo độ hiếm
                rarity_icons = {
                    "common": "⚪",
                    "uncommon": "🟢",
                    "rare": "🔵",
                    "epic": "🟣",
                    "legendary": "🟠",
                    "mythic": "🔴",
                    "divine": "🟡",
                    "artifact": "⚡"
                }

                rarity_icon = rarity_icons.get(item_data.get("rarity", "common"), "⚪")
                item_name = f"{rarity_icon} {item_data['name']}"

                # Lấy thông tin người bán
                seller_id = auction["seller_id"]
                seller = self.bot.get_user(seller_id)
                seller_name = seller.name if seller else "Không xác định"

                # Lấy thông tin giá khởi điểm và giá cao nhất hiện tại
                starting_price = auction["starting_price"]
                current_price = starting_price

                if auction["bids"]:
                    # Sắp xếp các lượt đặt giá theo giá giảm dần
                    sorted_bids = sorted(auction["bids"], key=lambda x: x["amount"], reverse=True)
                    current_price = sorted_bids[0]["amount"]

                # Tính thời gian còn lại
                end_time = auction["end_time"]
                time_left = end_time - datetime.datetime.utcnow()

                days, remainder = divmod(time_left.total_seconds(), 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)

                if days > 0:
                    time_str = f"{int(days)} ngày {int(hours)} giờ"
                elif hours > 0:
                    time_str = f"{int(hours)} giờ {int(minutes)} phút"
                else:
                    time_str = f"{int(minutes)} phút {int(seconds)} giây"

                # Tạo chuỗi hiển thị thông tin đấu giá
                value = f"**Vật phẩm:** {item_name} (x{auction['quantity']})\n"
                value += f"**Người bán:** {seller_name}\n"
                value += f"**Giá khởi điểm:** {format_number(starting_price)} linh thạch\n"
                value += f"**Giá cao nhất hiện tại:** {format_number(current_price)} linh thạch\n"
                value += f"**Thời gian còn lại:** {time_str}\n"
                value += f"**ID đấu giá:** `{auction['auction_id']}`"

                embed.add_field(
                    name=f"#{i}. {item_name}",
                    value=value,
                    inline=False
                )

        # Thêm hướng dẫn sử dụng
        embed.set_footer(
            text="Sử dụng !auction info <ID đấu giá> để xem chi tiết | !auction bid <ID đấu giá> <số tiền> để đặt giá")

        # Gửi embed
        await ctx.send(embed=embed)

    @auction.command(name="info")
    async def auction_info(self, ctx, auction_id: str):
        """Xem thông tin chi tiết về một đấu giá"""
        # Lấy thông tin đấu giá từ database
        auction = await self.mongo_handler.find_one_async(
            "auctions",
            {"auction_id": auction_id, "status": "active"}
        )

        if not auction:
            embed = create_error_embed(
                title="❌ Không Tìm Thấy",
                description="Không tìm thấy đấu giá với ID đã cung cấp hoặc đấu giá đã kết thúc."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_id = auction["item_id"]
        item_data = self.items_cache.get(item_id, {"name": f"Vật phẩm #{item_id}"})

        # Định dạng tên vật phẩm theo độ hiếm
        rarity_icons = {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟠",
            "mythic": "🔴",
            "divine": "🟡",
            "artifact": "⚡"
        }

        rarity_colors = {
            "common": discord.Color.light_grey(),
            "uncommon": discord.Color.green(),
            "rare": discord.Color.blue(),
            "epic": discord.Color.purple(),
            "legendary": discord.Color.orange(),
            "mythic": discord.Color.red(),
            "divine": discord.Color.gold(),
            "artifact": discord.Color(0x738ADB)  # Màu đặc biệt cho artifact
        }

        rarity = item_data.get("rarity", "common")
        rarity_icon = rarity_icons.get(rarity, "⚪")
        embed_color = rarity_colors.get(rarity, discord.Color.default())

        # Lấy thông tin người bán
        seller_id = auction["seller_id"]
        seller = self.bot.get_user(seller_id)
        seller_name = seller.name if seller else "Không xác định"

        # Lấy thông tin giá khởi điểm và giá cao nhất hiện tại
        starting_price = auction["starting_price"]
        current_price = starting_price
        highest_bidder = "Chưa có"

        if auction["bids"]:
            # Sắp xếp các lượt đặt giá theo giá giảm dần
            sorted_bids = sorted(auction["bids"], key=lambda x: x["amount"], reverse=True)
            highest_bid = sorted_bids[0]
            current_price = highest_bid["amount"]

            # Lấy thông tin người đặt giá cao nhất
            bidder_id = highest_bid["bidder_id"]
            bidder = self.bot.get_user(bidder_id)
            highest_bidder = bidder.name if bidder else f"Người dùng #{bidder_id}"

        # Tính thời gian còn lại
        end_time = auction["end_time"]
        time_left = end_time - datetime.datetime.utcnow()

        days, remainder = divmod(time_left.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            time_str = f"{int(days)} ngày {int(hours)} giờ {int(minutes)} phút {int(seconds)} giây"
        elif hours > 0:
            time_str = f"{int(hours)} giờ {int(minutes)} phút {int(seconds)} giây"
        else:
            time_str = f"{int(minutes)} phút {int(seconds)} giây"

        # Tạo embed hiển thị thông tin đấu giá
        embed = create_embed(
            title=f"🔨 Đấu Giá: {rarity_icon} {item_data['name']}",
            description=item_data.get("description", "Không có mô tả"),
            color=embed_color
        )

        # Thêm thông tin cơ bản
        embed.add_field(name="Số lượng", value=str(auction["quantity"]), inline=True)
        embed.add_field(name="Người bán", value=seller_name, inline=True)
        embed.add_field(name="ID đấu giá", value=auction_id, inline=True)

        # Thêm thông tin giá
        embed.add_field(name="Giá khởi điểm", value=f"{format_number(starting_price)} linh thạch", inline=True)
        embed.add_field(name="Giá cao nhất hiện tại", value=f"{format_number(current_price)} linh thạch", inline=True)
        embed.add_field(name="Người đặt giá cao nhất", value=highest_bidder, inline=True)

        # Thêm thông tin thời gian
        embed.add_field(name="Thời gian còn lại", value=time_str, inline=True)
        embed.add_field(name="Kết thúc vào", value=end_time.strftime("%d/%m/%Y %H:%M:%S UTC"), inline=True)

        # Thêm thông tin vật phẩm
        if "required_level" in item_data and item_data["required_level"] > 0:
            embed.add_field(name="Yêu cầu cấp độ", value=str(item_data["required_level"]), inline=True)

        if "required_realm" in item_data and item_data["required_realm"]:
            embed.add_field(name="Yêu cầu cảnh giới", value=item_data["required_realm"], inline=True)

        # Thêm thông tin đặc biệt theo loại vật phẩm
        item_type = item_data.get("item_type", "")

        if item_type == "equipment":
            # Hiển thị thông tin trang bị
            embed.add_field(name="Loại trang bị", value=self.translate_equipment_slot(item_data.get("slot", "")),
                            inline=True)

            # Hiển thị chỉ số
            stats_text = ""
            for stat, value in item_data.get("stats", {}).items():
                if value != 0:
                    stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

            if stats_text:
                embed.add_field(name="Chỉ số", value=stats_text, inline=False)

        # Thêm lịch sử đặt giá
        if auction["bids"]:
            # Sắp xếp các lượt đặt giá theo thời gian giảm dần
            sorted_bids = sorted(auction["bids"], key=lambda x: x["time"], reverse=True)

            bid_history = ""
            for i, bid in enumerate(sorted_bids[:5], 1):
                bidder_id = bid["bidder_id"]
                bidder = self.bot.get_user(bidder_id)
                bidder_name = bidder.name if bidder else f"Người dùng #{bidder_id}"

                bid_time = bid["time"].strftime("%d/%m/%Y %H:%M:%S")
                bid_history += f"{i}. **{bidder_name}**: {format_number(bid['amount'])} linh thạch ({bid_time})\n"

            if len(sorted_bids) > 5:
                bid_history += f"... và {len(sorted_bids) - 5} lượt đặt giá khác"

            embed.add_field(name="Lịch sử đặt giá", value=bid_history, inline=False)

        # Thêm hình ảnh nếu có
        if "image_url" in item_data and item_data["image_url"]:
            embed.set_thumbnail(url=item_data["image_url"])

        # Thêm hướng dẫn đặt giá
        embed.set_footer(text=f"Sử dụng !auction bid {auction_id} <số tiền> để đặt giá")

        # Gửi embed
        await ctx.send(embed=embed)

    @auction.command(name="bid")
    async def auction_bid(self, ctx, auction_id: str, amount: int):
        """Đặt giá cho một đấu giá"""
        # Kiểm tra số tiền
        if amount <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Số tiền phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin đấu giá từ database
        auction = await self.mongo_handler.find_one_async(
            "auctions",
            {"auction_id": auction_id, "status": "active"}
        )

        if not auction:
            embed = create_error_embed(
                title="❌ Không Tìm Thấy",
                description="Không tìm thấy đấu giá với ID đã cung cấp hoặc đấu giá đã kết thúc."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem người dùng có phải là người bán không
        if auction["seller_id"] == ctx.author.id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn không thể đặt giá cho đấu giá của chính mình."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem đấu giá đã kết thúc chưa
        if auction["end_time"] <= datetime.datetime.utcnow():
            embed = create_error_embed(
                title="❌ Đấu Giá Đã Kết Thúc",
                description="Đấu giá này đã kết thúc."
            )
            return await ctx.send(embed=embed)

        # Lấy giá cao nhất hiện tại
        current_price = auction["starting_price"]

        if auction["bids"]:
            # Sắp xếp các lượt đặt giá theo giá giảm dần
            sorted_bids = sorted(auction["bids"], key=lambda x: x["amount"], reverse=True)
            current_price = sorted_bids[0]["amount"]

        # Kiểm tra xem giá đặt có cao hơn giá hiện tại không
        min_bid = current_price + max(1, int(current_price * 0.05))  # Tối thiểu cao hơn 5%

        if amount < min_bid:
            embed = create_error_embed(
                title="❌ Giá Đặt Quá Thấp",
                description=f"Giá đặt phải cao hơn giá hiện tại ít nhất 5%.\nGiá tối thiểu: {format_number(min_bid)} linh thạch"
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem người dùng có đủ linh thạch không
        if user.resources["spirit_stones"] < amount:
            embed = create_error_embed(
                title="❌ Không Đủ Linh Thạch",
                description=f"Bạn không có đủ linh thạch. Hiện tại bạn có {format_number(user.resources['spirit_stones'])} linh thạch."
            )
            return await ctx.send(embed=embed)

        # Tạo embed xác nhận
        item_id = auction["item_id"]
        item_data = self.items_cache.get(item_id, {"name": f"Vật phẩm #{item_id}"})

        embed = create_embed(
            title="🔨 Xác Nhận Đặt Giá",
            description=f"Bạn sắp đặt giá {format_number(amount)} linh thạch cho {item_data['name']} (x{auction['quantity']}).\n\n"
                        f"**Lưu ý:** Linh thạch sẽ bị khóa cho đến khi đấu giá kết thúc hoặc có người đặt giá cao hơn."
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
            if user.resources["spirit_stones"] < amount:
                await interaction.response.send_message(
                    "Không đủ linh thạch để đặt giá!",
                    ephemeral=True
                )
                return

            # Kiểm tra lại xem đấu giá còn hoạt động không
            current_auction = await self.mongo_handler.find_one_async(
                "auctions",
                {"auction_id": auction_id, "status": "active"}
            )

            if not current_auction:
                await interaction.response.send_message(
                    "Đấu giá này đã kết thúc hoặc không còn tồn tại!",
                    ephemeral=True
                )
                return

            # Kiểm tra lại giá cao nhất hiện tại
            current_price = current_auction["starting_price"]

            if current_auction["bids"]:
                # Sắp xếp các lượt đặt giá theo giá giảm dần
                sorted_bids = sorted(current_auction["bids"], key=lambda x: x["amount"], reverse=True)
                current_price = sorted_bids[0]["amount"]

            # Kiểm tra lại xem giá đặt có cao hơn giá hiện tại không
            min_bid = current_price + max(1, int(current_price * 0.05))  # Tối thiểu cao hơn 5%

            if amount < min_bid:
                await interaction.response.send_message(
                    f"Giá đặt quá thấp! Giá tối thiểu hiện tại là {format_number(min_bid)} linh thạch.",
                    ephemeral=True
                )
                return

            # Hoàn trả linh thạch cho người đặt giá cao nhất trước đó
            if current_auction["bids"]:
                # Sắp xếp các lượt đặt giá theo giá giảm dần
                sorted_bids = sorted(current_auction["bids"], key=lambda x: x["amount"], reverse=True)
                highest_bid = sorted_bids[0]

                # Nếu người đặt giá cao nhất không phải là người hiện tại
                if highest_bid["bidder_id"] != ctx.author.id:
                    # Lấy dữ liệu người đặt giá cao nhất trước đó
                    previous_bidder = await self.get_user_data(highest_bid["bidder_id"])
                    if previous_bidder:
                        # Hoàn trả linh thạch
                        previous_bidder.add_spirit_stones(highest_bid["amount"])
                        await self.save_user_data(previous_bidder)

                        # Gửi thông báo cho người đặt giá trước đó
                        try:
                            previous_user = self.bot.get_user(highest_bid["bidder_id"])
                            if previous_user:
                                embed = create_embed(
                                    title="📢 Đã Bị Vượt Giá",
                                    description=f"Bạn đã bị vượt giá trong đấu giá {item_data['name']}.\n"
                                                f"Linh thạch đã được hoàn trả: {format_number(highest_bid['amount'])} linh thạch."
                                )

                                await previous_user.send(embed=embed)
                        except:
                            pass

            # Trừ linh thạch của người đặt giá mới
            user.resources["spirit_stones"] -= amount
            await self.save_user_data(user)

            # Thêm lượt đặt giá mới
            new_bid = {
                "bidder_id": ctx.author.id,
                "amount": amount,
                "time": datetime.datetime.utcnow()
            }

            # Cập nhật đấu giá trong database
            await self.mongo_handler.update_one_async(
                "auctions",
                {"auction_id": auction_id},
                {"$push": {"bids": new_bid}}
            )

            # Cập nhật cache
            if auction_id in self.active_auctions:
                self.active_auctions[auction_id]["bids"].append(new_bid)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đặt Giá Thành Công",
                description=f"Bạn đã đặt giá {format_number(amount)} linh thạch cho {item_data['name']} (x{auction['quantity']})."
            )

            # Thêm thông tin số dư còn lại
            embed.add_field(
                name="Số dư còn lại",
                value=f"{format_number(user.resources['spirit_stones'])} linh thạch",
                inline=False
            )

            # Thêm thông tin thời gian kết thúc
            end_time = auction["end_time"]
            time_left = end_time - datetime.datetime.utcnow()

            days, remainder = divmod(time_left.total_seconds(), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            if days > 0:
                time_str = f"{int(days)} ngày {int(hours)} giờ"
            elif hours > 0:
                time_str = f"{int(hours)} giờ {int(minutes)} phút"
            else:
                time_str = f"{int(minutes)} phút {int(seconds)} giây"

            embed.add_field(
                name="Thời gian còn lại",
                value=time_str,
                inline=False
            )

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy đặt giá.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    @auction.command(name="create", aliases=["new", "tao"])
    async def auction_create(self, ctx, item_index: int, quantity: int = 1, starting_price: int = None,
                             duration: int = 24):
        """Tạo một đấu giá mới"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra số lượng
        if quantity <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Số lượng phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra thời gian
        if duration < 1 or duration > 168:  # 1 giờ đến 7 ngày
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Thời gian đấu giá phải từ 1 đến 168 giờ (7 ngày)."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra chỉ số vật phẩm hợp lệ
        if item_index < 1 or item_index > len(user.inventory["items"]):
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Chỉ số vật phẩm không hợp lệ. Phải từ 1 đến {len(user.inventory['items'])}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_entry = user.inventory["items"][item_index - 1]
        item_id = item_entry["item_id"]
        max_quantity = item_entry["quantity"]

        # Kiểm tra số lượng
        if quantity > max_quantity:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn chỉ có {max_quantity} vật phẩm này."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.items_cache.get(item_id)
        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem vật phẩm có thể đấu giá không
        if not item_data.get("tradeable", True):
            embed = create_error_embed(
                title="❌ Không thể đấu giá",
                description=f"Vật phẩm {item_data['name']} không thể giao dịch hoặc đấu giá."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem vật phẩm có bị khóa không
        if item_entry.get("bound", False):
            embed = create_error_embed(
                title="❌ Vật phẩm bị khóa",
                description=f"Vật phẩm {item_data['name']} đã bị khóa và không thể đấu giá."
            )
            return await ctx.send(embed=embed)

        # Nếu không chỉ định giá khởi điểm, sử dụng giá trị mặc định
        if starting_price is None:
            starting_price = item_data.get("value", 100) * quantity

        # Kiểm tra giá khởi điểm
        if starting_price <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Giá khởi điểm phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Tính phí đăng ký đấu giá (1% giá khởi điểm, tối thiểu 10 linh thạch)
        listing_fee = max(10, int(starting_price * 0.01))

        # Kiểm tra xem có đủ linh thạch để trả phí không
        if user.resources["spirit_stones"] < listing_fee:
            embed = create_error_embed(
                title="❌ Không đủ linh thạch",
                description=f"Bạn cần {format_number(listing_fee)} linh thạch để đăng ký đấu giá."
            )
            return await ctx.send(embed=embed)

        # Tạo embed xác nhận
        embed = create_embed(
            title="🔨 Xác Nhận Tạo Đấu Giá",
            description=f"Bạn sắp tạo đấu giá cho {item_data['name']} (x{quantity}) với giá khởi điểm {format_number(starting_price)} linh thạch.\n\n"
                        f"**Thời gian:** {duration} giờ\n"
                        f"**Phí đăng ký:** {format_number(listing_fee)} linh thạch"
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

            # Kiểm tra lại xem có đủ linh thạch để trả phí không
            if user.resources["spirit_stones"] < listing_fee:
                await interaction.response.send_message(
                    "Không đủ linh thạch để đăng ký đấu giá!",
                    ephemeral=True
                )
                return

            # Kiểm tra lại xem còn vật phẩm không
            if not user.has_item(item_id, quantity):
                await interaction.response.send_message(
                    "Bạn không còn đủ vật phẩm để đấu giá!",
                    ephemeral=True
                )
                return

            # Trừ phí đăng ký
            user.spend_spirit_stones(listing_fee)

            # Xóa vật phẩm khỏi kho đồ
            user.remove_item(item_id, quantity)

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo ID đấu giá
            import uuid
            auction_id = str(uuid.uuid4())[:8]

            # Tính thời gian kết thúc
            end_time = datetime.datetime.utcnow() + datetime.timedelta(hours=duration)

            # Tạo đấu giá mới
            new_auction = {
                "auction_id": auction_id,
                "seller_id": ctx.author.id,
                "item_id": item_id,
                "quantity": quantity,
                "starting_price": starting_price,
                "current_price": starting_price,
                "bids": [],
                "created_at": datetime.datetime.utcnow(),
                "end_time": end_time,
                "status": "active"
            }

            # Lưu đấu giá vào database
            await self.mongo_handler.insert_one_async("auctions", new_auction)

            # Thêm vào cache
            self.active_auctions[auction_id] = new_auction

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Tạo Đấu Giá Thành Công",
                description=f"Đã tạo đấu giá cho {item_data['name']} (x{quantity}) với giá khởi điểm {format_number(starting_price)} linh thạch."
            )

            # Thêm thông tin
            embed.add_field(
                name="ID đấu giá",
                value=auction_id,
                inline=True
            )

            embed.add_field(
                name="Thời gian kết thúc",
                value=end_time.strftime("%d/%m/%Y %H:%M:%S UTC"),
                inline=True
            )

            embed.add_field(
                name="Phí đã trả",
                value=f"{format_number(listing_fee)} linh thạch",
                inline=True
            )

            # Thêm thông tin số dư còn lại
            embed.add_field(
                name="Số dư còn lại",
                value=f"{format_number(user.resources['spirit_stones'])} linh thạch",
                inline=False
            )

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy tạo đấu giá.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    @auction.command(name="cancel", aliases=["huy"])
    async def auction_cancel(self, ctx, auction_id: str):
        """Hủy một đấu giá đang diễn ra"""
        # Lấy thông tin đấu giá từ database
        auction = await self.mongo_handler.find_one_async(
            "auctions",
            {"auction_id": auction_id, "status": "active"}
        )

        if not auction:
            embed = create_error_embed(
                title="❌ Không Tìm Thấy",
                description="Không tìm thấy đấu giá với ID đã cung cấp hoặc đấu giá đã kết thúc."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem người dùng có phải là người bán không
        if auction["seller_id"] != ctx.author.id:
            embed = create_error_embed(
                title="❌ Không Có Quyền",
                description="Bạn không phải là người tạo đấu giá này."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem đã có người đặt giá chưa
        if auction["bids"]:
            embed = create_error_embed(
                title="❌ Không Thể Hủy",
                description="Không thể hủy đấu giá đã có người đặt giá."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Không tìm thấy dữ liệu người dùng."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_id = auction["item_id"]
        quantity = auction["quantity"]
        item_data = self.items_cache.get(item_id, {"name": f"Vật phẩm #{item_id}"})

        # Tạo embed xác nhận
        embed = create_embed(
            title="🔨 Xác Nhận Hủy Đấu Giá",
            description=f"Bạn có chắc chắn muốn hủy đấu giá {item_data['name']} (x{quantity}) không?\n\n"
                        f"**Lưu ý:** Phí đăng ký sẽ không được hoàn lại."
        )

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Xác nhận", style=discord.ButtonStyle.danger)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Kiểm tra lại xem đấu giá còn tồn tại không
            current_auction = await self.mongo_handler.find_one_async(
                "auctions",
                {"auction_id": auction_id, "status": "active"}
            )

            if not current_auction:
                await interaction.response.send_message(
                    "Đấu giá này đã kết thúc hoặc không còn tồn tại!",
                    ephemeral=True
                )
                return

            # Kiểm tra lại xem đã có người đặt giá chưa
            if current_auction["bids"]:
                await interaction.response.send_message(
                    "Không thể hủy đấu giá đã có người đặt giá!",
                    ephemeral=True
                )
                return

            # Trả lại vật phẩm cho người bán
            user.add_item(item_id, quantity)
            await self.save_user_data(user)

            # Cập nhật trạng thái đấu giá trong database
            await self.mongo_handler.update_one_async(
                "auctions",
                {"auction_id": auction_id},
                {"$set": {"status": "cancelled"}}
            )

            # Xóa khỏi cache
            if auction_id in self.active_auctions:
                self.active_auctions.pop(auction_id)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Hủy Đấu Giá",
                description=f"Đã hủy đấu giá {item_data['name']} (x{quantity}).\n"
                            f"Vật phẩm đã được trả lại vào kho đồ của bạn."
            )

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy thao tác.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    @auction.command(name="history", aliases=["lichsu"])
    async def auction_history(self, ctx, page: int = 1):
        """Xem lịch sử đấu giá của bạn"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra trang hợp lệ
        if page < 1:
            page = 1

        # Số đấu giá mỗi trang
        auctions_per_page = 5

        # Lấy danh sách đấu giá từ database
        auctions = await self.mongo_handler.find_async(
            "auctions",
            {"$or": [
                {"seller_id": ctx.author.id},
                {"bids.bidder_id": ctx.author.id}
            ]},
            sort=[("end_time", -1)]  # Sắp xếp theo thời gian kết thúc giảm dần
        )

        # Chuyển đổi kết quả thành list
        auctions_list = await auctions.to_list(length=None)

        # Tính toán số trang
        total_auctions = len(auctions_list)
        total_pages = max(1, (total_auctions + auctions_per_page - 1) // auctions_per_page)

        if page > total_pages:
            page = total_pages

        # Tính chỉ số bắt đầu và kết thúc
        start_idx = (page - 1) * auctions_per_page
        end_idx = min(start_idx + auctions_per_page, total_auctions)

        # Tạo embed hiển thị lịch sử đấu giá
        embed = create_embed(
            title="📜 Lịch Sử Đấu Giá",
            description=f"Lịch sử đấu giá của bạn\nTrang {page}/{total_pages}"
        )

        # Thêm thông tin từng đấu giá
        if not auctions_list:
            embed.add_field(name="Không có dữ liệu", value="Bạn chưa tham gia đấu giá nào.", inline=False)
        else:
            current_auctions = auctions_list[start_idx:end_idx]

            for i, auction in enumerate(current_auctions, start=start_idx + 1):
                # Lấy thông tin vật phẩm
                item_id = auction["item_id"]
                item_data = self.items_cache.get(item_id, {"name": f"Vật phẩm #{item_id}"})

                # Định dạng tên vật phẩm theo độ hiếm
                rarity_icons = {
                    "common": "⚪",
                    "uncommon": "🟢",
                    "rare": "🔵",
                    "epic": "🟣",
                    "legendary": "🟠",
                    "mythic": "🔴",
                    "divine": "🟡",
                    "artifact": "⚡"
                }

                rarity_icon = rarity_icons.get(item_data.get("rarity", "common"), "⚪")
                item_name = f"{rarity_icon} {item_data['name']}"

                # Xác định vai trò (người bán hoặc người mua)
                is_seller = auction["seller_id"] == ctx.author.id
                role = "Người bán" if is_seller else "Người đặt giá"

                # Lấy thông tin giá cuối cùng
                final_price = auction["starting_price"]
                winner = "Không có người đặt giá"

                if auction["bids"]:
                    # Sắp xếp các lượt đặt giá theo giá giảm dần
                    sorted_bids = sorted(auction["bids"], key=lambda x: x["amount"], reverse=True)
                    highest_bid = sorted_bids[0]
                    final_price = highest_bid["amount"]

                    # Lấy thông tin người thắng
                    winner_id = highest_bid["bidder_id"]
                    winner_user = self.bot.get_user(winner_id)
                    winner = winner_user.name if winner_user else f"Người dùng #{winner_id}"

                # Xác định trạng thái
                now = datetime.datetime.utcnow()
                status = auction.get("status", "active")

                if status == "active":
                    if auction["end_time"] > now:
                        status_text = "🟢 Đang diễn ra"
                    else:
                        status_text = "🟡 Đang xử lý kết quả"
                elif status == "ended":
                    status_text = "🔵 Đã kết thúc"
                elif status == "cancelled":
                    status_text = "🔴 Đã hủy"
                else:
                    status_text = "⚪ Không xác định"

                # Tạo chuỗi hiển thị thông tin đấu giá
                value = f"**Vật phẩm:** {item_name} (x{auction['quantity']})\n"
                value += f"**Vai trò:** {role}\n"
                value += f"**Giá cuối cùng:** {format_number(final_price)} linh thạch\n"

                if not is_seller:
                    # Tìm giá đặt cao nhất của người dùng
                    user_bids = [bid for bid in auction["bids"] if bid["bidder_id"] == ctx.author.id]
                    if user_bids:
                        user_highest_bid = max(user_bids, key=lambda x: x["amount"])
                        value += f"**Giá bạn đặt:** {format_number(user_highest_bid['amount'])} linh thạch\n"

                value += f"**Người thắng:** {winner}\n"
                value += f"**Trạng thái:** {status_text}\n"
                value += f"**Thời gian kết thúc:** {auction['end_time'].strftime('%d/%m/%Y %H:%M:%S')}"

                embed.add_field(
                    name=f"#{i}. {item_name}",
                    value=value,
                    inline=False
                )

        # Gửi embed
        await ctx.send(embed=embed)

    def translate_equipment_slot(self, slot: str) -> str:
        """Chuyển đổi vị trí trang bị sang tiếng Việt"""
        translations = {
            "weapon": "Vũ khí",
            "armor": "Áo giáp",
            "helmet": "Mũ",
            "boots": "Giày",
            "belt": "Đai",
            "necklace": "Dây chuyền",
            "ring": "Nhẫn",
            "talisman": "Bùa hộ mệnh",
            "spirit_pet": "Linh thú"
        }

        return translations.get(slot, "Không xác định")

    def translate_stat(self, stat: str) -> str:
        """Chuyển đổi tên chỉ số sang tiếng Việt"""
        translations = {
            "hp": "Máu",
            "max_hp": "Máu tối đa",
            "mp": "Linh lực",
            "max_mp": "Linh lực tối đa",
            "physical_power": "Thân thể lực",
            "spiritual_power": "Thần thức lực",
            "attack": "Công kích",
            "defense": "Phòng thủ",
            "speed": "Tốc độ",
            "crit_rate": "Tỷ lệ bạo kích",
            "crit_damage": "Sát thương bạo kích",
            "dodge": "Né tránh",
            "accuracy": "Chính xác",
            "elemental_wood": "Nguyên tố Mộc",
            "elemental_fire": "Nguyên tố Hỏa",
            "elemental_earth": "Nguyên tố Thổ",
            "elemental_metal": "Nguyên tố Kim",
            "elemental_water": "Nguyên tố Thủy",
            "elemental_wind": "Nguyên tố Phong",
            "elemental_lightning": "Nguyên tố Lôi",
            "elemental_ice": "Nguyên tố Băng",
            "elemental_light": "Nguyên tố Quang",
            "elemental_dark": "Nguyên tố Ám",
            "resistance_wood": "Kháng Mộc",
            "resistance_fire": "Kháng Hỏa",
            "resistance_earth": "Kháng Thổ",
            "resistance_metal": "Kháng Kim",
            "resistance_water": "Kháng Thủy",
            "resistance_wind": "Kháng Phong",
            "resistance_lightning": "Kháng Lôi",
            "resistance_ice": "Kháng Băng",
            "resistance_light": "Kháng Quang",
            "resistance_dark": "Kháng Ám",
            "cultivation_speed": "Tốc độ tu luyện",
            "exp_bonus": "Tăng kinh nghiệm",
            "spirit_stone_bonus": "Tăng linh thạch",
            "luck": "May mắn"
        }

        return translations.get(stat, stat)


def setup(bot):
    bot.add_cog(AuctionCog(bot))
