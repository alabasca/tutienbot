# modules/social/friends.py
import discord
from discord.ext import commands
import asyncio
import datetime
import logging
from typing import Dict, List, Optional, Union, Any

from database.mongo_handler import MongoHandler
from database.models.user_model import User
from utils.embed_utils import create_embed, create_success_embed, create_error_embed
from utils.text_utils import format_number

# Cấu hình logging
logger = logging.getLogger("tutien-bot.friends")


class FriendsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_handler = MongoHandler()
        self.friend_requests = {}  # {user_id: [request1, request2, ...]}

    async def get_user_data(self, user_id: int) -> Optional[User]:
        """Lấy dữ liệu người dùng từ database"""
        user_data = await self.mongo_handler.find_one_async("users", {"user_id": user_id})
        if user_data:
            return User.from_dict(user_data)
        return None

    async def save_user_data(self, user: User) -> bool:
        """Lưu dữ liệu người dùng vào database"""
        result = await self.mongo_handler.update_one_async(
            "users",
            {"user_id": user.user_id},
            {"$set": user.to_dict()},
            upsert=True
        )
        return result.acknowledged

    @commands.group(name="friend", aliases=["friends", "banbe"], invoke_without_command=True)
    async def friend(self, ctx):
        """Hiển thị danh sách bạn bè"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Lấy danh sách bạn bè
        friends = user.social.get("friends", [])

        # Tạo embed hiển thị danh sách bạn bè
        embed = create_embed(
            title="👥 Danh Sách Bạn Bè",
            description=f"Bạn có {len(friends)} người bạn"
        )

        # Nếu không có bạn bè
        if not friends:
            embed.add_field(
                name="Không có bạn bè",
                value="Bạn chưa có bạn bè nào. Sử dụng `!friend add @người_dùng` để thêm bạn bè.",
                inline=False
            )
        else:
            # Hiển thị danh sách bạn bè
            for i, friend_data in enumerate(friends, 1):
                friend_id = friend_data.get("user_id")
                added_date = friend_data.get("added_date", datetime.datetime.utcnow())

                # Lấy thông tin người dùng từ Discord
                friend = self.bot.get_user(friend_id)
                friend_name = friend.name if friend else f"Người dùng #{friend_id}"

                # Lấy thông tin người dùng từ database
                friend_user = await self.get_user_data(friend_id)

                if friend_user:
                    # Hiển thị thông tin cơ bản
                    value = f"**Cảnh giới:** {friend_user.cultivation['realm']} cảnh {friend_user.cultivation['realm_level']}\n"
                    value += f"**Kết bạn từ:** {added_date.strftime('%d/%m/%Y')}\n"

                    # Kiểm tra xem có online không
                    if friend and friend.status != discord.Status.offline:
                        value += "**Trạng thái:** 🟢 Đang online"
                    else:
                        value += "**Trạng thái:** ⚪ Offline"
                else:
                    value = "*Không tìm thấy thông tin người dùng*"

                embed.add_field(
                    name=f"{i}. {friend_name}",
                    value=value,
                    inline=False
                )

        # Thêm hướng dẫn sử dụng
        embed.set_footer(text="Sử dụng !friend add @người_dùng để thêm bạn | !friend remove @người_dùng để xóa bạn")

        # Gửi embed
        await ctx.send(embed=embed)

    @friend.command(name="add", aliases=["them"])
    async def friend_add(self, ctx, member: discord.Member):
        """Gửi lời mời kết bạn cho người khác"""
        # Kiểm tra xem có phải tự kết bạn với mình không
        if member.id == ctx.author.id:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn không thể kết bạn với chính mình."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem người được mời có phải là bot không
        if member.bot:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn không thể kết bạn với bot."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người được mời
        target_user = await self.get_user_data(member.id)
        if not target_user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"{member.display_name} chưa bắt đầu tu tiên."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem đã là bạn bè chưa
        for friend in user.social.get("friends", []):
            if friend.get("user_id") == member.id:
                embed = create_error_embed(
                    title="❌ Đã Là Bạn Bè",
                    description=f"Bạn và {member.display_name} đã là bạn bè rồi."
                )
                return await ctx.send(embed=embed)

        # Kiểm tra xem đã gửi lời mời trước đó chưa
        if member.id in self.friend_requests.get(ctx.author.id, []):
            embed = create_error_embed(
                title="❌ Lời Mời Đang Chờ",
                description=f"Bạn đã gửi lời mời kết bạn cho {member.display_name} rồi. Vui lòng đợi họ chấp nhận."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem người được mời đã gửi lời mời cho mình chưa
        if ctx.author.id in self.friend_requests.get(member.id, []):
            # Tự động chấp nhận lời mời
            # Thêm vào danh sách bạn bè của người gửi
            user.social.setdefault("friends", []).append({
                "user_id": member.id,
                "added_date": datetime.datetime.utcnow()
            })
            await self.save_user_data(user)

            # Thêm vào danh sách bạn bè của người được mời
            target_user.social.setdefault("friends", []).append({
                "user_id": ctx.author.id,
                "added_date": datetime.datetime.utcnow()
            })
            await self.save_user_data(target_user)

            # Xóa lời mời
            if member.id in self.friend_requests:
                self.friend_requests[member.id].remove(ctx.author.id)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Kết Bạn",
                description=f"Bạn và {member.mention} đã trở thành bạn bè!"
            )

            await ctx.send(embed=embed)

            # Gửi thông báo cho người được mời
            try:
                embed = create_success_embed(
                    title="✅ Đã Kết Bạn",
                    description=f"{ctx.author.mention} đã chấp nhận lời mời kết bạn của bạn!"
                )
                await member.send(embed=embed)
            except:
                pass  # Bỏ qua nếu không gửi được DM

            return

        # Kiểm tra cài đặt của người được mời
        if not target_user.settings.get("friend_requests", True):
            embed = create_error_embed(
                title="❌ Không Thể Gửi Lời Mời",
                description=f"{member.display_name} đã tắt tính năng nhận lời mời kết bạn."
            )
            return await ctx.send(embed=embed)

        # Thêm vào danh sách lời mời đang chờ
        if member.id not in self.friend_requests:
            self.friend_requests[member.id] = []
        self.friend_requests[member.id].append(ctx.author.id)

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Gửi Lời Mời",
            description=f"Đã gửi lời mời kết bạn cho {member.mention}. Vui lòng đợi họ chấp nhận."
        )

        await ctx.send(embed=embed)

        # Gửi thông báo cho người được mời
        try:
            embed = create_embed(
                title="👋 Lời Mời Kết Bạn",
                description=f"{ctx.author.mention} muốn kết bạn với bạn!\n\n"
                            f"Sử dụng `!friend accept @{ctx.author.name}` để chấp nhận hoặc `!friend reject @{ctx.author.name}` để từ chối."
            )
            await member.send(embed=embed)
        except:
            # Nếu không gửi được DM, thông báo trong kênh
            await ctx.send(
                f"Lưu ý: Không thể gửi thông báo trực tiếp cho {member.mention}. Họ có thể không nhận được thông báo về lời mời kết bạn.")

    @friend.command(name="remove", aliases=["xoa", "delete"])
    async def friend_remove(self, ctx, member: discord.Member):
        """Xóa một người khỏi danh sách bạn bè"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem có phải là bạn bè không
        friend_index = None
        for i, friend in enumerate(user.social.get("friends", [])):
            if friend.get("user_id") == member.id:
                friend_index = i
                break

        if friend_index is None:
            embed = create_error_embed(
                title="❌ Không Phải Bạn Bè",
                description=f"Bạn và {member.display_name} không phải là bạn bè."
            )
            return await ctx.send(embed=embed)

        # Tạo embed xác nhận
        embed = create_embed(
            title="❓ Xác Nhận Xóa Bạn",
            description=f"Bạn có chắc chắn muốn xóa {member.mention} khỏi danh sách bạn bè không?"
        )

        # Tạo view xác nhận
        view = discord.ui.View(timeout=30)

        # Nút xác nhận
        confirm_button = discord.ui.Button(label="Xác nhận", style=discord.ButtonStyle.danger)

        # Nút hủy
        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.secondary)

        # Xử lý khi người dùng xác nhận
        async def confirm_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể xác nhận thao tác này!", ephemeral=True)
                return

            # Xóa khỏi danh sách bạn bè của người gửi
            user.social["friends"].pop(friend_index)
            await self.save_user_data(user)

            # Lấy dữ liệu người bị xóa
            target_user = await self.get_user_data(member.id)
            if target_user:
                # Xóa khỏi danh sách bạn bè của người bị xóa
                for i, friend in enumerate(target_user.social.get("friends", [])):
                    if friend.get("user_id") == ctx.author.id:
                        target_user.social["friends"].pop(i)
                        await self.save_user_data(target_user)
                        break

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Xóa Bạn",
                description=f"Đã xóa {member.mention} khỏi danh sách bạn bè của bạn."
            )

            await interaction.response.send_message(embed=embed)

            # Gửi thông báo cho người bị xóa
            try:
                embed = create_embed(
                    title="👋 Thông Báo",
                    description=f"{ctx.author.mention} đã xóa bạn khỏi danh sách bạn bè của họ."
                )
                await member.send(embed=embed)
            except:
                pass  # Bỏ qua nếu không gửi được DM

        # Xử lý khi người dùng hủy
        async def cancel_callback(interaction):
            # Kiểm tra xem người dùng có phải là người gọi lệnh không
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("Bạn không thể hủy thao tác này!", ephemeral=True)
                return

            await interaction.response.send_message("Đã hủy thao tác xóa bạn.", ephemeral=True)

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view.add_item(confirm_button)
        view.add_item(cancel_button)

        # Gửi embed xác nhận
        await ctx.send(embed=embed, view=view)

    @friend.command(name="accept", aliases=["chapnhan"])
    async def friend_accept(self, ctx, member: discord.Member):
        """Chấp nhận lời mời kết bạn"""
        # Kiểm tra xem có lời mời không
        if ctx.author.id not in self.friend_requests or member.id not in self.friend_requests.get(ctx.author.id, []):
            embed = create_error_embed(
                title="❌ Không Có Lời Mời",
                description=f"Bạn không có lời mời kết bạn nào từ {member.display_name}."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Lấy dữ liệu người gửi lời mời
        target_user = await self.get_user_data(member.id)
        if not target_user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description=f"{member.display_name} chưa bắt đầu tu tiên."
            )
            return await ctx.send(embed=embed)

        # Kiểm tra xem đã là bạn bè chưa
        for friend in user.social.get("friends", []):
            if friend.get("user_id") == member.id:
                embed = create_error_embed(
                    title="❌ Đã Là Bạn Bè",
                    description=f"Bạn và {member.display_name} đã là bạn bè rồi."
                )
                return await ctx.send(embed=embed)

        # Thêm vào danh sách bạn bè của người chấp nhận
        user.social.setdefault("friends", []).append({
            "user_id": member.id,
            "added_date": datetime.datetime.utcnow()
        })
        await self.save_user_data(user)

        # Thêm vào danh sách bạn bè của người gửi lời mời
        target_user.social.setdefault("friends", []).append({
            "user_id": ctx.author.id,
            "added_date": datetime.datetime.utcnow()
        })
        await self.save_user_data(target_user)

        # Xóa lời mời
        self.friend_requests[ctx.author.id].remove(member.id)

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Chấp Nhận Lời Mời",
            description=f"Bạn và {member.mention} đã trở thành bạn bè!"
        )

        await ctx.send(embed=embed)

        # Gửi thông báo cho người gửi lời mời
        try:
            embed = create_success_embed(
                title="✅ Lời Mời Được Chấp Nhận",
                description=f"{ctx.author.mention} đã chấp nhận lời mời kết bạn của bạn!"
            )
            await member.send(embed=embed)
        except:
            pass  # Bỏ qua nếu không gửi được DM

    @friend.command(name="reject", aliases=["tuchoi"])
    async def friend_reject(self, ctx, member: discord.Member):
        """Từ chối lời mời kết bạn"""
        # Kiểm tra xem có lời mời không
        if ctx.author.id not in self.friend_requests or member.id not in self.friend_requests.get(ctx.author.id, []):
            embed = create_error_embed(
                title="❌ Không Có Lời Mời",
                description=f"Bạn không có lời mời kết bạn nào từ {member.display_name}."
            )
            return await ctx.send(embed=embed)

        # Xóa lời mời
        self.friend_requests[ctx.author.id].remove(member.id)

        # Tạo embed thông báo
        embed = create_success_embed(
            title="✅ Đã Từ Chối Lời Mời",
            description=f"Bạn đã từ chối lời mời kết bạn từ {member.mention}."
        )

        await ctx.send(embed=embed)

        # Gửi thông báo cho người gửi lời mời
        try:
            embed = create_embed(
                title="👋 Lời Mời Bị Từ Chối",
                description=f"{ctx.author.mention} đã từ chối lời mời kết bạn của bạn."
            )
            await member.send(embed=embed)
        except:
            pass  # Bỏ qua nếu không gửi được DM

    @friend.command(name="requests", aliases=["loimoi"])
    async def friend_requests(self, ctx):
        """Xem danh sách lời mời kết bạn"""
        # Kiểm tra xem có lời mời không
        if ctx.author.id not in self.friend_requests or not self.friend_requests[ctx.author.id]:
            embed = create_embed(
                title="📬 Lời Mời Kết Bạn",
                description="Bạn không có lời mời kết bạn nào."
            )
            return await ctx.send(embed=embed)

        # Tạo embed hiển thị danh sách lời mời
        embed = create_embed(
            title="📬 Lời Mời Kết Bạn",
            description=f"Bạn có {len(self.friend_requests[ctx.author.id])} lời mời kết bạn"
        )

        # Hiển thị danh sách lời mời
        for i, user_id in enumerate(self.friend_requests[ctx.author.id], 1):
            # Lấy thông tin người dùng từ Discord
            user = self.bot.get_user(user_id)
            user_name = user.name if user else f"Người dùng #{user_id}"

            # Lấy thông tin người dùng từ database
            friend_user = await self.get_user_data(user_id)

            if friend_user:
                # Hiển thị thông tin cơ bản
                value = f"**Cảnh giới:** {friend_user.cultivation['realm']} cảnh {friend_user.cultivation['realm_level']}\n"
                value += f"Sử dụng `!friend accept @{user_name}` để chấp nhận hoặc `!friend reject @{user_name}` để từ chối."
            else:
                value = "*Không tìm thấy thông tin người dùng*"

            embed.add_field(
                name=f"{i}. {user_name}",
                value=value,
                inline=False
            )

        # Gửi embed
        await ctx.send(embed=embed)

    @friend.command(name="settings", aliases=["caidat"])
    async def friend_settings(self, ctx, setting: str = None, value: str = None):
        """Thay đổi cài đặt bạn bè"""
        # Lấy dữ liệu người dùng
        user = await self.get_user_data(ctx.author.id)
        if not user:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Bạn chưa bắt đầu tu tiên. Hãy sử dụng lệnh `!start` để bắt đầu."
            )
            return await ctx.send(embed=embed)

        # Nếu không có tham số, hiển thị cài đặt hiện tại
        if not setting:
            embed = create_embed(
                title="⚙️ Cài Đặt Bạn Bè",
                description="Cài đặt hiện tại của bạn"
            )

            # Hiển thị cài đặt nhận lời mời
            friend_requests = user.settings.get("friend_requests", True)
            embed.add_field(
                name="Nhận lời mời kết bạn",
                value=f"{'✅ Bật' if friend_requests else '❌ Tắt'}\n"
                      f"Sử dụng `!friend settings requests on/off` để thay đổi",
                inline=False
            )

            # Hiển thị cài đặt thông báo
            friend_notifications = user.settings.get("friend_notifications", True)
            embed.add_field(
                name="Thông báo bạn bè",
                value=f"{'✅ Bật' if friend_notifications else '❌ Tắt'}\n"
                      f"Sử dụng `!friend settings notifications on/off` để thay đổi",
                inline=False
            )

            await ctx.send(embed=embed)
            return

        # Xử lý thay đổi cài đặt
        if setting.lower() in ["requests", "loimoi"]:
            if not value or value.lower() not in ["on", "off"]:
                embed = create_error_embed(
                    title="❌ Lỗi",
                    description="Giá trị không hợp lệ. Sử dụng `on` hoặc `off`."
                )
                return await ctx.send(embed=embed)

            # Thay đổi cài đặt
            user.settings["friend_requests"] = (value.lower() == "on")
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Thay Đổi Cài Đặt",
                description=f"Đã {'bật' if value.lower() == 'on' else 'tắt'} nhận lời mời kết bạn."
            )

            await ctx.send(embed=embed)

        elif setting.lower() in ["notifications", "thongbao"]:
            if not value or value.lower() not in ["on", "off"]:
                embed = create_error_embed(
                    title="❌ Lỗi",
                    description="Giá trị không hợp lệ. Sử dụng `on` hoặc `off`."
                )
                return await ctx.send(embed=embed)

            # Thay đổi cài đặt
            user.settings["friend_notifications"] = (value.lower() == "on")
            await self.save_user_data(user)

            # Tạo embed thông báo
            embed = create_success_embed(
                title="✅ Đã Thay Đổi Cài Đặt",
                description=f"Đã {'bật' if value.lower() == 'on' else 'tắt'} thông báo bạn bè."
            )

            await ctx.send(embed=embed)

        else:
            embed = create_error_embed(
                title="❌ Lỗi",
                description="Cài đặt không hợp lệ. Các cài đặt hợp lệ: `requests`, `notifications`."
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Xử lý khi thành viên rời server"""
        # Xóa lời mời kết bạn
        if member.id in self.friend_requests:
            del self.friend_requests[member.id]

        # Xóa lời mời kết bạn từ thành viên này
        for user_id in self.friend_requests:
            if member.id in self.friend_requests[user_id]:
                self.friend_requests[user_id].remove(member.id)

        # Không xóa khỏi danh sách bạn bè để giữ lại mối quan hệ nếu họ quay lại


def setup(bot):
    bot.add_cog(FriendsCog(bot))
