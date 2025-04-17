import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
import json
import os
from typing import Dict, List

from database.mongo_handler import get_user_or_create, update_user, add_user_linh_thach, add_user_exp
from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMOJI_EXP, EMOJI_HEALTH, EMOJI_ATTACK,
    EMOJI_DEFENSE, EMOJI_LINH_THACH, get_power_multiplier
)

# Cấu hình logging
logger = logging.getLogger("tutien-bot.monster")


class MonsterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_monsters()
        self.load_bosses()

    def load_monsters(self):
        """Tải dữ liệu quái vật từ tệp JSON hoặc tạo mới nếu chưa có"""
        try:
            if os.path.exists("data/monsters.json"):
                with open("data/monsters.json", "r", encoding="utf-8") as f:
                    self.monsters = json.load(f)
                logger.info(f"Đã tải {len(self.monsters)} quái vật từ tệp JSON")
            else:
                # Tạo dữ liệu mặc định
                self.monsters = [
                    {"id": 1, "name": "Yêu Lang", "level": 1, "health": 100, "attack": 15, "defense": 5,
                     "exp_reward": 10, "linh_thach_min": 5, "linh_thach_max": 15, "drop_rate": 0.3,
                     "drops": [{"item_id": "healing_potion", "chance": 0.2}]},
                    {"id": 2, "name": "Hắc Hổ", "level": 3, "health": 150, "attack": 25, "defense": 10,
                     "exp_reward": 20, "linh_thach_min": 10, "linh_thach_max": 25, "drop_rate": 0.4,
                     "drops": [{"item_id": "strength_potion", "chance": 0.15}]},
                    {"id": 3, "name": "Độc Xà", "level": 5, "health": 200, "attack": 30, "defense": 15,
                     "exp_reward": 30, "linh_thach_min": 15, "linh_thach_max": 35, "drop_rate": 0.5,
                     "drops": [{"item_id": "poison_essence", "chance": 0.25}]},
                    {"id": 4, "name": "Thiết Giáp Thú", "level": 8, "health": 250, "attack": 35, "defense": 25,
                     "exp_reward": 45, "linh_thach_min": 20, "linh_thach_max": 50, "drop_rate": 0.4,
                     "drops": [{"item_id": "iron_scale", "chance": 0.3}]},
                    {"id": 5, "name": "U Linh", "level": 10, "health": 300, "attack": 40, "defense": 20,
                     "exp_reward": 60, "linh_thach_min": 30, "linh_thach_max": 70, "drop_rate": 0.45,
                     "drops": [{"item_id": "spirit_essence", "chance": 0.2}]},
                    {"id": 6, "name": "Hỏa Kỳ Lân", "level": 12, "health": 350, "attack": 50, "defense": 30,
                     "exp_reward": 80, "linh_thach_min": 40, "linh_thach_max": 90, "drop_rate": 0.5,
                     "drops": [{"item_id": "fire_crystal", "chance": 0.2}]},
                    {"id": 7, "name": "Bạch Cốt Ma", "level": 15, "health": 400, "attack": 60, "defense": 35,
                     "exp_reward": 100, "linh_thach_min": 50, "linh_thach_max": 110, "drop_rate": 0.55,
                     "drops": [{"item_id": "bone_fragment", "chance": 0.25}]},
                    {"id": 8, "name": "Thâm Hải Chi Long", "level": 18, "health": 500, "attack": 70, "defense": 40,
                     "exp_reward": 130, "linh_thach_min": 60, "linh_thach_max": 140, "drop_rate": 0.6,
                     "drops": [{"item_id": "dragon_scale", "chance": 0.15}]},
                    {"id": 9, "name": "Huyết Yêu", "level": 20, "health": 600, "attack": 80, "defense": 50,
                     "exp_reward": 160, "linh_thach_min": 70, "linh_thach_max": 170, "drop_rate": 0.65,
                     "drops": [{"item_id": "blood_essence", "chance": 0.2}]},
                    {"id": 10, "name": "Thiên Ma", "level": 25, "health": 700, "attack": 90, "defense": 60,
                     "exp_reward": 200, "linh_thach_min": 80, "linh_thach_max": 200, "drop_rate": 0.7,
                     "drops": [{"item_id": "demon_heart", "chance": 0.1}]},
                ]

                # Tạo thư mục data nếu chưa tồn tại
                os.makedirs("data", exist_ok=True)

                # Lưu vào tệp JSON
                with open("data/monsters.json", "w", encoding="utf-8") as f:
                    json.dump(self.monsters, f, ensure_ascii=False, indent=4)

                logger.info(f"Đã tạo và lưu {len(self.monsters)} quái vật mặc định")
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu quái vật: {e}")
            # Dữ liệu mặc định nếu có lỗi
            self.monsters = [
                {"id": 1, "name": "Yêu Lang", "level": 1, "health": 100, "attack": 15, "defense": 5, "exp_reward": 10,
                 "linh_thach_min": 5, "linh_thach_max": 15, "drop_rate": 0.3,
                 "drops": [{"item_id": "healing_potion", "chance": 0.2}]},
                {"id": 2, "name": "Hắc Hổ", "level": 3, "health": 150, "attack": 25, "defense": 10, "exp_reward": 20,
                 "linh_thach_min": 10, "linh_thach_max": 25, "drop_rate": 0.4,
                 "drops": [{"item_id": "strength_potion", "chance": 0.15}]},
            ]

    def load_bosses(self):
        """Tải dữ liệu boss từ tệp JSON hoặc tạo mới nếu chưa có"""
        try:
            if os.path.exists("data/bosses.json"):
                with open("data/bosses.json", "r", encoding="utf-8") as f:
                    self.bosses = json.load(f)
                logger.info(f"Đã tải {len(self.bosses)} boss từ tệp JSON")
            else:
                # Tạo dữ liệu mặc định
                self.bosses = [
                    {"id": 1, "name": "Hắc Long Vương", "level": 15, "health": 1000, "attack": 120, "defense": 80,
                     "exp_reward": 300, "linh_thach_min": 100, "linh_thach_max": 300, "drop_rate": 0.8,
                     "drops": [{"item_id": "dragon_heart", "chance": 0.3}, {"item_id": "dragon_scale", "chance": 0.5}]},
                    {"id": 2, "name": "Cửu Vĩ Yêu Hồ", "level": 18, "health": 1500, "attack": 150, "defense": 100,
                     "exp_reward": 500, "linh_thach_min": 150, "linh_thach_max": 400, "drop_rate": 0.85,
                     "drops": [{"item_id": "fox_tail", "chance": 0.4}, {"item_id": "fox_fur", "chance": 0.6}]},
                    {"id": 3, "name": "Ma Đế", "level": 20, "health": 2000, "attack": 180, "defense": 120,
                     "exp_reward": 700, "linh_thach_min": 200, "linh_thach_max": 500, "drop_rate": 0.9,
                     "drops": [{"item_id": "demon_soul", "chance": 0.3}, {"item_id": "demon_horn", "chance": 0.5}]},
                    {"id": 4, "name": "Tà Thần", "level": 25, "health": 3000, "attack": 250, "defense": 150,
                     "exp_reward": 1000, "linh_thach_min": 300, "linh_thach_max": 700, "drop_rate": 0.95,
                     "drops": [{"item_id": "evil_core", "chance": 0.2}, {"item_id": "god_blood", "chance": 0.4}]},
                    {"id": 5, "name": "Thiên Ngoại Yêu Thi", "level": 30, "health": 5000, "attack": 350, "defense": 200,
                     "exp_reward": 1500, "linh_thach_min": 500, "linh_thach_max": 1000, "drop_rate": 1.0,
                     "drops": [{"item_id": "cosmic_essence", "chance": 0.1},
                               {"item_id": "star_fragment", "chance": 0.3}]},
                ]

                # Tạo thư mục data nếu chưa tồn tại
                os.makedirs("data", exist_ok=True)

                # Lưu vào tệp JSON
                with open("data/bosses.json", "w", encoding="utf-8") as f:
                    json.dump(self.bosses, f, ensure_ascii=False, indent=4)

                logger.info(f"Đã tạo và lưu {len(self.bosses)} boss mặc định")
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu boss: {e}")
            # Dữ liệu mặc định nếu có lỗi
            self.bosses = [
                {"id": 1, "name": "Hắc Long Vương", "level": 15, "health": 1000, "attack": 120, "defense": 80,
                 "exp_reward": 300, "linh_thach_min": 100, "linh_thach_max": 300, "drop_rate": 0.8,
                 "drops": [{"item_id": "dragon_heart", "chance": 0.3}, {"item_id": "dragon_scale", "chance": 0.5}]},
            ]

    def get_suitable_monsters(self, user_realm_id):
        """Lấy danh sách quái vật phù hợp với cảnh giới của người dùng"""
        # Xác định phạm vi cấp độ quái vật
        min_level = max(1, user_realm_id // 3)
        max_level = min(30, min_level + 5)

        # Lọc quái vật trong phạm vi
        suitable_monsters = [m for m in self.monsters if min_level <= m["level"] <= max_level]

        # Nếu không có quái vật phù hợp, lấy con yếu nhất
        if not suitable_monsters:
            return [self.monsters[0]]

        return suitable_monsters

    def get_suitable_bosses(self, user_realm_id):
        """Lấy danh sách boss phù hợp với cảnh giới của người dùng"""
        # Xác định phạm vi cấp độ boss
        min_level = max(10, user_realm_id)

        # Lọc boss trong phạm vi
        suitable_bosses = [b for b in self.bosses if b["level"] >= min_level]

        # Nếu không có boss phù hợp, lấy con yếu nhất
        if not suitable_bosses:
            return [self.bosses[0]]

        return suitable_bosses

    def get_random_monster(self, user_realm_id):
        """Lấy một quái vật ngẫu nhiên phù hợp với cảnh giới của người dùng"""
        suitable_monsters = self.get_suitable_monsters(user_realm_id)
        return random.choice(suitable_monsters)

    def get_random_boss(self, user_realm_id):
        """Lấy một boss ngẫu nhiên phù hợp với cảnh giới của người dùng"""
        suitable_bosses = self.get_suitable_bosses(user_realm_id)
        return random.choice(suitable_bosses)

    @commands.command(name="quaivat", aliases=["qv", "monster", "monsters"])
    async def list_monsters(self, ctx):
        """Liệt kê các loại quái vật trong khu vực"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Lấy danh sách quái vật phù hợp
        suitable_monsters = self.get_suitable_monsters(user["realm_id"])

        # Tạo embed
        embed = discord.Embed(
            title="Quái Vật Trong Khu Vực",
            description=f"Danh sách quái vật phù hợp với cảnh giới **{CULTIVATION_REALMS[user['realm_id']]['name']}**",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng quái vật
        for monster in suitable_monsters:
            embed.add_field(
                name=f"{monster['name']} [Cấp {monster['level']}]",
                value=(
                    f"{EMOJI_HEALTH} HP: {monster['health']}\n"
                    f"{EMOJI_ATTACK} Tấn công: {monster['attack']}\n"
                    f"{EMOJI_DEFENSE} Phòng thủ: {monster['defense']}\n"
                    f"{EMOJI_EXP} Kinh nghiệm: {monster['exp_reward']}\n"
                    f"{EMOJI_LINH_THACH} Linh thạch: {monster['linh_thach_min']}-{monster['linh_thach_max']}"
                ),
                inline=True
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="boss", aliases=["bosses"])
    async def list_bosses(self, ctx):
        """Liệt kê các loại boss trong khu vực"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Lấy danh sách boss phù hợp
        suitable_bosses = self.get_suitable_bosses(user["realm_id"])

        # Tạo embed
        embed = discord.Embed(
            title="Boss Trong Khu Vực",
            description=f"Danh sách boss phù hợp với cảnh giới **{CULTIVATION_REALMS[user['realm_id']]['name']}**",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng boss
        for boss in suitable_bosses:
            embed.add_field(
                name=f"{boss['name']} [Cấp {boss['level']}]",
                value=(
                    f"{EMOJI_HEALTH} HP: {boss['health']}\n"
                    f"{EMOJI_ATTACK} Tấn công: {boss['attack']}\n"
                    f"{EMOJI_DEFENSE} Phòng thủ: {boss['defense']}\n"
                    f"{EMOJI_EXP} Kinh nghiệm: {boss['exp_reward']}\n"
                    f"{EMOJI_LINH_THACH} Linh thạch: {boss['linh_thach_min']}-{boss['linh_thach_max']}"
                ),
                inline=True
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="timquai", aliases=["tq", "find"])
    async def find_monster(self, ctx):
        """Tìm kiếm quái vật ngẫu nhiên trong khu vực"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Tìm quái vật ngẫu nhiên
        monster = self.get_random_monster(user["realm_id"])

        # Tạo embed
        embed = discord.Embed(
            title=f"Phát Hiện: {monster['name']}",
            description=f"Bạn đã tìm thấy **{monster['name']}** [Cấp {monster['level']}] trong khu vực!",
            color=EMBED_COLOR
        )

        # Thêm thông tin quái vật
        embed.add_field(
            name="Thông Tin",
            value=(
                f"{EMOJI_HEALTH} HP: {monster['health']}\n"
                f"{EMOJI_ATTACK} Tấn công: {monster['attack']}\n"
                f"{EMOJI_DEFENSE} Phòng thủ: {monster['defense']}\n"
                f"{EMOJI_EXP} Kinh nghiệm: {monster['exp_reward']}\n"
                f"{EMOJI_LINH_THACH} Linh thạch: {monster['linh_thach_min']}-{monster['linh_thach_max']}"
            ),
            inline=False
        )

        # Thêm hướng dẫn
        embed.add_field(
            name="Hành Động",
            value="Sử dụng lệnh `!danhquai` để tiến hành tấn công!",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="timboss", aliases=["tb", "findboss"])
    async def find_boss(self, ctx):
        """Tìm kiếm boss ngẫu nhiên trong khu vực"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Tìm boss ngẫu nhiên
        boss = self.get_random_boss(user["realm_id"])

        # Tạo embed
        embed = discord.Embed(
            title=f"⚠️ Phát Hiện: {boss['name']}",
            description=f"Bạn đã tìm thấy **{boss['name']}** [Cấp {boss['level']}] trong khu vực!",
            color=discord.Color.red()
        )

        # Thêm thông tin boss
        embed.add_field(
            name="Thông Tin",
            value=(
                f"{EMOJI_HEALTH} HP: {boss['health']}\n"
                f"{EMOJI_ATTACK} Tấn công: {boss['attack']}\n"
                f"{EMOJI_DEFENSE} Phòng thủ: {boss['defense']}\n"
                f"{EMOJI_EXP} Kinh nghiệm: {boss['exp_reward']}\n"
                f"{EMOJI_LINH_THACH} Linh thạch: {boss['linh_thach_min']}-{boss['linh_thach_max']}"
            ),
            inline=False
        )

        # Thêm hướng dẫn
        embed.add_field(
            name="Hành Động",
            value="Sử dụng lệnh `!danhboss` để tiến hành tấn công!",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MonsterCog(bot))