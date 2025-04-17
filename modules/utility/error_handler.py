import discord
from discord.ext import commands
import traceback
import sys
import logging
from typing import Dict, List, Optional

from config import EMBED_COLOR_ERROR

# Cấu hình logging
logger = logging.getLogger("tutien-bot.error_handler")


class ErrorHandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Xử lý lỗi khi thực hiện lệnh"""
        # Nếu lệnh có error handler riêng, bỏ qua
        if hasattr(ctx.command, 'on_error'):
            return

        # Lấy lỗi gốc nếu được bọc trong CommandInvokeError
        error = getattr(error, 'original', error)

        # Bỏ qua lỗi CommandNotFound
        if isinstance(error, commands.CommandNotFound):
            return

        # Xử lý từng loại lỗi
        if isinstance(error, commands.DisabledCommand):
            # Lệnh bị vô hiệu hóa
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Lệnh `{ctx.command}` đã bị vô hiệu hóa.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.NoPrivateMessage):
            # Lệnh không được sử dụng trong DM
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Lệnh `{ctx.command}` không thể sử dụng trong tin nhắn riêng.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.BadArgument):
            # Đối số không hợp lệ
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Đối số không hợp lệ cho lệnh `{ctx.command}`.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            # Thiếu đối số bắt buộc
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Thiếu đối số **{error.param.name}** cho lệnh `{ctx.command}`.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            # Lệnh đang trong thời gian hồi
            minutes, seconds = divmod(int(error.retry_after), 60)

            if minutes > 0:
                time_format = f"**{minutes} phút {seconds} giây**"
            else:
                time_format = f"**{seconds} giây**"

            embed = discord.Embed(
                title="⏳ Cooldown",
                description=f"Lệnh `{ctx.command}` đang trong thời gian hồi. Vui lòng thử lại sau {time_format}.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.CheckFailure):
            # Không đủ quyền hoặc không thỏa điều kiện
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Bạn không có quyền sử dụng lệnh `{ctx.command}`.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lỗi chung khác
        # Log lỗi
        logger.error(f"Lỗi khi thực hiện lệnh {ctx.command}: {error}")
        logger.error(traceback.format_exception(type(error), error, error.__traceback__))

        # Thông báo cho người dùng
        embed = discord.Embed(
            title="❌ Lỗi",
            description=f"Đã xảy ra lỗi khi thực hiện lệnh `{ctx.command}`:\n```{str(error)}```",
            color=EMBED_COLOR_ERROR
        )

        # Thêm hướng dẫn
        embed.add_field(
            name="Hướng Dẫn",
            value="Vui lòng kiểm tra cú pháp lệnh hoặc thử lại sau. Nếu lỗi vẫn tiếp tục, hãy báo cáo cho quản trị viên.",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Kiểm tra độ trễ của bot"""
        # Tính toán độ trễ
        latency = round(self.bot.latency * 1000)

        # Tạo embed
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Độ trễ: **{latency}ms**",
            color=discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 200 else discord.Color.red()
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="info", aliases=["botinfo", "thongtin"])
    async def bot_info(self, ctx):
        """Hiển thị thông tin về bot"""
        # Tạo embed
        embed = discord.Embed(
            title="🤖 Thông Tin Bot",
            color=discord.Color.blue()
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
        import platform
        import discord

        embed.add_field(
            name="Phiên Bản Discord.py",
            value=discord.__version__,
            inline=True
        )

        embed.add_field(
            name="Python",
            value=platform.python_version(),
            inline=True
        )

        embed.add_field(
            name="Hệ Điều Hành",
            value=platform.system(),
            inline=True
        )

        # Thêm thông tin server
        guild_count = len(self.bot.guilds)

        embed.add_field(
            name="Số Server",
            value=guild_count,
            inline=True
        )

        # Tính tổng số thành viên
        member_count = sum(guild.member_count for guild in self.bot.guilds)

        embed.add_field(
            name="Số Thành Viên",
            value=member_count,
            inline=True
        )

        # Thêm thông tin ping
        embed.add_field(
            name="Ping",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )

        # Thêm thời gian hoạt động
        from datetime import datetime
        import psutil

        # Lấy thời gian tiến trình Python đã chạy
        process = psutil.Process()
        uptime = datetime.now() - datetime.fromtimestamp(process.create_time())

        # Định dạng thời gian hoạt động
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = f"{days} ngày, {hours} giờ, {minutes} phút, {seconds} giây"

        embed.add_field(
            name="Thời Gian Hoạt Động",
            value=uptime_str,
            inline=False
        )

        # Thêm thông tin bộ nhớ
        ram_usage = psutil.Process().memory_info().rss / 1024 ** 2  # Đổi sang MB

        embed.add_field(
            name="Sử Dụng RAM",
            value=f"{ram_usage:.2f} MB",
            inline=True
        )

        # Thêm thông tin CPU
        cpu_usage = psutil.Process().cpu_percent() / psutil.cpu_count()

        embed.add_field(
            name="Sử Dụng CPU",
            value=f"{cpu_usage:.2f}%",
            inline=True
        )

        # Thêm avatar
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="restart", aliases=["reboot"])
    @commands.is_owner()
    async def restart(self, ctx):
        """Khởi động lại bot (chỉ dành cho chủ bot)"""
        # Tạo embed
        embed = discord.Embed(
            title="🔄 Khởi Động Lại",
            description="Bot đang được khởi động lại. Vui lòng đợi trong giây lát...",
            color=discord.Color.orange()
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Khởi động lại bot
        import os
        import sys

        # Log thông tin
        logger.info("Bot đang được khởi động lại...")

        # Khởi động lại tiến trình Python
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command(name="servers", aliases=["guilds"])
    @commands.is_owner()
    async def list_servers(self, ctx):
        """Liệt kê các server bot đang tham gia (chỉ dành cho chủ bot)"""
        # Tạo embed
        embed = discord.Embed(
            title="🌐 Danh Sách Server",
            description=f"Bot đang tham gia {len(self.bot.guilds)} server:",
            color=discord.Color.blue()
        )

        # Thêm thông tin từng server
        for guild in self.bot.guilds:
            embed.add_field(
                name=guild.name,
                value=(
                    f"ID: {guild.id}\n"
                    f"Chủ sở hữu: {guild.owner}\n"
                    f"Thành viên: {guild.member_count}\n"
                    f"Ngày tham gia: {guild.me.joined_at.strftime('%d/%m/%Y')}"
                ),
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)


async def setup(bot):
    try:
        # Tạo thư mục logs nếu chưa tồn tại
        import os
        os.makedirs("logs", exist_ok=True)

        # Thêm cog
        await bot.add_cog(ErrorHandlerCog(bot))
        logger.info("Đã tải ErrorHandlerCog")
    except Exception as e:
        logger.error(f"Lỗi khi tải ErrorHandlerCog: {e}")