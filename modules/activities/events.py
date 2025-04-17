import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import random
import logging
import json
import os
from typing import List, Dict, Any, Optional, Union

from database.mongo_handler import get_user_or_create, update_user, add_user_linh_thach, add_user_exp
from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR, EMOJI_LINH_THACH, EMOJI_EXP
)
from utils.text_utils import format_number, generate_random_quote
from utils.time_utils import format_seconds

# Cấu hình logging
logger = logging.getLogger("tutien-bot.events")


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_events = {}  # {event_id: event_data}
        self.load_events()
        self.event_check.start()

    def cog_unload(self):
        """Hủy task khi unload cog"""
        self.event_check.cancel()

    def load_events(self):
        """Tải danh sách sự kiện từ JSON"""
        try:
            if os.path.exists("data/events.json"):
                with open("data/events.json", "r", encoding="utf-8") as f:
                    self.event_templates = json.load(f)
                logger.info(f"Đã tải {len(self.event_templates.get('events', []))} mẫu sự kiện từ JSON")
            else:
                logger.warning("Không tìm thấy file data/events.json")
                # Tạo dữ liệu mặc định
                self.event_templates = self.create_default_events()

                # Lưu vào file
                os.makedirs("data", exist_ok=True)
                with open("data/events.json", "w", encoding="utf-8") as f:
                    json.dump(self.event_templates, f, ensure_ascii=False, indent=4)

                logger.info(
                    f"Đã tạo file events.json với {len(self.event_templates.get('events', []))} sự kiện mặc định")
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu sự kiện: {e}")
            self.event_templates = self.create_default_events()

    def create_default_events(self) -> Dict[str, List[Dict[str, Any]]]:
        """Tạo danh sách sự kiện mặc định"""
        return {
            "events": [
                {
                    "id": "danhdoi",
                    "name": "Đán Hội Đại Tái",
                    "description": "Sự kiện thi đấu võ đạo Đán Hội tổ chức 100 năm một lần, quy tụ các thiên tài tu tiên trẻ từ khắp nơi.",
                    "type": "combat",
                    "duration": 7200,  # 2 giờ
                    "cooldown": 86400,  # 24 giờ
                    "min_realm": 5,  # Luyện Khí tầng 5 trở lên
                    "max_realm": 12,  # Đến Trúc Cơ Viên Mãn
                    "rewards": {
                        "exp_min": 100,
                        "exp_max": 500,
                        "linh_thach_min": 100,
                        "linh_thach_max": 500,
                        "special_items": [
                            {"id": "danhhoi_medal", "name": "Huy Chương Đán Hội", "chance": 0.1}
                        ]
                    }
                },
                {
                    "id": "khoangsan",
                    "name": "Mỏ Linh Thạch",
                    "description": "Một mỏ linh thạch vừa được phát hiện! Hãy nhanh chóng đến khai thác.",
                    "type": "mining",
                    "duration": 3600,  # 1 giờ
                    "cooldown": 43200,  # 12 giờ
                    "min_realm": 1,  # Luyện Khí tầng 1 trở lên
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 10,
                        "exp_max": 100,
                        "linh_thach_min": 50,
                        "linh_thach_max": 300,
                        "special_items": [
                            {"id": "earth_crystal", "name": "Thổ Linh Tinh", "chance": 0.2},
                            {"id": "fire_crystal", "name": "Hỏa Linh Tinh", "chance": 0.2},
                            {"id": "water_crystal", "name": "Thủy Linh Tinh", "chance": 0.2},
                            {"id": "wood_crystal", "name": "Mộc Linh Tinh", "chance": 0.2},
                            {"id": "metal_crystal", "name": "Kim Linh Tinh", "chance": 0.2}
                        ]
                    }
                },
                {
                    "id": "thuclinh",
                    "name": "Thú Linh Xuất Hiện",
                    "description": "Một đàn thú linh đã xuất hiện tại khu rừng gần đây. Săn bắt chúng để nhận phần thưởng!",
                    "type": "hunting",
                    "duration": 5400,  # 1.5 giờ
                    "cooldown": 64800,  # 18 giờ
                    "min_realm": 3,  # Luyện Khí tầng 3 trở lên
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 50,
                        "exp_max": 200,
                        "linh_thach_min": 30,
                        "linh_thach_max": 200,
                        "special_items": [
                            {"id": "beast_core", "name": "Thú Linh Đan", "chance": 0.3},
                            {"id": "beast_hide", "name": "Da Thú Linh", "chance": 0.5},
                            {"id": "beast_claw", "name": "Vuốt Thú Linh", "chance": 0.4}
                        ]
                    }
                },
                {
                    "id": "haiduong",
                    "name": "Hải Dương Linh Quả",
                    "description": "Một loại linh quả hiếm có mọc dưới đáy biển đã chín muồi. Hãy lặn xuống hái nó!",
                    "type": "gathering",
                    "duration": 3600,  # 1 giờ
                    "cooldown": 72000,  # 20 giờ
                    "min_realm": 7,  # Luyện Khí tầng 7 trở lên
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 80,
                        "exp_max": 300,
                        "linh_thach_min": 80,
                        "linh_thach_max": 250,
                        "special_items": [
                            {"id": "ocean_fruit", "name": "Hải Dương Linh Quả", "chance": 0.2},
                            {"id": "sea_pearl", "name": "Hải Châu", "chance": 0.3},
                            {"id": "water_essence", "name": "Thủy Chi Tinh Hoa", "chance": 0.15}
                        ]
                    }
                },
                {
                    "id": "luyendan",
                    "name": "Luyện Đan Đại Hội",
                    "description": "Một cuộc thi luyện đan được tổ chức. Hãy tham gia để trổ tài luyện đan của bạn!",
                    "type": "crafting",
                    "duration": 4500,  # 1.25 giờ
                    "cooldown": 54000,  # 15 giờ
                    "min_realm": 9,  # Luyện Khí tầng 9 trở lên
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 100,
                        "exp_max": 400,
                        "linh_thach_min": 100,
                        "linh_thach_max": 400,
                        "special_items": [
                            {"id": "spirit_pill", "name": "Linh Đan", "chance": 0.25},
                            {"id": "healing_pill", "name": "Linh Hồi Đan", "chance": 0.35},
                            {"id": "pill_recipe", "name": "Đan Phương", "chance": 0.1}
                        ]
                    }
                },
                {
                    "id": "sapmothienti",
                    "name": "Sấm Mở Thiên Địa",
                    "description": "Một hiện tượng thiên địa hiếm gặp đang xảy ra! Nhanh chóng ngồi xuống tu luyện để cảm ngộ thiên đạo!",
                    "type": "meditation",
                    "duration": 2700,  # 45 phút
                    "cooldown": 129600,  # 36 giờ
                    "min_realm": 0,  # Tất cả các cảnh giới
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 200,
                        "exp_max": 1000,
                        "linh_thach_min": 50,
                        "linh_thach_max": 200,
                        "special_items": [
                            {"id": "enlightenment", "name": "Thiên Đạo Cảm Ngộ", "chance": 0.05},
                            {"id": "dao_fragment", "name": "Đạo Vận Mảnh", "chance": 0.2}
                        ]
                    }
                },
                {
                    "id": "phongmothienky",
                    "name": "Phong Mở Thiên Ký",
                    "description": "Một luồng phong nguyên tố vừa xuất hiện! Tiếp nhận lực lượng phong nguyên tố để tăng cường sức mạnh!",
                    "type": "elemental",
                    "duration": 2700,  # 45 phút
                    "cooldown": 100800,  # 28 giờ
                    "min_realm": 4,  # Luyện Khí tầng 4 trở lên
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 150,
                        "exp_max": 600,
                        "linh_thach_min": 80,
                        "linh_thach_max": 300,
                        "special_items": [
                            {"id": "wind_essence", "name": "Phong Chi Tinh Hoa", "chance": 0.15},
                            {"id": "feather_artifact", "name": "Phi Vũ", "chance": 0.05}
                        ]
                    }
                },
                {
                    "id": "chienthanh",
                    "name": "Chiến Thành Thủ Vệ",
                    "description": "Một đội quân tà ma đang tấn công thành phố! Hãy tham gia bảo vệ thành phố!",
                    "type": "defense",
                    "duration": 5400,  # 1.5 giờ
                    "cooldown": 86400,  # 24 giờ
                    "min_realm": 10,  # Trúc Cơ Sơ Kỳ trở lên
                    "max_realm": 28,  # Không giới hạn cảnh giới
                    "rewards": {
                        "exp_min": 300,
                        "exp_max": 1200,
                        "linh_thach_min": 200,
                        "linh_thach_max": 800,
                        "special_items": [
                            {"id": "hero_medal", "name": "Anh Hùng Lệnh", "chance": 0.1},
                            {"id": "demon_core", "name": "Ma Tinh", "chance": 0.3},
                            {"id": "city_reward", "name": "Thành Thưởng", "chance": 0.5}
                        ]
                    }
                }
            ]
        }

    @tasks.loop(minutes=5)
    async def event_check(self):
        """Kiểm tra và tạo sự kiện ngẫu nhiên"""
        try:
            # Chỉ tạo sự kiện khi có ít hơn 2 sự kiện đang hoạt động
            if len(self.active_events) < 2:
                # Có 15% cơ hội tạo sự kiện mới mỗi 5 phút
                if random.random() < 0.15:
                    await self.create_random_event()

            # Kiểm tra các sự kiện đã hết thời gian
            current_time = datetime.datetime.now()
            events_to_remove = []

            for event_id, event_data in self.active_events.items():
                end_time = datetime.datetime.fromisoformat(event_data["end_time"])
                if current_time > end_time:
                    events_to_remove.append(event_id)

            # Kết thúc các sự kiện đã hết thời gian
            for event_id in events_to_remove:
                await self.end_event(event_id)

        except Exception as e:
            logger.error(f"Lỗi trong event_check: {e}")

    @event_check.before_loop
    async def before_event_check(self):
        """Đợi bot sẵn sàng trước khi bắt đầu kiểm tra sự kiện"""
        await self.bot.wait_until_ready()

    async def create_random_event(self):
        """Tạo một sự kiện ngẫu nhiên"""
        try:
            # Kiểm tra có sự kiện nào có sẵn không
            available_events = self.event_templates.get("events", [])
            if not available_events:
                return

            # Chọn ngẫu nhiên một sự kiện
            event_template = random.choice(available_events)

            # Tạo ID duy nhất cho sự kiện
            event_id = f"{event_template['id']}_{int(datetime.datetime.now().timestamp())}"

            # Thiết lập thời gian
            start_time = datetime.datetime.now()
            end_time = start_time + datetime.timedelta(seconds=event_template["duration"])

            # Tạo dữ liệu sự kiện
            event_data = {
                "id": event_id,
                "template_id": event_template["id"],
                "name": event_template["name"],
                "description": event_template["description"],
                "type": event_template["type"],
                "min_realm": event_template["min_realm"],
                "max_realm": event_template["max_realm"],
                "rewards": event_template["rewards"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "participants": []
            }

            # Thêm vào danh sách sự kiện đang hoạt động
            self.active_events[event_id] = event_data

            # Thông báo sự kiện mới
            await self.announce_event(event_data)

            # Log thông tin
            logger.info(f"Đã tạo sự kiện mới: {event_data['name']} (ID: {event_id})")

        except Exception as e:
            logger.error(f"Lỗi khi tạo sự kiện ngẫu nhiên: {e}")

    async def announce_event(self, event_data: Dict[str, Any]):
        """Thông báo sự kiện mới"""
        try:
            # Tạo embed thông báo
            embed = discord.Embed(
                title=f"🎉 Sự Kiện Mới: {event_data['name']}",
                description=event_data["description"],
                color=discord.Color.gold()
            )

            # Thêm thông tin
            start_time = datetime.datetime.fromisoformat(event_data["start_time"])
            end_time = datetime.datetime.fromisoformat(event_data["end_time"])
            duration = (end_time - start_time).total_seconds()

            embed.add_field(
                name="Thời Gian",
                value=f"Kết thúc sau: **{format_seconds(duration)}**",
                inline=True
            )

            # Thêm thông tin cảnh giới yêu cầu
            min_realm_name = CULTIVATION_REALMS[event_data["min_realm"]]["name"] if event_data["min_realm"] < len(
                CULTIVATION_REALMS) else "Không giới hạn"
            max_realm_name = CULTIVATION_REALMS[event_data["max_realm"]]["name"] if event_data["max_realm"] < len(
                CULTIVATION_REALMS) else "Không giới hạn"

            realm_text = f"Từ **{min_realm_name}**"
            if event_data["max_realm"] < len(CULTIVATION_REALMS) - 1:
                realm_text += f" đến **{max_realm_name}**"

            embed.add_field(
                name="Yêu Cầu Cảnh Giới",
                value=realm_text,
                inline=True
            )

            # Thêm loại sự kiện
            event_types = {
                "combat": "⚔️ Chiến Đấu",
                "mining": "⛏️ Khai Thác",
                "hunting": "🏹 Săn Bắn",
                "gathering": "🌿 Thu Thập",
                "crafting": "⚒️ Chế Tạo",
                "meditation": "🧘 Tu Luyện",
                "elemental": "🌀 Nguyên Tố",
                "defense": "🛡️ Phòng Thủ"
            }

            event_type = event_types.get(event_data["type"], event_data["type"])

            embed.add_field(
                name="Loại Sự Kiện",
                value=event_type,
                inline=True
            )

            # Thêm phần thưởng
            rewards = event_data["rewards"]
            reward_text = (
                f"{EMOJI_EXP} Kinh nghiệm: **{rewards['exp_min']} - {rewards['exp_max']}**\n"
                f"{EMOJI_LINH_THACH} Linh thạch: **{rewards['linh_thach_min']} - {rewards['linh_thach_max']}**"
            )

            if "special_items" in rewards and rewards["special_items"]:
                reward_text += "\n**Vật phẩm đặc biệt:**\n"
                for item in rewards["special_items"]:
                    chance_percent = item["chance"] * 100
                    reward_text += f"- {item['name']} ({chance_percent:.1f}%)\n"

            embed.add_field(
                name="Phần Thưởng",
                value=reward_text,
                inline=False
            )

            # Thêm hướng dẫn tham gia
            embed.add_field(
                name="Cách Tham Gia",
                value=f"Sử dụng lệnh `!sukien thamgia {event_data['id']}` để tham gia sự kiện.",
                inline=False
            )

            # Thêm footer
            embed.set_footer(
                text=f"ID Sự kiện: {event_data['id']} • Bắt đầu lúc: {start_time.strftime('%H:%M:%S %d/%m/%Y')}")

            # Gửi thông báo đến tất cả các server
            for guild in self.bot.guilds:
                # Tìm kênh thông báo hoặc general
                announcement_channel = discord.utils.get(guild.text_channels, name="thông-báo") or discord.utils.get(
                    guild.text_channels, name="thongbao") or discord.utils.get(guild.text_channels,
                                                                               name="announcements") or discord.utils.get(
                    guild.text_channels, name="general") or discord.utils.get(guild.text_channels, name="chung")

                if announcement_channel and announcement_channel.permissions_for(guild.me).send_messages:
                    await announcement_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Lỗi khi thông báo sự kiện: {e}")

    async def end_event(self, event_id: str):
        """Kết thúc một sự kiện"""
        try:
            # Kiểm tra sự kiện có tồn tại không
            if event_id not in self.active_events:
                return

            # Lấy thông tin sự kiện
            event_data = self.active_events[event_id]

            # Xóa sự kiện khỏi danh sách
            del self.active_events[event_id]

            # Thông báo kết thúc sự kiện
            await self.announce_event_end(event_data)

            # Log thông tin
            logger.info(f"Đã kết thúc sự kiện: {event_data['name']} (ID: {event_id})")

        except Exception as e:
            logger.error(f"Lỗi khi kết thúc sự kiện: {e}")

    async def announce_event_end(self, event_data: Dict[str, Any]):
        """Thông báo kết thúc sự kiện"""
        try:
            # Tạo embed thông báo
            embed = discord.Embed(
                title=f"🏁 Sự Kiện Kết Thúc: {event_data['name']}",
                description=f"Sự kiện **{event_data['name']}** đã kết thúc!",
                color=discord.Color.dark_blue()
            )

            # Thêm thông tin người tham gia
            participants = event_data.get("participants", [])

            if participants:
                embed.add_field(
                    name="Số Người Tham Gia",
                    value=str(len(participants)),
                    inline=True
                )

                # Hiển thị top 5 người có nhiều điểm nhất
                if len(participants) > 1:
                    participants.sort(key=lambda x: x.get("points", 0), reverse=True)
                    top_participants = participants[:5]

                    top_text = ""
                    for i, participant in enumerate(top_participants, 1):
                        user_id = participant["user_id"]
                        points = participant.get("points", 0)

                        user = self.bot.get_user(user_id)
                        name = user.name if user else f"User {user_id}"

                        top_text += f"{i}. **{name}** - {points} điểm\n"

                    embed.add_field(
                        name="Top Người Tham Gia",
                        value=top_text,
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Số Người Tham Gia",
                    value="Không có ai tham gia sự kiện này.",
                    inline=True
                )

            # Gửi thông báo đến tất cả các server
            for guild in self.bot.guilds:
                # Tìm kênh thông báo hoặc general
                announcement_channel = discord.utils.get(guild.text_channels, name="thông-báo") or discord.utils.get(
                    guild.text_channels, name="thongbao") or discord.utils.get(guild.text_channels,
                                                                               name="announcements") or discord.utils.get(
                    guild.text_channels, name="general") or discord.utils.get(guild.text_channels, name="chung")

                if announcement_channel and announcement_channel.permissions_for(guild.me).send_messages:
                    await announcement_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Lỗi khi thông báo kết thúc sự kiện: {e}")

    @commands.group(name="sukien", aliases=["event", "sk"], invoke_without_command=True)
    async def event(self, ctx):
        """Hiển thị danh sách sự kiện đang diễn ra"""
        # Kiểm tra có sự kiện nào đang diễn ra không
        if not self.active_events:
            embed = discord.Embed(
                title="📅 Sự Kiện",
                description="Hiện tại không có sự kiện nào đang diễn ra.",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        # Tạo embed hiển thị danh sách sự kiện
        embed = discord.Embed(
            title="📅 Sự Kiện Đang Diễn Ra",
            description=f"Hiện có **{len(self.active_events)}** sự kiện đang diễn ra:",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng sự kiện
        for event_id, event_data in self.active_events.items():
            # Tính thời gian còn lại
            end_time = datetime.datetime.fromisoformat(event_data["end_time"])
            time_left = (end_time - datetime.datetime.now()).total_seconds()

            if time_left <= 0:
                continue  # Bỏ qua sự kiện đã kết thúc

            # Thêm vào embed
            embed.add_field(
                name=event_data["name"],
                value=(
                    f"{event_data['description']}\n"
                    f"⏳ Kết thúc sau: **{format_seconds(time_left)}**\n"
                    f"👥 Người tham gia: **{len(event_data.get('participants', []))}**\n"
                    f"🔍 ID: `{event_id}`"
                ),
                inline=False
            )

        # Thêm hướng dẫn
        embed.add_field(
            name="Lệnh Hữu Ích",
            value=(
                "`!sukien info [ID]` - Xem thông tin chi tiết về sự kiện\n"
                "`!sukien thamgia [ID]` - Tham gia sự kiện\n"
                "`!sukien huydangky [ID]` - Hủy đăng ký tham gia sự kiện"
            ),
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @event.command(name="info", aliases=["thongtin", "chitiet"])
    async def event_info(self, ctx, event_id: str):
        """Hiển thị thông tin chi tiết về một sự kiện"""
        # Kiểm tra sự kiện có tồn tại không
        if event_id not in self.active_events:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Không tìm thấy sự kiện với ID đã cung cấp.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin sự kiện
        event_data = self.active_events[event_id]

        # Tạo embed
        embed = discord.Embed(
            title=f"📋 Thông Tin Sự Kiện: {event_data['name']}",
            description=event_data["description"],
            color=EMBED_COLOR
        )

        # Thêm thông tin thời gian
        start_time = datetime.datetime.fromisoformat(event_data["start_time"])
        end_time = datetime.datetime.fromisoformat(event_data["end_time"])
        time_left = (end_time - datetime.datetime.now()).total_seconds()

        embed.add_field(
            name="Thời Gian",
            value=(
                f"Bắt đầu: **{start_time.strftime('%H:%M:%S %d/%m/%Y')}**\n"
                f"Kết thúc: **{end_time.strftime('%H:%M:%S %d/%m/%Y')}**\n"
                f"Thời gian còn lại: **{format_seconds(time_left)}**"
            ),
            inline=False
        )

        # Thêm thông tin cảnh giới yêu cầu
        min_realm_name = CULTIVATION_REALMS[event_data["min_realm"]]["name"] if event_data["min_realm"] < len(
            CULTIVATION_REALMS) else "Không giới hạn"
        max_realm_name = CULTIVATION_REALMS[event_data["max_realm"]]["name"] if event_data["max_realm"] < len(
            CULTIVATION_REALMS) else "Không giới hạn"

        realm_text = f"Từ **{min_realm_name}**"
        if event_data["max_realm"] < len(CULTIVATION_REALMS) - 1:
            realm_text += f" đến **{max_realm_name}**"

        embed.add_field(
            name="Yêu Cầu Cảnh Giới",
            value=realm_text,
            inline=True
        )

        # Thêm loại sự kiện
        event_types = {
            "combat": "⚔️ Chiến Đấu",
            "mining": "⛏️ Khai Thác",
            "hunting": "🏹 Săn Bắn",
            "gathering": "🌿 Thu Thập",
            "crafting": "⚒️ Chế Tạo",
            "meditation": "🧘 Tu Luyện",
            "elemental": "🌀 Nguyên Tố",
            "defense": "🛡️ Phòng Thủ"
        }

        event_type = event_types.get(event_data["type"], event_data["type"])

        embed.add_field(
            name="Loại Sự Kiện",
            value=event_type,
            inline=True
        )

        # Thêm phần thưởng
        rewards = event_data["rewards"]
        reward_text = (
            f"{EMOJI_EXP} Kinh nghiệm: **{rewards['exp_min']} - {rewards['exp_max']}**\n"
            f"{EMOJI_LINH_THACH} Linh thạch: **{rewards['linh_thach_min']} - {rewards['linh_thach_max']}**"
        )

        if "special_items" in rewards and rewards["special_items"]:
            reward_text += "\n**Vật phẩm đặc biệt:**\n"
            for item in rewards["special_items"]:
                chance_percent = item["chance"] * 100
                reward_text += f"- {item['name']} ({chance_percent:.1f}%)\n"

        embed.add_field(
            name="Phần Thưởng",
            value=reward_text,
            inline=False
        )

        # Thêm thông tin người tham gia
        participants = event_data.get("participants", [])

        if participants:
            participant_text = f"Tổng số: **{len(participants)}** người\n\n"

            # Hiển thị top 5 người tham gia
            if len(participants) > 1:
                sorted_participants = sorted(participants, key=lambda x: x.get("points", 0), reverse=True)
                top_participants = sorted_participants[:5]

                participant_text += "**Top 5:**\n"
                for i, participant in enumerate(top_participants, 1):
                    user_id = participant["user_id"]
                    points = participant.get("points", 0)

                    user = self.bot.get_user(user_id)
                    name = user.name if user else f"User {user_id}"

                    participant_text += f"{i}. **{name}** - {points} điểm\n"

            embed.add_field(
                name="Người Tham Gia",
                value=participant_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Người Tham Gia",
                value="Chưa có ai tham gia sự kiện này.",
                inline=False
            )

        # Thêm trạng thái đăng ký của người dùng
        user_participating = False
        for participant in participants:
            if participant["user_id"] == ctx.author.id:
                user_participating = True
                break

        if user_participating:
            embed.add_field(
                name="Trạng Thái",
                value="Bạn đã đăng ký tham gia sự kiện này.",
                inline=True
            )
        else:
            # Kiểm tra xem người dùng có đủ điều kiện tham gia không
            user = await get_user_or_create(ctx.author.id, ctx.author.name)
            user_realm_id = user.get("realm_id", 0)

            if user_realm_id < event_data["min_realm"] or user_realm_id > event_data["max_realm"]:
                embed.add_field(
                    name="Trạng Thái",
                    value=f"Bạn không đủ điều kiện tham gia (cảnh giới của bạn: **{CULTIVATION_REALMS[user_realm_id]['name']}**).",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Trạng Thái",
                    value=f"Bạn chưa đăng ký tham gia. Sử dụng `!sukien thamgia {event_id}` để tham gia.",
                    inline=True
                )

        # Gửi embed
        await ctx.send(embed=embed)

    @event.command(name="thamgia", aliases=["join", "tg", "dangky"])
    async def join_event(self, ctx, event_id: str):
        """Tham gia một sự kiện"""
        # Kiểm tra sự kiện có tồn tại không
        if event_id not in self.active_events:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Không tìm thấy sự kiện với ID đã cung cấp.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin sự kiện
        event_data = self.active_events[event_id]

        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)
        user_realm_id = user.get("realm_id", 0)

        # Kiểm tra cảnh giới yêu cầu
        if user_realm_id < event_data["min_realm"] or user_realm_id > event_data["max_realm"]:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=(
                    f"Bạn không đủ điều kiện tham gia sự kiện này.\n\n"
                    f"Yêu cầu cảnh giới: từ **{CULTIVATION_REALMS[event_data['min_realm']]['name']}** "
                    f"đến **{CULTIVATION_REALMS[event_data['max_realm']]['name']}**\n"
                    f"Cảnh giới của bạn: **{CULTIVATION_REALMS[user_realm_id]['name']}**"
                ),
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra đã tham gia chưa
        participants = event_data.get("participants", [])

        for participant in participants:
            if participant["user_id"] == ctx.author.id:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Bạn đã đăng ký tham gia sự kiện này rồi.",
                    color=EMBED_COLOR_ERROR
                )
                return await ctx.send(embed=embed)

        # Thêm người dùng vào danh sách tham gia
        new_participant = {
            "user_id": ctx.author.id,
            "join_time": datetime.datetime.now().isoformat(),
            "points": 0
        }

        self.active_events[event_id]["participants"].append(new_participant)

        # Tạo embed thông báo
        embed = discord.Embed(
            title="✅ Đăng Ký Thành Công",
            description=f"Bạn đã đăng ký tham gia sự kiện **{event_data['name']}**!",
            color=EMBED_COLOR_SUCCESS
        )

        # Thêm thông tin thời gian còn lại
        end_time = datetime.datetime.fromisoformat(event_data["end_time"])
        time_left = (end_time - datetime.datetime.now()).total_seconds()

        embed.add_field(
            name="Thời Gian Còn Lại",
            value=format_seconds(time_left),
            inline=True
        )

        # Thêm hướng dẫn
        event_types = {
            "combat": "Hãy sử dụng lệnh `!danhquai` và `!danhboss` để tích lũy điểm.",
            "mining": "Hãy sử dụng lệnh `!daomo` để tích lũy điểm.",
            "hunting": "Hãy sử dụng lệnh `!sanban` để tích lũy điểm.",
            "gathering": "Hãy sử dụng lệnh `!haithuoc` để tích lũy điểm.",
            "crafting": "Hãy sử dụng lệnh `!luyendan` để tích lũy điểm.",
            "meditation": "Hãy sử dụng lệnh `!tunluyen` để tích lũy điểm.",
            "elemental": "Hãy sử dụng lệnh `!nguyento` để tích lũy điểm.",
            "defense": "Hãy sử dụng lệnh `!phongve` để tích lũy điểm."
        }

        guide_text = event_types.get(event_data["type"], "Sử dụng các lệnh liên quan để tích lũy điểm.")

        embed.add_field(
            name="Hướng Dẫn",
            value=guide_text,
            inline=False
        )

        # Thêm thông tin huỷ đăng ký
        embed.add_field(
            name="Huỷ Đăng Ký",
            value=f"Nếu bạn muốn huỷ đăng ký, sử dụng lệnh `!sukien huydangky {event_id}`.",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log thông tin
        logger.info(f"Người dùng {ctx.author.name} đã đăng ký tham gia sự kiện {event_data['name']} (ID: {event_id})")

        # Cập nhật điểm ngẫu nhiên (giả lập việc tham gia)
        await self.simulate_event_participation(event_id, ctx.author.id)

    @event.command(name="huydangky", aliases=["leave", "huy", "cancel"])
    async def leave_event(self, ctx, event_id: str):
        """Huỷ đăng ký tham gia sự kiện"""
        # Kiểm tra sự kiện có tồn tại không
        if event_id not in self.active_events:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Không tìm thấy sự kiện với ID đã cung cấp.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin sự kiện
        event_data = self.active_events[event_id]

        # Kiểm tra đã tham gia chưa
        participants = event_data.get("participants", [])
        participant_index = None

        for i, participant in enumerate(participants):
            if participant["user_id"] == ctx.author.id:
                participant_index = i
                break

        if participant_index is None:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn chưa đăng ký tham gia sự kiện này.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Xóa người dùng khỏi danh sách tham gia
        del self.active_events[event_id]["participants"][participant_index]

        # Tạo embed thông báo
        embed = discord.Embed(
            title="✅ Huỷ Đăng Ký Thành Công",
            description=f"Bạn đã huỷ đăng ký tham gia sự kiện **{event_data['name']}**.",
            color=EMBED_COLOR_SUCCESS
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log thông tin
        logger.info(
            f"Người dùng {ctx.author.name} đã huỷ đăng ký tham gia sự kiện {event_data['name']} (ID: {event_id})")

    @event.command(name="taosu", aliases=["create", "new"])
    @commands.has_permissions(administrator=True)
    async def create_event(self, ctx, template_id: str, duration_hours: float = None):
        """Tạo một sự kiện mới (chỉ dành cho quản trị viên)"""
        # Tìm mẫu sự kiện
        template = None
        for event_template in self.event_templates["events"]:
            if event_template["id"] == template_id:
                template = event_template
                break

        if not template:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy mẫu sự kiện với ID '{template_id}'.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Đặt thời lượng sự kiện
        duration = template["duration"]
        if duration_hours:
            duration = int(duration_hours * 3600)

        # Tạo ID duy nhất cho sự kiện
        event_id = f"{template_id}_{int(datetime.datetime.now().timestamp())}"

        # Thiết lập thời gian
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=duration)

        # Tạo dữ liệu sự kiện
        event_data = {
            "id": event_id,
            "template_id": template["id"],
            "name": template["name"],
            "description": template["description"],
            "type": template["type"],
            "min_realm": template["min_realm"],
            "max_realm": template["max_realm"],
            "rewards": template["rewards"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "participants": []
        }

        # Thêm vào danh sách sự kiện đang hoạt động
        self.active_events[event_id] = event_data

        # Thông báo sự kiện mới
        await self.announce_event(event_data)

        # Tạo embed thông báo cho người tạo
        embed = discord.Embed(
            title="✅ Đã Tạo Sự Kiện",
            description=f"Sự kiện **{event_data['name']}** đã được tạo thành công!",
            color=EMBED_COLOR_SUCCESS
        )

        # Thêm ID sự kiện
        embed.add_field(
            name="ID Sự Kiện",
            value=event_id,
            inline=True
        )

        # Thêm thời gian
        embed.add_field(
            name="Thời Gian",
            value=f"Kết thúc sau: **{format_seconds(duration)}**",
            inline=True
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log thông tin
        logger.info(f"Quản trị viên {ctx.author.name} đã tạo sự kiện {event_data['name']} (ID: {event_id})")

    @event.command(name="ketthuc", aliases=["end", "stop"])
    @commands.has_permissions(administrator=True)
    async def end_event_command(self, ctx, event_id: str):
        """Kết thúc một sự kiện (chỉ dành cho quản trị viên)"""
        # Kiểm tra sự kiện có tồn tại không
        if event_id not in self.active_events:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Không tìm thấy sự kiện với ID đã cung cấp.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin sự kiện
        event_data = self.active_events[event_id]

        # Kết thúc sự kiện
        await self.end_event(event_id)

        # Tạo embed thông báo
        embed = discord.Embed(
            title="✅ Đã Kết Thúc Sự Kiện",
            description=f"Sự kiện **{event_data['name']}** đã được kết thúc thủ công.",
            color=EMBED_COLOR_SUCCESS
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log thông tin
        logger.info(f"Quản trị viên {ctx.author.name} đã kết thúc sự kiện {event_data['name']} (ID: {event_id})")

    @event.command(name="danhsach", aliases=["list", "ds"])
    async def list_event_templates(self, ctx):
        """Hiển thị danh sách các mẫu sự kiện có sẵn"""
        templates = self.event_templates.get("events", [])

        if not templates:
            embed = discord.Embed(
                title="📋 Danh Sách Mẫu Sự Kiện",
                description="Không có mẫu sự kiện nào có sẵn.",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        # Tạo embed
        embed = discord.Embed(
            title="📋 Danh Sách Mẫu Sự Kiện",
            description=f"Có **{len(templates)}** mẫu sự kiện có sẵn:",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng mẫu
        for template in templates:
            # Thêm vào embed
            min_realm_name = CULTIVATION_REALMS[template["min_realm"]]["name"] if template["min_realm"] < len(
                CULTIVATION_REALMS) else "Không giới hạn"

            embed.add_field(
                name=f"{template['name']} (ID: {template['id']})",
                value=(
                    f"{template['description']}\n"
                    f"Loại: **{template['type']}**\n"
                    f"Yêu cầu cảnh giới: **{min_realm_name}** trở lên\n"
                    f"Thời lượng mặc định: **{format_seconds(template['duration'])}**"
                ),
                inline=False
            )

        # Thêm hướng dẫn cho admin
        if ctx.author.guild_permissions.administrator:
            embed.add_field(
                name="Dành Cho Quản Trị Viên",
                value="`!sukien taosu [template_id] [duration_hours]` - Tạo một sự kiện mới từ mẫu",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @event.command(name="thuong", aliases=["reward", "nhan"])
    async def claim_event_rewards(self, ctx, event_id: str):
        """Nhận phần thưởng từ sự kiện đã kết thúc"""
        # TODO: Implement reward claiming
        embed = discord.Embed(
            title="⚠️ Chưa Triển Khai",
            description="Tính năng này đang được phát triển và sẽ có trong bản cập nhật sắp tới.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    async def simulate_event_participation(self, event_id: str, user_id: int):
        """Giả lập việc tham gia sự kiện và cập nhật điểm"""
        # Chỉ dùng cho mục đích minh họa
        try:
            # Ngẫu nhiên cộng điểm trong khoảng thời gian
            for _ in range(random.randint(3, 8)):
                # Kiểm tra sự kiện có còn tồn tại không
                if event_id not in self.active_events:
                    break

                # Tìm người dùng trong danh sách tham gia
                participants = self.active_events[event_id]["participants"]
                participant_index = None

                for i, participant in enumerate(participants):
                    if participant["user_id"] == user_id:
                        participant_index = i
                        break

                if participant_index is None:
                    break

                # Cộng điểm ngẫu nhiên
                points = random.randint(10, 50)
                self.active_events[event_id]["participants"][participant_index]["points"] += points

                # Đợi một khoảng thời gian ngẫu nhiên
                await asyncio.sleep(random.randint(300, 900))  # 5-15 phút
        except Exception as e:
            logger.error(f"Lỗi khi giả lập tham gia sự kiện: {e}")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Bắt sự kiện khi có lệnh được gọi"""
        # Kiểm tra người dùng có tham gia sự kiện nào không
        for event_id, event_data in self.active_events.items():
            participants = event_data.get("participants", [])
            participant_index = None

            for i, participant in enumerate(participants):
                if participant["user_id"] == ctx.author.id:
                    participant_index = i
                    break

            if participant_index is None:
                continue

            # Nếu lệnh phù hợp với loại sự kiện, cộng điểm
            command_name = ctx.command.name.lower()
            event_type = event_data["type"]

            if self.is_event_related_command(command_name, event_type):
                # Cộng điểm
                points = random.randint(5, 15)
                self.active_events[event_id]["participants"][participant_index]["points"] += points

    def is_event_related_command(self, command_name: str, event_type: str) -> bool:
        """Kiểm tra xem lệnh có liên quan đến loại sự kiện không"""
        event_commands = {
            "combat": ["danhquai", "danhboss", "combat", "pk", "pvp"],
            "mining": ["daomo", "khaithac", "mine"],
            "hunting": ["sanban", "danhquai", "hunt"],
            "gathering": ["haithuoc", "gather", "collect"],
            "crafting": ["luyendan", "craft", "che"],
            "meditation": ["tunluyen", "meditate", "tu"],
            "elemental": ["nguyento", "element"],
            "defense": ["phongve", "defend", "defense"]
        }

        related_commands = event_commands.get(event_type, [])
        return command_name in related_commands


async def setup(bot):
    await bot.add_cog(EventsCog(bot))