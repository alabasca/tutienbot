import discord
from discord.ext import commands
import asyncio
import logging
from typing import Dict, List, Optional

from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMOJI_LINH_THACH, EMOJI_EXP,
    EMOJI_HEALTH, EMOJI_ATTACK, EMOJI_DEFENSE, DANHQUAI_COOLDOWN,
    DANHBOSS_COOLDOWN, COMBAT_COOLDOWN
)

# Cấu hình logging
logger = logging.getLogger("tutien-bot.help")


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.original_help_command


class CustomHelpCommand(commands.HelpCommand):
    """Lệnh help tùy chỉnh"""

    async def send_bot_help(self, mapping):
        """Hiển thị tổng quan các lệnh"""
        ctx = self.context

        # Tạo embed
        embed = discord.Embed(
            title="🔮 Trợ Giúp Tu Tiên Bot",
            description="Bot Discord về đề tài tu tiên, nơi bạn có thể tu luyện, chiến đấu và khám phá thế giới tiên hiệp!",
            color=EMBED_COLOR
        )

        # Thêm hình ảnh
        embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)

        # Nhóm các lệnh theo cog
        command_groups = {}
        for cog, cmds in mapping.items():
            # Bỏ qua lệnh trợ giúp
            filtered_cmds = [cmd for cmd in cmds if cmd.qualified_name != "help"]

            if not filtered_cmds:
                continue

            cog_name = getattr(cog, "qualified_name", "Khác")

            # Đổi tên cog thành tiếng Việt
            translated_name = self.translate_cog_name(cog_name)

            # Thêm vào dict
            command_groups[translated_name] = filtered_cmds

        # Thêm các nhóm lệnh vào embed
        for group_name, cmds in command_groups.items():
            # Tạo danh sách tên lệnh
            cmd_names = [f"`!{cmd.name}`" for cmd in cmds]
            cmd_desc = ", ".join(cmd_names)

            # Thêm vào embed
            embed.add_field(
                name=group_name,
                value=cmd_desc,
                inline=False
            )

        # Thêm hướng dẫn
        embed.add_field(
            name="Cách Sử Dụng",
            value="Sử dụng `!help [lệnh]` để xem thêm chi tiết về một lệnh cụ thể.",
            inline=False
        )

        # Thêm thông tin bot
        embed.set_footer(text="Tu Tiên Bot | Hãy bắt đầu hành trình tu tiên của bạn!")

        # Gửi embed
        await ctx.send(embed=embed)

    async def send_command_help(self, command):
        """Hiển thị thông tin chi tiết về một lệnh"""
        ctx = self.context

        # Tạo embed
        embed = discord.Embed(
            title=f"Lệnh: !{command.name}",
            description=command.help or "Không có mô tả chi tiết.",
            color=EMBED_COLOR
        )

        # Thêm cú pháp
        embed.add_field(
            name="Cú Pháp",
            value=f"`!{command.name}`",
            inline=False
        )

        # Thêm bí danh (aliases) nếu có
        if command.aliases:
            aliases = [f"`!{alias}`" for alias in command.aliases]
            embed.add_field(
                name="Lệnh Thay Thế",
                value=", ".join(aliases),
                inline=False
            )

        # Thêm thông tin cooldown nếu có
        if command.name in ["danhquai", "danhboss", "combat"]:
            cooldown_text = ""
            if command.name == "danhquai":
                minutes = DANHQUAI_COOLDOWN // 60
                cooldown_text = f"{minutes} phút"
            elif command.name == "danhboss":
                minutes = DANHBOSS_COOLDOWN // 60
                cooldown_text = f"{minutes} phút"
            elif command.name == "combat":
                minutes = COMBAT_COOLDOWN // 60
                cooldown_text = f"{minutes} phút"

            if cooldown_text:
                embed.add_field(
                    name="Thời Gian Hồi",
                    value=cooldown_text,
                    inline=False
                )

        # Gửi embed
        await ctx.send(embed=embed)

    async def send_group_help(self, group):
        """Hiển thị trợ giúp cho nhóm lệnh"""
        ctx = self.context

        # Tạo embed
        embed = discord.Embed(
            title=f"Nhóm Lệnh: !{group.name}",
            description=group.help or "Không có mô tả chi tiết.",
            color=EMBED_COLOR
        )

        # Thêm thông tin các lệnh con
        for command in group.commands:
            embed.add_field(
                name=f"!{command.name}",
                value=command.help or "Không có mô tả.",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    async def send_cog_help(self, cog):
        """Hiển thị trợ giúp cho một cog"""
        ctx = self.context

        # Tạo embed
        embed = discord.Embed(
            title=f"Nhóm: {self.translate_cog_name(cog.qualified_name)}",
            description="Danh sách các lệnh trong nhóm này:",
            color=EMBED_COLOR
        )

        # Thêm từng lệnh
        for command in cog.get_commands():
            embed.add_field(
                name=f"!{command.name}",
                value=command.help or "Không có mô tả.",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    def translate_cog_name(self, cog_name):
        """Dịch tên cog sang tiếng Việt"""
        translations = {
            "CultivationCog": "🧘 Tu Luyện",
            "CombatCog": "⚔️ Chiến Đấu",
            "MonsterCog": "👹 Quái Vật",
            "InventoryCog": "🎒 Kho Đồ",
            "DailyCog": "📅 Điểm Danh",
            "SectCog": "🏛️ Môn Phái",
            "HelpCog": "❓ Trợ Giúp",
            "ErrorHandlerCog": "🛠️ Xử Lý Lỗi"
        }
        return translations.get(cog_name, cog_name)

    async def send_error_message(self, error):
        """Gửi thông báo lỗi"""
        ctx = self.context

        # Tạo embed
        embed = discord.Embed(
            title="❌ Lỗi",
            description=str(error),
            color=discord.Color.red()
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="tuluyenhelp", aliases=["tuhelp", "tutrointro"])
    async def cultivation_guide(self, ctx):
        """Hiển thị hướng dẫn về hệ thống tu luyện"""
        # Tạo embed
        embed = discord.Embed(
            title="📚 Hướng Dẫn Tu Luyện",
            description="Hệ thống tu luyện trong bot Tu Tiên",
            color=EMBED_COLOR
        )

        # Thêm thông tin cảnh giới
        realms_text = ""
        for realm in CULTIVATION_REALMS:
            if realm["id"] % 3 == 0 or realm["id"] == 0 or realm["id"] == 1 or realm["id"] == len(
                    CULTIVATION_REALMS) - 1:
                realms_text += f"- **{realm['name']}** (EXP: {realm['exp_required']:,})\n"

        embed.add_field(
            name="Cảnh Giới Tu Luyện",
            value=realms_text,
            inline=False
        )

        # Thêm thông tin cách tu luyện
        embed.add_field(
            name="Cách Tu Luyện",
            value=(
                f"1. **Chat trong Discord**: +{EMOJI_EXP} 1 exp mỗi tin nhắn\n"
                f"2. **Voice Chat**: +{EMOJI_EXP} 2 exp mỗi phút\n"
                f"3. **Đánh Quái**: +{EMOJI_EXP} exp tùy theo cấp độ quái\n"
                f"4. **Đánh Boss**: +{EMOJI_EXP} nhiều exp hơn\n"
                f"5. **Điểm Danh Hàng Ngày**: +{EMOJI_EXP} 20 exp\n"
                f"6. **Sử Dụng Vật Phẩm**: Một số vật phẩm có thể tăng exp"
            ),
            inline=False
        )

        # Thêm lợi ích khi tu luyện
        embed.add_field(
            name="Lợi Ích Khi Tu Luyện",
            value=(
                f"1. {EMOJI_HEALTH} **Tăng HP**: Cảnh giới càng cao, HP càng lớn\n"
                f"2. {EMOJI_ATTACK} **Tăng Tấn Công**: Cảnh giới càng cao, sức tấn công càng mạnh\n"
                f"3. {EMOJI_DEFENSE} **Tăng Phòng Thủ**: Cảnh giới càng cao, khả năng phòng thủ càng cao\n"
                f"4. **Mở Khóa Nội Dung**: Một số tính năng chỉ mở khi đạt cảnh giới nhất định\n"
                f"5. **Uy Tín**: Thứ hạng cao trên bảng xếp hạng"
            ),
            inline=False
        )

        # Thêm các lệnh liên quan
        embed.add_field(
            name="Các Lệnh Liên Quan",
            value=(
                "`!canhgioi` - Xem cảnh giới hiện tại\n"
                "`!xephang` - Xem bảng xếp hạng tu luyện\n"
                "`!danhquai` - Đánh quái để nhận exp\n"
                "`!diemdanh` - Điểm danh hàng ngày"
            ),
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="gioi", aliases=["intro", "gt", "gioithieu"])
    async def bot_intro(self, ctx):
        """Hiển thị giới thiệu về bot"""
        # Tạo embed
        embed = discord.Embed(
            title="🔮 Giới Thiệu Tu Tiên Bot",
            description="Discord bot với chủ đề tu tiên, nơi bạn có thể trải nghiệm thế giới tiên hiệp đầy hấp dẫn!",
            color=EMBED_COLOR
        )

        # Thêm hình ảnh
        embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)

        # Thêm tính năng chính
        embed.add_field(
            name="Tính Năng Chính",
            value=(
                "1. **Hệ Thống Tu Luyện**: 9 cảnh giới tu tiên\n"
                "2. **Chiến Đấu**: Đánh quái, boss và PvP\n"
                "3. **Môn Phái**: Tạo và tham gia môn phái\n"
                "4. **Vật Phẩm**: Kho đồ và cửa hàng\n"
                "5. **Điểm Danh**: Nhận thưởng hàng ngày\n"
                "6. **Nhiều Tính Năng Khác**: Sự kiện, nhiệm vụ, v.v."
            ),
            inline=False
        )

        # Thêm hướng dẫn bắt đầu
        embed.add_field(
            name="Bắt Đầu Ngay",
            value=(
                "1. `!diemdanh` - Nhận thưởng hàng ngày\n"
                "2. `!canhgioi` - Xem cảnh giới hiện tại\n"
                "3. `!danhquai` - Đánh quái để tu luyện\n"
                "4. `!cuahang` - Mua vật phẩm hỗ trợ\n"
                "5. `!help` - Xem thêm các lệnh khác"
            ),
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))