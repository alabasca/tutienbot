import discord
from discord.ext import commands
import asyncio
import datetime
import logging
import re
from typing import Optional, Union

from utils.embed_utils import create_embed, create_success_embed, create_error_embed

# Cấu hình logging
logger = logging.getLogger("tutien-bot.moderation")


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warning_db = {}  # {guild_id: {user_id: [warning1, warning2, ...]}}

    async def cog_check(self, ctx):
        """Kiểm tra quyền quản lý"""
        return (
                ctx.author.guild_permissions.manage_messages or
                ctx.author.guild_permissions.kick_members or
                ctx.author.guild_permissions.ban_members or
                await self.bot.is_owner(ctx.author)
        )

    @commands.command(name="clear", aliases=["purge", "xoa"])
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, amount: int = 5):
        """Xóa một số lượng tin nhắn nhất định"""
        # Kiểm tra số lượng hợp lệ
        if amount <= 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Số lượng tin nhắn cần xóa phải lớn hơn 0."
            )
            return await ctx.send(embed=embed)

        if amount > 100:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Không thể xóa quá 100 tin nhắn cùng lúc do giới hạn của Discord."
            )
            return await ctx.send(embed=embed)

        # Xóa tin nhắn lệnh gọi đầu tiên
        await ctx.message.delete()

        # Xóa tin nhắn
        deleted = await ctx.channel.purge(limit=amount)

        # Gửi thông báo
        embed = create_success_embed(
            title="🧹 Đã Xóa Tin Nhắn",
            description=f"Đã xóa **{len(deleted)}** tin nhắn từ kênh {ctx.channel.mention}."
        )

        message = await ctx.send(embed=embed)

        # Tự động xóa thông báo sau 5 giây
        await asyncio.sleep(5)
        await message.delete()

        # Log hành động
        logger.info(f"Mod {ctx.author.name} đã xóa {len(deleted)} tin nhắn trong kênh {ctx.channel.name}")

    @commands.command(name="kick", aliases=["duoi"])
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        """Đuổi một thành viên khỏi server"""
        # Kiểm tra quyền hạn
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bạn không thể đuổi thành viên có vai trò cao hơn hoặc ngang với bạn."
            )
            return await ctx.send(embed=embed)

        if member.top_role >= ctx.guild.me.top_role:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bot không thể đuổi thành viên có vai trò cao hơn hoặc ngang với bot."
            )
            return await ctx.send(embed=embed)

        # Tạo embed xác nhận
        embed = create_embed(
            title="⚠️ Xác Nhận Đuổi Thành Viên",
            description=f"Bạn có chắc chắn muốn đuổi {member.mention} khỏi server không?\n\n**Lý do:** {reason}",
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
                    description="Hành động đuổi thành viên đã bị hủy.",
                    color=discord.Color.red()
                )
                await confirm_msg.edit(embed=cancel_embed)
                return

            # Cố gắng gửi DM cho thành viên bị đuổi
            try:
                dm_embed = create_embed(
                    title="⚠️ Bạn Đã Bị Đuổi",
                    description=f"Bạn đã bị đuổi khỏi server **{ctx.guild.name}**.\n\n**Lý do:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Bỏ qua nếu không gửi được DM

            # Đuổi thành viên
            await member.kick(reason=f"Bởi {ctx.author.name}: {reason}")

            # Tạo embed thông báo
            success_embed = create_success_embed(
                title="✅ Đã Đuổi Thành Viên",
                description=f"{member.mention} ({member.name}) đã bị đuổi khỏi server.\n\n**Lý do:** {reason}"
            )

            # Cập nhật tin nhắn
            await confirm_msg.edit(embed=success_embed)

            # Log hành động
            logger.info(f"Mod {ctx.author.name} đã đuổi {member.name} vì lý do: {reason}")

        except asyncio.TimeoutError:
            # Nếu hết thời gian
            timeout_embed = create_embed(
                title="⏰ Hết Thời Gian",
                description="Đã hết thời gian xác nhận. Hành động bị hủy.",
                color=discord.Color.red()
            )
            await confirm_msg.edit(embed=timeout_embed)

    @commands.command(name="ban", aliases=["cam"])
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        """Cấm một thành viên khỏi server"""
        # Kiểm tra quyền hạn
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bạn không thể cấm thành viên có vai trò cao hơn hoặc ngang với bạn."
            )
            return await ctx.send(embed=embed)

        if member.top_role >= ctx.guild.me.top_role:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bot không thể cấm thành viên có vai trò cao hơn hoặc ngang với bot."
            )
            return await ctx.send(embed=embed)

        # Tạo embed xác nhận
        embed = create_embed(
            title="⚠️ Xác Nhận Cấm Thành Viên",
            description=f"Bạn có chắc chắn muốn cấm {member.mention} khỏi server không?\n\n**Lý do:** {reason}",
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
                    description="Hành động cấm thành viên đã bị hủy.",
                    color=discord.Color.red()
                )
                await confirm_msg.edit(embed=cancel_embed)
                return

            # Cố gắng gửi DM cho thành viên bị cấm
            try:
                dm_embed = create_embed(
                    title="⚠️ Bạn Đã Bị Cấm",
                    description=f"Bạn đã bị cấm khỏi server **{ctx.guild.name}**.\n\n**Lý do:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except:
                pass  # Bỏ qua nếu không gửi được DM

            # Cấm thành viên
            await member.ban(reason=f"Bởi {ctx.author.name}: {reason}")

            # Tạo embed thông báo
            success_embed = create_success_embed(
                title="✅ Đã Cấm Thành Viên",
                description=f"{member.mention} ({member.name}) đã bị cấm khỏi server.\n\n**Lý do:** {reason}"
            )

            # Cập nhật tin nhắn
            await confirm_msg.edit(embed=success_embed)

            # Log hành động
            logger.info(f"Mod {ctx.author.name} đã cấm {member.name} vì lý do: {reason}")

        except asyncio.TimeoutError:
            # Nếu hết thời gian
            timeout_embed = create_embed(
                title="⏰ Hết Thời Gian",
                description="Đã hết thời gian xác nhận. Hành động bị hủy.",
                color=discord.Color.red()
            )
            await confirm_msg.edit(embed=timeout_embed)

    @commands.command(name="unban", aliases=["uncam", "huycam"])
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, *, user: str):
        """Hủy cấm một thành viên"""
        # Lấy danh sách thành viên bị cấm
        banned_users = [entry async for entry in ctx.guild.bans()]

        # Tìm người dùng
        banned_user = None
        for ban_entry in banned_users:
            # Kiểm tra tên hoặc ID
            if user.isdigit():
                # Nếu là ID
                if str(ban_entry.user.id) == user:
                    banned_user = ban_entry.user
                    break
            else:
                # Nếu là tên
                if user.lower() in ban_entry.user.name.lower() or (hasattr(ban_entry.user, 'nick') and
                                                                   ban_entry.user.nick and
                                                                   user.lower() in ban_entry.user.nick.lower()):
                    banned_user = ban_entry.user
                    break

        # Nếu không tìm thấy
        if not banned_user:
            embed = create_error_embed(
                title="❌ Không Tìm Thấy",
                description="Không tìm thấy người dùng bị cấm phù hợp với tên hoặc ID đã cung cấp."
            )
            return await ctx.send(embed=embed)

        # Hủy cấm người dùng
        await ctx.guild.unban(banned_user, reason=f"Bởi {ctx.author.name}")

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Hủy Cấm",
            description=f"Đã hủy cấm {banned_user.mention} ({banned_user.name})."
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        logger.info(f"Mod {ctx.author.name} đã hủy cấm {banned_user.name}")

    @commands.command(name="warn", aliases=["warning", "canh_cao"])
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        """Cảnh cáo một thành viên"""
        # Kiểm tra quyền hạn
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bạn không thể cảnh cáo thành viên có vai trò cao hơn hoặc ngang với bạn."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra nếu thành viên là bot
        if member.bot:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Không thể cảnh cáo bot."
            )
            return await ctx.send(embed=embed)

        # Tạo warning
        guild_id = ctx.guild.id
        member_id = member.id

        # Khởi tạo dictionary nếu cần
        if guild_id not in self.warning_db:
            self.warning_db[guild_id] = {}

        if member_id not in self.warning_db[guild_id]:
            self.warning_db[guild_id][member_id] = []

        # Thêm warning mới
        warning = {
            "reason": reason,
            "moderator_id": ctx.author.id,
            "timestamp": datetime.datetime.now().isoformat()
        }

        self.warning_db[guild_id][member_id].append(warning)

        # Đếm số lượng cảnh cáo
        warning_count = len(self.warning_db[guild_id][member_id])

        # Cố gắng gửi DM cho thành viên
        try:
            dm_embed = create_embed(
                title="⚠️ Cảnh Báo",
                description=f"Bạn đã bị cảnh cáo trong server **{ctx.guild.name}**.\n\n**Lý do:** {reason}\n**Số cảnh cáo hiện tại:** {warning_count}",
                color=discord.Color.orange()
            )
            await member.send(embed=dm_embed)
        except:
            pass  # Bỏ qua nếu không gửi được DM

        # Tạo embed thông báo
        embed = create_success_embed(
            title="⚠️ Đã Cảnh Cáo Thành Viên",
            description=f"{member.mention} đã bị cảnh cáo.\n\n**Lý do:** {reason}\n**Số cảnh cáo hiện tại:** {warning_count}"
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        logger.info(f"Mod {ctx.author.name} đã cảnh cáo {member.name} vì lý do: {reason}")

        # Thực hiện hành động tự động dựa trên số lượng cảnh cáo
        if warning_count == 3:
            # Gửi thông báo cho người điều hành
            mod_embed = create_embed(
                title="⚠️ Cảnh Báo Tự Động",
                description=f"{member.mention} đã nhận được 3 cảnh cáo. Cân nhắc đuổi hoặc cấm thành viên này.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=mod_embed)

        elif warning_count >= 5:
            # Kiểm tra quyền đuổi người
            if ctx.guild.me.guild_permissions.kick_members:
                # Cố gắng gửi DM cho thành viên trước khi đuổi
                try:
                    dm_embed = create_embed(
                        title="⚠️ Tự Động Đuổi",
                        description=f"Bạn đã bị đuổi khỏi server **{ctx.guild.name}** vì nhận quá nhiều cảnh cáo (5+).",
                        color=discord.Color.red()
                    )
                    await member.send(embed=dm_embed)
                except:
                    pass  # Bỏ qua nếu không gửi được DM

                # Đuổi thành viên
                await member.kick(reason=f"Tự động đuổi: Quá nhiều cảnh cáo (5+)")

                # Thông báo
                kick_embed = create_embed(
                    title="🚫 Tự Động Đuổi",
                    description=f"{member.mention} đã bị đuổi tự động do nhận quá nhiều cảnh cáo (5+).",
                    color=discord.Color.red()
                )
                await ctx.send(embed=kick_embed)

                # Log hành động
                logger.info(f"Hệ thống đã tự động đuổi {member.name} do nhận quá nhiều cảnh cáo (5+)")

    @commands.command(name="warnings", aliases=["listwarn", "dscanhcao"])
    @commands.has_permissions(manage_messages=True)
    async def list_warnings(self, ctx, member: discord.Member):
        """Liệt kê các cảnh cáo của một thành viên"""
        guild_id = ctx.guild.id
        member_id = member.id

        # Kiểm tra xem có cảnh cáo nào không
        if (guild_id not in self.warning_db) or (member_id not in self.warning_db[guild_id]) or (
                not self.warning_db[guild_id][member_id]):
            embed = create_embed(
                title="📋 Danh Sách Cảnh Cáo",
                description=f"{member.mention} không có cảnh cáo nào.",
                color=discord.Color.green()
            )
            return await ctx.send(embed=embed)

        # Lấy danh sách cảnh cáo
        warnings = self.warning_db[guild_id][member_id]

        # Tạo embed
        embed = create_embed(
            title=f"📋 Danh Sách Cảnh Cáo - {member.display_name}",
            description=f"{member.mention} có **{len(warnings)}** cảnh cáo:",
            color=discord.Color.orange()
        )

        # Thêm từng cảnh cáo
        for i, warning in enumerate(warnings, 1):
            # Lấy thông tin người điều hành
            mod_id = warning["moderator_id"]
            mod = ctx.guild.get_member(mod_id)
            mod_name = mod.name if mod else "Không xác định"

            # Lấy thời gian
            try:
                timestamp = datetime.datetime.fromisoformat(warning["timestamp"])
                time_str = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            except:
                time_str = "Không xác định"

            # Thêm vào embed
            embed.add_field(
                name=f"Cảnh Cáo #{i}",
                value=f"**Lý do:** {warning['reason']}\n**Bởi:** {mod_name}\n**Thời gian:** {time_str}",
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @commands.command(name="clearwarn", aliases=["delwarn", "xoacanhcao"])
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member, index: int = None):
        """Xóa một hoặc tất cả cảnh cáo của một thành viên"""
        guild_id = ctx.guild.id
        member_id = member.id

        # Kiểm tra xem có cảnh cáo nào không
        if (guild_id not in self.warning_db) or (member_id not in self.warning_db[guild_id]) or (
                not self.warning_db[guild_id][member_id]):
            embed = create_error_embed(
                title="❌ Không Có Cảnh Cáo",
                description=f"{member.mention} không có cảnh cáo nào để xóa."
            )
            return await ctx.send(embed=embed)

        # Xóa cảnh cáo cụ thể hoặc tất cả
        if index is not None:
            # Kiểm tra index hợp lệ
            if index <= 0 or index > len(self.warning_db[guild_id][member_id]):
                embed = create_error_embed(
                    title="❌ Lỗi",
                    description=f"Chỉ số cảnh cáo không hợp lệ. Thành viên có {len(self.warning_db[guild_id][member_id])} cảnh cáo, từ 1 đến {len(self.warning_db[guild_id][member_id])}."
                )
                return await ctx.send(embed=embed)

            # Xóa cảnh cáo cụ thể
            removed_warning = self.warning_db[guild_id][member_id].pop(index - 1)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Xóa Cảnh Cáo",
                description=f"Đã xóa cảnh cáo #{index} của {member.mention}."
            )

            # Thêm thông tin cảnh cáo đã xóa
            embed.add_field(
                name="Thông Tin Cảnh Cáo Đã Xóa",
                value=f"**Lý do:** {removed_warning['reason']}",
                inline=False
            )

            # Gửi embed thông báo
            await ctx.send(embed=embed)

            # Log hành động
            logger.info(f"Mod {ctx.author.name} đã xóa cảnh cáo #{index} của {member.name}")

        else:
            # Xác nhận xóa tất cả
            confirm_embed = create_embed(
                title="⚠️ Xác Nhận",
                description=f"Bạn có chắc chắn muốn xóa tất cả **{len(self.warning_db[guild_id][member_id])}** cảnh cáo của {member.mention} không?",
                color=discord.Color.orange()
            )

            # Gửi embed xác nhận
            confirm_msg = await ctx.send(embed=confirm_embed)

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
                        description="Hành động xóa tất cả cảnh cáo đã bị hủy.",
                        color=discord.Color.red()
                    )
                    await confirm_msg.edit(embed=cancel_embed)
                    return

                # Lưu số lượng để hiển thị
                warning_count = len(self.warning_db[guild_id][member_id])

                # Xóa tất cả cảnh cáo
                self.warning_db[guild_id][member_id].clear()

                # Tạo embed thông báo
                embed = create_success_embed(
                    title="✅ Đã Xóa Tất Cả Cảnh Cáo",
                    description=f"Đã xóa tất cả **{warning_count}** cảnh cáo của {member.mention}."
                )

                # Cập nhật tin nhắn
                await confirm_msg.edit(embed=embed)

                # Log hành động
                logger.info(f"Mod {ctx.author.name} đã xóa tất cả cảnh cáo của {member.name}")

                return

            except asyncio.TimeoutError:
                # Nếu hết thời gian
                timeout_embed = create_embed(
                    title="⏰ Hết Thời Gian",
                    description="Đã hết thời gian xác nhận. Hành động bị hủy.",
                    color=discord.Color.red()
                )
                await confirm_msg.edit(embed=timeout_embed)
                return

    @commands.command(name="mute", aliases=["cam_chat"])
    @commands.has_permissions(manage_roles=True)
    async def mute_member(self, ctx, member: discord.Member, duration: Optional[str] = None, *,
                          reason: str = "Không có lý do"):
        """Cấm chat một thành viên"""
        # Kiểm tra quyền hạn
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bạn không thể cấm chat thành viên có vai trò cao hơn hoặc ngang với bạn."
            )
            return await ctx.send(embed=embed)

        if member.top_role >= ctx.guild.me.top_role:
            embed = create_error_embed(
                title="❌ Lỗi Quyền Hạn",
                description="Bot không thể cấm chat thành viên có vai trò cao hơn hoặc ngang với bot."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra vai trò Muted
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        # Nếu chưa có vai trò Muted, tạo mới
        if not muted_role:
            try:
                # Tạo vai trò mới
                muted_role = await ctx.guild.create_role(
                    name="Muted",
                    reason="Tạo vai trò Muted cho lệnh mute"
                )

                # Cập nhật quyền cho tất cả kênh
                for channel in ctx.guild.channels:
                    await channel.set_permissions(
                        muted_role,
                        send_messages=False,
                        speak=False,
                        add_reactions=False
                    )
            except Exception as e:
                # Nếu không tạo được vai trò
                embed = create_error_embed(
                    title="❌ Lỗi",
                    description=f"Không thể tạo vai trò Muted: {str(e)}"
                )
                return await ctx.send(embed=embed)

        # Kiểm tra đã có vai trò Muted chưa
        if muted_role in member.roles:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"{member.mention} đã bị cấm chat rồi."
            )
            return await ctx.send(embed=embed)

        # Phân tích thời gian
        duration_seconds = 0
        if duration:
            duration_seconds = self.parse_time(duration)

        # Thêm vai trò Muted
        await member.add_roles(muted_role, reason=f"Bởi {ctx.author.name}: {reason}")

        # Cố gắng gửi DM cho thành viên
        try:
            dm_embed = create_embed(
                title="⚠️ Bạn Đã Bị Cấm Chat",
                description=(
                    f"Bạn đã bị cấm chat trong server **{ctx.guild.name}**.\n\n"
                    f"**Lý do:** {reason}\n"
                    f"**Thời hạn:** {duration if duration else 'Vô thời hạn'}"
                ),
                color=discord.Color.red()
            )
            await member.send(embed=dm_embed)
        except:
            pass  # Bỏ qua nếu không gửi được DM

        # Tạo embed thông báo
        embed = create_success_embed(
            title="🔇 Đã Cấm Chat",
            description=(
                f"{member.mention} đã bị cấm chat.\n\n"
                f"**Lý do:** {reason}\n"
                f"**Thời hạn:** {duration if duration else 'Vô thời hạn'}"
            )
        )

        # Gửi embed
        mute_msg = await ctx.send(embed=embed)

        # Log hành động
        logger.info(
            f"Mod {ctx.author.name} đã cấm chat {member.name} với lý do: {reason}, thời hạn: {duration if duration else 'Vô thời hạn'}")

        # Nếu có thời hạn, đặt hẹn giờ hủy cấm chat
        if duration_seconds > 0:
            # Tạo task để hủy cấm chat sau khi hết thời gian
            await asyncio.sleep(duration_seconds)

            # Kiểm tra xem thành viên còn trong server không
            member = ctx.guild.get_member(member.id)
            if not member:
                return

            # Kiểm tra xem thành viên còn bị cấm chat không
            if muted_role in member.roles:
                # Hủy cấm chat
                await member.remove_roles(muted_role, reason="Hết thời hạn cấm chat")

                # Tạo embed thông báo
                unmute_embed = create_success_embed(
                    title="🔊 Đã Hết Thời Hạn Cấm Chat",
                    description=f"{member.mention} đã được hủy cấm chat tự động sau khi hết thời hạn."
                )

                # Gửi embed
                await ctx.send(embed=unmute_embed)

                # Cố gắng gửi DM cho thành viên
                try:
                    dm_embed = create_embed(
                        title="✅ Hết Thời Hạn Cấm Chat",
                        description=f"Bạn đã được hủy cấm chat trong server **{ctx.guild.name}** sau khi hết thời hạn.",
                        color=discord.Color.green()
                    )
                    await member.send(embed=dm_embed)
                except:
                    pass  # Bỏ qua nếu không gửi được DM

                # Log hành động
                logger.info(f"Hệ thống đã tự động hủy cấm chat cho {member.name} sau khi hết thời hạn")

    @commands.command(name="unmute", aliases=["huycamchat"])
    @commands.has_permissions(manage_roles=True)
    async def unmute_member(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        """Hủy cấm chat một thành viên"""
        # Kiểm tra vai trò Muted
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        # Nếu không có vai trò Muted
        if not muted_role:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Không tìm thấy vai trò Muted trong server này."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem thành viên có bị cấm chat không
        if muted_role not in member.roles:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"{member.mention} không bị cấm chat."
            )
            return await ctx.send(embed=embed)

        # Hủy cấm chat
        await member.remove_roles(muted_role, reason=f"Bởi {ctx.author.name}: {reason}")

        # Tạo embed thông báo
        embed = create_success_embed(
            title="🔊 Đã Hủy Cấm Chat",
            description=f"{member.mention} đã được hủy cấm chat.\n\n**Lý do:** {reason}"
        )

        # Gửi embed
        await ctx.send(embed=embed)

        # Cố gắng gửi DM cho thành viên
        try:
            dm_embed = create_embed(
                title="✅ Bạn Đã Được Hủy Cấm Chat",
                description=f"Bạn đã được hủy cấm chat trong server **{ctx.guild.name}**.\n\n**Lý do:** {reason}",
                color=discord.Color.green()
            )
            await member.send(embed=dm_embed)
        except:
            pass  # Bỏ qua nếu không gửi được DM

        # Log hành động
        logger.info(f"Mod {ctx.author.name} đã hủy cấm chat cho {member.name} với lý do: {reason}")

    @commands.command(name="slowmode", aliases=["cham", "slow"])
    @commands.has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int = None):
        """Đặt chế độ chậm cho kênh hiện tại"""
        # Nếu không cung cấp thời gian, hiển thị trạng thái hiện tại
        if seconds is None:
            current_slowmode = ctx.channel.slowmode_delay

            if current_slowmode == 0:
                embed = create_embed(
                    title="⏱️ Chế Độ Chậm",
                    description=f"Chế độ chậm hiện tại của kênh {ctx.channel.mention} đang tắt.",
                    color=discord.Color.blue()
                )
            else:
                embed = create_embed(
                    title="⏱️ Chế Độ Chậm",
                    description=f"Chế độ chậm hiện tại của kênh {ctx.channel.mention} là **{current_slowmode}** giây.",
                    color=discord.Color.blue()
                )

            # Thêm hướng dẫn
            embed.add_field(
                name="Hướng Dẫn",
                value="Sử dụng `!slowmode <seconds>` để đặt chế độ chậm, hoặc `!slowmode 0` để tắt chế độ chậm.",
                inline=False
            )

            return await ctx.send(embed=embed)

        # Kiểm tra giới hạn
        if seconds < 0:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Thời gian chế độ chậm không thể là số âm."
            )
            return await ctx.send(embed=embed)

        if seconds > 21600:  # 6 giờ
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Thời gian chế độ chậm không thể vượt quá 21600 giây (6 giờ)."
            )
            return await ctx.send(embed=embed)

        # Đặt chế độ chậm
        await ctx.channel.edit(slowmode_delay=seconds)

        # Tạo embed thông báo
        if seconds == 0:
            embed = create_success_embed(
                title="✅ Đã Tắt Chế Độ Chậm",
                description=f"Đã tắt chế độ chậm cho kênh {ctx.channel.mention}."
            )
        else:
            embed = create_success_embed(
                title="⏱️ Đã Đặt Chế Độ Chậm",
                description=f"Đã đặt chế độ chậm **{seconds}** giây cho kênh {ctx.channel.mention}."
            )

        # Gửi embed
        await ctx.send(embed=embed)

        # Log hành động
        if seconds == 0:
            logger.info(f"Mod {ctx.author.name} đã tắt chế độ chậm cho kênh {ctx.channel.name}")
        else:
            logger.info(f"Mod {ctx.author.name} đã đặt chế độ chậm {seconds} giây cho kênh {ctx.channel.name}")

    def parse_time(self, time_str: str) -> int:
        """Phân tích chuỗi thời gian và chuyển đổi thành số giây"""
        import re

        # Loại bỏ khoảng trắng và chuyển sang chữ thường
        time_str = time_str.lower().strip()

        # Thời gian mặc định (1 giờ)
        if time_str.isdigit():
            return int(time_str) * 60  # Nếu chỉ là số, giả định là phút

        # Tìm kiếm các đơn vị thời gian
        seconds = 0

        # Tìm kiếm số giây (s)
        if 's' in time_str:
            s_match = re.search(r'(\d+)s', time_str)
            if s_match:
                seconds += int(s_match.group(1))

        # Tìm kiếm số phút (m)
        if 'm' in time_str:
            m_match = re.search(r'(\d+)m', time_str)
            if m_match:
                seconds += int(m_match.group(1)) * 60

        # Tìm kiếm số giờ (h)
        if 'h' in time_str:
            h_match = re.search(r'(\d+)h', time_str)
            if h_match:
                seconds += int(h_match.group(1)) * 3600

        # Tìm kiếm số ngày (d)
        if 'd' in time_str:
            d_match = re.search(r'(\d+)d', time_str)
            if d_match:
                seconds += int(d_match.group(1)) * 86400

        # Nếu không tìm thấy đơn vị thời gian, giả định là phút
        if seconds == 0:
            try:
                seconds = int(re.search(r'(\d+)', time_str).group(1)) * 60
            except (AttributeError, ValueError):
                seconds = 3600  # Mặc định 1 giờ

        return seconds

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Xử lý lỗi lệnh"""
        if isinstance(error, commands.MissingRequiredArgument):
            embed = create_error_embed(
                title="❌ Thiếu Tham Số",
                description=f"Thiếu tham số cần thiết: `{error.param.name}`.\nVui lòng sử dụng `!help {ctx.command}` để xem cách sử dụng lệnh."
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BadArgument):
            embed = create_error_embed(
                title="❌ Tham Số Không Hợp Lệ",
                description=f"Tham số không hợp lệ: {str(error)}.\nVui lòng sử dụng `!help {ctx.command}` để xem cách sử dụng lệnh."
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingPermissions):
            embed = create_error_embed(
                title="❌ Không Đủ Quyền Hạn",
                description="Bạn không có đủ quyền hạn để sử dụng lệnh này."
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BotMissingPermissions):
            embed = create_error_embed(
                title="❌ Bot Không Đủ Quyền Hạn",
                description=f"Bot không có đủ quyền hạn để thực hiện lệnh này.\nCần quyền: {', '.join(error.missing_permissions)}"
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = create_error_embed(
                title="⏱️ Lệnh Đang Trong Thời Gian Hồi",
                description=f"Vui lòng thử lại sau {error.retry_after:.2f} giây."
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CheckFailure):
            embed = create_error_embed(
                title="❌ Không Thể Thực Hiện",
                description="Bạn không thể sử dụng lệnh này."
            )
            await ctx.send(embed=embed)

        else:
            # Log lỗi không xác định
            logger.error(f"Lỗi không xác định khi thực hiện lệnh {ctx.command}: {error}", exc_info=error)

            embed = create_error_embed(
                title="❌ Đã Xảy Ra Lỗi",
                description="Đã xảy ra lỗi khi thực hiện lệnh này. Vui lòng thử lại sau hoặc liên hệ quản trị viên."
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ModerationCog(bot))
