import discord
from discord.ext import commands
import asyncio
from typing import List, Dict, Any, Optional

from database.mongo_handler import get_user_or_create
from config import CULTIVATION_REALMS, EMBED_COLOR


async def check_user_exists(ctx: commands.Context) -> Optional[Dict[str, Any]]:
    """Kiểm tra người dùng đã đăng ký chưa và trả về thông tin người dùng"""
    # Lấy thông tin người dùng
    user = await get_user_or_create(ctx.author.id, ctx.author.name)
    return user


async def handle_pagination(
        bot: commands.Bot,
        ctx: commands.Context,
        embeds: List[discord.Embed]
) -> None:
    """Xử lý phân trang cho các embed"""
    # Nếu không có trang nào
    if not embeds:
        return

    # Nếu chỉ có một trang
    if len(embeds) == 1:
        return await ctx.send(embed=embeds[0])

    # Các emoji điều hướng
    emojis = ["⬅️", "➡️", "❌"]

    # Biến theo dõi trang hiện tại
    current_page = 0

    # Gửi trang đầu tiên
    message = await ctx.send(embed=embeds[current_page])

    # Thêm các reaction điều hướng
    for emoji in emojis:
        await message.add_reaction(emoji)

    # Hàm kiểm tra reaction
    def check(reaction, user):
        return (
                user.id == ctx.author.id
                and reaction.message.id == message.id
                and str(reaction.emoji) in emojis
        )

    # Vòng lặp xử lý phân trang
    while True:
        try:
            # Chờ reaction
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

            # Xử lý reaction
            if str(reaction.emoji) == "⬅️":
                # Trang trước
                if current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])

            elif str(reaction.emoji) == "➡️":
                # Trang tiếp theo
                if current_page < len(embeds) - 1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])

            elif str(reaction.emoji) == "❌":
                # Kết thúc phân trang
                await message.clear_reactions()
                break

            # Xóa reaction của người dùng
            await message.remove_reaction(str(reaction.emoji), user)

        except asyncio.TimeoutError:
            # Nếu hết thời gian, xóa tất cả reaction
            await message.clear_reactions()
            break


async def check_cooldown(
        ctx: commands.Context,
        user_data: Dict[str, Any],
        cooldown_field: str,
        cooldown_seconds: int,
        action_name: str
) -> bool:
    """Kiểm tra và thông báo cooldown, trả về True nếu đang trong cooldown"""
    import datetime

    # Kiểm tra cooldown
    now = datetime.datetime.now()
    last_action = user_data.get(cooldown_field)

    if last_action:
        last_action = datetime.datetime.fromisoformat(last_action)
        time_diff = (now - last_action).total_seconds()

        if time_diff < cooldown_seconds:
            remaining = cooldown_seconds - time_diff
            minutes, seconds = divmod(int(remaining), 60)

            embed = discord.Embed(
                title="⏳ Cooldown",
                description=f"Bạn cần nghỉ ngơi **{minutes} phút {seconds} giây** nữa mới có thể {action_name} tiếp!",
                color=discord.Color.red()
            )

            await ctx.send(embed=embed)
            return True

    return False


def get_realm_name(realm_id: int) -> str:
    """Lấy tên cảnh giới từ ID"""
    if 0 <= realm_id < len(CULTIVATION_REALMS):
        return CULTIVATION_REALMS[realm_id]["name"]
    return "Không xác định"