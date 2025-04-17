import discord
import datetime
from typing import List, Dict, Any, Optional

from config import (
    EMBED_COLOR, EMBED_COLOR_SUCCESS, EMBED_COLOR_ERROR, EMBED_COLOR_WARNING,
    EMOJI_LINH_THACH, EMOJI_EXP, EMOJI_HEALTH, EMOJI_ATTACK, EMOJI_DEFENSE
)


def create_embed(
        title: str,
        description: str = None,
        color: discord.Color = EMBED_COLOR,
        fields: List[Dict[str, Any]] = None,
        author: Dict[str, Any] = None,
        footer: Dict[str, Any] = None,
        thumbnail: str = None,
        image: str = None,
        timestamp: bool = False
) -> discord.Embed:
    """Tạo embed với các thông số tùy chỉnh"""
    # Tạo embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    # Thêm trường
    if fields:
        for field in fields:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )

    # Thêm author
    if author:
        embed.set_author(
            name=author.get("name", ""),
            icon_url=author.get("icon_url", None),
            url=author.get("url", None)
        )

    # Thêm footer
    if footer:
        embed.set_footer(
            text=footer.get("text", ""),
            icon_url=footer.get("icon_url", None)
        )

    # Thêm thumbnail
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    # Thêm hình ảnh
    if image:
        embed.set_image(url=image)

    # Thêm timestamp
    if timestamp:
        embed.timestamp = datetime.datetime.now()

    return embed


def create_success_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
    """Tạo embed thành công"""
    return create_embed(
        title=title,
        description=description,
        color=EMBED_COLOR_SUCCESS,
        **kwargs
    )


def create_error_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
    """Tạo embed lỗi"""
    return create_embed(
        title=title,
        description=description,
        color=EMBED_COLOR_ERROR,
        **kwargs
    )


def create_warning_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
    """Tạo embed cảnh báo"""
    return create_embed(
        title=title,
        description=description,
        color=EMBED_COLOR_WARNING,
        **kwargs
    )


def create_profile_embed(user: discord.Member, user_data: Dict[str, Any], realm_name: str) -> discord.Embed:
    """Tạo embed hiển thị thông tin nhân vật"""
    # Lấy dữ liệu cơ bản
    realm_id = user_data.get("realm_id", 0)
    experience = user_data.get("experience", 0)
    linh_thach = user_data.get("linh_thach", 0)
    health = user_data.get("health", 100)
    attack = user_data.get("attack", 10)
    defense = user_data.get("defense", 5)

    # Tạo embed
    embed = discord.Embed(
        title=f"Thông Tin Tu Luyện - {user.display_name}",
        description=f"Tu vi hiện tại: **{realm_name}**",
        color=EMBED_COLOR
    )

    # Thêm thông tin cơ bản
    embed.add_field(
        name="Linh Lực",
        value=f"{EMOJI_EXP} Kinh nghiệm: **{experience:,}**",
        inline=True
    )

    embed.add_field(
        name="Tài Nguyên",
        value=f"{EMOJI_LINH_THACH} Linh thạch: **{linh_thach:,}**",
        inline=True
    )

    # Thêm thông tin chiến đấu
    embed.add_field(
        name="Thông Số Chiến Đấu",
        value=(
            f"{EMOJI_HEALTH} HP: **{health}**\n"
            f"{EMOJI_ATTACK} Tấn công: **{attack}**\n"
            f"{EMOJI_DEFENSE} Phòng thủ: **{defense}**"
        ),
        inline=False
    )

    # Thêm môn phái nếu có
    sect_id = user_data.get("sect_id")
    if sect_id:
        # Lấy tên môn phái từ database (tạm thời để trống)
        sect_name = "Đang tải..."
        embed.add_field(
            name="Môn Phái",
            value=f"**{sect_name}**",
            inline=True
        )

    # Thêm avatar
    embed.set_thumbnail(url=user.display_avatar.url)

    # Thêm timestamp
    embed.timestamp = datetime.datetime.now()

    return embed


def create_pagination_embeds(
        title: str,
        items: List[Dict[str, Any]],
        items_per_page: int = 5,
        color: discord.Color = EMBED_COLOR,
        thumbnail: str = None
) -> List[discord.Embed]:
    """Tạo danh sách các embed cho hệ thống phân trang"""
    # Tính số trang
    total_pages = (len(items) + items_per_page - 1) // items_per_page

    # Tạo danh sách embeds
    embeds = []

    for page in range(1, total_pages + 1):
        # Tính chỉ số bắt đầu và kết thúc
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        current_items = items[start_idx:end_idx]

        # Tạo embed cho trang hiện tại
        embed = discord.Embed(
            title=f"{title} - Trang {page}/{total_pages}",
            color=color
        )

        # Thêm các mục
        for item in current_items:
            embed.add_field(
                name=item["name"],
                value=item["value"],
                inline=item.get("inline", False)
            )

        # Thêm hướng dẫn điều hướng
        embed.set_footer(text=f"Trang {page}/{total_pages} | Sử dụng các reaction để điều hướng")

        # Thêm thumbnail nếu có
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        embeds.append(embed)

    return embeds