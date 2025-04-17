import discord
from datetime import datetime
import config
from utils.text_utils import format_number


def create_embed(title=None, description=None, color=None, author=None, footer=None, thumbnail=None, image=None,
                 fields=None, timestamp=True):
    """
    Tạo một embed Discord với các thông số tùy chỉnh

    Parameters:
    -----------
    title: str
        Tiêu đề của embed
    description: str
        Mô tả của embed
    color: discord.Color
        Màu của embed, mặc định là màu chính của bot
    author: dict
        Thông tin về tác giả, bao gồm 'name', 'icon_url' và 'url' (tùy chọn)
    footer: dict
        Thông tin về footer, bao gồm 'text' và 'icon_url' (tùy chọn)
    thumbnail: str
        URL của hình ảnh thumbnail
    image: str
        URL của hình ảnh chính
    fields: list
        Danh sách các trường, mỗi trường là một dict với 'name', 'value' và 'inline' (tùy chọn)
    timestamp: bool
        Có hiển thị timestamp hay không

    Returns:
    --------
    discord.Embed
        Embed đã được tạo
    """
    # Thiết lập màu mặc định nếu không được chỉ định
    if color is None:
        color = config.EMBED_COLOR

    # Tạo embed cơ bản
    embed = discord.Embed(title=title, description=description, color=color)

    # Thêm timestamp nếu được yêu cầu
    if timestamp:
        embed.timestamp = datetime.utcnow()

    # Thêm tác giả nếu được cung cấp
    if author:
        name = author.get('name', '')
        icon_url = author.get('icon_url', '')
        url = author.get('url', discord.Embed.Empty)
        embed.set_author(name=name, icon_url=icon_url, url=url)

    # Thêm footer nếu được cung cấp
    if footer:
        text = footer.get('text', '')
        icon_url = footer.get('icon_url', '')
        embed.set_footer(text=text, icon_url=icon_url)
    else:
        embed.set_footer(text=config.DEFAULT_FOOTER)

    # Thêm thumbnail nếu được cung cấp
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    # Thêm hình ảnh chính nếu được cung cấp
    if image:
        embed.set_image(url=image)

    # Thêm các trường nếu được cung cấp
    if fields:
        for field in fields:
            name = field.get('name', '')
            value = field.get('value', '')
            inline = field.get('inline', False)
            if name and value:  # Chỉ thêm trường nếu có cả name và value
                embed.add_field(name=name, value=value, inline=inline)

    return embed


def create_user_embed(user_data, member=None):
    """
    Tạo embed hiển thị thông tin người dùng

    Parameters:
    -----------
    user_data: dict
        Dữ liệu người dùng từ database
    member: discord.Member
        Đối tượng Member của Discord, nếu có

    Returns:
    --------
    discord.Embed
        Embed thông tin người dùng
    """
    # Thiết lập thông tin cơ bản
    username = user_data.get('username', 'Không xác định')
    if member:
        username = member.display_name

    embed = create_embed(
        title=f"Thông tin tu luyện của {username}",
        color=config.EMBED_COLOR
    )

    # Thêm avatar nếu có member
    if member:
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    # Thông tin tu luyện
    cultivation_realm = user_data.get('cultivation', {}).get('realm', 'Phàm Nhân')
    cultivation_stage = user_data.get('cultivation', {}).get('stage', 1)
    cultivation_progress = user_data.get('cultivation', {}).get('progress', 0)
    max_progress = user_data.get('cultivation', {}).get('max_progress', 100)

    # Tính toán thanh tiến trình
    progress_bar = create_progress_bar(cultivation_progress, max_progress)

    embed.add_field(
        name="Cảnh giới",
        value=f"**{cultivation_realm}** cấp {cultivation_stage}",
        inline=False
    )

    embed.add_field(
        name="Tiến trình tu luyện",
        value=f"{progress_bar} ({cultivation_progress}/{max_progress})",
        inline=False
    )

    # Thông tin chiến đấu
    combat_power = user_data.get('combat_power', 0)
    health = user_data.get('health', 100)
    max_health = user_data.get('max_health', 100)

    embed.add_field(
        name="Sức mạnh chiến đấu",
        value=format_number(combat_power),
        inline=True
    )

    embed.add_field(
        name="Sinh lực",
        value=f"{health}/{max_health}",
        inline=True
    )

    # Thông tin tài nguyên
    spirit_stones = user_data.get('spirit_stones', 0)
    contribution = user_data.get('contribution', 0)

    embed.add_field(
        name="Linh thạch",
        value=format_number(spirit_stones),
        inline=True
    )

    # Thông tin môn phái nếu có
    sect_name = user_data.get('sect', {}).get('name', 'Không có')
    sect_role = user_data.get('sect', {}).get('role', 'Không có')

    if sect_name != 'Không có':
        embed.add_field(
            name="Môn phái",
            value=f"{sect_name} - {sect_role}",
            inline=False
        )

        embed.add_field(
            name="Công hiến",
            value=format_number(contribution),
            inline=True
        )

    return embed


def create_progress_bar(current, maximum, length=10, filled='█', empty='░'):
    """
    Tạo thanh tiến trình dạng text

    Parameters:
    -----------
    current: int
        Giá trị hiện tại
    maximum: int
        Giá trị tối đa
    length: int
        Độ dài của thanh tiến trình
    filled: str
        Ký tự hiển thị phần đã hoàn thành
    empty: str
        Ký tự hiển thị phần chưa hoàn thành

    Returns:
    --------
    str
        Thanh tiến trình dạng text
    """
    if maximum <= 0:
        return empty * length

    progress = min(current / maximum, 1.0)
    filled_length = int(length * progress)

    bar = filled * filled_length + empty * (length - filled_length)
    return bar


def create_inventory_embed(user_data, page=1, items_per_page=10):
    """
    Tạo embed hiển thị kho đồ của người chơi

    Parameters:
    -----------
    user_data: dict
        Dữ liệu người dùng từ database
    page: int
        Trang hiện tại
    items_per_page: int
        Số lượng vật phẩm hiển thị trên mỗi trang

    Returns:
    --------
    discord.Embed
        Embed kho đồ
    """
    username = user_data.get('username', 'Không xác định')
    inventory = user_data.get('inventory', [])

    # Tính toán số trang
    total_pages = max(1, (len(inventory) + items_per_page - 1) // items_per_page)
    page = max(1, min(page, total_pages))

    embed = create_embed(
        title=f"Kho đồ của {username}",
        description=f"Trang {page}/{total_pages}",
        color=config.EMBED_COLOR
    )

    # Nếu không có vật phẩm
    if not inventory:
        embed.add_field(name="Trống", value="Kho đồ của bạn đang trống.", inline=False)
        return embed

    # Hiển thị vật phẩm theo trang
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(inventory))

    for i in range(start_idx, end_idx):
        item = inventory[i]
        item_name = item.get('name', 'Vật phẩm không xác định')
        item_quantity = item.get('quantity', 1)
        item_description = item.get('description', 'Không có mô tả')
        item_id = item.get('item_id', 0)

        embed.add_field(
            name=f"{item_name} (x{item_quantity}) [ID: {item_id}]",
            value=item_description,
            inline=False
        )

    return embed


def create_shop_embed(shop_items, page=1, items_per_page=5):
    """
    Tạo embed hiển thị cửa hàng

    Parameters:
    -----------
    shop_items: list
        Danh sách các vật phẩm trong cửa hàng
    page: int
        Trang hiện tại
    items_per_page: int
        Số lượng vật phẩm hiển thị trên mỗi trang

    Returns:
    --------
    discord.Embed
        Embed cửa hàng
    """
    # Tính toán số trang
    total_pages = max(1, (len(shop_items) + items_per_page - 1) // items_per_page)
    page = max(1, min(page, total_pages))

    embed = create_embed(
        title="Cửa hàng Linh Vật",
        description=f"Trang {page}/{total_pages}\nSử dụng `mua <ID> [số lượng]` để mua vật phẩm.",
        color=config.EMBED_COLOR
    )

    # Nếu không có vật phẩm
    if not shop_items:
        embed.add_field(name="Trống", value="Cửa hàng hiện không có vật phẩm nào.", inline=False)
        return embed

    # Hiển thị vật phẩm theo trang
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(shop_items))

    for i in range(start_idx, end_idx):
        item = shop_items[i]
        item_name = item.get('name', 'Vật phẩm không xác định')
        item_price = item.get('price', 0)
        item_description = item.get('description', 'Không có mô tả')
        item_id = item.get('id', 0)

        embed.add_field(
            name=f"{item_name} [ID: {item_id}] - {format_number(item_price)} linh thạch",
            value=item_description,
            inline=False
        )

    return embed


def create_sect_embed(sect_data):
    """
    Tạo embed hiển thị thông tin môn phái

    Parameters:
    -----------
    sect_data: dict
        Dữ liệu môn phái từ database

    Returns:
    --------
    discord.Embed
        Embed thông tin môn phái
    """
    sect_name = sect_data.get('name', 'Không xác định')
    sect_level = sect_data.get('level', 1)
    sect_description = sect_data.get('description', 'Không có mô tả')
    sect_members = sect_data.get('members', [])
    sect_resources = sect_data.get('resources', 0)
    sect_leader = sect_data.get('leader', {}).get('name', 'Không xác định')

    embed = create_embed(
        title=f"Môn phái: {sect_name} (Cấp {sect_level})",
        description=sect_description,
        color=config.EMBED_COLOR
    )

    # Thêm thông tin cơ bản
    embed.add_field(
        name="Chưởng môn",
        value=sect_leader,
        inline=True
    )

    embed.add_field(
        name="Số thành viên",
        value=f"{len(sect_members)}/{10 + sect_level * 5}",
        inline=True
    )

    embed.add_field(
        name="Tài nguyên môn phái",
        value=format_number(sect_resources),
        inline=True
    )

    # Thêm danh sách thành viên (tối đa 10 người)
    member_list = ""
    for i, member in enumerate(sect_members[:10]):
        member_name = member.get('name', 'Không xác định')
        member_role = member.get('role', 'Đệ tử')
        member_list += f"{i + 1}. {member_name} - {member_role}\n"

    if member_list:
        embed.add_field(
            name="Danh sách thành viên",
            value=member_list,
            inline=False
        )

    if len(sect_members) > 10:
        embed.add_field(
            name="",
            value=f"*Và {len(sect_members) - 10} thành viên khác...*",
            inline=False
        )

    return embed


def create_combat_embed(attacker, defender, attack_result):
    """
    Tạo embed hiển thị kết quả chiến đấu

    Parameters:
    -----------
    attacker: dict
        Thông tin người tấn công
    defender: dict
        Thông tin người/quái vật bị tấn công
    attack_result: dict
        Kết quả của đòn tấn công

    Returns:
    --------
    discord.Embed
        Embed kết quả chiến đấu
    """
    # Xác định loại chiến đấu (PvP hoặc PvE)
    is_pvp = 'username' in defender

    # Thiết lập tiêu đề và màu sắc
    title = "Kết quả chiến đấu"
    if is_pvp:
        title = f"PvP: {attacker.get('username', 'Người chơi')} vs {defender.get('username', 'Đối thủ')}"
    else:
        title = f"Săn: {attacker.get('username', 'Người chơi')} vs {defender.get('name', 'Quái vật')}"

    # Xác định màu dựa trên kết quả
    color = discord.Color.blue()
    if attack_result.get('is_critical', False):
        color = discord.Color.gold()
    elif attack_result.get('is_miss', False):
        color = discord.Color.light_grey()

    embed = create_embed(
        title=title,
        color=color
    )

    # Thông tin đòn tấn công
    damage = attack_result.get('damage', 0)
    damage_text = format_number(damage)

    if attack_result.get('is_critical', False):
        damage_text += " (Chí mạng!)"
    elif attack_result.get('is_miss', False):
        damage_text = "Hụt!"

    embed.add_field(
        name="Sát thương",
        value=damage_text,
        inline=True
    )

    # Thông tin người tấn công
    attacker_health = attack_result.get('attacker_health', {})
    attacker_health_bar = create_progress_bar(
        attacker_health.get('current', 0),
        attacker_health.get('max', 100)
    )

    embed.add_field(
        name=f"{attacker.get('username', 'Người chơi')}",
        value=f"HP: {attacker_health_bar} ({attacker_health.get('current', 0)}/{attacker_health.get('max', 100)})",
        inline=False
    )

    # Thông tin người/quái vật bị tấn công
    defender_health = attack_result.get('defender_health', {})
    defender_health_bar = create_progress_bar(
        defender_health.get('current', 0),
        defender_health.get('max', 100)
    )

    defender_name = defender.get('username', defender.get('name', 'Đối thủ'))
    embed.add_field(
        name=f"{defender_name}",
        value=f"HP: {defender_health_bar} ({defender_health.get('current', 0)}/{defender_health.get('max', 100)})",
        inline=False
    )

    # Thông tin bổ sung
    if 'message' in attack_result:
        embed.add_field(
            name="Thông tin",
            value=attack_result['message'],
            inline=False
        )

    return embed


def create_monster_embed(monster_data):
    """
    Tạo embed hiển thị thông tin quái vật

    Parameters:
    -----------
    monster_data: dict
        Dữ liệu quái vật từ database

    Returns:
    --------
    discord.Embed
        Embed thông tin quái vật
    """
    monster_name = monster_data.get('name', 'Quái vật không xác định')
    monster_level = monster_data.get('level', 1)
    monster_description = monster_data.get('description', 'Không có mô tả')
    monster_health = monster_data.get('health', 100)
    monster_combat_power = monster_data.get('combat_power', 0)
    monster_drops = monster_data.get('drops', [])
    monster_image = monster_data.get('image', None)

    embed = create_embed(
        title=f"{monster_name} (Cấp {monster_level})",
        description=monster_description,
        color=discord.Color.dark_red()
    )

    if monster_image:
        embed.set_thumbnail(url=monster_image)

    # Thông tin cơ bản
    embed.add_field(
        name="Sinh lực",
        value=str(monster_health),
        inline=True
    )

    embed.add_field(
        name="Sức mạnh chiến đấu",
        value=format_number(monster_combat_power),
        inline=True
    )

    # Thông tin vật phẩm rơi ra
    if monster_drops:
        drops_text = ""
        for drop in monster_drops:
            item_name = drop.get('name', 'Vật phẩm không xác định')
            drop_chance = drop.get('chance', 0)
            drops_text += f"• {item_name} ({drop_chance}%)\n"

        embed.add_field(
            name="Vật phẩm rơi ra",
            value=drops_text,
            inline=False
        )

    # Thông tin kinh nghiệm và linh thạch
    exp_reward = monster_data.get('exp_reward', 0)
    spirit_stone_reward = monster_data.get('spirit_stone_reward', 0)

    embed.add_field(
        name="Phần thưởng",
        value=f"Kinh nghiệm: {format_number(exp_reward)}\nLinh thạch: {format_number(spirit_stone_reward)}",
        inline=False
    )

    return embed


def create_leaderboard_embed(leaderboard_data, title="Bảng xếp hạng", page=1, users_per_page=10):
    """
    Tạo embed hiển thị bảng xếp hạng

    Parameters:
    -----------
    leaderboard_data: list
        Danh sách người chơi và thông tin xếp hạng
    title: str
        Tiêu đề của bảng xếp hạng
    page: int
        Trang hiện tại
    users_per_page: int
        Số lượng người chơi hiển thị trên mỗi trang

    Returns:
    --------
    discord.Embed
        Embed bảng xếp hạng
    """
    # Tính toán số trang
    total_pages = max(1, (len(leaderboard_data) + users_per_page - 1) // users_per_page)
    page = max(1, min(page, total_pages))

    embed = create_embed(
        title=title,
        description=f"Trang {page}/{total_pages}",
        color=config.EMBED_COLOR
    )

    # Nếu không có dữ liệu
    if not leaderboard_data:
        embed.add_field(name="Trống", value="Chưa có dữ liệu xếp hạng.", inline=False)
        return embed

    # Hiển thị người chơi theo trang
    start_idx = (page - 1) * users_per_page
    end_idx = min(start_idx + users_per_page, len(leaderboard_data))

    leaderboard_text = ""
    for i in range(start_idx, end_idx):
        user = leaderboard_data[i]
        rank = i + 1
        username = user.get('username', 'Không xác định')

        # Xác định giá trị hiển thị (có thể là sức mạnh, linh thạch, v.v.)
        value = user.get('value', 0)
        value_text = format_number(value)

        # Thêm biểu tượng cho top 3
        if rank == 1:
            rank_icon = "🥇"
        elif rank == 2:
            rank_icon = "🥈"
        elif rank == 3:
            rank_icon = "🥉"
        else:
            rank_icon = f"{rank}."

        leaderboard_text += f"{rank_icon} **{username}** - {value_text}\n"

    embed.description += f"\n\n{leaderboard_text}"

    return embed


def create_help_embed(command_list, category=None):
    """
    Tạo embed hiển thị trợ giúp lệnh

    Parameters:
    -----------
    command_list: dict
        Danh sách lệnh và mô tả
    category: str
        Danh mục lệnh cần hiển thị, None để hiển thị tất cả

    Returns:
    --------
    discord.Embed
        Embed trợ giúp
    """
    if category:
        title = f"Trợ giúp: {category}"
        commands = command_list.get(category, {})
    else:
        title = "Danh sách lệnh"
        commands = {}
        for cat in command_list:
            commands.update(command_list[cat])

    embed = create_embed(
        title=title,
        description="Sử dụng `help <lệnh>` để xem chi tiết về một lệnh cụ thể.",
        color=config.EMBED_COLOR
    )

    # Nếu không có lệnh
    if not commands:
        embed.add_field(name="Trống", value="Không có lệnh nào trong danh mục này.", inline=False)
        return embed

    # Nếu hiển thị tất cả danh mục
    if not category:
        for cat in command_list:
            cmd_text = ""
            for cmd_name in command_list[cat]:
                cmd_text += f"`{cmd_name}` "

            if cmd_text:
                embed.add_field(
                    name=cat,
                    value=cmd_text,
                    inline=False
                )
    # Nếu hiển thị một danh mục cụ thể
    else:
        for cmd_name, cmd_info in commands.items():
            embed.add_field(
                name=f"{config.PREFIX}{cmd_name} {cmd_info.get('usage', '')}",
                value=cmd_info.get('description', 'Không có mô tả'),
                inline=False
            )

    return embed


def create_command_help_embed(command_name, command_info):
    """
    Tạo embed hiển thị trợ giúp chi tiết cho một lệnh

    Parameters:
    -----------
    command_name: str
        Tên lệnh
    command_info: dict
        Thông tin chi tiết về lệnh

    Returns:
    --------
    discord.Embed
        Embed trợ giúp chi tiết
    """
    embed = create_embed(
        title=f"Trợ giúp: {config.PREFIX}{command_name}",
        color=config.EMBED_COLOR
    )

    # Thông tin cơ bản
    embed.add_field(
        name="Mô tả",
        value=command_info.get('description', 'Không có mô tả'),
        inline=False
    )

    # Cách sử dụng
    usage = command_info.get('usage', '')
    embed.add_field(
        name="Cách sử dụng",
        value=f"{config.PREFIX}{command_name} {usage}",
        inline=False
    )

    # Ví dụ
    examples = command_info.get('examples', [])
    if examples:
        examples_text = "\n".join([f"{config.PREFIX}{example}" for example in examples])
        embed.add_field(
            name="Ví dụ",
            value=examples_text,
            inline=False
        )

    # Bí danh
    aliases = command_info.get('aliases', [])
    if aliases:
        aliases_text = ", ".join([f"{config.PREFIX}{alias}" for alias in aliases])
        embed.add_field(
            name="Bí danh",
            value=aliases_text,
            inline=False
        )

    # Thời gian hồi
    cooldown = command_info.get('cooldown', 0)
    if cooldown:
        embed.add_field(
            name="Thời gian hồi",
            value=f"{cooldown} giây",
            inline=True
        )

    return embed
