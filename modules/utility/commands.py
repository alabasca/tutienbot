import discord
from discord.ext import commands
import asyncio
import datetime
import logging
import sys
import os
import time
import psutil

from database.mongo_handler import get_user_or_create, users_collection
from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR, EMOJI_LINH_THACH, EMOJI_EXP
)
from utils.text_utils import format_number, generate_random_quote
from utils.time_utils import get_vietnamese_date_string

# Cấu hình logging
logger = logging.getLogger("tutien-bot.commands")


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now()

    @commands.command(name="thongtin", aliases=["info", "botinfo"])
    async def bot_info(self, ctx):
        """Hiển thị thông tin về bot"""
        # Tính thời gian hoạt động
        uptime = datetime.datetime.now() - self.start_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = f"{int(days)} ngày, {int(hours)} giờ, {int(minutes)} phút, {int(seconds)} giây"

        # Tạo embed
        embed = discord.Embed(
            title="🤖 Thông Tin Bot Tu Tiên",
            description="Bot Discord với chủ đề tu tiên, nơi bạn có thể trải nghiệm việc tu luyện, chiến đấu và khám phá thế giới tiên hiệp!",
            color=EMBED_COLOR
        )

        # Thêm thông tin bot
        embed.add_field(
            name="Tên",
            value=self.bot.user.name,
            inline=True
        )

        embed.add_field(
            name="ID",
            value=self.bot.user.id,
            inline=True
        )

        # Thêm thông tin hệ thống
        embed.add_field(
            name="Phiên Bản Discord.py",
            value=discord.__version__,
            inline=True
        )

        embed.add_field(
            name="Python",
            value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            inline=True
        )

        # Thêm thông tin hoạt động
        embed.add_field(
            name="Thời Gian Hoạt Động",
            value=uptime_str,
            inline=True
        )

        # Thông tin server
        embed.add_field(
            name="Số Server",
            value=len(self.bot.guilds),
            inline=True
        )

        # Thông tin người dùng
        try:
            user_count = await users_collection.count_documents({})
            embed.add_field(
                name="Số Người Dùng",
                value=user_count,
                inline=True
            )
        except:
            pass

        # Thêm thông tin tài nguyên
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 ** 2  # Chuyển đổi sang MB

        embed.add_field(
            name="Sử Dụng RAM",
            value=f"{memory_usage:.2f} MB",
            inline=True
        )

        # Thêm thông tin tác giả
        embed.add_field(
            name="Tác Giả",
            value="Team Thiên Đạo",
            inline=True
        )

        # Thêm avatar
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Thêm footer
        embed.set_footer(text=f"Cập nhật lần cuối: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx):
        """Kiểm tra độ trễ của bot"""
        # Tính toán độ trễ
        start_time = time.time()
        message = await ctx.send("Đang kiểm tra...")
        end_time = time.time()

        # Độ trễ API
        api_latency = round(self.bot.latency * 1000)

        # Độ trễ thực tế
        message_latency = round((end_time - start_time) * 1000)

        # Tạo embed
        embed = discord.Embed(
            title="🏓 Ping!",
            description=f"**Độ trễ API:** {api_latency}ms\n**Độ trễ tin nhắn:** {message_latency}ms",
            color=discord.Color.green() if api_latency < 200 else discord.Color.orange() if api_latency < 500 else discord.Color.red()
        )

        # Cập nhật tin nhắn
        await message.edit(content=None, embed=embed)

    @commands.command(name="lenh", aliases=["help", "commands", "trogiup"])
    async def help_command(self, ctx, *, command_name: str = None):
        """Hiển thị danh sách lệnh và cách sử dụng"""
        prefix = self.bot.command_prefix

        # Nếu có tên lệnh cụ thể
        if command_name:
            # Tìm lệnh
            command = self.bot.get_command(command_name)

            # Nếu không tìm thấy
            if not command:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description=f"Không tìm thấy lệnh `{command_name}`.",
                    color=EMBED_COLOR_ERROR
                )
                return await ctx.send(embed=embed)

            # Tạo embed thông tin lệnh
            embed = discord.Embed(
                title=f"Lệnh: {prefix}{command.name}",
                description=command.help or "Không có mô tả chi tiết.",
                color=EMBED_COLOR
            )

            # Thêm cú pháp
            embed.add_field(
                name="Cú Pháp",
                value=f"`{prefix}{command.name}`",
                inline=False
            )

            # Thêm bí danh (aliases) nếu có
            if command.aliases:
                aliases = [f"`{prefix}{alias}`" for alias in command.aliases]
                embed.add_field(
                    name="Lệnh Thay Thế",
                    value=", ".join(aliases),
                    inline=False
                )

            # Gửi embed
            await ctx.send(embed=embed)

        else:
            # Tạo embed danh sách lệnh
            embed = discord.Embed(
                title="📖 Danh Sách Lệnh",
                description=f"Sử dụng `{prefix}lenh [tên lệnh]` để xem chi tiết về một lệnh cụ thể.",
                color=EMBED_COLOR
            )

            # Nhóm lệnh theo cog
            command_groups = {}
            for command in self.bot.commands:
                cog_name = command.cog_name or "Khác"

                if cog_name not in command_groups:
                    command_groups[cog_name] = []

                command_groups[cog_name].append(command)

            # Thêm các nhóm lệnh vào embed
            for cog_name, commands_list in sorted(command_groups.items()):
                # Bỏ qua các lệnh ẩn
                visible_commands = [command for command in commands_list if not command.hidden]

                if not visible_commands:
                    continue

                # Tạo danh sách tên lệnh
                command_names = [f"`{prefix}{command.name}`" for command in visible_commands]

                # Thêm trường
                embed.add_field(
                    name=self.translate_cog_name(cog_name),
                    value=", ".join(command_names),
                    inline=False
                )

            # Gửi embed
            await ctx.send(embed=embed)

    def translate_cog_name(self, cog_name: str) -> str:
        """Dịch tên cog sang tiếng Việt"""
        translations = {
            "CultivationCog": "🧘 Tu Luyện",
            "CombatCog": "⚔️ Chiến Đấu",
            "MonsterCog": "👹 Quái Vật",
            "InventoryCog": "🎒 Kho Đồ",
            "DailyCog": "📅 Điểm Danh",
            "SectCog": "🏛️ Môn Phái",
            "CommandsCog": "🛠️ Tiện Ích",
            "HelpCog": "❓ Trợ Giúp",
            "ErrorHandlerCog": "⚠️ Xử Lý Lỗi"
        }
        return translations.get(cog_name, cog_name)

    @commands.command(name="timkiem", aliases=["search", "tim"])
    async def search_user(self, ctx, *, search_term: str):
        """Tìm kiếm người dùng theo tên hoặc cảnh giới"""
        # Kiểm tra từ khóa tìm kiếm
        if not search_term:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Vui lòng cung cấp tên người dùng hoặc cảnh giới để tìm kiếm.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Tìm kiếm theo cảnh giới
        if search_term.lower().startswith(("cảnh giới:", "canh gioi:", "realm:")):
            # Lấy tên cảnh giới
            realm_term = search_term.split(":", 1)[1].strip().lower()

            # Tìm ID cảnh giới phù hợp
            realm_id = None
            for realm in CULTIVATION_REALMS:
                if realm_term in realm["name"].lower():
                    realm_id = realm["id"]
                    break

            # Nếu không tìm thấy cảnh giới
            if realm_id is None:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description=f"Không tìm thấy cảnh giới nào khớp với từ khóa `{realm_term}`.",
                    color=EMBED_COLOR_ERROR
                )
                return await ctx.send(embed=embed)

            # Tìm kiếm trong database
            cursor = users_collection.find({"realm_id": realm_id}).sort("experience", -1).limit(10)
            users = await cursor.to_list(length=10)

            # Nếu không tìm thấy kết quả
            if not users:
                embed = discord.Embed(
                    title="❓ Không Có Kết Quả",
                    description=f"Không tìm thấy người dùng nào ở cảnh giới {CULTIVATION_REALMS[realm_id]['name']}.",
                    color=EMBED_COLOR
                )
                return await ctx.send(embed=embed)

            # Tạo embed kết quả
            embed = discord.Embed(
                title=f"🔍 Kết Quả Tìm Kiếm: Cảnh Giới {CULTIVATION_REALMS[realm_id]['name']}",
                description=f"Tìm thấy {len(users)} người dùng ở cảnh giới này:",
                color=EMBED_COLOR
            )

            # Thêm thông tin từng người dùng
            for i, user in enumerate(users, 1):
                # Lấy thông tin thành viên
                member = ctx.guild.get_member(user["user_id"])
                name = member.display_name if member else user.get("username", "Không xác định")

                # Thêm vào embed
                embed.add_field(
                    name=f"{i}. {name}",
                    value=f"Kinh nghiệm: **{format_number(user['experience'])}**\nLinh thạch: **{format_number(user.get('linh_thach', 0))}**",
                    inline=True
                )

        else:
            # Tìm kiếm theo tên
            # Lấy danh sách thành viên trong server
            members = ctx.guild.members

            # Lọc theo tên
            found_members = [member for member in members if
                             search_term.lower() in member.display_name.lower() or search_term.lower() in member.name.lower()]

            # Nếu không tìm thấy kết quả
            if not found_members:
                embed = discord.Embed(
                    title="❓ Không Có Kết Quả",
                    description=f"Không tìm thấy người dùng nào khớp với từ khóa `{search_term}`.",
                    color=EMBED_COLOR
                )
                return await ctx.send(embed=embed)

            # Giới hạn số lượng kết quả
            found_members = found_members[:10]

            # Tạo embed kết quả
            embed = discord.Embed(
                title=f"🔍 Kết Quả Tìm Kiếm: {search_term}",
                description=f"Tìm thấy {len(found_members)} người dùng:",
                color=EMBED_COLOR
            )

            # Thêm thông tin từng người dùng
            for i, member in enumerate(found_members, 1):
                # Lấy thông tin từ database
                user_data = await get_user_or_create(member.id, member.name)

                # Lấy tên cảnh giới
                realm_id = user_data.get("realm_id", 0)
                realm_name = CULTIVATION_REALMS[realm_id]["name"] if realm_id < len(
                    CULTIVATION_REALMS) else "Không xác định"

                # Thêm vào embed
                embed.add_field(
                    name=f"{i}. {member.display_name}",
                    value=f"Cảnh giới: **{realm_name}**\nKinh nghiệm: **{format_number(user_data.get('experience', 0))}**",
                    inline=True
                )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="server", aliases=["serverinfo", "guild"])
    async def server_info(self, ctx):
        """Hiển thị thông tin về server hiện tại"""
        guild = ctx.guild

        # Tạo embed
        embed = discord.Embed(
            title=f"📊 Thông Tin Server: {guild.name}",
            description=guild.description or "Không có mô tả",
            color=EMBED_COLOR
        )

        # Thêm thông tin cơ bản
        embed.add_field(
            name="ID",
            value=guild.id,
            inline=True
        )

        embed.add_field(
            name="Chủ Sở Hữu",
            value=guild.owner.mention if guild.owner else "Không xác định",
            inline=True
        )

        embed.add_field(
            name="Ngày Tạo",
            value=guild.created_at.strftime("%d/%m/%Y"),
            inline=True
        )

        # Thêm thông tin số lượng
        embed.add_field(
            name="Số Thành Viên",
            value=guild.member_count,
            inline=True
        )

        embed.add_field(
            name="Số Kênh",
            value=f"Text: {len(guild.text_channels)}\nVoice: {len(guild.voice_channels)}",
            inline=True
        )

        embed.add_field(
            name="Số Role",
            value=len(guild.roles),
            inline=True
        )

        # Thêm thông tin bổ sung
        embed.add_field(
            name="Mức Xác Minh",
            value=str(guild.verification_level).capitalize(),
            inline=True
        )

        # Thêm icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="thamgia", aliases=["join"])
    async def join_date(self, ctx, member: discord.Member = None):
        """Hiển thị ngày tham gia server của bản thân hoặc người khác"""
        # Nếu không chỉ định member, lấy người gọi lệnh
        if member is None:
            member = ctx.author

        # Tạo embed
        embed = discord.Embed(
            title=f"📅 Thông Tin Tham Gia - {member.display_name}",
            color=EMBED_COLOR
        )

        # Thêm thông tin
        embed.add_field(
            name="Tham Gia Discord",
            value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"),
            inline=False
        )

        embed.add_field(
            name="Tham Gia Server",
            value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S") if member.joined_at else "Không xác định",
            inline=False
        )

        # Tính thời gian
        if member.joined_at:
            joined_days = (datetime.datetime.now() - member.joined_at).days
            embed.add_field(
                name="Thời Gian Trong Server",
                value=f"{joined_days} ngày",
                inline=False
            )

        # Thêm avatar
        embed.set_thumbnail(url=member.display_avatar.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Hiển thị avatar của bản thân hoặc người khác"""
        # Nếu không chỉ định member, lấy người gọi lệnh
        if member is None:
            member = ctx.author

        # Tạo embed
        embed = discord.Embed(
            title=f"🖼️ Avatar - {member.display_name}",
            color=EMBED_COLOR
        )

        # Thêm avatar
        embed.set_image(url=member.display_avatar.url)

        # Thêm link
        embed.add_field(
            name="Liên Kết",
            value=f"[PNG]({member.display_avatar.replace(format='png', size=1024).url}) | [JPG]({member.display_avatar.replace(format='jpg', size=1024).url}) | [WEBP]({member.display_avatar.replace(format='webp', size=1024).url})",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="ngaythang", aliases=["date", "today"])
    async def show_date(self, ctx):
        """Hiển thị ngày tháng hiện tại"""
        # Lấy ngày tháng
        date_string = get_vietnamese_date_string()

        # Tạo embed
        embed = discord.Embed(
            title="📆 Ngày Tháng Hiện Tại",
            description=f"**{date_string}**",
            color=EMBED_COLOR
        )

        # Thêm câu nói ngẫu nhiên
        quote = generate_random_quote()
        embed.set_footer(text=quote)

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))