import discord
from discord.ext import commands
import random
import asyncio
from database.mongo_handler import MongoHandler
from utils.embed_utils import create_embed, create_progress_bar
from utils.text_utils import format_number
import config


class Dungeons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = MongoHandler()
        self.active_dungeons = {}

    @commands.command(name="dungeon", aliases=["dongphu"])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 giờ cooldown
    async def dungeon(self, ctx):
        """Khám phá động phủ để tìm kiếm kho báu và đánh quái vật"""
        # Kiểm tra người dùng
        user_data = await self.db.get_user(ctx.author.id)
        if not user_data:
            return await ctx.send("Bạn chưa bắt đầu tu luyện. Hãy sử dụng lệnh `start` trước.")

        # Kiểm tra xem người dùng đã có phiên khám phá động phủ đang diễn ra không
        if ctx.author.id in self.active_dungeons:
            return await ctx.send(
                "Bạn đang trong một phiên khám phá động phủ. Hãy hoàn thành hoặc thoát trước khi bắt đầu phiên mới.")

        # Tạo phiên khám phá động phủ mới
        dungeon_level = min(10, max(1, user_data.get('cultivation', {}).get('stage', 1)))
        dungeon_data = self._generate_dungeon(dungeon_level)

        self.active_dungeons[ctx.author.id] = {
            "level": dungeon_level,
            "rooms": dungeon_data["rooms"],
            "current_room": 0,
            "health": user_data.get('health', 100),
            "max_health": user_data.get('max_health', 100),
            "rewards": {
                "exp": 0,
                "spirit_stones": 0,
                "items": []
            }
        }

        # Hiển thị thông tin động phủ
        embed = create_embed(
            title=f"Động phủ cấp {dungeon_level}",
            description=f"Bạn đã tìm thấy một động phủ cấp {dungeon_level} với {len(dungeon_data['rooms'])} phòng.\n"
                        f"Hãy khám phá để tìm kiếm kho báu và đánh bại quái vật!\n\n"
                        f"Sinh lực: {self.active_dungeons[ctx.author.id]['health']}/{self.active_dungeons[ctx.author.id]['max_health']}",
            color=discord.Color.dark_gold()
        )

        # Tạo các nút điều khiển
        explore_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Khám phá", custom_id="explore")
        exit_button = discord.ui.Button(style=discord.ButtonStyle.red, label="Thoát", custom_id="exit")

        view = discord.ui.View()
        view.add_item(explore_button)
        view.add_item(exit_button)

        dungeon_msg = await ctx.send(embed=embed, view=view)

        # Xử lý tương tác
        while ctx.author.id in self.active_dungeons:
            try:
                def check(interaction):
                    return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

                interaction = await self.bot.wait_for("interaction", check=check, timeout=300.0)

                if interaction.data["custom_id"] == "explore":
                    await self._explore_room(ctx, interaction, dungeon_msg)
                elif interaction.data["custom_id"] == "exit":
                    await self._exit_dungeon(ctx, interaction, dungeon_msg)
                    break

            except asyncio.TimeoutError:
                if ctx.author.id in self.active_dungeons:
                    await dungeon_msg.edit(
                        embed=create_embed(
                            title="Động phủ đã đóng",
                            description="Phiên khám phá động phủ đã kết thúc do không có hoạt động.",
                            color=discord.Color.grey()
                        ),
                        view=None
                    )
                    del self.active_dungeons[ctx.author.id]
                break

    def _generate_dungeon(self, level):
        """Tạo dữ liệu động phủ ngẫu nhiên"""
        num_rooms = random.randint(3, 5 + level)
        rooms = []

        for i in range(num_rooms):
            # Xác định loại phòng (quái vật, kho báu, bẫy, trống)
            room_type = random.choices(
                ["monster", "treasure", "trap", "empty"],
                weights=[0.4, 0.3, 0.2, 0.1],
                k=1
            )[0]

            room = {"type": room_type}

            if room_type == "monster":
                # Tạo quái vật ngẫu nhiên
                monster_level = max(1, level + random.randint(-2, 2))
                combat_power = monster_level * 100 * random.uniform(0.8, 1.2)
                health = monster_level * 50 * random.uniform(0.8, 1.2)

                room["monster"] = {
                    "name": f"Quái vật cấp {monster_level}",
                    "level": monster_level,
                    "combat_power": combat_power,
                    "health": health,
                    "max_health": health
                }

                # Phần thưởng khi đánh bại quái vật
                room["rewards"] = {
                    "exp": monster_level * 20 * random.uniform(0.8, 1.2),
                    "spirit_stones": monster_level * 50 * random.uniform(0.8, 1.2)
                }

                # Cơ hội rơi vật phẩm
                if random.random() < 0.3:  # 30% cơ hội rơi vật phẩm
                    room["rewards"]["items"] = [{
                        "item_id": random.randint(1, 10),  # ID vật phẩm ngẫu nhiên
                        "quantity": 1
                    }]

            elif room_type == "treasure":
                # Tạo kho báu ngẫu nhiên
                treasure_quality = random.choices(
                    ["common", "uncommon", "rare", "epic"],
                    weights=[0.4, 0.3, 0.2, 0.1],
                    k=1
                )[0]

                multiplier = {
                    "common": 1,
                    "uncommon": 2,
                    "rare": 3,
                    "epic": 5
                }[treasure_quality]

                room["treasure"] = {
                    "quality": treasure_quality,
                    "description": f"Bạn tìm thấy một rương {treasure_quality}!"
                }

                room["rewards"] = {
                    "spirit_stones": level * 100 * multiplier * random.uniform(0.8, 1.2),
                    "exp": level * 10 * multiplier * random.uniform(0.8, 1.2)
                }

                # Cơ hội có vật phẩm trong kho báu
                if random.random() < 0.5 * multiplier:  # Cơ hội tăng theo chất lượng kho báu
                    room["rewards"]["items"] = [{
                        "item_id": random.randint(1, 10),  # ID vật phẩm ngẫu nhiên
                        "quantity": random.randint(1, 3)
                    }]

            elif room_type == "trap":
                # Tạo bẫy ngẫu nhiên
                trap_difficulty = random.choices(
                    ["easy", "medium", "hard"],
                    weights=[0.5, 0.3, 0.2],
                    k=1
                )[0]

                damage_multiplier = {
                    "easy": 0.1,
                    "medium": 0.2,
                    "hard": 0.3
                }[trap_difficulty]

                room["trap"] = {
                    "difficulty": trap_difficulty,
                    "damage_percent": damage_multiplier,
                    "description": f"Bạn gặp phải một cái bẫy {trap_difficulty}!"
                }

            elif room_type == "empty":
                # Phòng trống
                room["description"] = random.choice([
                    "Một căn phòng trống, không có gì đáng chú ý.",
                    "Bạn thấy một căn phòng đã bị cướp phá từ trước.",
                    "Căn phòng này chỉ chứa đầy bụi và mạng nhện."
                ])

            rooms.append(room)

        return {"rooms": rooms}

    async def _explore_room(self, ctx, interaction, dungeon_msg):
        """Xử lý khám phá phòng trong động phủ"""
        await interaction.response.defer()

        dungeon_data = self.active_dungeons[ctx.author.id]
        current_room_idx = dungeon_data["current_room"]

        # Kiểm tra xem đã khám phá hết các phòng chưa
        if current_room_idx >= len(dungeon_data["rooms"]):
            await self._complete_dungeon(ctx, interaction, dungeon_msg)
            return

        # Lấy thông tin phòng hiện tại
        current_room = dungeon_data["rooms"][current_room_idx]
        room_type = current_room["type"]

        # Xử lý theo loại phòng
        if room_type == "monster":
            await self._handle_monster_room(ctx, interaction, dungeon_msg, current_room)
        elif room_type == "treasure":
            await self._handle_treasure_room(ctx, interaction, dungeon_msg, current_room)
        elif room_type == "trap":
            await self._handle_trap_room(ctx, interaction, dungeon_msg, current_room)
        elif room_type == "empty":
            await self._handle_empty_room(ctx, interaction, dungeon_msg, current_room)

        # Tăng chỉ số phòng hiện tại
        dungeon_data["current_room"] += 1

        # Kiểm tra xem người chơi còn sống không
        if dungeon_data["health"] <= 0:
            await self._handle_death(ctx, interaction, dungeon_msg)
            return

        # Kiểm tra xem đã khám phá hết các phòng chưa
        if dungeon_data["current_room"] >= len(dungeon_data["rooms"]):
            await self._complete_dungeon(ctx, interaction, dungeon_msg)
            return

        # Cập nhật embed và view
        embed = create_embed(
            title=f"Động phủ cấp {dungeon_data['level']}",
            description=f"Phòng: {dungeon_data['current_room'] + 1}/{len(dungeon_data['rooms'])}\n"
                        f"Sinh lực: {dungeon_data['health']}/{dungeon_data['max_health']}\n\n"
                        f"Phần thưởng hiện tại:\n"
                        f"- Kinh nghiệm: {format_number(dungeon_data['rewards']['exp'])}\n"
                        f"- Linh thạch: {format_number(dungeon_data['rewards']['spirit_stones'])}\n"
                        f"- Vật phẩm: {len(dungeon_data['rewards']['items'])}",
            color=discord.Color.dark_gold()
        )

        # Tạo các nút điều khiển
        explore_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Khám phá", custom_id="explore")
        exit_button = discord.ui.Button(style=discord.ButtonStyle.red, label="Thoát", custom_id="exit")

        view = discord.ui.View()
        view.add_item(explore_button)
        view.add_item(exit_button)

        await dungeon_msg.edit(embed=embed, view=view)

    async def _handle_monster_room(self, ctx, interaction, dungeon_msg, room_data):
        """Xử lý phòng có quái vật"""
        monster = room_data["monster"]
        user_data = await self.db.get_user(ctx.author.id)

        # Tính toán kết quả chiến đấu
        user_combat_power = user_data.get('combat_power', 100)
        monster_combat_power = monster["combat_power"]

        # Tạo embed thông báo gặp quái vật
        embed = create_embed(
            title="Gặp quái vật!",
            description=f"Bạn đã gặp {monster['name']} trong phòng này!\n\n"
                        f"Sức mạnh chiến đấu của bạn: {format_number(user_combat_power)}\n"
                        f"Sức mạnh chiến đấu của quái vật: {format_number(monster_combat_power)}",
            color=discord.Color.red()
        )

        # Hiển thị thanh máu
        user_health_bar = create_progress_bar(
            self.active_dungeons[ctx.author.id]["health"],
            self.active_dungeons[ctx.author.id]["max_health"]
        )

        monster_health_bar = create_progress_bar(
            monster["health"],
            monster["max_health"]
        )

        embed.add_field(
            name=f"{ctx.author.display_name}",
            value=f"HP: {user_health_bar} ({self.active_dungeons[ctx.author.id]['health']}/{self.active_dungeons[ctx.author.id]['max_health']})",
            inline=False
        )

        embed.add_field(
            name=f"{monster['name']}",
            value=f"HP: {monster_health_bar} ({int(monster['health'])}/{int(monster['max_health'])})",
            inline=False
        )

        # Tạo các nút điều khiển
        attack_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Tấn công", custom_id="attack")
        flee_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Chạy trốn", custom_id="flee")

        view = discord.ui.View()
        view.add_item(attack_button)
        view.add_item(flee_button)

        await dungeon_msg.edit(embed=embed, view=view)

        # Xử lý chiến đấu
        while monster["health"] > 0 and self.active_dungeons[ctx.author.id]["health"] > 0:
            try:
                def check(interaction):
                    return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

                battle_interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)

                if battle_interaction.data["custom_id"] == "attack":
                    await battle_interaction.response.defer()

                    # Tính toán sát thương
                    user_damage = max(1, int(user_combat_power * random.uniform(0.8, 1.2) / 10))
                    monster_damage = max(1, int(monster_combat_power * random.uniform(0.8, 1.2) / 10))

                    # Cơ hội chí mạng
                    is_critical = random.random() < 0.1  # 10% cơ hội chí mạng
                    if is_critical:
                        user_damage = int(user_damage * 1.5)

                    # Giảm máu quái vật
                    monster["health"] -= user_damage

                    # Nếu quái vật vẫn sống, nó sẽ tấn công lại
                    if monster["health"] > 0:
                        self.active_dungeons[ctx.author.id]["health"] -= monster_damage

                    # Cập nhật embed
                    battle_result = ""
                    if is_critical:
                        battle_result += f"Bạn gây ra đòn chí mạng! Sát thương: {user_damage}\n"
                    else:
                        battle_result += f"Bạn gây ra {user_damage} sát thương\n"

                    if monster["health"] > 0:
                        battle_result += f"{monster['name']} gây ra {monster_damage} sát thương cho bạn"
                    else:
                        battle_result += f"Bạn đã đánh bại {monster['name']}!"

                    # Cập nhật thanh máu
                    user_health_bar = create_progress_bar(
                        self.active_dungeons[ctx.author.id]["health"],
                        self.active_dungeons[ctx.author.id]["max_health"]
                    )

                    monster_health = max(0, monster["health"])
                    monster_health_bar = create_progress_bar(
                        monster_health,
                        monster["max_health"]
                    )

                    embed = create_embed(
                        title="Chiến đấu với quái vật!",
                        description=battle_result,
                        color=discord.Color.red()
                    )

                    embed.add_field(
                        name=f"{ctx.author.display_name}",
                        value=f"HP: {user_health_bar} ({self.active_dungeons[ctx.author.id]['health']}/{self.active_dungeons[ctx.author.id]['max_health']})",
                        inline=False
                    )

                    embed.add_field(
                        name=f"{monster['name']}",
                        value=f"HP: {monster_health_bar} ({int(monster_health)}/{int(monster['max_health'])})",
                        inline=False
                    )

                    # Kiểm tra kết quả chiến đấu
                    if monster["health"] <= 0:
                        # Người chơi thắng
                        rewards = room_data.get("rewards", {})

                        # Cộng phần thưởng vào tổng
                        self.active_dungeons[ctx.author.id]["rewards"]["exp"] += rewards.get("exp", 0)
                        self.active_dungeons[ctx.author.id]["rewards"]["spirit_stones"] += rewards.get("spirit_stones",
                                                                                                       0)

                        if "items" in rewards:
                            self.active_dungeons[ctx.author.id]["rewards"]["items"].extend(rewards["items"])

                        embed.add_field(
                            name="Phần thưởng",
                            value=f"Kinh nghiệm: +{format_number(rewards.get('exp', 0))}\n"
                                  f"Linh thạch: +{format_number(rewards.get('spirit_stones', 0))}\n"
                                  f"Vật phẩm: +{len(rewards.get('items', []))}",
                            inline=False
                        )

                        # Tạo nút tiếp tục
                        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục",
                                                            custom_id="continue")

                        view = discord.ui.View()
                        view.add_item(continue_button)

                        await dungeon_msg.edit(embed=embed, view=view)

                        # Chờ người chơi nhấn nút tiếp tục
                        def continue_check(interaction):
                            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

                        await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)
                        break

                    elif self.active_dungeons[ctx.author.id]["health"] <= 0:
                        # Người chơi thua
                        await self._handle_death(ctx, battle_interaction, dungeon_msg)
                        return

                    await dungeon_msg.edit(embed=embed, view=view)

                elif battle_interaction.data["custom_id"] == "flee":
                    await battle_interaction.response.defer()

                    # Xác suất chạy trốn thành công
                    flee_chance = 0.5  # 50% cơ hội chạy trốn thành công

                    if random.random() < flee_chance:
                        # Chạy trốn thành công
                        embed = create_embed(
                            title="Chạy trốn thành công!",
                            description=f"Bạn đã chạy trốn khỏi {monster['name']} thành công.",
                            color=discord.Color.green()
                        )

                        # Tạo nút tiếp tục
                        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục",
                                                            custom_id="continue")

                        view = discord.ui.View()
                        view.add_item(continue_button)

                        await dungeon_msg.edit(embed=embed, view=view)

                        # Chờ người chơi nhấn nút tiếp tục
                        def continue_check(interaction):
                            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

                        await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)
                        break
                    else:
                        # Chạy trốn thất bại
                        monster_damage = max(1, int(monster_combat_power * random.uniform(0.8, 1.2) / 10))
                        self.active_dungeons[ctx.author.id]["health"] -= monster_damage

                        embed = create_embed(
                            title="Chạy trốn thất bại!",
                            description=f"Bạn không thể chạy trốn khỏi {monster['name']}.\n"
                                        f"{monster['name']} gây ra {monster_damage} sát thương cho bạn.",
                            color=discord.Color.red()
                        )

                        # Cập nhật thanh máu
                        user_health_bar = create_progress_bar(
                            self.active_dungeons[ctx.author.id]["health"],
                            self.active_dungeons[ctx.author.id]["max_health"]
                        )

                        monster_health_bar = create_progress_bar(
                            monster["health"],
                            monster["max_health"]
                        )

                        embed.add_field(
                            name=f"{ctx.author.display_name}",
                            value=f"HP: {user_health_bar} ({self.active_dungeons[ctx.author.id]['health']}/{self.active_dungeons[ctx.author.id]['max_health']})",
                            inline=False
                        )

                        embed.add_field(
                            name=f"{monster['name']}",
                            value=f"HP: {monster_health_bar} ({int(monster['health'])}/{int(monster['max_health'])})",
                            inline=False
                        )

                        # Kiểm tra xem người chơi còn sống không
                        if self.active_dungeons[ctx.author.id]["health"] <= 0:
                            await self._handle_death(ctx, battle_interaction, dungeon_msg)
                            return

                        await dungeon_msg.edit(embed=embed, view=view)

            except asyncio.TimeoutError:
                # Tự động tấn công nếu người chơi không phản hồi
                user_damage = max(1, int(user_combat_power * random.uniform(0.8, 1.2) / 10))
                monster_damage = max(1, int(monster_combat_power * random.uniform(0.8, 1.2) / 10))

                monster["health"] -= user_damage

                if monster["health"] > 0:
                    self.active_dungeons[ctx.author.id]["health"] -= monster_damage

                # Cập nhật embed
                battle_result = f"Tự động tấn công!\n"
                battle_result += f"Bạn gây ra {user_damage} sát thương\n"

                if monster["health"] > 0:
                    battle_result += f"{monster['name']} gây ra {monster_damage} sát thương cho bạn"
                else:
                    battle_result += f"Bạn đã đánh bại {monster['name']}!"

                # Cập nhật thanh máu
                user_health_bar = create_progress_bar(
                    self.active_dungeons[ctx.author.id]["health"],
                    self.active_dungeons[ctx.author.id]["max_health"]
                )

                monster_health = max(0, monster["health"])
                monster_health_bar = create_progress_bar(
                    monster_health,
                    monster["max_health"]
                )

                embed = create_embed(
                    title="Chiến đấu với quái vật!",
                    description=battle_result,
                    color=discord.Color.red()
                )

                embed.add_field(
                    name=f"{ctx.author.display_name}",
                    value=f"HP: {user_health_bar} ({self.active_dungeons[ctx.author.id]['health']}/{self.active_dungeons[ctx.author.id]['max_health']})",
                    inline=False
                )

                embed.add_field(
                    name=f"{monster['name']}",
                    value=f"HP: {monster_health_bar} ({int(monster_health)}/{int(monster['max_health'])})",
                    inline=False
                )

                # Kiểm tra kết quả chiến đấu
                if monster["health"] <= 0:
                    # Người chơi thắng
                    rewards = room_data.get("rewards", {})

                    # Cộng phần thưởng vào tổng
                    self.active_dungeons[ctx.author.id]["rewards"]["exp"] += rewards.get("exp", 0)
                    self.active_dungeons[ctx.author.id]["rewards"]["spirit_stones"] += rewards.get("spirit_stones", 0)

                    if "items" in rewards:
                        self.active_dungeons[ctx.author.id]["rewards"]["items"].extend(rewards["items"])

                    embed.add_field(
                        name="Phần thưởng",
                        value=f"Kinh nghiệm: +{format_number(rewards.get('exp', 0))}\n"
                              f"Linh thạch: +{format_number(rewards.get('spirit_stones', 0))}\n"
                              f"Vật phẩm: +{len(rewards.get('items', []))}",
                        inline=False
                    )

                    # Tạo nút tiếp tục
                    continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục",
                                                        custom_id="continue")

                    view = discord.ui.View()
                    view.add_item(continue_button)

                    await dungeon_msg.edit(embed=embed, view=view)
                    break

                elif self.active_dungeons[ctx.author.id]["health"] <= 0:
                    # Người chơi thua
                    await self._handle_death(ctx, interaction, dungeon_msg)
                    return

                await dungeon_msg.edit(embed=embed, view=view)

    async def _handle_treasure_room(self, ctx, interaction, dungeon_msg, room_data):
        """Xử lý phòng có kho báu"""
        treasure = room_data["treasure"]
        rewards = room_data.get("rewards", {})

        # Tạo embed thông báo tìm thấy kho báu
        embed = create_embed(
            title="Tìm thấy kho báu!",
            description=treasure["description"],
            color=discord.Color.gold()
        )

        # Hiển thị phần thưởng
        reward_text = ""
        if "exp" in rewards:
            reward_text += f"Kinh nghiệm: +{format_number(rewards['exp'])}\n"
            self.active_dungeons[ctx.author.id]["rewards"]["exp"] += rewards["exp"]

        if "spirit_stones" in rewards:
            reward_text += f"Linh thạch: +{format_number(rewards['spirit_stones'])}\n"
            self.active_dungeons[ctx.author.id]["rewards"]["spirit_stones"] += rewards["spirit_stones"]

        if "items" in rewards:
            reward_text += f"Vật phẩm: +{len(rewards['items'])}\n"
            self.active_dungeons[ctx.author.id]["rewards"]["items"].extend(rewards["items"])

        embed.add_field(
            name="Phần thưởng",
            value=reward_text,
            inline=False
        )

        # Tạo nút tiếp tục
        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục", custom_id="continue")

        view = discord.ui.View()
        view.add_item(continue_button)

        await dungeon_msg.edit(embed=embed, view=view)

        # Chờ người chơi nhấn nút tiếp tục
        def continue_check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

        await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)

    async def _handle_trap_room(self, ctx, interaction, dungeon_msg, room_data):
        """Xử lý phòng có bẫy"""
        trap = room_data["trap"]

        # Tính toán sát thương từ bẫy
        damage_percent = trap["damage_percent"]
        max_health = self.active_dungeons[ctx.author.id]["max_health"]
        damage = int(max_health * damage_percent)

        # Giảm máu người chơi
        self.active_dungeons[ctx.author.id]["health"] -= damage

        # Tạo embed thông báo gặp bẫy
        embed = create_embed(
            title="Gặp bẫy!",
            description=f"{trap['description']}\n\nBạn bị mất {damage} sinh lực.",
            color=discord.Color.dark_red()
        )

        # Hiển thị thanh máu
        user_health_bar = create_progress_bar(
            self.active_dungeons[ctx.author.id]["health"],
            self.active_dungeons[ctx.author.id]["max_health"]
        )

        embed.add_field(
            name="Sinh lực",
            value=f"HP: {user_health_bar} ({self.active_dungeons[ctx.author.id]['health']}/{self.active_dungeons[ctx.author.id]['max_health']})",
            inline=False
        )

        # Kiểm tra xem người chơi còn sống không
        if self.active_dungeons[ctx.author.id]["health"] <= 0:
            await self._handle_death(ctx, interaction, dungeon_msg)
            return

        # Tạo nút tiếp tục
        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục", custom_id="continue")

        view = discord.ui.View()
        view.add_item(continue_button)

        await dungeon_msg.edit(embed=embed, view=view)

        # Chờ người chơi nhấn nút tiếp tục
        def continue_check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

        await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)

    async def _handle_empty_room(self, ctx, interaction, dungeon_msg, room_data):
        """Xử lý phòng trống"""
        # Tạo embed thông báo phòng trống
        embed = create_embed(
            title="Phòng trống",
            description=room_data["description"],
            color=discord.Color.light_grey()
        )

        # Tạo nút tiếp tục
        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục", custom_id="continue")

        view = discord.ui.View()
        view.add_item(continue_button)

        await dungeon_msg.edit(embed=embed, view=view)

        # Chờ người chơi nhấn nút tiếp tục
        def continue_check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

        await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)

    async def _handle_death(self, ctx, interaction, dungeon_msg):
        """Xử lý khi người chơi chết trong động phủ"""
        # Tính toán phần thưởng giảm
        rewards = self.active_dungeons[ctx.author.id]["rewards"]
        rewards["exp"] = int(rewards["exp"] * 0.5)  # Giảm 50% kinh nghiệm
        rewards["spirit_stones"] = int(rewards["spirit_stones"] * 0.5)  # Giảm 50% linh thạch
        rewards["items"] = []  # Mất tất cả vật phẩm

        # Tạo embed thông báo tử vong
        embed = create_embed(
            title="Bạn đã tử vong!",
            description="Bạn đã tử vong trong động phủ. Phần thưởng của bạn bị giảm 50% và mất tất cả vật phẩm.",
            color=discord.Color.dark_red()
        )

        # Hiển thị phần thưởng còn lại
        embed.add_field(
            name="Phần thưởng còn lại",
            value=f"Kinh nghiệm: {format_number(rewards['exp'])}\n"
                  f"Linh thạch: {format_number(rewards['spirit_stones'])}\n"
                  f"Vật phẩm: 0",
            inline=False
        )

        # Tạo nút tiếp tục
        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Tiếp tục", custom_id="continue")

        view = discord.ui.View()
        view.add_item(continue_button)

        await dungeon_msg.edit(embed=embed, view=view)

        # Chờ người chơi nhấn nút tiếp tục
        def continue_check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

        try:
            await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)
        except asyncio.TimeoutError:
            pass

        # Cập nhật phần thưởng vào database
        await self._update_rewards(ctx.author.id)

        # Xóa thông tin động phủ
        if ctx.author.id in self.active_dungeons:
            del self.active_dungeons[ctx.author.id]

    async def _complete_dungeon(self, ctx, interaction, dungeon_msg):
        """Xử lý khi người chơi hoàn thành động phủ"""
        rewards = self.active_dungeons[ctx.author.id]["rewards"]

        # Tạo embed thông báo hoàn thành
        embed = create_embed(
            title="Hoàn thành động phủ!",
            description=f"Chúc mừng! Bạn đã hoàn thành động phủ cấp {self.active_dungeons[ctx.author.id]['level']}.",
            color=discord.Color.green()
        )

        # Hiển thị phần thưởng
        embed.add_field(
            name="Phần thưởng",
            value=f"Kinh nghiệm: {format_number(rewards['exp'])}\n"
                  f"Linh thạch: {format_number(rewards['spirit_stones'])}\n"
                  f"Vật phẩm: {len(rewards['items'])}",
            inline=False
        )

        # Tạo nút tiếp tục
        continue_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Nhận thưởng", custom_id="continue")

        view = discord.ui.View()
        view.add_item(continue_button)

        await dungeon_msg.edit(embed=embed, view=view)

        # Chờ người chơi nhấn nút tiếp tục
        def continue_check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == dungeon_msg.id

        try:
            await self.bot.wait_for("interaction", check=continue_check, timeout=60.0)
        except asyncio.TimeoutError:
            pass

        # Cập nhật phần thưởng vào database
        await self._update_rewards(ctx.author.id)

        # Xóa thông tin động phủ
        if ctx.author.id in self.active_dungeons:
            del self.active_dungeons[ctx.author.id]

    async def _exit_dungeon(self, ctx, interaction, dungeon_msg):
        """Xử lý khi người chơi thoát khỏi động phủ"""
        await interaction.response.defer()

        # Tính toán phần thưởng giảm
        rewards = self.active_dungeons[ctx.author.id]["rewards"]
        rewards["exp"] = int(rewards["exp"] * 0.7)  # Giảm 30% kinh nghiệm
        rewards["spirit_stones"] = int(rewards["spirit_stones"] * 0.7)  # Giảm 30% linh thạch

        # Tạo embed thông báo thoát
        embed = create_embed(
            title="Thoát khỏi động phủ",
            description="Bạn đã thoát khỏi động phủ. Phần thưởng của bạn bị giảm 30%.",
            color=discord.Color.orange()
        )

        # Hiển thị phần thưởng còn lại
        embed.add_field(
            name="Phần thưởng còn lại",
            value=f"Kinh nghiệm: {format_number(rewards['exp'])}\n"
                  f"Linh thạch: {format_number(rewards['spirit_stones'])}\n"
                  f"Vật phẩm: {len(rewards['items'])}",
            inline=False
        )

        await dungeon_msg.edit(embed=embed, view=None)

        # Cập nhật phần thưởng vào database
        await self._update_rewards(ctx.author.id)

        # Xóa thông tin động phủ
        if ctx.author.id in self.active_dungeons:
            del self.active_dungeons[ctx.author.id]

    async def _update_rewards(self, user_id):
        """Cập nhật phần thưởng vào database"""
        if user_id not in self.active_dungeons:
            return

        rewards = self.active_dungeons[user_id]["rewards"]

        # Cập nhật kinh nghiệm
        if rewards["exp"] > 0:
            await self.db.add_exp(user_id, rewards["exp"])

        # Cập nhật linh thạch
        if rewards["spirit_stones"] > 0:
            await self.db.update_spirit_stones(user_id, rewards["spirit_stones"])

        # Cập nhật vật phẩm
        for item in rewards["items"]:
            await self.db.add_item(user_id, item["item_id"], item["quantity"])


def setup(bot):
    bot.add_cog(Dungeons(bot))
