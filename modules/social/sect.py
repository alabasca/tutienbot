import discord
from discord.ext import commands
import asyncio
import datetime
import random
import logging
import json
import os
from typing import Dict, List, Optional

from database.mongo_handler import get_user_or_create, update_user, get_sect, create_sect, add_member_to_sect, \
    remove_member_from_sect
from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR, EMOJI_LINH_THACH
)

# Cấu hình logging
logger = logging.getLogger("tutien-bot.sect")


class SectCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_sects()

    def load_sects(self):
        """Tải dữ liệu các môn phái từ JSON"""
        try:
            if os.path.exists("data/sects.json"):
                with open("data/sects.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sect_templates = data.get("sects", [])
                logger.info(f"Đã tải {len(self.sect_templates)} mẫu môn phái từ JSON")
            else:
                logger.warning("Không tìm thấy file data/sects.json")
                self.sect_templates = []
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu môn phái: {e}")
            self.sect_templates = []

    @commands.group(name="monphai", aliases=["mp", "sect"], invoke_without_command=True)
    async def sect(self, ctx):
        """Hiển thị thông tin về môn phái của bạn hoặc danh sách các môn phái"""
        if ctx.invoked_subcommand is None:
            # Lấy thông tin người dùng
            user = await get_user_or_create(ctx.author.id, ctx.author.name)
            sect_id = user.get("sect_id")

            # Nếu người dùng đã gia nhập môn phái
            if sect_id:
                # Lấy thông tin môn phái
                sect = await get_sect(sect_id)

                if sect:
                    # Tạo embed hiển thị thông tin môn phái
                    embed = discord.Embed(
                        title=f"Môn Phái: {sect['name']}",
                        description=sect.get("description", "Không có mô tả"),
                        color=EMBED_COLOR
                    )

                    # Thêm thông tin chủ sở hữu
                    owner_id = sect["owner_id"]
                    owner = self.bot.get_user(owner_id)
                    owner_name = owner.name if owner else "Không xác định"

                    embed.add_field(
                        name="Chưởng Môn",
                        value=owner_name,
                        inline=True
                    )

                    # Thêm thông tin cấp độ và tài nguyên
                    embed.add_field(
                        name="Cấp Độ",
                        value=str(sect.get("level", 1)),
                        inline=True
                    )

                    embed.add_field(
                        name="Tài Nguyên",
                        value=f"{EMOJI_LINH_THACH} {sect.get('resources', 0):,}",
                        inline=True
                    )

                    # Thêm thông tin thành viên
                    member_count = len(sect.get("members", []))
                    embed.add_field(
                        name="Thành Viên",
                        value=f"{member_count} thành viên",
                        inline=True
                    )

                    # Thêm thời gian thành lập
                    created_at = sect.get("created_at")
                    if created_at:
                        embed.add_field(
                            name="Thành Lập",
                            value=created_at.strftime("%d/%m/%Y") if isinstance(created_at, datetime.datetime) else str(
                                created_at),
                            inline=True
                        )

                    # Thêm hướng dẫn
                    embed.add_field(
                        name="Lệnh Liên Quan",
                        value=(
                            "`!monphai thanhvien` - Xem danh sách thành viên\n"
                            "`!monphai roi` - Rời khỏi môn phái\n"
                            "`!monphai conghien [số linh thạch]` - Cống hiến linh thạch cho môn phái"
                        ),
                        inline=False
                    )

                    # Gửi embed
                    await ctx.send(embed=embed)
                else:
                    # Nếu không tìm thấy thông tin môn phái
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description=f"Không tìm thấy thông tin về môn phái của bạn. Có thể do lỗi dữ liệu.",
                        color=EMBED_COLOR_ERROR
                    )
                    await ctx.send(embed=embed)
            else:
                # Nếu chưa gia nhập môn phái
                embed = discord.Embed(
                    title="Môn Phái",
                    description="Bạn chưa gia nhập môn phái nào. Hãy sử dụng lệnh `!monphai danhsach` để xem danh sách các môn phái hoặc `!monphai tao [tên] [mô tả]` để tạo môn phái mới.",
                    color=EMBED_COLOR
                )
                await ctx.send(embed=embed)

    @sect.command(name="danhsach", aliases=["ds", "list"])
    async def sect_list(self, ctx):
        """Hiển thị danh sách các môn phái mẫu"""
        # Kiểm tra có dữ liệu không
        if not self.sect_templates:
            embed = discord.Embed(
                title="Danh Sách Môn Phái",
                description="Không có dữ liệu về các môn phái mẫu. Hãy sử dụng lệnh `!monphai tao [tên] [mô tả]` để tạo môn phái mới.",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        # Tạo embed
        embed = discord.Embed(
            title="Danh Sách Môn Phái",
            description="Các môn phái tiêu biểu trong thế giới tu tiên:",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng môn phái
        for i, sect in enumerate(self.sect_templates, 1):
            embed.add_field(
                name=f"{i}. {sect['name']}",
                value=f"{sect['description']}\nVị trí: {sect.get('base_location', 'Không rõ')}\nTông chủ: {sect.get('founder', 'Không rõ')}",
                inline=False
            )

        # Thêm hướng dẫn
        embed.add_field(
            name="Tham Gia Môn Phái",
            value="Sử dụng lệnh `!monphai thamgia [tên môn phái]` để xin gia nhập môn phái.\nHoặc tạo môn phái riêng với lệnh `!monphai tao [tên] [mô tả]`.",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

    @sect.command(name="thanhvien", aliases=["tv", "members"])
    async def sect_members(self, ctx):
        """Hiển thị danh sách thành viên của môn phái"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)
        sect_id = user.get("sect_id")

        # Kiểm tra đã gia nhập môn phái chưa
        if not sect_id:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn chưa gia nhập môn phái nào.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin môn phái
        sect = await get_sect(sect_id)

        if not sect:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về môn phái của bạn. Có thể do lỗi dữ liệu.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy danh sách thành viên
        members = sect.get("members", [])

        # Nếu không có thành viên
        if not members:
            embed = discord.Embed(
                title=f"Thành Viên Môn Phái: {sect['name']}",
                description="Môn phái chưa có thành viên nào.",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        # Tạo embed
        embed = discord.Embed(
            title=f"Thành Viên Môn Phái: {sect['name']}",
            description=f"Tổng số: {len(members)} thành viên",
            color=EMBED_COLOR
        )

        # Thêm thông tin từng thành viên
        from database.mongo_handler import users_collection

        # Lấy thông tin chi tiết của các thành viên
        member_details = []
        for member_id in members:
            user_data = await users_collection.find_one({"user_id": member_id})
            if user_data:
                # Lấy thông tin tu vi
                realm_id = user_data.get("realm_id", 0)
                realm_name = CULTIVATION_REALMS[realm_id]["name"] if realm_id < len(CULTIVATION_REALMS) else "Không rõ"

                # Lấy thông tin discord
                member = ctx.guild.get_member(member_id)
                name = member.display_name if member else user_data.get("username", "Không rõ")

                # Đánh dấu chủ sở hữu
                if member_id == sect["owner_id"]:
                    name = f"👑 {name}"

                member_details.append({
                    "name": name,
                    "realm": realm_name,
                    "exp": user_data.get("experience", 0),
                    "is_owner": member_id == sect["owner_id"]
                })

        # Sắp xếp: chủ sở hữu đầu tiên, sau đó theo kinh nghiệm
        member_details.sort(key=lambda x: (-1 if x["is_owner"] else 0, -x["exp"]))

        # Thêm vào embed
        member_text = ""
        for i, member in enumerate(member_details, 1):
            member_text += f"{i}. **{member['name']}** - {member['realm']}\n"

            # Giới hạn số lượng hiển thị
            if i >= 20:
                member_text += f"... và {len(member_details) - 20} thành viên khác"
                break

        embed.description = member_text

        # Gửi embed
        await ctx.send(embed=embed)

    @sect.command(name="tao", aliases=["create", "new"])
    async def create_sect(self, ctx, *, info: str = None):
        """Tạo môn phái mới"""
        # Kiểm tra thông tin đầu vào
        if not info:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Vui lòng cung cấp tên và mô tả cho môn phái.\nVí dụ: `!monphai tao Thiên Long Tông | Môn phái chuyên tu luyện thủy thuộc tính`",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Tách tên và mô tả
        parts = info.split("|", 1)
        name = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else "Không có mô tả"

        # Kiểm tra độ dài tên
        if len(name) < 3 or len(name) > 30:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Tên môn phái phải có độ dài từ 3 đến 30 ký tự.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra đã có môn phái chưa
        if user.get("sect_id"):
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn đã là thành viên của một môn phái. Hãy rời khỏi môn phái hiện tại trước khi tạo môn phái mới.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra cảnh giới tối thiểu (Trúc Cơ)
        if user.get("realm_id", 0) < 10:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Bạn cần đạt ít nhất cảnh giới **Trúc Cơ** để tạo môn phái. Cảnh giới hiện tại: **{CULTIVATION_REALMS[user.get('realm_id', 0)]['name']}**",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra linh thạch (1000)
        if user.get("linh_thach", 0) < 1000:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Bạn cần có ít nhất **1000** linh thạch để tạo môn phái. Linh thạch hiện có: **{user.get('linh_thach', 0)}**",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Tạo môn phái mới
        try:
            # Trừ linh thạch
            await update_user(ctx.author.id, {"linh_thach": user.get("linh_thach", 0) - 1000})

            # Tạo môn phái
            sect = await create_sect(ctx.author.id, name, description)

            # Tạo embed thông báo
            embed = discord.Embed(
                title="✅ Tạo Môn Phái Thành Công",
                description=f"Chúc mừng! Bạn đã tạo môn phái **{name}** thành công!",
                color=EMBED_COLOR_SUCCESS
            )

            # Thêm chi tiết
            embed.add_field(
                name="Chi Phí",
                value=f"{EMOJI_LINH_THACH} -1000 linh thạch",
                inline=False
            )

            embed.add_field(
                name="Hướng Dẫn",
                value=(
                        "1. Sử dụng `!monphai thanhvien` để xem danh sách thành viên\n"
                        "2. Mời người khác tham gia bằng cách họ sử dụng lệnh `!monphai thamgia " + name + "`\n"
                                                                                                           "3. Phát triển môn phái bằng cách đóng góp linh thạch với lệnh `!monphai conghien [số lượng]`"
                ),
                inline=False
            )

            # Gửi embed
            await ctx.send(embed=embed)

            # Log
            logger.info(f"{ctx.author.name} đã tạo môn phái mới: {name}")

        except Exception as e:
            # Xử lý lỗi
            logger.error(f"Lỗi khi tạo môn phái: {e}")

            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Đã xảy ra lỗi khi tạo môn phái: {str(e)}",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)

    @sect.command(name="thamgia", aliases=["join"])
    async def join_sect(self, ctx, *, sect_name: str = None):
        """Tham gia vào môn phái"""
        # Kiểm tra tên môn phái
        if not sect_name:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Vui lòng cung cấp tên môn phái bạn muốn tham gia.\nVí dụ: `!monphai thamgia Thiên Long Tông`",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)

        # Kiểm tra đã có môn phái chưa
        if user.get("sect_id"):
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn đã là thành viên của một môn phái. Hãy rời khỏi môn phái hiện tại trước khi tham gia môn phái khác.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Tìm kiếm môn phái theo tên
        from database.mongo_handler import sects_collection
        sect = await sects_collection.find_one({"name": {"$regex": f"^{sect_name}$", "$options": "i"}})

        # Nếu không tìm thấy
        if not sect:
            # Kiểm tra mẫu môn phái
            template_sect = None
            for s in self.sect_templates:
                if s["name"].lower() == sect_name.lower():
                    template_sect = s
                    break

            if template_sect:
                # Hiển thị thông tin môn phái mẫu
                embed = discord.Embed(
                    title=f"Môn Phái: {template_sect['name']}",
                    description=template_sect.get("description", "Không có mô tả"),
                    color=EMBED_COLOR
                )

                embed.add_field(
                    name="Thông Tin",
                    value=(
                        f"Vị trí: {template_sect.get('base_location', 'Không rõ')}\n"
                        f"Tông chủ: {template_sect.get('founder', 'Không rõ')}\n"
                        f"Năm thành lập: {template_sect.get('establishment_year', 'Không rõ')}"
                    ),
                    inline=False
                )

                embed.add_field(
                    name="Lưu Ý",
                    value="Đây là môn phái mẫu trong thế giới tu tiên. Để tham gia, bạn cần tìm một môn phái được tạo bởi người chơi khác, hoặc tạo môn phái riêng của mình với lệnh `!monphai tao`.",
                    inline=False
                )

                return await ctx.send(embed=embed)
            else:
                # Không tìm thấy môn phái
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description=f"Không tìm thấy môn phái nào có tên **{sect_name}**. Hãy kiểm tra lại tên hoặc sử dụng lệnh `!monphai danhsach` để xem danh sách các môn phái mẫu.",
                    color=EMBED_COLOR_ERROR
                )
                return await ctx.send(embed=embed)

        # Lấy thông tin chủ sở hữu
        owner_id = sect["owner_id"]
        owner = self.bot.get_user(owner_id)
        owner_name = owner.name if owner else "Không xác định"

        # Tạo embed xác nhận
        embed = discord.Embed(
            title=f"Xác Nhận Tham Gia Môn Phái: {sect['name']}",
            description=f"Bạn có chắc chắn muốn tham gia môn phái **{sect['name']}**?\n\nChủ sở hữu: {owner_name}\nSố thành viên: {len(sect.get('members', []))}\nMô tả: {sect.get('description', 'Không có mô tả')}",
            color=EMBED_COLOR
        )

        # Gửi embed xác nhận
        confirm_msg = await ctx.send(embed=embed)

        # Thêm reaction để xác nhận
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        # Hàm kiểm tra reaction
        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["✅",
                                                                        "❌"] and reaction.message.id == confirm_msg.id

        try:
            # Chờ phản ứng
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

            # Nếu từ chối
            if str(reaction.emoji) == "❌":
                embed = discord.Embed(
                    title="❌ Đã Hủy",
                    description="Bạn đã hủy yêu cầu tham gia môn phái.",
                    color=EMBED_COLOR_ERROR
                )
                return await ctx.send(embed=embed)

            # Nếu đồng ý, thêm vào môn phái
            result = await add_member_to_sect(sect["sect_id"], ctx.author.id)

            if result:
                # Gửi thông báo thành công
                embed = discord.Embed(
                    title="✅ Tham Gia Thành Công",
                    description=f"Chúc mừng! Bạn đã trở thành thành viên của môn phái **{sect['name']}**!",
                    color=EMBED_COLOR_SUCCESS
                )

                # Thêm hướng dẫn
                embed.add_field(
                    name="Lệnh Hữu Ích",
                    value=(
                        "`!monphai` - Xem thông tin môn phái\n"
                        "`!monphai thanhvien` - Xem danh sách thành viên\n"
                        "`!monphai conghien [số lượng]` - Đóng góp linh thạch cho môn phái"
                    ),
                    inline=False
                )

                await ctx.send(embed=embed)

                # Thông báo cho chủ sở hữu
                try:
                    owner_user = self.bot.get_user(owner_id)
                    if owner_user:
                        owner_embed = discord.Embed(
                            title="🔔 Thông Báo Môn Phái",
                            description=f"**{ctx.author.name}** đã tham gia môn phái **{sect['name']}** của bạn!",
                            color=EMBED_COLOR_SUCCESS
                        )
                        await owner_user.send(embed=owner_embed)
                except:
                    pass  # Bỏ qua nếu không gửi được DM
            else:
                # Gửi thông báo lỗi
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Đã xảy ra lỗi khi tham gia môn phái. Vui lòng thử lại sau.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            # Nếu hết thời gian
            embed = discord.Embed(
                title="⏰ Hết Thời Gian",
                description="Bạn đã không phản hồi kịp thời. Yêu cầu tham gia môn phái đã bị hủy.",
                color=EMBED_COLOR_ERROR
            )
            await ctx.send(embed=embed)

    @sect.command(name="roi", aliases=["leave", "quit"])
    async def leave_sect(self, ctx):
        """Rời khỏi môn phái hiện tại"""
        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)
        sect_id = user.get("sect_id")

        # Kiểm tra đã có môn phái chưa
        if not sect_id:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn chưa tham gia môn phái nào.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin môn phái
        sect = await get_sect(sect_id)

        if not sect:
            # Nếu không tìm thấy thông tin môn phái
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về môn phái của bạn. Có thể do lỗi dữ liệu.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra nếu là chủ sở hữu
        if sect["owner_id"] == ctx.author.id:
            # Tạo embed cảnh báo
            embed = discord.Embed(
                title="⚠️ Cảnh Báo",
                description=f"Bạn là chủ sở hữu của môn phái **{sect['name']}**. Nếu rời đi, môn phái sẽ bị giải tán và tất cả thành viên sẽ bị đuổi. Bạn có chắc chắn muốn tiếp tục?",
                color=discord.Color.orange()
            )

            # Gửi embed cảnh báo
            confirm_msg = await ctx.send(embed=embed)

            # Thêm reaction để xác nhận
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")

            # Hàm kiểm tra reaction
            def check(reaction, user):
                return user.id == ctx.author.id and str(reaction.emoji) in ["✅",
                                                                            "❌"] and reaction.message.id == confirm_msg.id

            try:
                # Chờ phản ứng
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                # Nếu từ chối
                if str(reaction.emoji) == "❌":
                    embed = discord.Embed(
                        title="❌ Đã Hủy",
                        description="Bạn đã hủy yêu cầu rời khỏi môn phái.",
                        color=EMBED_COLOR_ERROR
                    )
                    return await ctx.send(embed=embed)

                # Nếu đồng ý, giải tán môn phái
                from database.mongo_handler import sects_collection, users_collection

                # Lấy danh sách thành viên
                members = sect.get("members", [])

                # Cập nhật thông tin cho tất cả thành viên
                for member_id in members:
                    await update_user(member_id, {"sect_id": None})

                # Xóa môn phái
                await sects_collection.delete_one({"sect_id": sect_id})

                # Gửi thông báo thành công
                embed = discord.Embed(
                    title="✅ Giải Tán Môn Phái",
                    description=f"Môn phái **{sect['name']}** đã được giải tán. Tất cả thành viên đã được đưa ra khỏi môn phái.",
                    color=EMBED_COLOR_SUCCESS
                )

                await ctx.send(embed=embed)

                # Thông báo cho các thành viên
                for member_id in members:
                    if member_id != ctx.author.id:
                        try:
                            member_user = self.bot.get_user(member_id)
                            if member_user:
                                member_embed = discord.Embed(
                                    title="🔔 Thông Báo Môn Phái",
                                    description=f"Môn phái **{sect['name']}** đã bị giải tán bởi chủ sở hữu **{ctx.author.name}**. Bạn không còn là thành viên của môn phái này nữa.",
                                    color=EMBED_COLOR_ERROR
                                )
                                await member_user.send(embed=member_embed)
                        except:
                            pass  # Bỏ qua nếu không gửi được DM

            except asyncio.TimeoutError:
                # Nếu hết thời gian
                embed = discord.Embed(
                    title="⏰ Hết Thời Gian",
                    description="Bạn đã không phản hồi kịp thời. Yêu cầu giải tán môn phái đã bị hủy.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.send(embed=embed)
        else:
            # Nếu là thành viên thường
            # Tạo embed xác nhận
            embed = discord.Embed(
                title="⚠️ Xác Nhận",
                description=f"Bạn có chắc chắn muốn rời khỏi môn phái **{sect['name']}**?",
                color=discord.Color.orange()
            )

            # Gửi embed xác nhận
            confirm_msg = await ctx.send(embed=embed)

            # Thêm reaction để xác nhận
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")

            # Hàm kiểm tra reaction
            def check(reaction, user):
                return user.id == ctx.author.id and str(reaction.emoji) in ["✅",
                                                                            "❌"] and reaction.message.id == confirm_msg.id

            try:
                # Chờ phản ứng
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                # Nếu từ chối
                if str(reaction.emoji) == "❌":
                    embed = discord.Embed(
                        title="❌ Đã Hủy",
                        description="Bạn đã hủy yêu cầu rời khỏi môn phái.",
                        color=EMBED_COLOR_ERROR
                    )
                    return await ctx.send(embed=embed)

                # Nếu đồng ý, rời khỏi môn phái
                result = await remove_member_from_sect(sect_id, ctx.author.id)

                if result:
                    # Gửi thông báo thành công
                    embed = discord.Embed(
                        title="✅ Rời Khỏi Môn Phái",
                        description=f"Bạn đã rời khỏi môn phái **{sect['name']}** thành công.",
                        color=EMBED_COLOR_SUCCESS
                    )

                    await ctx.send(embed=embed)

                    # Thông báo cho chủ sở hữu
                    try:
                        owner_user = self.bot.get_user(sect["owner_id"])
                        if owner_user:
                            owner_embed = discord.Embed(
                                title="🔔 Thông Báo Môn Phái",
                                description=f"**{ctx.author.name}** đã rời khỏi môn phái **{sect['name']}** của bạn!",
                                color=EMBED_COLOR
                            )
                            await owner_user.send(embed=owner_embed)
                    except:
                        pass  # Bỏ qua nếu không gửi được DM
                else:
                    # Gửi thông báo lỗi
                    embed = discord.Embed(
                        title="❌ Lỗi",
                        description="Đã xảy ra lỗi khi rời khỏi môn phái. Vui lòng thử lại sau.",
                        color=EMBED_COLOR_ERROR
                    )
                    await ctx.send(embed=embed)

            except asyncio.TimeoutError:
                # Nếu hết thời gian
                embed = discord.Embed(
                    title="⏰ Hết Thời Gian",
                    description="Bạn đã không phản hồi kịp thời. Yêu cầu rời khỏi môn phái đã bị hủy.",
                    color=EMBED_COLOR_ERROR
                )
                await ctx.send(embed=embed)

    @sect.command(name="conghien", aliases=["donate", "contribute"])
    async def contribute_sect(self, ctx, amount: int = None):
        """Đóng góp linh thạch cho môn phái"""
        # Kiểm tra số lượng
        if amount is None or amount <= 0:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Vui lòng cung cấp số lượng linh thạch hợp lệ để đóng góp.\nVí dụ: `!monphai conghien 100`",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(ctx.author.id, ctx.author.name)
        sect_id = user.get("sect_id")

        # Kiểm tra đã có môn phái chưa
        if not sect_id:
            embed = discord.Embed(
                title="❌ Lỗi",
                description="Bạn chưa tham gia môn phái nào.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Kiểm tra đủ linh thạch
        user_linh_thach = user.get("linh_thach", 0)

        if user_linh_thach < amount:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Bạn không đủ linh thạch để đóng góp. Linh thạch hiện có: **{user_linh_thach}**",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin môn phái
        sect = await get_sect(sect_id)

        if not sect:
            # Nếu không tìm thấy thông tin môn phái
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Không tìm thấy thông tin về môn phái của bạn. Có thể do lỗi dữ liệu.",
                color=EMBED_COLOR_ERROR
            )
            return await ctx.send(embed=embed)

        # Cập nhật tài nguyên môn phái
        from database.mongo_handler import sects_collection
        current_resources = sect.get("resources", 0)
        new_resources = current_resources + amount

        # Cập nhật trong database
        await sects_collection.update_one(
            {"sect_id": sect_id},
            {"$set": {"resources": new_resources}}
        )

        # Trừ linh thạch của người dùng
        new_linh_thach = user_linh_thach - amount
        await update_user(ctx.author.id, {"linh_thach": new_linh_thach})

        # Kiểm tra có tăng cấp không
        level_up = False
        current_level = sect.get("level", 1)
        new_level = current_level

        # Quy tắc tăng cấp: mỗi cấp cần 1000 * cấp hiện tại
        required_resources = 1000 * current_level

        if new_resources >= required_resources:
            new_level = current_level + 1
            level_up = True

            # Cập nhật cấp độ môn phái
            await sects_collection.update_one(
                {"sect_id": sect_id},
                {"$set": {"level": new_level}}
            )

        # Gửi thông báo thành công
        embed = discord.Embed(
            title="✅ Đóng Góp Thành Công",
            description=f"Bạn đã đóng góp **{amount}** linh thạch cho môn phái **{sect['name']}**!",
            color=EMBED_COLOR_SUCCESS
        )

        # Thêm thông tin tài nguyên
        embed.add_field(
            name="Tài Nguyên Môn Phái",
            value=f"{EMOJI_LINH_THACH} {new_resources} (+{amount})",
            inline=True
        )

        # Thêm thông tin cấp độ
        if level_up:
            embed.add_field(
                name="🎉 Tăng Cấp!",
                value=f"Môn phái đã tăng lên cấp **{new_level}**!",
                inline=True
            )
        else:
            # Hiển thị tiến độ
            next_level_resources = 1000 * current_level
            progress = (new_resources / next_level_resources) * 100
            embed.add_field(
                name="Tiến Độ Tăng Cấp",
                value=f"Cấp độ hiện tại: **{current_level}**\nTiến độ: **{progress:.1f}%** ({new_resources}/{next_level_resources})",
                inline=True
            )

        # Thêm thông tin linh thạch còn lại
        embed.add_field(
            name="Linh Thạch Còn Lại",
            value=f"{EMOJI_LINH_THACH} {new_linh_thach}",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Thông báo cho chủ sở hữu nếu không phải là người đóng góp
        if ctx.author.id != sect["owner_id"]:
            try:
                owner_user = self.bot.get_user(sect["owner_id"])
                if owner_user:
                    owner_embed = discord.Embed(
                        title="🔔 Thông Báo Môn Phái",
                        description=f"**{ctx.author.name}** đã đóng góp **{amount}** linh thạch cho môn phái **{sect['name']}** của bạn!",
                        color=EMBED_COLOR_SUCCESS
                    )

                    # Thêm thông tin tăng cấp nếu có
                    if level_up:
                        owner_embed.add_field(
                            name="🎉 Tăng Cấp!",
                            value=f"Môn phái đã tăng lên cấp **{new_level}**!",
                            inline=False
                        )

                    await owner_user.send(embed=owner_embed)
            except:
                pass  # Bỏ qua nếu không gửi được DM

        # Log
        logger.info(f"{ctx.author.name} đã đóng góp {amount} linh thạch cho môn phái {sect['name']}")


async def setup(bot):
    await bot.add_cog(SectCog(bot))