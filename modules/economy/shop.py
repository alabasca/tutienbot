# modules/economy/shop.py
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
logger = logging.getLogger("tutien-bot.shop")


class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_handler = MongoHandler()
        self.shop_items = {}
        self.load_shop_data()

        # Danh sách các cửa hàng
        self.shops = {
            "general": {
                "name": "Cửa Hàng Tổng Hợp",
                "description": "Nơi bán các vật phẩm cơ bản cho tu tiên giả",
                "emoji": "🏪",
                "items": ["minor_healing_pill", "minor_mana_pill", "qi_gathering_stone", "spirit_stone_pouch",
                          "basic_talisman"]
            },
            "alchemy": {
                "name": "Lò Đan Dược",
                "description": "Nơi bán các loại đan dược và nguyên liệu luyện đan",
                "emoji": "🧪",
                "items": ["minor_herb", "common_herb", "foundation_pill", "qi_condensation_pill",
                          "meridian_cleansing_pill"]
            },
            "weapons": {
                "name": "Vũ Khí Các",
                "description": "Nơi bán các loại vũ khí cho tu tiên giả",
                "emoji": "⚔️",
                "items": ["basic_sword", "iron_sword", "spirit_sword", "basic_saber", "iron_saber"]
            },
            "armor": {
                "name": "Phòng Cụ Các",
                "description": "Nơi bán các loại áo giáp và phòng cụ",
                "emoji": "🛡️",
                "items": ["basic_robe", "iron_armor", "spirit_robe", "basic_boots", "iron_boots"]
            },
            "accessories": {
                "name": "Phù Lục Các",
                "description": "Nơi bán các loại phù lục và trang sức",
                "emoji": "📿",
                "items": ["basic_talisman", "spirit_talisman", "basic_ring", "basic_necklace", "spirit_bead"]
            },
            "books": {
                "name": "Thư Các",
                "description": "Nơi bán các loại công pháp và bí kíp",
                "emoji": "📚",
                "items": ["basic_cultivation_manual", "basic_sword_technique", "basic_body_technique",
                          "basic_alchemy_manual", "basic_talisman_technique"]
            },
            "sect": {
                "name": "Cửa Hàng Môn Phái",
                "description": "Nơi đổi điểm cống hiến lấy vật phẩm đặc biệt",
                "emoji": "🏯",
                "items": ["sect_cultivation_manual", "sect_weapon", "sect_armor", "sect_pill", "sect_talisman"],
                "currency": "contribution"
            }
        }

    def load_shop_data(self):
        """Tải dữ liệu cửa hàng từ file JSON"""
        import json
        import os

        try:
            with open(os.path.join("data", "items.json"), "r", encoding="utf-8") as f:
                self.shop_items = json.load(f)
            logger.info(f"Đã tải {len(self.shop_items)} vật phẩm từ file JSON")
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu cửa hàng: {e}")

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

    @commands.group(name="shop", aliases=["cuahang", "store"], invoke_without_command=True)
    async def shop(self, ctx):
        """Hiển thị danh sách các cửa hàng"""
        # Tạo embed hiển thị danh sách cửa hàng
        embed = create_embed(
            title="🏪 Hệ Thống Cửa Hàng",
            description="Chào mừng đến với khu chợ! Dưới đây là danh sách các cửa hàng:"
        )

        # Thêm thông tin từng cửa hàng
        for shop_id, shop_info in self.shops.items():
            embed.add_field(
                name=f"{shop_info['emoji']} {shop_info['name']}",
                value=f"{shop_info['description']}\nSử dụng `!shop {shop_id}` để xem",
                inline=False
            )

        # Thêm hướng dẫn sử dụng
        embed.set_footer(text="Sử dụng !shop <tên cửa hàng> để xem các vật phẩm trong cửa hàng")

        # Gửi embed
        await ctx.send(embed=embed)

    @shop.command(name="general", aliases=["tonghop"])
    async def shop_general(self, ctx, page: int = 1):
        """Hiển thị cửa hàng tổng hợp"""
        await self.show_shop(ctx, "general", page)

    @shop.command(name="alchemy", aliases=["danduoc", "dan"])
    async def shop_alchemy(self, ctx, page: int = 1):
        """Hiển thị lò đan dược"""
        await self.show_shop(ctx, "alchemy", page)

    @shop.command(name="weapons", aliases=["vukhi"])
    async def shop_weapons(self, ctx, page: int = 1):
        """Hiển thị vũ khí các"""
        await self.show_shop(ctx, "weapons", page)

    @shop.command(name="armor", aliases=["giap", "phongcu"])
    async def shop_armor(self, ctx, page: int = 1):
        """Hiển thị phòng cụ các"""
        await self.show_shop(ctx, "armor", page)

    @shop.command(name="accessories", aliases=["phuluc", "trangsuc"])
    async def shop_accessories(self, ctx, page: int = 1):
        """Hiển thị phù lục các"""
        await self.show_shop(ctx, "accessories", page)

    @shop.command(name="books", aliases=["thucac", "congphap"])
    async def shop_books(self, ctx, page: int = 1):
        """Hiển thị thư các"""
        await self.show_shop(ctx, "books", page)

    @shop.command(name="sect", aliases=["monphai"])
    async def shop_sect(self, ctx, page: int = 1):
        """Hiển thị cửa hàng môn phái"""
        # Kiểm tra xem người dùng có trong môn phái không
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        if not user.sect["sect_id"]:
            embed = create_error_embed(
                title="❌ Không Thể Truy Cập",
                description="Bạn không thuộc môn phái nào. Hãy gia nhập một môn phái để truy cập cửa hàng này."
            )
            return await ctx.send(embed=embed)

        await self.show_shop(ctx, "sect", page)

    async def show_shop(self, ctx, shop_id: str, page: int = 1):
        """Hiển thị cửa hàng cụ thể"""
        # Kiểm tra shop_id hợp lệ
        if shop_id not in self.shops:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy cửa hàng {shop_id}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin cửa hàng
        shop_info = self.shops[shop_id]

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

        # Số vật phẩm mỗi trang
        items_per_page = 5

        # Tính toán số trang
        total_items = len(shop_info["items"])
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

        if page > total_pages:
            page = total_pages

        # Tính chỉ số bắt đầu và kết thúc
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)

        # Loại tiền tệ
        currency = shop_info.get("currency", "spirit_stones")
        currency_name = "linh thạch" if currency == "spirit_stones" else "điểm cống hiến"
        currency_emoji = "💰" if currency == "spirit_stones" else "🏆"

        # Số dư hiện tại
        balance = user.resources[currency]

        # Tạo embed hiển thị cửa hàng
        embed = create_embed(
            title=f"{shop_info['emoji']} {shop_info['name']}",
            description=f"{shop_info['description']}\n\n"
                        f"Số dư: {format_number(balance)} {currency_name} {currency_emoji}\n"
                        f"Trang {page}/{total_pages}"
        )

        # Thêm thông tin vật phẩm
        current_items = shop_info["items"][start_idx:end_idx]

        for i, item_id in enumerate(current_items, start=start_idx + 1):
            # Lấy thông tin vật phẩm
            item_data = self.shop_items.get(item_id)

            if item_data:
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

                # Giá bán
                price = item_data.get("value", 100)
                if currency == "contribution":
                    price = item_data.get("contribution_value", price // 2)

                # Hiển thị mô tả và giá
                value = f"{item_data.get('description', 'Không có mô tả')}\n"
                value += f"Giá: **{format_number(price)}** {currency_name} {currency_emoji}"

                # Thêm yêu cầu nếu có
                if "required_realm" in item_data and item_data["required_realm"]:
                    value += f"\nYêu cầu: {item_data['required_realm']}"

                embed.add_field(
                    name=f"{i}. {item_name}",
                    value=value,
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{i}. Vật phẩm không xác định",
                    value=f"ID: {item_id}",
                    inline=False
                )

        # Thêm hướng dẫn sử dụng
        embed.set_footer(text=f"Sử dụng !buy {shop_id} <số thứ tự> [số lượng] để mua vật phẩm")

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="buy", aliases=["mua"])
    async def buy_item(self, ctx, shop_id: str, item_index: int, quantity: int = 1):
        """Mua vật phẩm từ cửa hàng"""
        # Kiểm tra shop_id hợp lệ
        if shop_id not in self.shops:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy cửa hàng {shop_id}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin cửa hàng
        shop_info = self.shops[shop_id]

        # Kiểm tra nếu là cửa hàng môn phái
        if shop_id == "sect":
            # Kiểm tra xem người dùng có trong môn phái không
            user = await self.get_user_data(ctx.author.id)
            if not user:
                embed = create_error_embed(
                    title="❌ Lỗi",
                    description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
                )
                return await ctx.send(embed=embed)

            if not user.sect["sect_id"]:
                embed = create_error_embed(
                    title="❌ Không Thể Truy Cập",
                    description="Bạn không thuộc môn phái nào. Hãy gia nhập một môn phái để truy cập cửa hàng này."
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

        # Kiểm tra số lượng
        if quantity <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Số lượng phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra chỉ số vật phẩm hợp lệ
        shop_items = shop_info["items"]
        if item_index < 1 or item_index > len(shop_items):
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Chỉ số vật phẩm không hợp lệ. Phải từ 1 đến {len(shop_items)}."
            )
            return await ctx.send(embed=embed)

        # Lấy ID vật phẩm
        item_id = shop_items[item_index - 1]

        # Lấy thông tin vật phẩm
        item_data = self.shop_items.get(item_id)
        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Loại tiền tệ
        currency = shop_info.get("currency", "spirit_stones")
        currency_name = "linh thạch" if currency == "spirit_stones" else "điểm cống hiến"

        # Giá bán
        price = item_data.get("value", 100)
        if currency == "contribution":
            price = item_data.get("contribution_value", price // 2)

        # Tính tổng giá
        total_price = price * quantity

        # Kiểm tra xem có đủ tiền không
        if user.resources[currency] < total_price:
            embed = create_error_embed(
                title="❌ Không đủ tiền",
                description=f"Bạn không có đủ {currency_name}. Cần {format_number(total_price)} {currency_name} để mua {quantity} {item_data['name']}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra yêu cầu cảnh giới
        if "required_realm" in item_data and item_data["required_realm"]:
            realm_levels = ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể",
                            "Đại Thừa", "Độ Kiếp", "Tiên Nhân"]
            required_realm_index = realm_levels.index(item_data["required_realm"]) if item_data[
                                                                                          "required_realm"] in realm_levels else -1
            current_realm_index = realm_levels.index(user.cultivation["realm"]) if user.cultivation[
                                                                                       "realm"] in realm_levels else -1

            if current_realm_index < required_realm_index:
                embed = create_error_embed(
                    title="❌ Cảnh giới không đủ",
                    description=f"Cảnh giới của bạn không đủ để mua vật phẩm này. Yêu cầu: {item_data['required_realm']}"
                )
                return await ctx.send(embed=embed)

        # Kiểm tra sức chứa kho đồ
        if not item_data.get("stackable", True):
            # Nếu vật phẩm không thể xếp chồng, mỗi vật phẩm chiếm 1 ô
            current_items = len(user.inventory["items"])
            if current_items + quantity > user.inventory["capacity"]:
                embed = create_error_embed(
                    title="❌ Kho đồ đầy",
                    description=f"Kho đồ của bạn không đủ chỗ. Cần {quantity} ô trống."
                )
                return await ctx.send(embed=embed)
        else:
            # Nếu vật phẩm có thể xếp chồng, kiểm tra xem có đủ chỗ không
            # Đếm số lượng vật phẩm hiện có
            existing_quantity = 0
            for item in user.inventory["items"]:
                if item["item_id"] == item_id:
                    existing_quantity += item["quantity"]

            # Nếu chưa có vật phẩm này, cần 1 ô trống
            if existing_quantity == 0:
                current_items = len(user.inventory["items"])
                if current_items >= user.inventory["capacity"]:
                    embed = create_error_embed(
                        title="❌ Kho đồ đầy",
                        description="Kho đồ của bạn đã đầy. Hãy vứt bỏ một số vật phẩm để có chỗ trống."
                    )
                    return await ctx.send(embed=embed)

        # Trừ tiền
        if currency == "spirit_stones":
            user.spend_spirit_stones(total_price)
        else:
            user.resources[currency] -= total_price

        # Thêm vật phẩm vào kho đồ
        user.add_item(item_id, quantity)

        # Lưu dữ liệu người dùng
        await self.save_user_data(user)

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Mua Hàng Thành Công",
            description=f"Bạn đã mua {quantity} {item_data['name']} với giá {format_number(total_price)} {currency_name}."
        )

        # Thêm thông tin số dư còn lại
        embed.add_field(
            name="Số dư còn lại",
            value=f"{format_number(user.resources[currency])} {currency_name}",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="sell", aliases=["ban"])
    async def sell_item(self, ctx, item_index: int, quantity: int = 1):
        """Bán vật phẩm để lấy linh thạch"""
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
        item_data = self.shop_items.get(item_id)
        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem vật phẩm có thể bán không
        if not item_data.get("sellable", True):
            embed = create_error_embed(
                title="❌ Không thể bán",
                description=f"Vật phẩm {item_data['name']} không thể bán."
            )
            return await ctx.send(embed=embed)

        # Tính giá bán (thường là 50% giá mua)
        sell_price = item_data.get("sell_value", item_data.get("value", 100) // 2)
        total_price = sell_price * quantity

        # Tạo embed xác nhận
        embed = create_embed(
            title="💰 Xác Nhận Bán Vật Phẩm",
            description=f"Bạn sắp bán {quantity} {item_data['name']} với giá {format_number(total_price)} linh thạch."
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

            # Kiểm tra lại xem còn vật phẩm không
            if not user.has_item(item_id, quantity):
                await interaction.response.send_message(
                    "Bạn không còn đủ vật phẩm để bán!",
                    ephemeral=True
                )
                return

            # Xóa vật phẩm khỏi kho đồ
            user.remove_item(item_id, quantity)

            # Cộng linh thạch
            user.add_spirit_stones(total_price)

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Bán Hàng Thành Công",
                description=f"Bạn đã bán {quantity} {item_data['name']} và nhận được {format_number(total_price)} linh thạch."
            )

            # Thêm thông tin số dư hiện tại
            embed.add_field(
                name="Số dư hiện tại",
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

            await interaction.response.send_message("Đã hủy bán vật phẩm.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(ShopCog(bot))
