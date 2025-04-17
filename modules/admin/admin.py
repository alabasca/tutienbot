import discord
from discord.ext import commands
import asyncio
import datetime
import logging
import json
import os
from typing import List, Dict, Any, Optional, Union

from database.mongo_handler import get_user_or_create, update_user, users_collection, sects_collection
from config import (
    CULTIVATION_REALMS, EMBED_COLOR, EMBED_COLOR_SUCCESS,
    EMBED_COLOR_ERROR, EMOJI_LINH_THACH, EMOJI_EXP
)
from utils.text_utils import format_number
from utils.embed_utils import create_embed, create_success_embed, create_error_embed

# Cấu hình logging
logger = logging.getLogger("tutien-bot.admin")


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Kiểm tra quyền admin"""
        # Kiểm tra xem người dùng có quyền admin hay không
        return ctx.author.guild_permissions.administrator or await self.bot.is_owner(ctx.author)

    @commands.command(name="setexp", aliases=["setexperience", "setlevel"])
    @commands.is_owner()
    async def set_experience(self, ctx, member: discord.Member, amount: int):
        """Đặt kinh nghiệm cho người chơi (chỉ dành cho admin)"""
        # Kiểm tra số lượng hợp lệ
        if amount < 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Kinh nghiệm không thể là số âm."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lưu giá trị cũ để so sánh
        old_exp = user.get("experience", 0)
        old_realm_id = user.get("realm_id", 0)

        # Cập nhật kinh nghiệm
        await update_user(member.id, {"experience": amount})

        # Xác định cảnh giới mới
        new_realm_id = old_realm_id
        for realm in CULTIVATION_REALMS:
            if realm["id"] > old_realm_id and amount >= realm["exp_required"]:
                new_realm_id = realm["id"]
            elif realm["id"] <= old_realm_id and amount < realm["exp_required"]:
                new_realm_id = realm["id"] - 1
                break

        # Đảm bảo cảnh giới hợp lệ
        new_realm_id = max(0, min(new_realm_id, len(CULTIVATION_REALMS) - 1))

        # Cập nhật cảnh giới nếu có thay đổi
        if new_realm_id != old_realm_id:
            await update_user(member.id, {"realm_id": new_realm_id})

        # Lấy tên cảnh giới mới
        new_realm_name = CULTIVATION_REALMS[new_realm_id]["name"]

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Cập Nhật Kinh Nghiệm",
            description=f"Đã đặt kinh nghiệm cho {member.mention} thành **{format_number(amount)}**."
        )

        # Thêm thông tin thay đổi
        embed.add_field(
            name="Thay Đổi",
            value=f"Trước: **{format_number(old_exp)}** → Sau: **{format_number(amount)}**",
            inline=False
        )

        # Thêm thông tin cảnh giới nếu có thay đổi
        if new_realm_id != old_realm_id:
            old_realm_name = CULTIVATION_REALMS[old_realm_id]["name"]
            embed.add_field(
                name="Cảnh Giới",
                value=f"Trước: **{old_realm_name}** → Sau: **{new_realm_name}**",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        logger.info(f"Admin {ctx.author.name} đã đặt kinh nghiệm cho {member.name} thành {amount}")

    @commands.command(name="addexp", aliases=["addexperience", "giveexp"])
    @commands.is_owner()
    async def add_experience(self, ctx, member: discord.Member, amount: int):
        """Thêm kinh nghiệm cho người chơi (chỉ dành cho admin)"""
        # Kiểm tra số lượng hợp lệ
        if amount <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Kinh nghiệm thêm vào phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lưu giá trị cũ để so sánh
        old_exp = user.get("experience", 0)
        old_realm_id = user.get("realm_id", 0)

        # Tính giá trị mới
        new_exp = old_exp + amount

        # Cập nhật kinh nghiệm
        await update_user(member.id, {"experience": new_exp})

        # Xác định cảnh giới mới
        new_realm_id = old_realm_id
        for realm in CULTIVATION_REALMS:
            if realm["id"] > old_realm_id and new_exp >= realm["exp_required"]:
                new_realm_id = realm["id"]

        # Cập nhật cảnh giới nếu có thay đổi
        if new_realm_id != old_realm_id:
            await update_user(member.id, {"realm_id": new_realm_id})

        # Lấy tên cảnh giới mới
        new_realm_name = CULTIVATION_REALMS[new_realm_id]["name"]

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Thêm Kinh Nghiệm",
            description=f"Đã thêm **{format_number(amount)}** kinh nghiệm cho {member.mention}."
        )

        # Thêm thông tin thay đổi
        embed.add_field(
            name="Thay Đổi",
            value=f"Trước: **{format_number(old_exp)}** → Sau: **{format_number(new_exp)}**",
            inline=False
        )

        # Thêm thông tin cảnh giới nếu có thay đổi
        if new_realm_id != old_realm_id:
            old_realm_name = CULTIVATION_REALMS[old_realm_id]["name"]
            embed.add_field(
                name="Cảnh Giới",
                value=f"Trước: **{old_realm_name}** → Sau: **{new_realm_name}**",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        logger.info(f"Admin {ctx.author.name} đã thêm {amount} kinh nghiệm cho {member.name}")

    @commands.command(name="setlinhthach", aliases=["setmoney", "setcoin"])
    @commands.is_owner()
    async def set_linh_thach(self, ctx, member: discord.Member, amount: int):
        """Đặt số lượng linh thạch cho người chơi (chỉ dành cho admin)"""
        # Kiểm tra số lượng hợp lệ
        if amount < 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Linh thạch không thể là số âm."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lưu giá trị cũ để so sánh
        old_amount = user.get("linh_thach", 0)

        # Cập nhật linh thạch
        await update_user(member.id, {"linh_thach": amount})

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Cập Nhật Linh Thạch",
            description=f"Đã đặt linh thạch cho {member.mention} thành **{format_number(amount)}**."
        )

        # Thêm thông tin thay đổi
        embed.add_field(
            name="Thay Đổi",
            value=f"Trước: **{format_number(old_amount)}** → Sau: **{format_number(amount)}**",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        logger.info(f"Admin {ctx.author.name} đã đặt linh thạch cho {member.name} thành {amount}")

    @commands.command(name="addlinhthach", aliases=["addmoney", "givecoin"])
    @commands.is_owner()
    async def add_linh_thach(self, ctx, member: discord.Member, amount: int):
        """Thêm linh thạch cho người chơi (chỉ dành cho admin)"""
        # Kiểm tra số lượng hợp lệ
        if amount <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Linh thạch thêm vào phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        # Lấy thông tin người dùng
        user = await get_user_or_create(member.id, member.name)

        # Lưu giá trị cũ để so sánh
        old_amount = user.get("linh_thach", 0)

        # Tính giá trị mới
        new_amount = old_amount + amount

        # Cập nhật linh thạch
        await update_user(member.id, {"linh_thach": new_amount})

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Thêm Linh Thạch",
            description=f"Đã thêm **{format_number(amount)}** linh thạch cho {member.mention}."
        )

        # Thêm thông tin thay đổi
        embed.add_field(
            name="Thay Đổi",
            value=f"Trước: **{format_number(old_amount)}** → Sau: **{format_number(new_amount)}**",
            inline=False
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        logger.info(f"Admin {ctx.author.name} đã thêm {amount} linh thạch cho {member.name}")

    @commands.command(name="resetuser", aliases=["reset"])
    @commands.is_owner()
    async def reset_user(self, ctx, member: discord.Member):
        """Đặt lại toàn bộ dữ liệu của người chơi (chỉ dành cho admin)"""
        # Tạo embed xác nhận
        embed = create_embed(
            title="⚠️ Xác Nhận Đặt Lại",
            description=f"Bạn có chắc chắn muốn đặt lại toàn bộ dữ liệu của {member.mention}?\n\nHành động này không thể hoàn tác!",
            color=discord.Color.orange()
        )

        # Gửi embed xác nhận
        confirm_msg = await ctx.send(embed=embed)

        # Thêm các emoji xác nhận
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        # Hàm kiểm tra reaction
        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["✅",
                                                                        "❌"] and reaction.message.id == confirm_msg.id

        try:
            # Chờ phản ứng
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

            # Nếu từ chối
            if str(reaction.emoji) == "❌":
                cancel_embed = create_embed(
                    title="❌ Đã Hủy",
                    description="Hành động đặt lại dữ liệu đã bị hủy.",
                    color=EMBED_COLOR_ERROR
                )
                await confirm_msg.edit(embed=cancel_embed)
                return

            # Lấy thông tin người dùng
            user_data = await get_user_or_create(member.id, member.name)

            # Lưu thông tin môn phái
            sect_id = user_data.get("sect_id")

            if sect_id:
                # Nếu là chủ sở hữu môn phái
                sect = await sects_collection.find_one({"sect_id": sect_id})

                if sect and sect["owner_id"] == member.id:
                    # Lấy danh sách thành viên
                    members_list = sect.get("members", [])

                    # Cập nhật thông tin cho tất cả thành viên
                    for member_id in members_list:
                        if member_id != member.id:  # Bỏ qua chủ sở hữu
                            await update_user(member_id, {"sect_id": None})

                    # Xóa môn phái
                    await sects_collection.delete_one({"sect_id": sect_id})
                else:
                    # Nếu chỉ là thành viên, xóa khỏi môn phái
                    await sects_collection.update_one(
                        {"sect_id": sect_id},
                        {"$pull": {"members": member.id}}
                    )

            # Xóa dữ liệu người dùng
            await users_collection.delete_one({"user_id": member.id})

            # Tạo người dùng mới
            await get_user_or_create(member.id, member.name)

            # Tạo embed thông báo
            success_embed = create_success_embed(
                title="✅ Đã Đặt Lại Dữ Liệu",
                description=f"Toàn bộ dữ liệu của {member.mention} đã được đặt lại thành công."
            )

            if sect_id and sect and sect["owner_id"] == member.id:
                success_embed.add_field(
                    name="Môn Phái",
                    value=f"Môn phái **{sect['name']}** đã bị giải tán do chủ sở hữu bị đặt lại dữ liệu.",
                    inline=False
                )

            # Cập nhật tin nhắn
            await confirm_msg.edit(embed=success_embed)

            # Log hành động
            logger.info(f"Admin {ctx.author.name} đã đặt lại dữ liệu của {member.name}")

        except asyncio.TimeoutError:
            # Nếu hết thời gian
            timeout_embed = create_embed(
                title="⏰ Hết Thời Gian",
                description="Đã hết thời gian xác nhận. Hành động bị hủy.",
                color=EMBED_COLOR_ERROR
            )
            await confirm_msg.edit(embed=timeout_embed)

    @commands.command(name="announcement", aliases=["thongbao", "announce"])
    @commands.is_owner()
    async def send_announcement(self, ctx, *, message: str):
        """Gửi thông báo toàn server (chỉ dành cho admin)"""
        # Tạo embed thông báo
        embed = create_embed(
            title="📢 Thông Báo Quan Trọng",
            description=message
        )

        # Thêm thông tin người gửi
        embed.set_footer(text=f"Thông báo bởi {ctx.author.name} • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Tìm kênh thông báo
        announcement_channel = discord.utils.get(ctx.guild.text_channels, name="thông-báo") or discord.utils.get(
            ctx.guild.text_channels, name="thongbao") or discord.utils.get(ctx.guild.text_channels,
                                                                           name="announcements") or discord.utils.get(
            ctx.guild.text_channels, name="general") or ctx.channel

        # Gửi thông báo
        await announcement_channel.send(embed=embed)

        # Nếu gửi vào kênh khác với kênh hiện tại
        if announcement_channel.id != ctx.channel.id:
            confirm_embed = create_success_embed(
                title="✅ Đã Gửi Thông Báo",
                description=f"Thông báo đã được gửi vào kênh {announcement_channel.mention}."
            )
            await ctx.send(embed=confirm_embed)

        # Log hành động
        logger.info(f"Admin {ctx.author.name} đã gửi thông báo: {message}")

    @commands.command(name="serverinfo", aliases=["guildinfo"])
    @commands.has_permissions(administrator=True)
    async def server_info(self, ctx):
        """Hiển thị thông tin chi tiết về server (chỉ dành cho admin)"""
        guild = ctx.guild

        # Tạo embed
        embed = create_embed(
            title=f"📊 Thông Tin Chi Tiết Server: {guild.name}",
            description=guild.description or "Không có mô tả"
        )

        # Thêm thông tin cơ bản
        embed.add_field(
            name="ID",
            value=guild.id,
            inline=True
        )

        embed.add_field(
            name="Chủ Sở Hữu",
            value=f"{guild.owner.mention} ({guild.owner.id})" if guild.owner else "Không xác định",
            inline=True
        )

        embed.add_field(
            name="Ngày Tạo",
            value=f"{guild.created_at.strftime('%d/%m/%Y %H:%M:%S')} ({(datetime.datetime.now() - guild.created_at).days} ngày trước)",
            inline=True
        )

        # Thêm thông tin thành viên
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots

        embed.add_field(
            name="Thành Viên",
            value=f"Tổng: {guild.member_count}\nNgười: {humans}\nBot: {bots}",
            inline=True
        )

        # Thêm thông tin trạng thái
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])

        embed.add_field(
            name="Trạng Thái",
            value=f"🟢 Online: {online}\n🟡 Idle: {idle}\n🔴 DND: {dnd}\n⚫ Offline: {offline}",
            inline=True
        )

        # Thêm thông tin kênh
        embed.add_field(
            name="Kênh",
            value=f"Văn bản: {len(guild.text_channels)}\nThoại: {len(guild.voice_channels)}\nDanh mục: {len(guild.categories)}",
            inline=True
        )

        # Thêm thông tin nâng cao
        embed.add_field(
            name="Vai Trò",
            value=f"Số lượng: {len(guild.roles)}",
            inline=True
        )

        embed.add_field(
            name="Emoji",
            value=f"Số lượng: {len(guild.emojis)}/{guild.emoji_limit}",
            inline=True
        )

        embed.add_field(
            name="Boost",
            value=f"Cấp độ: {guild.premium_tier}\nBooster: {guild.premium_subscription_count}",
            inline=True
        )

        # Thêm thông tin bảo mật
        embed.add_field(
            name="Bảo Mật",
            value=f"Xác minh: {guild.verification_level}\nNội dung: {guild.explicit_content_filter}",
            inline=True
        )

        # Thêm thông tin máy chủ
        region = guild.region if hasattr(guild, "region") else "Không xác định"
        embed.add_field(
            name="Máy Chủ",
            value=f"Vùng: {region}",
            inline=True
        )

        # Thêm icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="reloadcog", aliases=["reload"])
    @commands.is_owner()
    async def reload_cog(self, ctx, *, cog: str):
        """Tải lại một module cog (chỉ dành cho owner)"""
        try:
            # Chuẩn hóa tên cog
            if not cog.startswith("modules."):
                cog = f"modules.{cog}"

            # Tải lại cog
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Tải Lại Module",
                description=f"Module `{cog}` đã được tải lại thành công."
            )

            await ctx.send(embed=embed)

            # Log hành động
            logger.info(f"Owner {ctx.author.name} đã tải lại module {cog}")

        except Exception as e:
            # Tạo embed thông báo lỗi
            embed = create_error_embed(
                title="❌ Lỗi Khi Tải Lại Module",
                description=f"Đã xảy ra lỗi khi tải lại module `{cog}`:\n```{str(e)}```"
            )

            await ctx.send(embed=embed)

            # Log lỗi
            logger.error(f"Lỗi khi tải lại module {cog}: {e}")

    @commands.command(name="loadcog", aliases=["load"])
    @commands.is_owner()
    async def load_cog(self, ctx, *, cog: str):
        """Tải một module cog (chỉ dành cho owner)"""
        try:
            # Chuẩn hóa tên cog
            if not cog.startswith("modules."):
                cog = f"modules.{cog}"

            # Tải cog
            await self.bot.load_extension(cog)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Tải Module",
                description=f"Module `{cog}` đã được tải thành công."
            )

            await ctx.send(embed=embed)

            # Log hành động
            logger.info(f"Owner {ctx.author.name} đã tải module {cog}")

        except Exception as e:
            # Tạo embed thông báo lỗi
            embed = create_error_embed(
                title="❌ Lỗi Khi Tải Module",
                description=f"Đã xảy ra lỗi khi tải module `{cog}`:\n```{str(e)}```"
            )

            await ctx.send(embed=embed)

            # Log lỗi
            logger.error(f"Lỗi khi tải module {cog}: {e}")

    @commands.command(name="unloadcog", aliases=["unload"])
    @commands.is_owner()
    async def unload_cog(self, ctx, *, cog: str):
        """Hủy tải một module cog (chỉ dành cho owner)"""
        try:
            # Không cho phép hủy tải module admin
            if cog.endswith("admin") or cog == "modules.admin.admin":
                embed = create_error_embed(
                    title="❌ Không Thể Hủy Tải",
                    description="Không thể hủy tải module admin để đảm bảo tính khả dụng."
                )
                return await ctx.send(embed=embed)

            # Chuẩn hóa tên cog
            if not cog.startswith("modules."):
                cog = f"modules.{cog}"

            # Hủy tải cog
            await self.bot.unload_extension(cog)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Hủy Tải Module",
                description=f"Module `{cog}` đã được hủy tải thành công."
            )

            await ctx.send(embed=embed)

            # Log hành động
            logger.info(f"Owner {ctx.author.name} đã hủy tải module {cog}")

        except Exception as e:
            # Tạo embed thông báo lỗi
            embed = create_error_embed(
                title="❌ Lỗi Khi Hủy Tải Module",
                description=f"Đã xảy ra lỗi khi hủy tải module `{cog}`:\n```{str(e)}```"
            )

            await ctx.send(embed=embed)

            # Log lỗi
            logger.error(f"Lỗi khi hủy tải module {cog}: {e}")


async def setup(bot):
    await bot.add_cog(AdminCog(bot))