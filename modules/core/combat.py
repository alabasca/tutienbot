import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
import math
from typing import Dict, List

from database.mongo_handler import get_user_or_create, update_user, add_user_linh_thach, add_user_exp
from config import (
    CULTIVATION_REALMS, COMBAT_COOLDOWN, DANHQUAI_COOLDOWN, DANHBOSS_COOLDOWN,
    QUAI_MIN_REWARD, QUAI_MAX_REWARD, BOSS_MIN_REWARD, BOSS_MAX_REWARD,
    COMBAT_WIN_REWARD, EMBED_COLOR, EMBED_COLOR_SUCCESS, EMBED_COLOR_ERROR,
    EMOJI_ATTACK, EMOJI_DEFENSE, EMOJI_HEALTH, EMOJI_LINH_THACH, EMOJI_EXP,
    get_power_multiplier
)

# Cấu hình logging
logger = logging.getLogger("tutien-bot.combat")


class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Danh sách quái vật
        self.monsters = [
            {"name": "Yêu Lang", "level": 1, "health": 100, "attack": 15, "defense": 5},
            {"name": "Hắc Hổ", "level": 2, "health": 150, "attack": 25, "defense": 10},
            {"name": "Độc Xà", "level": 3, "health": 200, "attack": 30, "defense": 15},
            {"name": "Thiết Giáp Thú", "level": 4, "health": 250, "attack": 35, "defense": 25},
            {"name": "U Linh", "level": 5, "health": 300, "attack": 40, "defense": 20},
            {"name": "Hỏa Kỳ Lân", "level": 6, "health": 350, "attack": 50, "defense": 30},
            {"name": "Bạch Cốt Ma", "level": 7, "health": 400, "attack": 60, "defense": 35},
            {"name": "Thâm Hải Chi Long", "level": 8, "health": 500, "attack": 70, "defense": 40},
            {"name": "Huyết Yêu", "level": 9, "health": 600, "attack": 80, "defense": 50},
            {"name": "Thiên Ma", "level": 10, "health": 700, "attack": 90, "defense": 60},
        ]

        # Danh sách boss
        self.bosses = [
            {"name": "Hắc Long Vương", "level": 15, "health": 1000, "attack": 120, "defense": 80},
            {"name": "Cửu Vĩ Yêu Hồ", "level": 18, "health": 1500, "attack": 150, "defense": 100},
            {"name": "Ma Đế", "level": 20, "health": 2000, "attack": 180, "defense": 120},
            {"name": "Tà Thần", "level": 25, "health": 3000, "attack": 250, "defense": 150},
            {"name": "Thiên Ngoại Yêu Thi", "level": 30, "health": 5000, "attack": 350, "defense": 200},
        ]

    def get_random_monster(self, user_realm_id):
        """Lấy một quái vật ngẫu nhiên dựa trên cảnh giới của người dùng"""
        # Xác định phạm vi cấp độ quái vật
        min_level = max(1, user_realm_id // 3)
        max_level = min(len(self.monsters), min_level + 3)

        # Lọc quái vật trong phạm vi
        suitable_monsters = [m for m in self.monsters if min_level <= m["level"] <= max_level]

        # Nếu không có quái vật phù hợp, lấy con yếu nhất
        if not suitable_monsters:
            return self.monsters[0]

        # Trả về quái vật ngẫu nhiên
        return random.choice(suitable_monsters)

    def get_random_boss(self, user_realm_id):
        """Lấy một boss ngẫu nhiên dựa trên cảnh giới của người dùng"""
        # Xác định phạm vi cấp độ boss
        min_level = max(15, (user_realm_id * 2) // 3)

        # Lọc boss trong phạm vi
        suitable_bosses = [b for b in self.bosses if b["level"] >= min_level]

        # Nếu không có boss phù hợp, lấy con yếu nhất
        if not suitable_bosses:
            return self.bosses[0]

        # Trả về boss ngẫu nhiên
        return random.choice(suitable_bosses)

    def calculate_damage(self, attacker, defender):
        """Tính toán sát thương"""
        base_damage = max(1, attacker["attack"] - (defender["defense"] // 2))

        # Thêm yếu tố ngẫu nhiên (+-20%)
        random_factor = random.uniform(0.8, 1.2)

        # Tính toán sát thương cuối cùng
        damage = int(base_damage * random_factor)

        # Crit (10% cơ hội)
        is_crit = random.random() < 0.1
        if is_crit:
            damage = int(damage * 1.5)

        return damage, is_crit

    async def simulate_combat(self, ctx, user, enemy, is_boss=False):
        """Mô phỏng chiến đấu giữa người dùng và quái vật/boss"""
        # Tạo embed cho trận đấu
        embed = discord.Embed(
            title=f"⚔️ {ctx.author.display_name} đối đầu với {enemy['name']}",
            description=f"Trận chiến bắt đầu!",
            color=EMBED_COLOR
        )

        # Thông tin người chơi
        player = {
            "name": ctx.author.display_name,
            "health": user["health"],
            "attack": user["attack"],
            "defense": user["defense"],
            "realm_id": user["realm_id"]
        }

        # Áp dụng hệ số sức mạnh theo cảnh giới
        power_multiplier = get_power_multiplier(player["realm_id"])
        player["attack"] = int(player["attack"] * power_multiplier)
        player["defense"] = int(player["defense"] * power_multiplier)
        player["health"] = int(player["health"] * power_multiplier)

        # Thêm thông tin người chơi và quái vật
        embed.add_field(
            name=f"{player['name']} [{CULTIVATION_REALMS[player['realm_id']]['name']}]",
            value=f"{EMOJI_HEALTH} HP: {player['health']}\n{EMOJI_ATTACK} Tấn công: {player['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {player['defense']}",
            inline=True
        )

        embed.add_field(
            name=f"{enemy['name']} [Cấp {enemy['level']}]",
            value=f"{EMOJI_HEALTH} HP: {enemy['health']}\n{EMOJI_ATTACK} Tấn công: {enemy['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {enemy['defense']}",
            inline=True
        )

        # Gửi thông tin ban đầu
        message = await ctx.send(embed=embed)

        # Mô phỏng chiến đấu
        round_num = 1
        player_hp = player["health"]
        enemy_hp = enemy["health"]
        battle_log = []

        while player_hp > 0 and enemy_hp > 0:
            # Người chơi tấn công trước
            damage, is_crit = self.calculate_damage(player, enemy)
            enemy_hp = max(0, enemy_hp - damage)

            # Tạo log
            crit_text = " (Chí mạng!)" if is_crit else ""
            battle_log.append(
                f"🔶 **Lượt {round_num}:** {player['name']} gây ra {damage} sát thương{crit_text}. {enemy['name']} còn {enemy_hp} HP.")

            # Nếu quái vật chết, kết thúc
            if enemy_hp <= 0:
                break

            # Quái vật tấn công
            damage, is_crit = self.calculate_damage(enemy, player)
            player_hp = max(0, player_hp - damage)

            # Tạo log
            crit_text = " (Chí mạng!)" if is_crit else ""
            battle_log.append(
                f"🔷 **Lượt {round_num}:** {enemy['name']} gây ra {damage} sát thương{crit_text}. {player['name']} còn {player_hp} HP.")

            # Tăng số lượt
            round_num += 1

            # Cập nhật embed
            embed.description = "\n".join(battle_log[-5:])  # Chỉ hiển thị 5 lượt gần nhất
            embed.set_field_at(0,
                               name=f"{player['name']} [{CULTIVATION_REALMS[player['realm_id']]['name']}]",
                               value=f"{EMOJI_HEALTH} HP: {player_hp}/{player['health']}\n{EMOJI_ATTACK} Tấn công: {player['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {player['defense']}",
                               inline=True
                               )
            embed.set_field_at(1,
                               name=f"{enemy['name']} [Cấp {enemy['level']}]",
                               value=f"{EMOJI_HEALTH} HP: {enemy_hp}/{enemy['health']}\n{EMOJI_ATTACK} Tấn công: {enemy['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {enemy['defense']}",
                               inline=True
                               )

            # Cập nhật tin nhắn
            await message.edit(embed=embed)

            # Tạm dừng để tạo hiệu ứng
            await asyncio.sleep(1)

        # Xác định người thắng
        if player_hp > 0:
            # Tính toán phần thưởng
            if is_boss:
                linh_thach = random.randint(BOSS_MIN_REWARD, BOSS_MAX_REWARD)
                exp = enemy["level"] * 50
            else:
                linh_thach = random.randint(QUAI_MIN_REWARD, QUAI_MAX_REWARD)
                exp = enemy["level"] * 20

            # Cộng phần thưởng
            await add_user_linh_thach(ctx.author.id, linh_thach)

            # Cộng kinh nghiệm
            cultivation_cog = self.bot.get_cog("CultivationCog")
            if cultivation_cog:
                success, new_realm = await cultivation_cog.add_exp(ctx.author.id, exp, f"đánh bại {enemy['name']}")

                # Thông báo đột phá nếu có
                if success:
                    breakthrough_text = f"\n{EMOJI_LEVEL_UP} Chúc mừng! Bạn đã đột phá lên **{new_realm}**!"
                else:
                    breakthrough_text = ""
            else:
                breakthrough_text = ""
                await add_user_exp(ctx.author.id, exp)

            # Cập nhật embed
            embed.color = EMBED_COLOR_SUCCESS
            embed.description = f"**{player['name']} đã chiến thắng {enemy['name']} sau {round_num} lượt!**\n\n" + "\n".join(
                battle_log[-3:])
            embed.add_field(
                name="Phần thưởng",
                value=f"{EMOJI_LINH_THACH} **+{linh_thach}** linh thạch\n{EMOJI_EXP} **+{exp}** kinh nghiệm{breakthrough_text}",
                inline=False
            )
        else:
            # Cập nhật embed khi thua
            embed.color = EMBED_COLOR_ERROR
            embed.description = f"**{player['name']} đã thất bại trước {enemy['name']} sau {round_num} lượt!**\n\n" + "\n".join(
                battle_log[-3:])

        # Cập nhật tin nhắn cuối cùng
        await message.edit(embed=embed)

        # Trả về kết quả
        return player_hp > 0

    @commands.command(name="danhquai", aliases=["dq", "hunt"])
    async def hunt_monster(self, ctx):
        """Đánh quái vật để nhận linh thạch và kinh nghiệm"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra cooldown
        now = datetime.datetime.now()
        last_hunt = user.get("last_danhquai")

        if last_hunt:
            last_hunt = datetime.datetime.fromisoformat(last_hunt)
            time_diff = (now - last_hunt).total_seconds()

            if time_diff < DANHQUAI_COOLDOWN:
                remaining = DANHQUAI_COOLDOWN - time_diff
                minutes, seconds = divmod(int(remaining), 60)

                embed = discord.Embed(
                    title="⏳ Cooldown",
                    description=f"Bạn cần nghỉ ngơi **{minutes} phút {seconds} giây** nữa mới có thể đánh quái tiếp!",
                    color=EMBED_COLOR_ERROR
                )

                return await ctx.send(embed=embed)

        # Lấy quái vật ngẫu nhiên
        monster = self.get_random_monster(user["realm_id"])

        # Mô phỏng chiến đấu
        result = await self.simulate_combat(ctx, user, monster)

        # Cập nhật thời gian đánh quái
        await update_user(ctx.author.id, {"last_danhquai": now.isoformat()})

    @commands.command(name="danhboss", aliases=["db", "boss"])
    async def hunt_boss(self, ctx):
        """Đánh boss để nhận nhiều linh thạch và kinh nghiệm hơn"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra cooldown
        now = datetime.datetime.now()
        last_boss = user.get("last_danhboss")

        if last_boss:
            last_boss = datetime.datetime.fromisoformat(last_boss)
            time_diff = (now - last_boss).total_seconds()

            if time_diff < DANHBOSS_COOLDOWN:
                remaining = DANHBOSS_COOLDOWN - time_diff
                minutes, seconds = divmod(int(remaining), 60)

                embed = discord.Embed(
                    title="⏳ Cooldown",
                    description=f"Bạn cần nghỉ ngơi **{minutes} phút {seconds} giây** nữa mới có thể đánh boss tiếp!",
                    color=EMBED_COLOR_ERROR
                )

                return await ctx.send(embed=embed)

        # Lấy boss ngẫu nhiên
        boss = self.get_random_boss(user["realm_id"])

        # Mô phỏng chiến đấu
        result = await self.simulate_combat(ctx, user, boss, is_boss=True)

        # Cập nhật thời gian đánh boss
        await update_user(ctx.author.id, {"last_danhboss": now.isoformat()})

    @commands.command(name="combat", aliases=["pvp", "pk"])
    async def combat_pvp(self, ctx, opponent: discord.Member = None):
        """Thách đấu PvP với người chơi khác"""
        # Kiểm tra xem có chỉ định đối thủ không
        if not opponent:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn cần chỉ định người chơi để thách đấu!\nVí dụ: `!combat @tên_người_chơi`",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra không thách đấu chính mình
        if opponent.id == ctx.author.id:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn không thể thách đấu chính mình!",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra không thách đấu bot
        if opponent.bot:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn không thể thách đấu với bot!",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra cooldown
        now = datetime.datetime.now()
        last_combat = user.get("last_combat")

        if last_combat:
            last_combat = datetime.datetime.fromisoformat(last_combat)
            time_diff = (now - last_combat).total_seconds()

            if time_diff < COMBAT_COOLDOWN:
                remaining = COMBAT_COOLDOWN - time_diff
                minutes, seconds = divmod(int(remaining), 60)

                embed = discord.Embed(
                    title="⏳ Cooldown",
                    description=f"Bạn cần nghỉ ngơi **{minutes} phút {seconds} giây** nữa mới có thể thách đấu tiếp!",
                    color=EMBED_COLOR_ERROR
                )

                return await ctx.send(embed=embed)

        # Lấy thông tin đối thủ
        opponent_user = await get_user_or_create(opponent.id, opponent.name)

        # Tạo embed thách đấu
        embed = discord.Embed(
            title="⚔️ Thách Đấu PvP",
            description=f"{ctx.author.mention} đã thách đấu {opponent.mention}!\n{opponent.mention} có 60 giây để chấp nhận hoặc từ chối.",
            color=EMBED_COLOR
        )

        # Thêm thông tin người chơi
        player_realm = CULTIVATION_REALMS[user["realm_id"]]["name"]
        opponent_realm = CULTIVATION_REALMS[opponent_user["realm_id"]]["name"]

        embed.add_field(
            name=f"{ctx.author.display_name} [{player_realm}]",
            value=f"{EMOJI_HEALTH} HP: {user['health']}\n{EMOJI_ATTACK} Tấn công: {user['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {user['defense']}",
            inline=True
        )

        embed.add_field(
            name=f"{opponent.display_name} [{opponent_realm}]",
            value=f"{EMOJI_HEALTH} HP: {opponent_user['health']}\n{EMOJI_ATTACK} Tấn công: {opponent_user['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {opponent_user['defense']}",
            inline=True
        )

        # Gửi tin nhắn thách đấu
        challenge_msg = await ctx.send(embed=embed)

        # Thêm reaction cho người chơi chọn
        await challenge_msg.add_reaction("✅")  # Đồng ý
        await challenge_msg.add_reaction("❌")  # Từ chối

        # Hàm kiểm tra reaction
        def check(reaction, user):
            return user.id == opponent.id and str(reaction.emoji) in ["✅",
                                                                      "❌"] and reaction.message.id == challenge_msg.id

        try:
            # Chờ phản ứng
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            # Nếu từ chối
            if str(reaction.emoji) == "❌":
                embed.description = f"{opponent.display_name} đã từ chối thách đấu!"
                embed.color = EMBED_COLOR_ERROR
                await challenge_msg.edit(embed=embed)
                return

            # Nếu đồng ý, bắt đầu chiến đấu
            embed.description = f"{opponent.display_name} đã chấp nhận thách đấu! Trận chiến bắt đầu!"
            await challenge_msg.edit(embed=embed)

            # Chuẩn bị thông tin người chơi
            player = {
                "name": ctx.author.display_name,
                "health": user["health"],
                "attack": user["attack"],
                "defense": user["defense"],
                "realm_id": user["realm_id"]
            }

            opponent_player = {
                "name": opponent.display_name,
                "health": opponent_user["health"],
                "attack": opponent_user["attack"],
                "defense": opponent_user["defense"],
                "realm_id": opponent_user["realm_id"]
            }

            # Áp dụng hệ số sức mạnh theo cảnh giới
            player_multiplier = get_power_multiplier(player["realm_id"])
            player["attack"] = int(player["attack"] * player_multiplier)
            player["defense"] = int(player["defense"] * player_multiplier)
            player["health"] = int(player["health"] * player_multiplier)

            opponent_multiplier = get_power_multiplier(opponent_player["realm_id"])
            opponent_player["attack"] = int(opponent_player["attack"] * opponent_multiplier)
            opponent_player["defense"] = int(opponent_player["defense"] * opponent_multiplier)
            opponent_player["health"] = int(opponent_player["health"] * opponent_multiplier)

            # Mô phỏng chiến đấu
            round_num = 1
            player_hp = player["health"]
            opponent_hp = opponent_player["health"]
            battle_log = []

            # Ai có tốc độ cao hơn sẽ đánh trước (dựa trên cảnh giới)
            player_goes_first = player["realm_id"] >= opponent_player["realm_id"]

            while player_hp > 0 and opponent_hp > 0:
                # Xác định thứ tự tấn công
                if player_goes_first:
                    first_attacker, second_attacker = player, opponent_player
                    first_hp, second_hp = player_hp, opponent_hp
                else:
                    first_attacker, second_attacker = opponent_player, player
                    first_hp, second_hp = opponent_hp, player_hp

                # Người đánh trước tấn công
                damage, is_crit = self.calculate_damage(first_attacker, second_attacker)
                second_hp = max(0, second_hp - damage)

                # Tạo log
                crit_text = " (Chí mạng!)" if is_crit else ""
                battle_log.append(
                    f"🔶 **Lượt {round_num}:** {first_attacker['name']} gây ra {damage} sát thương{crit_text}. {second_attacker['name']} còn {second_hp} HP.")

                # Nếu người thứ hai chết, kết thúc
                if second_hp <= 0:
                    break

                # Người thứ hai tấn công
                damage, is_crit = self.calculate_damage(second_attacker, first_attacker)
                first_hp = max(0, first_hp - damage)

                # Tạo log
                crit_text = " (Chí mạng!)" if is_crit else ""
                battle_log.append(
                    f"🔷 **Lượt {round_num}:** {second_attacker['name']} gây ra {damage} sát thương{crit_text}. {first_attacker['name']} còn {first_hp} HP.")

                # Cập nhật HP
                if player_goes_first:
                    player_hp, opponent_hp = first_hp, second_hp
                else:
                    opponent_hp, player_hp = first_hp, second_hp

                # Tăng số lượt
                round_num += 1

                # Cập nhật embed
                embed.description = "\n".join(battle_log[-5:])  # Chỉ hiển thị 5 lượt gần nhất
                embed.set_field_at(0,
                                   name=f"{player['name']} [{CULTIVATION_REALMS[player['realm_id']]['name']}]",
                                   value=f"{EMOJI_HEALTH} HP: {player_hp}/{player['health']}\n{EMOJI_ATTACK} Tấn công: {player['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {player['defense']}",
                                   inline=True
                                   )
                embed.set_field_at(1,
                                   name=f"{opponent_player['name']} [{CULTIVATION_REALMS[opponent_player['realm_id']]['name']}]",
                                   value=f"{EMOJI_HEALTH} HP: {opponent_hp}/{opponent_player['health']}\n{EMOJI_ATTACK} Tấn công: {opponent_player['attack']}\n{EMOJI_DEFENSE} Phòng thủ: {opponent_player['defense']}",
                                   inline=True
                                   )

                # Cập nhật tin nhắn
                await challenge_msg.edit(embed=embed)

                # Tạm dừng để tạo hiệu ứng
                await asyncio.sleep(1)

            # Xác định người thắng
            if player_hp > 0:
                winner = ctx.author
                loser = opponent
                winner_user = user

                # Cập nhật embed
                embed.color = EMBED_COLOR_SUCCESS
                embed.description = f"**{player['name']} đã chiến thắng {opponent_player['name']} sau {round_num} lượt!**\n\n" + "\n".join(
                    battle_log[-3:])
            else:
                winner = opponent
                loser = ctx.author
                winner_user = opponent_user

                # Cập nhật embed
                embed.color = EMBED_COLOR_ERROR
                embed.description = f"**{opponent_player['name']} đã chiến thắng {player['name']} sau {round_num} lượt!**\n\n" + "\n".join(
                    battle_log[-3:])

            # Thưởng linh thạch cho người thắng
            await add_user_linh_thach(winner.id, COMBAT_WIN_REWARD)

            # Thêm kinh nghiệm cho cả hai
            cultivation_cog = self.bot.get_cog("CultivationCog")
            if cultivation_cog:
                # Người thắng nhận nhiều kinh nghiệm hơn
                win_exp = 50
                lose_exp = 20

                # Thêm kinh nghiệm và kiểm tra đột phá
                win_success, win_realm = await cultivation_cog.add_exp(winner.id, win_exp,
                                                                       f"thắng PvP với {loser.display_name}")
                lose_success, lose_realm = await cultivation_cog.add_exp(loser.id, lose_exp,
                                                                         f"thua PvP với {winner.display_name}")

                # Thông báo đột phá
                breakthrough_text = ""
                if win_success:
                    breakthrough_text += f"\n{EMOJI_LEVEL_UP} {winner.mention} đã đột phá lên **{win_realm}**!"
                if lose_success:
                    breakthrough_text += f"\n{EMOJI_LEVEL_UP} {loser.mention} đã đột phá lên **{lose_realm}**!"
            else:
                win_exp = 50
                lose_exp = 20
                breakthrough_text = ""

                # Thêm kinh nghiệm
                await add_user_exp(winner.id, win_exp)
                await add_user_exp(loser.id, lose_exp)

            # Thêm thông tin phần thưởng vào embed
            embed.add_field(
                name="Phần thưởng",
                value=(
                    f"{winner.mention}:\n"
                    f"{EMOJI_LINH_THACH} **+{COMBAT_WIN_REWARD}** linh thạch\n"
                    f"{EMOJI_EXP} **+{win_exp}** kinh nghiệm\n\n"
                    f"{loser.mention}:\n"
                    f"{EMOJI_EXP} **+{lose_exp}** kinh nghiệm"
                    f"{breakthrough_text}"
                ),
                inline=False
            )

            # Cập nhật tin nhắn cuối cùng
            await challenge_msg.edit(embed=embed)

            # Cập nhật thời gian combat cho người gọi lệnh
            await update_user(ctx.author.id, {"last_combat": now.isoformat()})

        except asyncio.TimeoutError:
            # Nếu hết thời gian
            embed.description = f"{opponent.display_name} không phản hồi. Thách đấu bị hủy!"
            embed.color = EMBED_COLOR_ERROR
            await challenge_msg.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(CombatCog(bot))