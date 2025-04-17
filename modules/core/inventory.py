# modules/core/inventory.py
import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
from typing import Dict, List, Optional, Union, Any

from database.mongo_handler import MongoHandler
from database.models.user_model import User
from database.models.item_model import Item, Equipment, Consumable, Material, Treasure, Pill, SkillBook, SpiritStone
from utils.embed_utils import create_embed, create_success_embed, create_error_embed
from utils.text_utils import format_number, progress_bar

# Cấu hình logging
logger = logging.getLogger("tutien-bot.inventory")


class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_handler = MongoHandler()
        self.items_cache = {}  # Cache cho dữ liệu vật phẩm
        self.load_items_data()

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

    def get_item_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin vật phẩm từ cache hoặc database"""
        # Kiểm tra trong cache trước
        if item_id in self.items_cache:
            return self.items_cache[item_id]

        # Nếu không có trong cache, truy vấn từ database
        item_data = self.mongo_handler.find_one("items", {"item_id": item_id})
        if item_data:
            # Thêm vào cache để sử dụng sau này
            self.items_cache[item_id] = item_data
            return item_data

        return None

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

    @commands.group(name="inventory", aliases=["inv", "kho", "túi"], invoke_without_command=True)
    async def inventory(self, ctx, page: int = 1):
        """Xem kho đồ của bạn"""
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
        items_per_page = 10

        # Tính toán số trang
        total_items = len(user.inventory["items"])
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

        if page > total_pages:
            page = total_pages

        # Tính chỉ số bắt đầu và kết thúc
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)

        # Tạo embed
        embed = create_embed(
            title=f"🎒 Kho Đồ của {ctx.author.display_name}",
            description=f"Sức chứa: {total_items}/{user.inventory['capacity']} vật phẩm\n"
                        f"Trang {page}/{total_pages}"
        )

        # Thêm thông tin vật phẩm
        if total_items == 0:
            embed.add_field(name="Trống", value="Kho đồ của bạn đang trống.", inline=False)
        else:
            # Lấy danh sách vật phẩm hiện tại
            current_items = user.inventory["items"][start_idx:end_idx]

            for i, item_entry in enumerate(current_items, start=start_idx + 1):
                item_id = item_entry["item_id"]
                quantity = item_entry["quantity"]
                bound = item_entry.get("bound", False)

                # Lấy thông tin vật phẩm
                item_data = self.get_item_data(item_id)

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

                    # Thêm biểu tượng khóa nếu vật phẩm bị khóa
                    if bound:
                        item_name += " 🔒"

                    # Hiển thị số lượng và mô tả ngắn
                    value = f"Số lượng: **{quantity}**\n"
                    value += f"*{item_data.get('description', 'Không có mô tả')}*"

                    embed.add_field(
                        name=f"{i}. {item_name}",
                        value=value,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"{i}. Vật phẩm không xác định",
                        value=f"ID: {item_id}, Số lượng: {quantity}",
                        inline=False
                    )

        # Thêm hướng dẫn sử dụng
        embed.set_footer(
            text="Sử dụng !inventory <trang> để xem các trang khác | !inventory info <số thứ tự> để xem chi tiết vật phẩm")

        # Gửi embed
        await ctx.send(embed=embed)

    @inventory.command(name="info", aliases=["detail", "chi_tiet"])
    async def inventory_info(self, ctx, item_index: int):
        """Xem thông tin chi tiết về vật phẩm trong kho đồ"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra chỉ số hợp lệ
        if item_index < 1 or item_index > len(user.inventory["items"]):
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Chỉ số vật phẩm không hợp lệ. Phải từ 1 đến {len(user.inventory['items'])}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_entry = user.inventory["items"][item_index - 1]
        item_id = item_entry["item_id"]
        quantity = item_entry["quantity"]
        bound = item_entry.get("bound", False)

        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Tạo embed thông tin chi tiết
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

        embed_color = rarity_colors.get(item_data.get("rarity", "common"), discord.Color.default())

        embed = create_embed(
            title=f"{item_data['name']} {'🔒' if bound else ''}",
            description=item_data.get("description", "Không có mô tả"),
            color=embed_color
        )

        # Thêm thông tin cơ bản
        embed.add_field(name="Số lượng", value=str(quantity), inline=True)
        embed.add_field(name="Loại", value=self.translate_item_type(item_data.get("item_type", "unknown")), inline=True)
        embed.add_field(name="Độ hiếm", value=self.translate_rarity(item_data.get("rarity", "common")), inline=True)

        # Thêm giá trị
        if "value" in item_data:
            embed.add_field(name="Giá trị", value=f"{format_number(item_data['value'])} linh thạch", inline=True)

        # Thêm yêu cầu sử dụng
        if "required_level" in item_data and item_data["required_level"] > 0:
            embed.add_field(name="Yêu cầu cấp độ", value=str(item_data["required_level"]), inline=True)

        if "required_realm" in item_data and item_data["required_realm"]:
            embed.add_field(name="Yêu cầu cảnh giới", value=item_data["required_realm"], inline=True)

        # Thêm thông tin đặc biệt theo loại vật phẩm
        item_type = item_data.get("item_type", "")

        if item_type == "equipment":
            # Hiển thị thông tin trang bị
            embed.add_field(name="Vị trí trang bị", value=self.translate_equipment_slot(item_data.get("slot", "")),
                            inline=True)

            # Hiển thị chỉ số
            stats_text = ""
            for stat, value in item_data.get("stats", {}).items():
                if value != 0:
                    stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

            if stats_text:
                embed.add_field(name="Chỉ số", value=stats_text, inline=False)

            # Hiển thị độ bền
            durability = item_data.get("durability", 100)
            max_durability = item_data.get("max_durability", 100)
            durability_percent = int((durability / max_durability) * 100)
            durability_bar = progress_bar(durability, max_durability, 10)

            embed.add_field(
                name="Độ bền",
                value=f"{durability}/{max_durability} ({durability_percent}%)\n{durability_bar}",
                inline=False
            )

            # Hiển thị tinh luyện và ổ khảm
            refinement = item_data.get("refinement", 0)
            if refinement > 0:
                embed.add_field(name="Tinh luyện", value=f"+{refinement}", inline=True)

            sockets = item_data.get("sockets", 0)
            gems = item_data.get("gems", [])
            if sockets > 0:
                socket_text = f"{len(gems)}/{sockets} ổ đã khảm"
                if gems:
                    socket_text += "\n"
                    for i, gem_id in enumerate(gems, 1):
                        gem_data = self.get_item_data(gem_id)
                        gem_name = gem_data["name"] if gem_data else "Đá không xác định"
                        socket_text += f"• Ổ {i}: {gem_name}\n"

                embed.add_field(name="Ổ khảm", value=socket_text, inline=False)

            # Hiển thị hiệu ứng đặc biệt
            special_effects = item_data.get("special_effects", [])
            if special_effects:
                effects_text = ""
                for effect in special_effects:
                    effects_text += f"• {effect}\n"

                embed.add_field(name="Hiệu ứng đặc biệt", value=effects_text, inline=False)

        elif item_type == "consumable" or item_type == "pill":
            # Hiển thị thông tin vật phẩm tiêu hao
            effects_text = ""
            for effect in item_data.get("effects", []):
                effect_type = effect.get("type", "")
                effect_value = effect.get("value", 0)

                if effect_type == "heal":
                    effects_text += f"• Hồi {effect_value} HP\n"
                elif effect_type == "restore_mana":
                    effects_text += f"• Hồi {effect_value} MP\n"
                elif effect_type == "exp":
                    effects_text += f"• Tăng {effect_value} kinh nghiệm\n"
                elif effect_type == "spirit_stones":
                    effects_text += f"• Nhận {effect_value} linh thạch\n"
                elif effect_type == "stat_boost":
                    stat = effect.get("stat", "")
                    duration = effect.get("duration", 300)
                    effects_text += f"• Tăng {self.translate_stat(stat)} {effect_value} trong {duration // 60} phút\n"
                elif effect_type == "cultivation_boost":
                    duration = effect.get("duration", 3600)
                    effects_text += f"• Tăng tốc độ tu luyện {effect_value}x trong {duration // 60} phút\n"
                else:
                    effects_text += f"• {effect_type}: {effect_value}\n"

            if effects_text:
                embed.add_field(name="Hiệu ứng", value=effects_text, inline=False)

            # Hiển thị thời gian hồi chiêu
            cooldown = item_data.get("cooldown", 0)
            if cooldown > 0:
                embed.add_field(name="Thời gian hồi", value=f"{cooldown // 60} phút {cooldown % 60} giây", inline=True)

            # Hiển thị thời gian hiệu lực
            duration = item_data.get("duration", 0)
            if duration > 0:
                embed.add_field(name="Thời gian hiệu lực", value=f"{duration // 60} phút {duration % 60} giây",
                                inline=True)

            # Hiển thị tác dụng phụ (cho đan dược)
            if item_type == "pill":
                side_effects = item_data.get("side_effects", [])
                if side_effects:
                    side_effects_text = ""
                    for effect in side_effects:
                        side_effects_text += f"• {effect}\n"

                    embed.add_field(name="Tác dụng phụ", value=side_effects_text, inline=False)

                # Hiển thị tỷ lệ thành công và chất lượng
                success_rate = item_data.get("success_rate", 100)
                embed.add_field(name="Tỷ lệ thành công", value=f"{success_rate}%", inline=True)

                quality = item_data.get("quality", 0)
                quality_bar = progress_bar(quality, 100, 10)
                embed.add_field(name="Chất lượng", value=f"{quality}/100\n{quality_bar}", inline=True)

        elif item_type == "skill_book":
            # Hiển thị thông tin sách kỹ năng
            embed.add_field(name="Kỹ năng", value=item_data.get("skill_name", "Không xác định"), inline=True)
            embed.add_field(name="Loại kỹ năng", value=self.translate_skill_type(item_data.get("skill_type", "")),
                            inline=True)

            if "skill_description" in item_data:
                embed.add_field(name="Mô tả kỹ năng", value=item_data["skill_description"], inline=False)

            if item_data.get("one_time_use", True):
                embed.add_field(name="Lưu ý", value="Vật phẩm sẽ biến mất sau khi sử dụng", inline=False)

        # Thêm hình ảnh nếu có
        if "image_url" in item_data and item_data["image_url"]:
            embed.set_thumbnail(url=item_data["image_url"])

        # Thêm các nút tương tác
        view = discord.ui.View(timeout=60)

        # Nút sử dụng
        if item_type in ["consumable", "pill", "skill_book"]:
            use_button = discord.ui.Button(label="Sử dụng", style=discord.ButtonStyle.green)
            use_button.callback = lambda interaction: self.use_item_callback(interaction, ctx.author.id, item_index)
            view.add_item(use_button)

        # Nút trang bị (nếu là trang bị)
        if item_type == "equipment":
            equip_button = discord.ui.Button(label="Trang bị", style=discord.ButtonStyle.blurple)
            equip_button.callback = lambda interaction: self.equip_item_callback(interaction, ctx.author.id, item_index)
            view.add_item(equip_button)

        # Nút vứt bỏ
        discard_button = discord.ui.Button(label="Vứt bỏ", style=discord.ButtonStyle.red)
        discard_button.callback = lambda interaction: self.discard_item_callback(interaction, ctx.author.id, item_index)
        view.add_item(discard_button)

        # Gửi embed với các nút
        await ctx.send(embed=embed, view=view)

    async def use_item_callback(self, interaction, user_id, item_index):
        """Xử lý khi người dùng nhấn nút sử dụng vật phẩm"""
        # Kiểm tra xem người dùng có phải là người gọi lệnh không
        if interaction.user.id != user_id:
            await interaction.response.send_message("Bạn không thể sử dụng vật phẩm của người khác!", ephemeral=True)
            return

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(user_id)
        if not user:
            await interaction.response.send_message("Không tìm thấy dữ liệu người dùng!", ephemeral=True)
            return

        # Kiểm tra chỉ số hợp lệ
        if item_index < 1 or item_index > len(user.inventory["items"]):
            await interaction.response.send_message("Chỉ số vật phẩm không hợp lệ!", ephemeral=True)
            return

        # Lấy thông tin vật phẩm
        item_entry = user.inventory["items"][item_index - 1]
        item_id = item_entry["item_id"]

        # Sử dụng vật phẩm
        result = user.use_item(item_id)

        if result["success"]:
            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã sử dụng vật phẩm",
                description=f"Bạn đã sử dụng {result['item_name']}."
            )

            # Thêm thông tin về hiệu ứng
            if result["effects"]:
                effects_text = ""
                for effect in result["effects"]:
                    effects_text += f"• {effect}\n"

                embed.add_field(name="Hiệu ứng", value=effects_text, inline=False)

            # Thêm thông tin về đột phá nếu có
            if result.get("breakthrough", False):
                if result.get("realm_advancement", False):
                    embed.add_field(
                        name="🌟 Đột phá cảnh giới",
                        value=f"Chúc mừng! Bạn đã đột phá lên {result['new_realm']} cảnh {result['new_level']}!",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🌟 Đột phá tiểu cảnh",
                        value=f"Chúc mừng! Bạn đã đột phá lên {user.cultivation['realm']} cảnh {user.cultivation['realm_level']}!",
                        inline=False
                    )

            await interaction.response.send_message(embed=embed)
        else:
            # Tạo embed thông báo lỗi
            embed = create_error_embed(
                title="❌ Lỗi",
                description=result["message"]
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def equip_item_callback(self, interaction, user_id, item_index):
        """Xử lý khi người dùng nhấn nút trang bị vật phẩm"""
        # Kiểm tra xem người dùng có phải là người gọi lệnh không
        if interaction.user.id != user_id:
            await interaction.response.send_message("Bạn không thể trang bị vật phẩm của người khác!", ephemeral=True)
            return

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(user_id)
        if not user:
            await interaction.response.send_message("Không tìm thấy dữ liệu người dùng!", ephemeral=True)
            return

        # Kiểm tra chỉ số hợp lệ
        if item_index < 1 or item_index > len(user.inventory["items"]):
            await interaction.response.send_message("Chỉ số vật phẩm không hợp lệ!", ephemeral=True)
            return

        # Lấy thông tin vật phẩm
        item_entry = user.inventory["items"][item_index - 1]
        item_id = item_entry["item_id"]

        # Lấy dữ liệu vật phẩm
        item_data = self.get_item_data(item_id)
        if not item_data or item_data.get("item_type") != "equipment":
            await interaction.response.send_message("Vật phẩm này không phải là trang bị!", ephemeral=True)
            return

        # Tạo menu chọn vị trí trang bị
        slot_options = []
        slot_mapping = {
            "weapon": "Vũ khí",
            "armor": "Áo giáp",
            "helmet": "Mũ",
            "boots": "Giày",
            "belt": "Đai",
            "necklace": "Dây chuyền",
            "ring1": "Nhẫn 1",
            "ring2": "Nhẫn 2",
            "talisman": "Bùa hộ mệnh",
            "spirit_pet": "Linh thú"
        }

        # Chỉ hiển thị các vị trí phù hợp với loại trang bị
        equipment_slot = item_data.get("slot", "")
        if equipment_slot == "weapon":
            slot_options.append(discord.SelectOption(label="Vũ khí", value="weapon"))
        elif equipment_slot == "armor":
            slot_options.append(discord.SelectOption(label="Áo giáp", value="armor"))
        elif equipment_slot == "helmet":
            slot_options.append(discord.SelectOption(label="Mũ", value="helmet"))
        elif equipment_slot == "boots":
            slot_options.append(discord.SelectOption(label="Giày", value="boots"))
        elif equipment_slot == "belt":
            slot_options.append(discord.SelectOption(label="Đai", value="belt"))
        elif equipment_slot == "necklace":
            slot_options.append(discord.SelectOption(label="Dây chuyền", value="necklace"))
        elif equipment_slot == "ring":
            slot_options.append(discord.SelectOption(label="Nhẫn 1", value="ring1"))
            slot_options.append(discord.SelectOption(label="Nhẫn 2", value="ring2"))
        elif equipment_slot == "talisman":
            slot_options.append(discord.SelectOption(label="Bùa hộ mệnh", value="talisman"))
        elif equipment_slot == "spirit_pet":
            slot_options.append(discord.SelectOption(label="Linh thú", value="spirit_pet"))

        if not slot_options:
            await interaction.response.send_message("Không tìm thấy vị trí trang bị phù hợp!", ephemeral=True)
            return

        # Tạo menu chọn
        select = discord.ui.Select(
            placeholder="Chọn vị trí trang bị",
            options=slot_options
        )

        # Tạo view chứa menu
        view = discord.ui.View(timeout=30)
        view.add_item(select)

        # Xử lý khi người dùng chọn vị trí
        async def select_callback(interaction):
            slot = select.values[0]

            # Trang bị vật phẩm
            result = user.equip_item(item_id, slot)

            if result:
                # Lưu dữ liệu người dùng
                await self.save_user_data(user)

                # Tạo embed thông báo
                embed = create_success_embed(
                    title="✅ Đã trang bị",
                    description=f"Bạn đã trang bị {item_data['name']} vào vị trí {slot_mapping.get(slot, slot)}."
                )

                await interaction.response.send_message(embed=embed)
            else:
                # Tạo embed thông báo lỗi
                embed = create_error_embed(
                    title="❌ Lỗi",
                    description="Không thể trang bị vật phẩm này."
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = select_callback

        # Gửi menu chọn
        await interaction.response.send_message("Chọn vị trí trang bị:", view=view, ephemeral=True)

    async def discard_item_callback(self, interaction, user_id, item_index):
        """Xử lý khi người dùng nhấn nút vứt bỏ vật phẩm"""
        # Kiểm tra xem người dùng có phải là người gọi lệnh không
        if interaction.user.id != user_id:
            await interaction.response.send_message("Bạn không thể vứt bỏ vật phẩm của người khác!", ephemeral=True)
            return

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(user_id)
        if not user:
            await interaction.response.send_message("Không tìm thấy dữ liệu người dùng!", ephemeral=True)
            return

        # Kiểm tra chỉ số hợp lệ
        if item_index < 1 or item_index > len(user.inventory["items"]):
            await interaction.response.send_message("Chỉ số vật phẩm không hợp lệ!", ephemeral=True)
            return

        # Lấy thông tin vật phẩm
        item_entry = user.inventory["items"][item_index - 1]
        item_id = item_entry["item_id"]
        quantity = item_entry["quantity"]

        # Lấy dữ liệu vật phẩm
        item_data = self.get_item_data(item_id)
        item_name = item_data["name"] if item_data else f"Vật phẩm #{item_id}"

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Xác nhận", style=discord.ButtonStyle.danger)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Xóa vật phẩm
            user.remove_item(item_id, quantity)

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã vứt bỏ",
                description=f"Bạn đã vứt bỏ {quantity} {item_name}."
            )

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            await interaction.response.send_message("Đã hủy thao tác vứt bỏ vật phẩm.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi xác nhận
        await interaction.response.send_message(
            f"Bạn có chắc chắn muốn vứt bỏ {quantity} {item_name} không?",
            view=view,
            ephemeral=True
        )

    @inventory.command(name="equipment", aliases=["equip", "trang_bi"])
    async def inventory_equipment(self, ctx):
        """Xem trang bị đang mặc"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Tạo embed
        embed = create_embed(
            title=f"🛡️ Trang Bị của {ctx.author.display_name}",
            description="Danh sách trang bị đang mặc"
        )

        # Danh sách vị trí trang bị
        equipment_slots = {
            "weapon": "Vũ khí",
            "armor": "Áo giáp",
            "helmet": "Mũ",
            "boots": "Giày",
            "belt": "Đai",
            "necklace": "Dây chuyền",
            "ring1": "Nhẫn 1",
            "ring2": "Nhẫn 2",
            "talisman": "Bùa hộ mệnh",
            "spirit_pet": "Linh thú"
        }

        # Thêm thông tin trang bị
        for slot, slot_name in equipment_slots.items():
            item_id = user.inventory["equipped"].get(slot)

            if item_id:
                # Lấy thông tin vật phẩm
                item_data = self.get_item_data(item_id)

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

                    # Hiển thị thông tin cơ bản
                    value = f"*{item_data.get('description', 'Không có mô tả')}*\n"

                    # Hiển thị chỉ số
                    stats_text = ""
                    for stat, stat_value in item_data.get("stats", {}).items():
                        if stat_value != 0:
                            stats_text += f"• {self.translate_stat(stat)}: +{stat_value}\n"

                    if stats_text:
                        value += stats_text

                    # Hiển thị tinh luyện
                    refinement = item_data.get("refinement", 0)
                    if refinement > 0:
                        value += f"Tinh luyện: +{refinement}\n"

                    embed.add_field(
                        name=f"{slot_name}: {item_name}",
                        value=value,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"{slot_name}: Không xác định",
                        value=f"ID: {item_id}",
                        inline=False
                    )
            else:
                embed.add_field(
                    name=f"{slot_name}: Trống",
                    value="Không có trang bị",
                    inline=False
                )

        # Thêm hướng dẫn sử dụng
        embed.set_footer(text="Sử dụng !inventory info <số thứ tự> để xem chi tiết vật phẩm và trang bị")

        # Gửi embed
        await ctx.send(embed=embed)

    @inventory.command(name="unequip", aliases=["remove", "thao"])
    async def inventory_unequip(self, ctx, slot: str):
        """Tháo trang bị"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Chuyển đổi tên tiếng Việt sang key tiếng Anh
        slot_mapping = {
            "vũ khí": "weapon",
            "vu khi": "weapon",
            "vukhi": "weapon",
            "weapon": "weapon",

            "áo giáp": "armor",
            "ao giap": "armor",
            "aogiap": "armor",
            "armor": "armor",

            "mũ": "helmet",
            "mu": "helmet",
            "helmet": "helmet",

            "giày": "boots",
            "giay": "boots",
            "boots": "boots",

            "đai": "belt",
            "dai": "belt",
            "belt": "belt",

            "dây chuyền": "necklace",
            "day chuyen": "necklace",
            "daychuyen": "necklace",
            "necklace": "necklace",

            "nhẫn 1": "ring1",
            "nhan 1": "ring1",
            "nhan1": "ring1",
            "ring1": "ring1",

            "nhẫn 2": "ring2",
            "nhan 2": "ring2",
            "nhan2": "ring2",
            "ring2": "ring2",

            "bùa": "talisman",
            "bua": "talisman",
            "talisman": "talisman",

            "linh thú": "spirit_pet",
            "linh thu": "spirit_pet",
            "linhthu": "spirit_pet",
            "pet": "spirit_pet",
            "spirit_pet": "spirit_pet"
        }

        # Chuyển đổi slot
        slot_key = slot_mapping.get(slot.lower())

        if not slot_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vị trí trang bị không hợp lệ. Các vị trí hợp lệ: vũ khí, áo giáp, mũ, giày, đai, dây chuyền, nhẫn 1, nhẫn 2, bùa, linh thú."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có trang bị ở vị trí này không
        item_id = user.inventory["equipped"].get(slot_key)

        if not item_id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn không có trang bị ở vị trí {slot}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.get_item_data(item_id)
        item_name = item_data["name"] if item_data else f"Vật phẩm #{item_id}"

        # Tháo trang bị
        result = user.unequip_item(slot_key)

        if result:
            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã tháo trang bị",
                description=f"Bạn đã tháo {item_name} khỏi vị trí {slot}."
            )

            await ctx.send(embed=embed)
        else:
            # Tạo embed thông báo lỗi
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Không thể tháo trang bị này."
            )

            await ctx.send(embed=embed)

    @inventory.command(name="use", aliases=["su_dung"])
    async def inventory_use(self, ctx, item_index: int):
        """Sử dụng vật phẩm trong kho đồ"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra chỉ số hợp lệ
        if item_index < 1 or item_index > len(user.inventory["items"]):
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Chỉ số vật phẩm không hợp lệ. Phải từ 1 đến {len(user.inventory['items'])}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_entry = user.inventory["items"][item_index - 1]
        item_id = item_entry["item_id"]

        # Lấy dữ liệu vật phẩm
        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra loại vật phẩm
        item_type = item_data.get("item_type", "")

        if item_type not in ["consumable", "pill", "skill_book"]:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vật phẩm này không thể sử dụng trực tiếp."
            )
            return await ctx.send(embed=embed)

        # Sử dụng vật phẩm
        result = user.use_item(item_id)

        if result["success"]:
            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã sử dụng vật phẩm",
                description=f"Bạn đã sử dụng {result['item_name']}."
            )

            # Thêm thông tin về hiệu ứng
            if result["effects"]:
                effects_text = ""
                for effect in result["effects"]:
                    effects_text += f"• {effect}\n"

                embed.add_field(name="Hiệu ứng", value=effects_text, inline=False)

            # Thêm thông tin về đột phá nếu có
            if result.get("breakthrough", False):
                if result.get("realm_advancement", False):
                    embed.add_field(
                        name="🌟 Đột phá cảnh giới",
                        value=f"Chúc mừng! Bạn đã đột phá lên {result['new_realm']} cảnh {result['new_level']}!",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🌟 Đột phá tiểu cảnh",
                        value=f"Chúc mừng! Bạn đã đột phá lên {user.cultivation['realm']} cảnh {user.cultivation['realm_level']}!",
                        inline=False
                    )

            await ctx.send(embed=embed)
        else:
            # Tạo embed thông báo lỗi
            embed = create_error_embed(
                title="❌ Lỗi",
                description=result["message"]
            )

            await ctx.send(embed=embed)

    @inventory.command(name="discard", aliases=["drop", "vut_bo"])
    async def inventory_discard(self, ctx, item_index: int, quantity: int = None):
        """Vứt bỏ vật phẩm trong kho đồ"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra chỉ số hợp lệ
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

        # Nếu không chỉ định số lượng, vứt bỏ tất cả
        if quantity is None:
            quantity = max_quantity

        # Kiểm tra số lượng hợp lệ
        if quantity <= 0 or quantity > max_quantity:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Số lượng không hợp lệ. Phải từ 1 đến {max_quantity}."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu vật phẩm
        item_data = self.get_item_data(item_id)
        item_name = item_data["name"] if item_data else f"Vật phẩm #{item_id}"

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

            # Xóa vật phẩm
            user.remove_item(item_id, quantity)

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã vứt bỏ",
                description=f"Bạn đã vứt bỏ {quantity} {item_name}."
            )

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy thao tác vứt bỏ vật phẩm.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi xác nhận
        await ctx.send(
            f"Bạn có chắc chắn muốn vứt bỏ {quantity} {item_name} không?",
            view=view
        )

    @commands.command(name="repair", aliases=["sua_chua"])
    async def repair_equipment(self, ctx, slot: str = None):
        """Sửa chữa trang bị"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Danh sách vị trí trang bị
        equipment_slots = {
            "weapon": "Vũ khí",
            "armor": "Áo giáp",
            "helmet": "Mũ",
            "boots": "Giày",
            "belt": "Đai",
            "necklace": "Dây chuyền",
            "ring1": "Nhẫn 1",
            "ring2": "Nhẫn 2",
            "talisman": "Bùa hộ mệnh",
            "spirit_pet": "Linh thú"
        }

        # Chuyển đổi tên tiếng Việt sang key tiếng Anh
        slot_mapping = {
            "vũ khí": "weapon",
            "vu khi": "weapon",
            "vukhi": "weapon",
            "weapon": "weapon",

            "áo giáp": "armor",
            "ao giap": "armor",
            "aogiap": "armor",
            "armor": "armor",

            "mũ": "helmet",
            "mu": "helmet",
            "helmet": "helmet",

            "giày": "boots",
            "giay": "boots",
            "boots": "boots",

            "đai": "belt",
            "dai": "belt",
            "belt": "belt",

            "dây chuyền": "necklace",
            "day chuyen": "necklace",
            "daychuyen": "necklace",
            "necklace": "necklace",

            "nhẫn 1": "ring1",
            "nhan 1": "ring1",
            "nhan1": "ring1",
            "ring1": "ring1",

            "nhẫn 2": "ring2",
            "nhan 2": "ring2",
            "nhan2": "ring2",
            "ring2": "ring2",

            "bùa": "talisman",
            "bua": "talisman",
            "talisman": "talisman",

            "linh thú": "spirit_pet",
            "linh thu": "spirit_pet",
            "linhthu": "spirit_pet",
            "pet": "spirit_pet",
            "spirit_pet": "spirit_pet",

            "all": "all",
            "tất cả": "all",
            "tat ca": "all",
            "tatca": "all"
        }

        # Nếu không chỉ định slot, hiển thị danh sách trang bị cần sửa chữa
        if slot is None:
            # Tạo embed
            embed = create_embed(
                title=f"🔧 Sửa Chữa Trang Bị - {ctx.author.display_name}",
                description="Danh sách trang bị cần sửa chữa"
            )

            # Kiểm tra từng trang bị
            needs_repair = False

            for slot_key, slot_name in equipment_slots.items():
                item_id = user.inventory["equipped"].get(slot_key)

                if item_id:
                    # Lấy thông tin vật phẩm
                    item_data = self.get_item_data(item_id)

                    if item_data:
                        # Kiểm tra độ bền
                        durability = item_data.get("durability", 100)
                        max_durability = item_data.get("max_durability", 100)

                        if durability < max_durability:
                            needs_repair = True

                            # Tính chi phí sửa chữa
                            repair_cost = self.calculate_repair_cost(item_data, durability, max_durability)

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

                            # Hiển thị độ bền
                            durability_percent = int((durability / max_durability) * 100)
                            durability_bar = progress_bar(durability, max_durability, 10)

                            value = f"Độ bền: {durability}/{max_durability} ({durability_percent}%)\n"
                            value += f"{durability_bar}\n"
                            value += f"Chi phí sửa chữa: {format_number(repair_cost)} linh thạch"

                            embed.add_field(
                                name=f"{slot_name}: {item_name}",
                                value=value,
                                inline=False
                            )

            if not needs_repair:
                embed.add_field(
                    name="Không cần sửa chữa",
                    value="Tất cả trang bị của bạn đều trong tình trạng tốt.",
                    inline=False
                )
            else:
                # Thêm hướng dẫn sử dụng
                embed.add_field(
                    name="Hướng dẫn",
                    value="Sử dụng `!repair <vị trí>` để sửa chữa trang bị cụ thể, hoặc `!repair all` để sửa chữa tất cả.",
                    inline=False
                )

            # Gửi embed
            await ctx.send(embed=embed)
            return

        # Chuyển đổi slot
        slot_key = slot_mapping.get(slot.lower())

        if not slot_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vị trí trang bị không hợp lệ. Các vị trí hợp lệ: vũ khí, áo giáp, mũ, giày, đai, dây chuyền, nhẫn 1, nhẫn 2, bùa, linh thú, hoặc 'all' để sửa chữa tất cả."
            )
            return await ctx.send(embed=embed)

        # Sửa chữa tất cả trang bị
        if slot_key == "all":
            total_cost = 0
            repaired_items = []

            for slot_key, slot_name in equipment_slots.items():
                item_id = user.inventory["equipped"].get(slot_key)

                if item_id:
                    # Lấy thông tin vật phẩm
                    item_data = self.get_item_data(item_id)

                    if item_data:
                        # Kiểm tra độ bền
                        durability = item_data.get("durability", 100)
                        max_durability = item_data.get("max_durability", 100)

                        if durability < max_durability:
                            # Tính chi phí sửa chữa
                            repair_cost = self.calculate_repair_cost(item_data, durability, max_durability)

                            # Cập nhật tổng chi phí
                            total_cost += repair_cost

                            # Thêm vào danh sách đã sửa chữa
                            repaired_items.append({
                                "name": item_data["name"],
                                "slot": slot_name,
                                "cost": repair_cost
                            })

                            # Cập nhật độ bền
                            item_data["durability"] = max_durability

                            # Cập nhật cache
                            self.items_cache[item_id] = item_data

            # Nếu không có gì để sửa chữa
            if not repaired_items:
                embed = create_error_embed(
                    title="❌ Không cần sửa chữa",
                    description="Tất cả trang bị của bạn đều trong tình trạng tốt."
                )
                return await ctx.send(embed=embed)

            # Kiểm tra xem có đủ linh thạch không
            if user.resources["spirit_stones"] < total_cost:
                embed = create_error_embed(
                    title="❌ Không đủ linh thạch",
                    description=f"Bạn cần {format_number(total_cost)} linh thạch để sửa chữa tất cả trang bị."
                )
                return await ctx.send(embed=embed)

            # Trừ linh thạch
            user.spend_spirit_stones(total_cost)

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã sửa chữa tất cả trang bị",
                description=f"Đã chi {format_number(total_cost)} linh thạch để sửa chữa {len(repaired_items)} trang bị."
            )

            # Thêm chi tiết từng trang bị đã sửa
            for item in repaired_items:
                embed.add_field(
                    name=f"{item['slot']}: {item['name']}",
                    value=f"Chi phí: {format_number(item['cost'])} linh thạch",
                    inline=True
                )

            await ctx.send(embed=embed)
            return

        # Sửa chữa một trang bị cụ thể
        item_id = user.inventory["equipped"].get(slot_key)

        if not item_id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn không có trang bị ở vị trí {slot}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra độ bền
        durability = item_data.get("durability", 100)
        max_durability = item_data.get("max_durability", 100)

        if durability >= max_durability:
            embed = create_error_embed(
                title="❌ Không cần sửa chữa",
                description=f"Trang bị {item_data['name']} đang trong tình trạng tốt."
            )
            return await ctx.send(embed=embed)

        # Tính chi phí sửa chữa
        repair_cost = self.calculate_repair_cost(item_data, durability, max_durability)

        # Kiểm tra xem có đủ linh thạch không
        if user.resources["spirit_stones"] < repair_cost:
            embed = create_error_embed(
                title="❌ Không đủ linh thạch",
                description=f"Bạn cần {format_number(repair_cost)} linh thạch để sửa chữa {item_data['name']}."
            )
            return await ctx.send(embed=embed)

        # Trừ linh thạch
        user.spend_spirit_stones(repair_cost)

        # Cập nhật độ bền
        item_data["durability"] = max_durability

        # Cập nhật cache
        self.items_cache[item_id] = item_data

        # Lưu dữ liệu người dùng
        await self.save_user_data(user)

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã sửa chữa trang bị",
            description=f"Đã chi {format_number(repair_cost)} linh thạch để sửa chữa {item_data['name']}."
        )

        await ctx.send(embed=embed)

    def calculate_repair_cost(self, item_data: Dict[str, Any], durability: int, max_durability: int) -> int:
        """Tính chi phí sửa chữa trang bị"""
        # Tỷ lệ hư hỏng
        damage_ratio = 1 - (durability / max_durability)

        # Giá trị cơ bản của vật phẩm
        base_value = item_data.get("value", 100)

        # Hệ số theo độ hiếm
        rarity_multipliers = {
            "common": 0.5,
            "uncommon": 0.75,
            "rare": 1.0,
            "epic": 1.5,
            "legendary": 2.0,
            "mythic": 3.0,
            "divine": 5.0,
            "artifact": 10.0
        }

        rarity = item_data.get("rarity", "common")
        rarity_multiplier = rarity_multipliers.get(rarity, 1.0)

        # Tính chi phí
        repair_cost = int(base_value * damage_ratio * rarity_multiplier)

        # Đảm bảo chi phí tối thiểu
        return max(10, repair_cost)

    @commands.command(name="refine", aliases=["tinh_luyen"])
    async def refine_equipment(self, ctx, slot: str):
        """Tinh luyện trang bị"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Chuyển đổi tên tiếng Việt sang key tiếng Anh
        slot_mapping = {
            "vũ khí": "weapon",
            "vu khi": "weapon",
            "vukhi": "weapon",
            "weapon": "weapon",

            "áo giáp": "armor",
            "ao giap": "armor",
            "aogiap": "armor",
            "armor": "armor",

            "mũ": "helmet",
            "mu": "helmet",
            "helmet": "helmet",

            "giày": "boots",
            "giay": "boots",
            "boots": "boots",

            "đai": "belt",
            "dai": "belt",
            "belt": "belt",

            "dây chuyền": "necklace",
            "day chuyen": "necklace",
            "daychuyen": "necklace",
            "necklace": "necklace",

            "nhẫn 1": "ring1",
            "nhan 1": "ring1",
            "nhan1": "ring1",
            "ring1": "ring1",

            "nhẫn 2": "ring2",
            "nhan 2": "ring2",
            "nhan2": "ring2",
            "ring2": "ring2",

            "bùa": "talisman",
            "bua": "talisman",
            "talisman": "talisman",

            "linh thú": "spirit_pet",
            "linh thu": "spirit_pet",
            "linhthu": "spirit_pet",
            "pet": "spirit_pet",
            "spirit_pet": "spirit_pet"
        }

        # Chuyển đổi slot
        slot_key = slot_mapping.get(slot.lower())

        if not slot_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vị trí trang bị không hợp lệ. Các vị trí hợp lệ: vũ khí, áo giáp, mũ, giày, đai, dây chuyền, nhẫn 1, nhẫn 2, bùa, linh thú."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có trang bị ở vị trí này không
        item_id = user.inventory["equipped"].get(slot_key)

        if not item_id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn không có trang bị ở vị trí {slot}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra độ tinh luyện hiện tại
        refinement = item_data.get("refinement", 0)

        if refinement >= 10:
            embed = create_error_embed(
                title="❌ Đã đạt cấp tối đa",
                description=f"Trang bị {item_data['name']} đã đạt cấp tinh luyện tối đa (+10)."
            )
            return await ctx.send(embed=embed)

        # Tính chi phí tinh luyện
        refine_cost = self.calculate_refine_cost(item_data, refinement)

        # Tính tỷ lệ thành công
        success_rate = self.calculate_refine_success_rate(refinement)

        # Tạo embed xác nhận
        embed = create_embed(
            title=f"⚒️ Tinh Luyện Trang Bị - {item_data['name']}",
            description=f"Bạn có muốn tinh luyện {item_data['name']} từ +{refinement} lên +{refinement + 1} không?"
        )

        embed.add_field(name="Chi phí", value=f"{format_number(refine_cost)} linh thạch", inline=True)
        embed.add_field(name="Tỷ lệ thành công", value=f"{success_rate}%", inline=True)

        # Thêm cảnh báo
        if refinement >= 7:
            embed.add_field(
                name="⚠️ Cảnh báo",
                value="Nếu tinh luyện thất bại, trang bị có thể bị giảm cấp hoặc vỡ vụn!",
                inline=False
            )

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Tinh luyện", style=discord.ButtonStyle.primary)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Kiểm tra lại xem có đủ linh thạch không
            if user.resources["spirit_stones"] < refine_cost:
                await interaction.response.send_message(
                    f"Không đủ linh thạch! Bạn cần {format_number(refine_cost)} linh thạch để tinh luyện.",
                    ephemeral=True
                )
                return

            # Trừ linh thạch
            user.spend_spirit_stones(refine_cost)

            # Xác định kết quả tinh luyện
            import random
            success = random.random() * 100 <= success_rate

            if success:
                # Tinh luyện thành công
                item_data["refinement"] = refinement + 1

                # Tăng chỉ số theo tinh luyện
                for stat in item_data.get("stats", {}):
                    item_data["stats"][stat] = int(item_data["stats"][stat] * 1.1)

                # Cập nhật cache
                self.items_cache[item_id] = item_data

                # Lưu dữ liệu người dùng
                await self.save_user_data(user)

                # Tạo embed thông báo
                embed = create_success_embed(
                    title="✅ Tinh luyện thành công",
                    description=f"Đã tinh luyện {item_data['name']} lên +{refinement + 1}!"
                )

                # Thêm thông tin chỉ số mới
                stats_text = ""
                for stat, value in item_data.get("stats", {}).items():
                    if value != 0:
                        stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

                if stats_text:
                    embed.add_field(name="Chỉ số mới", value=stats_text, inline=False)

                await interaction.response.send_message(embed=embed)
            else:
                # Tinh luyện thất bại
                # Xác định hậu quả dựa trên cấp tinh luyện hiện tại
                if refinement >= 7:
                    # Có khả năng vỡ vụn hoặc giảm cấp
                    failure_roll = random.random()

                    if failure_roll < 0.3 and refinement >= 9:  # 30% vỡ vụn ở cấp 9+
                        # Vỡ vụn - xóa trang bị
                        user.inventory["equipped"][slot_key] = None

                        # Lưu dữ liệu người dùng
                        await self.save_user_data(user)

                        # Tạo embed thông báo
                        embed = create_error_embed(
                            title="💔 Tinh luyện thất bại!",
                            description=f"{item_data['name']} đã vỡ vụn trong quá trình tinh luyện!"
                        )

                        await interaction.response.send_message(embed=embed)
                    elif failure_roll < 0.5:  # 50% (hoặc 20% ở cấp 9+) giảm cấp
                        # Giảm cấp tinh luyện
                        new_refinement = max(0, refinement - 1)
                        item_data["refinement"] = new_refinement

                        # Giảm chỉ số
                        for stat in item_data.get("stats", {}):
                            item_data["stats"][stat] = int(item_data["stats"][stat] / 1.1)

                        # Cập nhật cache
                        self.items_cache[item_id] = item_data

                        # Lưu dữ liệu người dùng
                        await self.save_user_data(user)

                        # Tạo embed thông báo
                        embed = create_error_embed(
                            title="⬇️ Tinh luyện thất bại!",
                            description=f"{item_data['name']} đã giảm xuống +{new_refinement}!"
                        )

                        await interaction.response.send_message(embed=embed)
                    else:  # Không mất cấp
                        # Tạo embed thông báo
                        embed = create_error_embed(
                            title="❌ Tinh luyện thất bại!",
                            description=f"Tinh luyện {item_data['name']} không thành công, nhưng may mắn trang bị không bị ảnh hưởng."
                        )

                        # Lưu dữ liệu người dùng
                        await self.save_user_data(user)

                        await interaction.response.send_message(embed=embed)
                else:
                    # Dưới cấp 7, chỉ thất bại đơn giản
                    # Tạo embed thông báo
                    embed = create_error_embed(
                        title="❌ Tinh luyện thất bại!",
                        description=f"Tinh luyện {item_data['name']} không thành công."
                    )

                    # Lưu dữ liệu người dùng
                    await self.save_user_data(user)

                    await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy tinh luyện trang bị.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    def calculate_refine_cost(self, item_data: Dict[str, Any], current_refinement: int) -> int:
        """Tính chi phí tinh luyện trang bị"""
        # Giá trị cơ bản của vật phẩm
        base_value = item_data.get("value", 100)

        # Hệ số theo độ hiếm
        rarity_multipliers = {
            "common": 1.0,
            "uncommon": 1.5,
            "rare": 2.0,
            "epic": 3.0,
            "legendary": 5.0,
            "mythic": 8.0,
            "divine": 12.0,
            "artifact": 20.0
        }

        rarity = item_data.get("rarity", "common")
        rarity_multiplier = rarity_multipliers.get(rarity, 1.0)

        # Hệ số theo cấp tinh luyện hiện tại
        refinement_multiplier = 1.5 ** current_refinement

        # Tính chi phí
        refine_cost = int(base_value * rarity_multiplier * refinement_multiplier)

        # Đảm bảo chi phí tối thiểu
        return max(100, refine_cost)

    def calculate_refine_success_rate(self, current_refinement: int) -> int:
        """Tính tỷ lệ thành công khi tinh luyện"""
        # Tỷ lệ cơ bản giảm dần theo cấp tinh luyện
        base_rates = {
            0: 100,  # +0 -> +1: 100%
            1: 90,  # +1 -> +2: 90%
            2: 80,  # +2 -> +3: 80%
            3: 70,  # +3 -> +4: 70%
            4: 60,  # +4 -> +5: 60%
            5: 50,  # +5 -> +6: 50%
            6: 40,  # +6 -> +7: 40%
            7: 30,  # +7 -> +8: 30%
            8: 20,  # +8 -> +9: 20%
            9: 10  # +9 -> +10: 10%
        }

        return base_rates.get(current_refinement, 5)  # Mặc định 5% nếu vượt quá +9

    @commands.command(name="socket", aliases=["kham"])
    async def socket_equipment(self, ctx, slot: str):
        """Thêm ổ khảm cho trang bị"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Chuyển đổi tên tiếng Việt sang key tiếng Anh
        slot_mapping = {
            "vũ khí": "weapon",
            "vu khi": "weapon",
            "vukhi": "weapon",
            "weapon": "weapon",

            "áo giáp": "armor",
            "ao giap": "armor",
            "aogiap": "armor",
            "armor": "armor",

            "mũ": "helmet",
            "mu": "helmet",
            "helmet": "helmet",

            "giày": "boots",
            "giay": "boots",
            "boots": "boots",

            "đai": "belt",
            "dai": "belt",
            "belt": "belt",

            "dây chuyền": "necklace",
            "day chuyen": "necklace",
            "daychuyen": "necklace",
            "necklace": "necklace",

            "nhẫn 1": "ring1",
            "nhan 1": "ring1",
            "nhan1": "ring1",
            "ring1": "ring1",

            "nhẫn 2": "ring2",
            "nhan 2": "ring2",
            "nhan2": "ring2",
            "ring2": "ring2",

            "bùa": "talisman",
            "bua": "talisman",
            "talisman": "talisman"
        }

        # Chuyển đổi slot
        slot_key = slot_mapping.get(slot.lower())

        if not slot_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vị trí trang bị không hợp lệ. Các vị trí hợp lệ: vũ khí, áo giáp, mũ, giày, đai, dây chuyền, nhẫn 1, nhẫn 2, bùa."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có trang bị ở vị trí này không
        item_id = user.inventory["equipped"].get(slot_key)

        if not item_id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn không có trang bị ở vị trí {slot}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra số ổ khảm hiện tại
        sockets = item_data.get("sockets", 0)

        if sockets >= 3:
            embed = create_error_embed(
                title="❌ Đã đạt giới hạn",
                description=f"Trang bị {item_data['name']} đã đạt số ổ khảm tối đa (3)."
            )
            return await ctx.send(embed=embed)

        # Tính chi phí thêm ổ khảm
        socket_cost = self.calculate_socket_cost(item_data, sockets)

        # Tính tỷ lệ thành công
        success_rate = self.calculate_socket_success_rate(sockets)

        # Tạo embed xác nhận
        embed = create_embed(
            title=f"💎 Thêm Ổ Khảm - {item_data['name']}",
            description=f"Bạn có muốn thêm ổ khảm thứ {sockets + 1} cho {item_data['name']} không?"
        )

        embed.add_field(name="Chi phí", value=f"{format_number(socket_cost)} linh thạch", inline=True)
        embed.add_field(name="Tỷ lệ thành công", value=f"{success_rate}%", inline=True)

        # Thêm cảnh báo
        if sockets >= 1:
            embed.add_field(
                name="⚠️ Cảnh báo",
                value="Nếu thất bại, trang bị có thể bị hư hỏng, giảm độ bền!",
                inline=False
            )

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Thêm ổ khảm", style=discord.ButtonStyle.primary)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Kiểm tra lại xem có đủ linh thạch không
            if user.resources["spirit_stones"] < socket_cost:
                await interaction.response.send_message(
                    f"Không đủ linh thạch! Bạn cần {format_number(socket_cost)} linh thạch để thêm ổ khảm.",
                    ephemeral=True
                )
                return

            # Trừ linh thạch
            user.spend_spirit_stones(socket_cost)

            # Xác định kết quả
            import random
            success = random.random() * 100 <= success_rate

            if success:
                # Thêm ổ khảm thành công
                item_data["sockets"] = sockets + 1

                # Cập nhật cache
                self.items_cache[item_id] = item_data

                # Lưu dữ liệu người dùng
                await self.save_user_data(user)

                # Tạo embed thông báo
                embed = create_success_embed(
                    title="✅ Thêm ổ khảm thành công",
                    description=f"Đã thêm ổ khảm thứ {sockets + 1} cho {item_data['name']}!"
                )

                await interaction.response.send_message(embed=embed)
            else:
                # Thêm ổ khảm thất bại
                # Giảm độ bền trang bị
                durability = item_data.get("durability", 100)
                max_durability = item_data.get("max_durability", 100)

                # Giảm 20-50% độ bền
                durability_loss = random.randint(20, 50) / 100
                new_durability = max(1, int(durability * (1 - durability_loss)))
                item_data["durability"] = new_durability

                # Cập nhật cache
                self.items_cache[item_id] = item_data

                # Lưu dữ liệu người dùng
                await self.save_user_data(user)

                # Tạo embed thông báo
                embed = create_error_embed(
                    title="❌ Thêm ổ khảm thất bại!",
                    description=f"Thêm ổ khảm cho {item_data['name']} không thành công."
                )

                embed.add_field(
                    name="Hư hỏng",
                    value=f"Độ bền giảm từ {durability} xuống {new_durability} ({int(durability_loss * 100)}%)",
                    inline=False
                )

                await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy thêm ổ khảm.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    def calculate_socket_cost(self, item_data: Dict[str, Any], current_sockets: int) -> int:
        """Tính chi phí thêm ổ khảm"""
        # Giá trị cơ bản của vật phẩm
        base_value = item_data.get("value", 100)

        # Hệ số theo độ hiếm
        rarity_multipliers = {
            "common": 1.0,
            "uncommon": 1.5,
            "rare": 2.0,
            "epic": 3.0,
            "legendary": 5.0,
            "mythic": 8.0,
            "divine": 12.0,
            "artifact": 20.0
        }

        rarity = item_data.get("rarity", "common")
        rarity_multiplier = rarity_multipliers.get(rarity, 1.0)

        # Hệ số theo số ổ khảm hiện tại
        socket_multiplier = 2.0 ** current_sockets

        # Tính chi phí
        socket_cost = int(base_value * rarity_multiplier * socket_multiplier * 2)

        # Đảm bảo chi phí tối thiểu
        return max(200, socket_cost)

    def calculate_socket_success_rate(self, current_sockets: int) -> int:
        """Tính tỷ lệ thành công khi thêm ổ khảm"""
        # Tỷ lệ cơ bản giảm dần theo số ổ khảm hiện tại
        base_rates = {
            0: 80,  # Ổ đầu tiên: 80%
            1: 50,  # Ổ thứ hai: 50%
            2: 30  # Ổ thứ ba: 30%
        }

        return base_rates.get(current_sockets, 10)  # Mặc định 10% nếu vượt quá 2 ổ

    @commands.command(name="gem", aliases=["kham_da"])
    async def gem_equipment(self, ctx, slot: str, gem_index: int = None):
        """Khảm đá vào trang bị"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Chuyển đổi tên tiếng Việt sang key tiếng Anh
        slot_mapping = {
            "vũ khí": "weapon",
            "vu khi": "weapon",
            "vukhi": "weapon",
            "weapon": "weapon",

            "áo giáp": "armor",
            "ao giap": "armor",
            "aogiap": "armor",
            "armor": "armor",

            "mũ": "helmet",
            "mu": "helmet",
            "helmet": "helmet",

            "giày": "boots",
            "giay": "boots",
            "boots": "boots",

            "đai": "belt",
            "dai": "belt",
            "belt": "belt",

            "dây chuyền": "necklace",
            "day chuyen": "necklace",
            "daychuyen": "necklace",
            "necklace": "necklace",

            "nhẫn 1": "ring1",
            "nhan 1": "ring1",
            "nhan1": "ring1",
            "ring1": "ring1",

            "nhẫn 2": "ring2",
            "nhan 2": "ring2",
            "nhan2": "ring2",
            "ring2": "ring2",

            "bùa": "talisman",
            "bua": "talisman",
            "talisman": "talisman"
        }

        # Chuyển đổi slot
        slot_key = slot_mapping.get(slot.lower())

        if not slot_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vị trí trang bị không hợp lệ. Các vị trí hợp lệ: vũ khí, áo giáp, mũ, giày, đai, dây chuyền, nhẫn 1, nhẫn 2, bùa."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có trang bị ở vị trí này không
        item_id = user.inventory["equipped"].get(slot_key)

        if not item_id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn không có trang bị ở vị trí {slot}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra số ổ khảm
        sockets = item_data.get("sockets", 0)
        gems = item_data.get("gems", [])

        if sockets == 0:
            embed = create_error_embed(
                title="❌ Không có ổ khảm",
                description=f"Trang bị {item_data['name']} không có ổ khảm nào. Hãy thêm ổ khảm trước bằng lệnh `!socket`."
            )
            return await ctx.send(embed=embed)

        if len(gems) >= sockets:
            embed = create_error_embed(
                title="❌ Đã khảm đầy",
                description=f"Trang bị {item_data['name']} đã khảm đầy {sockets}/{sockets} ổ."
            )
            return await ctx.send(embed=embed)

        # Nếu không chỉ định gem_index, hiển thị danh sách đá có thể khảm
        if gem_index is None:
            # Tìm tất cả đá khảm trong kho đồ
            gem_items = []

            for i, item_entry in enumerate(user.inventory["items"]):
                item_id = item_entry["item_id"]
                item_data = self.get_item_data(item_id)

                if item_data and item_data.get("item_type") == "material" and "gem" in item_data.get("material_type",
                                                                                                     ""):
                    gem_items.append({
                        "index": i + 1,
                        "id": item_id,
                        "name": item_data["name"],
                        "description": item_data.get("description", ""),
                        "quantity": item_entry["quantity"],
                        "rarity": item_data.get("rarity", "common"),
                        "stats": item_data.get("stats", {})
                    })

            if not gem_items:
                embed = create_error_embed(
                    title="❌ Không có đá khảm",
                    description="Bạn không có đá khảm nào trong kho đồ."
                )
                return await ctx.send(embed=embed)

            # Tạo embed hiển thị danh sách đá khảm
            embed = create_embed(
                title=f"💎 Khảm Đá - {item_data['name']}",
                description=f"Chọn đá khảm để khảm vào ổ thứ {len(gems) + 1}/{sockets}:"
            )

            # Thêm thông tin từng loại đá
            for gem in gem_items:
                # Định dạng tên đá theo độ hiếm
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

                rarity_icon = rarity_icons.get(gem["rarity"], "⚪")
                gem_name = f"{rarity_icon} {gem['name']}"

                # Hiển thị chỉ số
                stats_text = ""
                for stat, value in gem["stats"].items():
                    if value != 0:
                        stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

                if not stats_text:
                    stats_text = "*Không có chỉ số*"

                embed.add_field(
                    name=f"{gem['index']}. {gem_name} (x{gem['quantity']})",
                    value=f"{gem['description']}\n{stats_text}",
                    inline=False
                )

            # Thêm hướng dẫn sử dụng
            embed.set_footer(text="Sử dụng !gem <vị trí trang bị> <số thứ tự đá> để khảm đá")

            # Gửi embed
            await ctx.send(embed=embed)
            return

        # Kiểm tra chỉ số đá hợp lệ
        if gem_index < 1 or gem_index > len(user.inventory["items"]):
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Chỉ số đá không hợp lệ. Phải từ 1 đến {len(user.inventory['items'])}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin đá
        gem_entry = user.inventory["items"][gem_index - 1]
        gem_id = gem_entry["item_id"]
        gem_data = self.get_item_data(gem_id)

        if not gem_data or gem_data.get("item_type") != "material" or "gem" not in gem_data.get("material_type", ""):
            embed = create_error_embed(
                title="❌ Không phải đá khảm",
                description="Vật phẩm bạn chọn không phải là đá khảm."
            )
            return await ctx.send(embed=embed)

        # Tính chi phí khảm đá
        gem_cost = self.calculate_gem_cost(item_data, gem_data)

        # Tạo embed xác nhận
        embed = create_embed(
            title=f"💎 Khảm Đá - {item_data['name']}",
            description=f"Bạn có muốn khảm {gem_data['name']} vào ổ thứ {len(gems) + 1}/{sockets} của {item_data['name']} không?"
        )

        # Hiển thị chỉ số của đá
        stats_text = ""
        for stat, value in gem_data.get("stats", {}).items():
            if value != 0:
                stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

        if stats_text:
            embed.add_field(name="Chỉ số đá", value=stats_text, inline=False)

        embed.add_field(name="Chi phí", value=f"{format_number(gem_cost)} linh thạch", inline=True)

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Khảm đá", style=discord.ButtonStyle.primary)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Kiểm tra lại xem có đủ linh thạch không
            if user.resources["spirit_stones"] < gem_cost:
                await interaction.response.send_message(
                    f"Không đủ linh thạch! Bạn cần {format_number(gem_cost)} linh thạch để khảm đá.",
                    ephemeral=True
                )
                return

            # Kiểm tra lại xem còn đá không
            if not user.has_item(gem_id):
                await interaction.response.send_message(
                    "Bạn không còn đá khảm này trong kho đồ!",
                    ephemeral=True
                )
                return

            # Trừ linh thạch
            user.spend_spirit_stones(gem_cost)

            # Xóa đá khỏi kho đồ
            user.remove_item(gem_id, 1)

            # Thêm đá vào trang bị
            if "gems" not in item_data:
                item_data["gems"] = []

            item_data["gems"].append(gem_id)

            # Cập nhật chỉ số trang bị từ đá
            for stat, value in gem_data.get("stats", {}).items():
                if stat not in item_data["stats"]:
                    item_data["stats"][stat] = 0

                item_data["stats"][stat] += value

            # Cập nhật cache
            self.items_cache[item_id] = item_data

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Khảm đá thành công",
                description=f"Đã khảm {gem_data['name']} vào ổ thứ {len(item_data['gems'])}/{sockets} của {item_data['name']}!"
            )

            # Hiển thị chỉ số mới
            stats_text = ""
            for stat, value in item_data["stats"].items():
                if value != 0:
                    stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

            if stats_text:
                embed.add_field(name="Chỉ số mới", value=stats_text, inline=False)

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy khảm đá.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    def calculate_gem_cost(self, item_data: Dict[str, Any], gem_data: Dict[str, Any]) -> int:
        """Tính chi phí khảm đá"""
        # Giá trị cơ bản của đá
        base_value = gem_data.get("value", 50)

        # Hệ số theo độ hiếm của đá
        gem_rarity_multipliers = {
            "common": 1.0,
            "uncommon": 1.5,
            "rare": 2.0,
            "epic": 3.0,
            "legendary": 5.0,
            "mythic": 8.0,
            "divine": 12.0,
            "artifact": 20.0
        }

        gem_rarity = gem_data.get("rarity", "common")
        gem_rarity_multiplier = gem_rarity_multipliers.get(gem_rarity, 1.0)

        # Hệ số theo độ hiếm của trang bị
        item_rarity = item_data.get("rarity", "common")
        item_rarity_multiplier = gem_rarity_multipliers.get(item_rarity, 1.0)

        # Tính chi phí
        gem_cost = int(base_value * gem_rarity_multiplier * item_rarity_multiplier)

        # Đảm bảo chi phí tối thiểu
        return max(100, gem_cost)

    @commands.command(name="ungem", aliases=["thao_da"])
    async def ungem_equipment(self, ctx, slot: str, socket_index: int = None):
        """Tháo đá khảm khỏi trang bị"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Chuyển đổi tên tiếng Việt sang key tiếng Anh
        slot_mapping = {
            "vũ khí": "weapon",
            "vu khi": "weapon",
            "vukhi": "weapon",
            "weapon": "weapon",

            "áo giáp": "armor",
            "ao giap": "armor",
            "aogiap": "armor",
            "armor": "armor",

            "mũ": "helmet",
            "mu": "helmet",
            "helmet": "helmet",

            "giày": "boots",
            "giay": "boots",
            "boots": "boots",

            "đai": "belt",
            "dai": "belt",
            "belt": "belt",

            "dây chuyền": "necklace",
            "day chuyen": "necklace",
            "daychuyen": "necklace",
            "necklace": "necklace",

            "nhẫn 1": "ring1",
            "nhan 1": "ring1",
            "nhan1": "ring1",
            "ring1": "ring1",

            "nhẫn 2": "ring2",
            "nhan 2": "ring2",
            "nhan2": "ring2",
            "ring2": "ring2",

            "bùa": "talisman",
            "bua": "talisman",
            "talisman": "talisman"
        }

        # Chuyển đổi slot
        slot_key = slot_mapping.get(slot.lower())

        if not slot_key:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Vị trí trang bị không hợp lệ. Các vị trí hợp lệ: vũ khí, áo giáp, mũ, giày, đai, dây chuyền, nhẫn 1, nhẫn 2, bùa."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có trang bị ở vị trí này không
        item_id = user.inventory["equipped"].get(slot_key)

        if not item_id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Bạn không có trang bị ở vị trí {slot}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin vật phẩm
        item_data = self.get_item_data(item_id)

        if not item_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra đá đã khảm
        gems = item_data.get("gems", [])

        if not gems:
            embed = create_error_embed(
                title="❌ Không có đá khảm",
                description=f"Trang bị {item_data['name']} không có đá khảm nào."
            )
            return await ctx.send(embed=embed)

        # Nếu không chỉ định socket_index, hiển thị danh sách đá đã khảm
        if socket_index is None:
            # Tạo embed hiển thị danh sách đá đã khảm
            embed = create_embed(
                title=f"💎 Đá Đã Khảm - {item_data['name']}",
                description=f"Danh sách đá đã khảm vào {item_data['name']}:"
            )

            # Thêm thông tin từng viên đá
            for i, gem_id in enumerate(gems, 1):
                gem_data = self.get_item_data(gem_id)

                if gem_data:
                    # Định dạng tên đá theo độ hiếm
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

                    rarity_icon = rarity_icons.get(gem_data.get("rarity", "common"), "⚪")
                    gem_name = f"{rarity_icon} {gem_data['name']}"

                    # Hiển thị chỉ số
                    stats_text = ""
                    for stat, value in gem_data.get("stats", {}).items():
                        if value != 0:
                            stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

                    if not stats_text:
                        stats_text = "*Không có chỉ số*"

                    embed.add_field(
                        name=f"Ổ {i}: {gem_name}",
                        value=f"{gem_data.get('description', '')}\n{stats_text}",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"Ổ {i}: Đá không xác định",
                        value=f"ID: {gem_id}",
                        inline=False
                    )

            # Thêm hướng dẫn sử dụng
            embed.set_footer(text="Sử dụng !ungem <vị trí trang bị> <số thứ tự ổ> để tháo đá")

            # Gửi embed
            await ctx.send(embed=embed)
            return

        # Kiểm tra chỉ số ổ hợp lệ
        if socket_index < 1 or socket_index > len(gems):
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Chỉ số ổ không hợp lệ. Phải từ 1 đến {len(gems)}."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin đá
        gem_id = gems[socket_index - 1]
        gem_data = self.get_item_data(gem_id)

        if not gem_data:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về đá có ID: {gem_id}."
            )
            return await ctx.send(embed=embed)

        # Tính chi phí tháo đá
        ungem_cost = self.calculate_ungem_cost(item_data, gem_data)

        # Tạo embed xác nhận
        embed = create_embed(
            title=f"💎 Tháo Đá - {item_data['name']}",
            description=f"Bạn có muốn tháo {gem_data['name']} khỏi ổ thứ {socket_index}/{len(gems)} của {item_data['name']} không?"
        )

        embed.add_field(name="Chi phí", value=f"{format_number(ungem_cost)} linh thạch", inline=True)
        embed.add_field(
            name="Lưu ý",
            value="Khi tháo đá, bạn sẽ nhận lại đá khảm, nhưng các ổ khảm sau sẽ bị dịch lên.",
            inline=False
        )

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Tháo đá", style=discord.ButtonStyle.primary)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Kiểm tra lại xem có đủ linh thạch không
            if user.resources["spirit_stones"] < ungem_cost:
                await interaction.response.send_message(
                    f"Không đủ linh thạch! Bạn cần {format_number(ungem_cost)} linh thạch để tháo đá.",
                    ephemeral=True
                )
                return

            # Trừ linh thạch
            user.spend_spirit_stones(ungem_cost)

            # Thêm đá vào kho đồ
            user.add_item(gem_id, 1)

            # Trừ chỉ số từ đá
            for stat, value in gem_data.get("stats", {}).items():
                if stat in item_data["stats"]:
                    item_data["stats"][stat] -= value

                    # Đảm bảo chỉ số không âm
                    if item_data["stats"][stat] <= 0:
                        item_data["stats"][stat] = 0

            # Xóa đá khỏi trang bị
            item_data["gems"].pop(socket_index - 1)

            # Cập nhật cache
            self.items_cache[item_id] = item_data

            # Lưu dữ liệu người dùng
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Tháo đá thành công",
                description=f"Đã tháo {gem_data['name']} khỏi {item_data['name']} và thêm vào kho đồ!"
            )

            # Hiển thị chỉ số mới
            stats_text = ""
            for stat, value in item_data["stats"].items():
                if value != 0:
                    stats_text += f"• {self.translate_stat(stat)}: +{value}\n"

            if stats_text:
                embed.add_field(name="Chỉ số mới", value=stats_text, inline=False)

            await interaction.response.send_message(embed=embed)

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy tháo đá.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    def calculate_ungem_cost(self, item_data: Dict[str, Any], gem_data: Dict[str, Any]) -> int:
        """Tính chi phí tháo đá"""
        # Giá trị cơ bản của đá
        base_value = gem_data.get("value", 50)

        # Hệ số theo độ hiếm của đá
        gem_rarity_multipliers = {
            "common": 0.5,
            "uncommon": 0.75,
            "rare": 1.0,
            "epic": 1.5,
            "legendary": 2.0,
            "mythic": 3.0,
            "divine": 5.0,
            "artifact": 10.0
        }

        gem_rarity = gem_data.get("rarity", "common")
        gem_rarity_multiplier = gem_rarity_multipliers.get(gem_rarity, 1.0)

        # Tính chi phí
        ungem_cost = int(base_value * gem_rarity_multiplier * 0.5)  # 50% giá trị đá

        # Đảm bảo chi phí tối thiểu
        return max(50, ungem_cost)

    def translate_item_type(self, item_type: str) -> str:
        """Chuyển đổi loại vật phẩm sang tiếng Việt"""
        translations = {
            "equipment": "Trang bị",
            "consumable": "Tiêu hao",
            "material": "Nguyên liệu",
            "treasure": "Bảo vật",
            "cultivation_resource": "Tài nguyên tu luyện",
            "talisman": "Phù lục",
            "pill": "Đan dược",
            "spirit_stone": "Linh thạch",
            "skill_book": "Sách kỹ năng",
            "quest_item": "Vật phẩm nhiệm vụ"
        }

        return translations.get(item_type, "Không xác định")

    def translate_rarity(self, rarity: str) -> str:
        """Chuyển đổi độ hiếm sang tiếng Việt"""
        translations = {
            "common": "Phổ thông",
            "uncommon": "Thường gặp",
            "rare": "Hiếm",
            "epic": "Sử thi",
            "legendary": "Huyền thoại",
            "mythic": "Thần thoại",
            "divine": "Thần thánh",
            "artifact": "Thần khí"
        }

        return translations.get(rarity, "Không xác định")

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

    def translate_skill_type(self, skill_type: str) -> str:
        """Chuyển đổi loại kỹ năng sang tiếng Việt"""
        translations = {
            "active": "Chủ động",
            "passive": "Bị động",
            "cultivation": "Tu luyện",
            "crafting": "Chế tạo",
            "movement": "Di chuyển",
            "support": "Hỗ trợ",
            "attack": "Tấn công",
            "defense": "Phòng thủ",
            "healing": "Hồi phục",
            "control": "Khống chế",
            "summoning": "Triệu hồi",
            "transformation": "Biến hình"
        }

        return translations.get(skill_type, "Không xác định")


def setup(bot):
    bot.add_cog(InventoryCog(bot))
