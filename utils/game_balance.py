"""
Mô-đun cân bằng game - chứa các hàm và hằng số để cân bằng trò chơi
"""
import random
import math
from config import CULTIVATION_REALMS

def calculate_combat_power(user_data):
    """
    Tính toán sức mạnh chiến đấu dựa trên dữ liệu người dùng

    Parameters:
    -----------
    user_data: dict
        Dữ liệu người dùng từ database

    Returns:
    --------
    int
        Sức mạnh chiến đấu
    """
    # Lấy thông tin cảnh giới
    cultivation = user_data.get('cultivation', {})
    realm = cultivation.get('realm', 'Phàm Nhân')
    stage = cultivation.get('stage', 1)

    # Lấy hệ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Tính toán sức mạnh cơ bản
    base_power = (realm_index + 1) * 1000 + stage * 100

    # Tính toán sức mạnh từ vật phẩm trang bị
    equipment_power = 0
    equipped_items = user_data.get('equipped_items', {})

    for slot, item in equipped_items.items():
        if item:
            equipment_power += item.get('power_bonus', 0)

    # Tính toán sức mạnh từ kỹ năng
    skill_power = 0
    skills = user_data.get('skills', [])

    for skill in skills:
        skill_power += skill.get('power', 0) * skill.get('level', 1)

    # Tính toán sức mạnh từ môn phái
    sect_power = 0
    sect = user_data.get('sect', {})

    if sect and sect.get('name', 'Không có') != 'Không có':
        sect_level = sect.get('level', 1)
        sect_power = sect_level * 50

    # Tính toán tổng sức mạnh
    total_power = base_power + equipment_power + skill_power + sect_power

    # Thêm một chút ngẫu nhiên (±5%)
    random_factor = random.uniform(0.95, 1.05)
    total_power = int(total_power * random_factor)

    return total_power

def calculate_exp_requirement(realm, stage):
    """
    Tính toán lượng kinh nghiệm cần thiết để lên cấp

    Parameters:
    -----------
    realm: str
        Cảnh giới hiện tại
    stage: int
        Cấp độ hiện tại

    Returns:
    --------
    int
        Lượng kinh nghiệm cần thiết
    """
    # Tìm chỉ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Công thức tính kinh nghiệm cần thiết
    base_exp = 100  # Kinh nghiệm cơ bản
    realm_multiplier = 2 ** realm_index  # Hệ số nhân theo cảnh giới
    stage_multiplier = stage ** 1.5  # Hệ số nhân theo cấp độ

    required_exp = int(base_exp * realm_multiplier * stage_multiplier)

    return required_exp

def calculate_cultivation_time(realm, stage, current_exp, target_exp):
    """
    Tính toán thời gian tu luyện cần thiết để đạt được lượng kinh nghiệm mục tiêu

    Parameters:
    -----------
    realm: str
        Cảnh giới hiện tại
    stage: int
        Cấp độ hiện tại
    current_exp: int
        Kinh nghiệm hiện tại
    target_exp: int
        Kinh nghiệm mục tiêu

    Returns:
    --------
    int
        Thời gian tu luyện cần thiết (giây)
    """
    # Tìm chỉ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Tính tốc độ tu luyện (kinh nghiệm/giây)
    base_rate = 0.5  # Tốc độ cơ bản
    realm_bonus = 1 + realm_index * 0.1  # Bonus theo cảnh giới
    stage_bonus = 1 + stage * 0.05  # Bonus theo cấp độ

    cultivation_rate = base_rate * realm_bonus * stage_bonus

    # Tính thời gian cần thiết
    exp_needed = target_exp - current_exp
    time_needed = int(exp_needed / cultivation_rate)

    return max(1, time_needed)  # Tối thiểu 1 giây

def calculate_monster_reward(monster_level):
    """
    Tính toán phần thưởng khi đánh bại quái vật

    Parameters:
    -----------
    monster_level: int
        Cấp độ quái vật

    Returns:
    --------
    dict
        Phần thưởng (kinh nghiệm, linh thạch)
    """
    # Công thức tính phần thưởng
    base_exp = 10  # Kinh nghiệm cơ bản
    base_spirit_stones = 20  # Linh thạch cơ bản

    level_multiplier = monster_level ** 1.2

    # Thêm yếu tố ngẫu nhiên (±20%)
    random_factor = random.uniform(0.8, 1.2)

    exp_reward = int(base_exp * level_multiplier * random_factor)
    spirit_stones_reward = int(base_spirit_stones * level_multiplier * random_factor)

    return {
        'exp': exp_reward,
        'spirit_stones': spirit_stones_reward
    }

def calculate_boss_reward(boss_level):
    """
    Tính toán phần thưởng khi đánh bại boss

    Parameters:
    -----------
    boss_level: int
        Cấp độ boss

    Returns:
    --------
    dict
        Phần thưởng (kinh nghiệm, linh thạch)
    """
    # Boss cho phần thưởng cao hơn quái thường
    monster_reward = calculate_monster_reward(boss_level)

    # Nhân với hệ số boss (5-10 lần)
    boss_multiplier = random.uniform(5, 10)

    exp_reward = int(monster_reward['exp'] * boss_multiplier)
    spirit_stones_reward = int(monster_reward['spirit_stones'] * boss_multiplier)

    return {
        'exp': exp_reward,
        'spirit_stones': spirit_stones_reward
    }

def calculate_pvp_reward(winner_data, loser_data):
    """
    Tính toán phần thưởng khi thắng PvP

    Parameters:
    -----------
    winner_data: dict
        Dữ liệu người thắng
    loser_data: dict
        Dữ liệu người thua

    Returns:
    --------
    dict
        Phần thưởng (kinh nghiệm, linh thạch)
    """
    # Lấy sức mạnh chiến đấu
    winner_power = winner_data.get('combat_power', 1000)
    loser_power = loser_data.get('combat_power', 1000)

    # Tính tỷ lệ sức mạnh
    power_ratio = loser_power / winner_power if winner_power > 0 else 1

    # Phần thưởng cơ bản
    base_exp = 50
    base_spirit_stones = 100

    # Điều chỉnh phần thưởng dựa trên tỷ lệ sức mạnh
    # Nếu người thắng yếu hơn, phần thưởng cao hơn
    exp_multiplier = 1 + max(0, power_ratio - 1) * 2
    spirit_stones_multiplier = 1 + max(0, power_ratio - 1) * 2

    # Giới hạn hệ số nhân
    exp_multiplier = min(5, max(0.5, exp_multiplier))
    spirit_stones_multiplier = min(5, max(0.5, spirit_stones_multiplier))

    # Tính phần thưởng
    exp_reward = int(base_exp * exp_multiplier)
    spirit_stones_reward = int(base_spirit_stones * spirit_stones_multiplier)

    return {
        'exp': exp_reward,
        'spirit_stones': spirit_stones_reward
    }

def calculate_item_value(item_data):
    """
    Tính toán giá trị của vật phẩm

    Parameters:
    -----------
    item_data: dict
        Dữ liệu vật phẩm

    Returns:
    --------
    int
        Giá trị vật phẩm (linh thạch)
    """
    # Lấy thông tin vật phẩm
    rarity = item_data.get('rarity', 'common')
    level = item_data.get('level', 1)

    # Hệ số theo độ hiếm
    rarity_multiplier = {
        'common': 1,
        'uncommon': 2,
        'rare': 5,
        'epic': 10,
        'legendary': 25,
        'mythic': 50
    }.get(rarity.lower(), 1)

    # Công thức tính giá trị
    base_value = 50  # Giá trị cơ bản
    level_multiplier = level ** 1.5

    item_value = int(base_value * rarity_multiplier * level_multiplier)

    return item_value

def calculate_sect_upgrade_cost(current_level):
    """
    Tính toán chi phí nâng cấp môn phái

    Parameters:
    -----------
    current_level: int
        Cấp độ hiện tại của môn phái

    Returns:
    --------
    dict
        Chi phí nâng cấp (linh thạch, công hiến)
    """
    # Công thức tính chi phí
    base_spirit_stones = 10000  # Chi phí linh thạch cơ bản
    base_contribution = 5000  # Chi phí công hiến cơ bản

    level_multiplier = current_level ** 2

    spirit_stones_cost = int(base_spirit_stones * level_multiplier)
    contribution_cost = int(base_contribution * level_multiplier)

    return {
        'spirit_stones': spirit_stones_cost,
        'contribution': contribution_cost
    }

def calculate_sect_benefits(sect_level):
    """
    Tính toán lợi ích của môn phái dựa trên cấp độ

    Parameters:
    -----------
    sect_level: int
        Cấp độ môn phái

    Returns:
    --------
    dict
        Các lợi ích (tốc độ tu luyện, sức mạnh chiến đấu)
    """
    # Công thức tính lợi ích
    cultivation_speed_bonus = 0.05 * sect_level  # +5% mỗi cấp
    combat_power_bonus = 0.03 * sect_level  # +3% mỗi cấp

    return {
        'cultivation_speed_bonus': cultivation_speed_bonus,
        'combat_power_bonus': combat_power_bonus
    }

def calculate_damage(attacker_power, defender_power):
    """
    Tính toán sát thương trong chiến đấu

    Parameters:
    -----------
    attacker_power: int
        Sức mạnh chiến đấu của người tấn công
    defender_power: int
        Sức mạnh chiến đấu của người phòng thủ

    Returns:
    --------
    dict
        Thông tin sát thương (damage, is_critical, is_miss)
    """
    # Tính tỷ lệ sức mạnh
    power_ratio = attacker_power / defender_power if defender_power > 0 else 2

    # Cơ hội chí mạng và hụt
    critical_chance = min(0.3, 0.1 + (power_ratio - 1) * 0.05)  # Tối đa 30%
    miss_chance = max(0.05, 0.2 - (power_ratio - 1) * 0.05)  # Tối thiểu 5%

    # Kiểm tra chí mạng và hụt
    is_critical = random.random() < critical_chance
    is_miss = random.random() < miss_chance

    # Tính sát thương
    if is_miss:
        damage = 0
    else:
        # Sát thương cơ bản
        base_damage = attacker_power * 0.1

        # Điều chỉnh theo tỷ lệ sức mạnh
        power_factor = math.sqrt(power_ratio)

        # Tính sát thương cuối cùng
        damage = base_damage * power_factor

        # Nếu chí mạng, nhân đôi sát thương
        if is_critical:
            damage *= 2

        # Thêm yếu tố ngẫu nhiên (±20%)
        random_factor = random.uniform(0.8, 1.2)
        damage *= random_factor

        damage = int(damage)

    return {
        'damage': damage,
        'is_critical': is_critical,
        'is_miss': is_miss
    }

def calculate_health(realm, stage):
    """
    Tính toán lượng máu tối đa dựa trên cảnh giới và cấp độ

    Parameters:
    -----------
    realm: str
        Cảnh giới hiện tại
    stage: int
        Cấp độ hiện tại

    Returns:
    --------
    int
        Lượng máu tối đa
    """
    # Tìm chỉ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Công thức tính máu tối đa
    base_health = 100  # Máu cơ bản
    realm_multiplier = 1 + realm_index * 0.5  # Hệ số nhân theo cảnh giới
    stage_multiplier = 1 + stage * 0.1  # Hệ số nhân theo cấp độ

    max_health = int(base_health * realm_multiplier * stage_multiplier)

    return max_health

def calculate_healing_rate(realm, stage):
    """
    Tính toán tốc độ hồi máu dựa trên cảnh giới và cấp độ

    Parameters:
    -----------
    realm: str
        Cảnh giới hiện tại
    stage: int
        Cấp độ hiện tại

    Returns:
    --------
    float
        Tốc độ hồi máu (% máu tối đa mỗi phút)
    """
    # Tìm chỉ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Công thức tính tốc độ hồi máu
    base_rate = 1.0  # Tốc độ cơ bản (1% mỗi phút)
    realm_bonus = realm_index * 0.2  # Bonus theo cảnh giới
    stage_bonus = stage * 0.05  # Bonus theo cấp độ

    healing_rate = base_rate + realm_bonus + stage_bonus

    return healing_rate


def calculate_auction_starting_bid(item_value):
    """
    Tính toán giá khởi điểm cho đấu giá

    Parameters:
    -----------
    item_value: int
        Giá trị vật phẩm

    Returns:
    --------
    int
        Giá khởi điểm đấu giá
    """
    # Giá khởi điểm thường là 60-80% giá trị vật phẩm
    starting_bid = int(item_value * random.uniform(0.6, 0.8))

    # Làm tròn đến hàng chục gần nhất
    starting_bid = int(round(starting_bid / 10) * 10)

    return max(10, starting_bid)  # Tối thiểu 10 linh thạch


def calculate_auction_bid_increment(current_bid):
    """
    Tính toán mức tăng tối thiểu cho lần đấu giá tiếp theo

    Parameters:
    -----------
    current_bid: int
        Giá đấu hiện tại

    Returns:
    --------
    int
        Mức tăng tối thiểu
    """
    # Mức tăng dựa trên giá hiện tại
    if current_bid < 100:
        return 10  # +10 cho giá dưới 100
    elif current_bid < 1000:
        return 50  # +50 cho giá từ 100-999
    elif current_bid < 10000:
        return 100  # +100 cho giá từ 1000-9999
    elif current_bid < 100000:
        return 500  # +500 cho giá từ 10000-99999
    else:
        return 1000  # +1000 cho giá từ 100000 trở lên


def calculate_shop_restock_time(shop_level):
    """
    Tính toán thời gian làm mới cửa hàng

    Parameters:
    -----------
    shop_level: int
        Cấp độ cửa hàng

    Returns:
    --------
    int
        Thời gian làm mới (giây)
    """
    # Thời gian cơ bản là 24 giờ
    base_time = 86400  # 24 giờ = 86400 giây

    # Giảm thời gian theo cấp độ cửa hàng
    level_reduction = shop_level * 1800  # Mỗi cấp giảm 30 phút

    restock_time = base_time - level_reduction

    # Giới hạn tối thiểu 6 giờ
    return max(21600, restock_time)


def calculate_quest_reward(quest_type, quest_difficulty, user_level):
    """
    Tính toán phần thưởng nhiệm vụ

    Parameters:
    -----------
    quest_type: str
        Loại nhiệm vụ
    quest_difficulty: int
        Độ khó nhiệm vụ (1-5)
    user_level: int
        Cấp độ người dùng

    Returns:
    --------
    dict
        Phần thưởng (kinh nghiệm, linh thạch)
    """
    # Phần thưởng cơ bản
    base_rewards = {
        "hunt": {"exp": 50, "spirit_stones": 100},
        "gather": {"exp": 30, "spirit_stones": 80},
        "cultivate": {"exp": 100, "spirit_stones": 50},
        "sect": {"exp": 40, "spirit_stones": 120},
        "pvp": {"exp": 80, "spirit_stones": 150}
    }

    # Lấy phần thưởng cơ bản theo loại nhiệm vụ
    base_exp = base_rewards.get(quest_type, {"exp": 50, "spirit_stones": 100})["exp"]
    base_spirit_stones = base_rewards.get(quest_type, {"exp": 50, "spirit_stones": 100})["spirit_stones"]

    # Điều chỉnh theo độ khó
    difficulty_multiplier = quest_difficulty ** 1.5

    # Điều chỉnh theo cấp độ người dùng
    level_multiplier = user_level ** 0.8

    # Tính phần thưởng cuối cùng
    exp_reward = int(base_exp * difficulty_multiplier * level_multiplier)
    spirit_stones_reward = int(base_spirit_stones * difficulty_multiplier * level_multiplier)

    # Thêm yếu tố ngẫu nhiên (±20%)
    random_factor = random.uniform(0.8, 1.2)
    exp_reward = int(exp_reward * random_factor)
    spirit_stones_reward = int(spirit_stones_reward * random_factor)

    return {
        "exp": exp_reward,
        "spirit_stones": spirit_stones_reward
    }


def calculate_dungeon_difficulty(dungeon_level, user_level):
    """
    Tính toán độ khó của động phủ

    Parameters:
    -----------
    dungeon_level: int
        Cấp độ động phủ
    user_level: int
        Cấp độ người dùng

    Returns:
    --------
    float
        Hệ số độ khó (1.0 = cân bằng)
    """
    # Tính chênh lệch cấp độ
    level_difference = dungeon_level - user_level

    # Điều chỉnh độ khó dựa trên chênh lệch
    difficulty_factor = 1.0 + level_difference * 0.2

    # Giới hạn độ khó
    return max(0.5, min(3.0, difficulty_factor))


def calculate_dungeon_reward(dungeon_level, completion_percent):
    """
    Tính toán phần thưởng khi hoàn thành động phủ

    Parameters:
    -----------
    dungeon_level: int
        Cấp độ động phủ
    completion_percent: float
        Phần trăm hoàn thành (0.0 - 1.0)

    Returns:
    --------
    dict
        Phần thưởng (kinh nghiệm, linh thạch)
    """
    # Phần thưởng cơ bản
    base_exp = 200 * dungeon_level
    base_spirit_stones = 500 * dungeon_level

    # Điều chỉnh theo phần trăm hoàn thành
    completion_multiplier = completion_percent ** 0.5  # Khuyến khích hoàn thành nhiều hơn

    # Tính phần thưởng cuối cùng
    exp_reward = int(base_exp * completion_multiplier)
    spirit_stones_reward = int(base_spirit_stones * completion_multiplier)

    # Thêm yếu tố ngẫu nhiên (±20%)
    random_factor = random.uniform(0.8, 1.2)
    exp_reward = int(exp_reward * random_factor)
    spirit_stones_reward = int(spirit_stones_reward * random_factor)

    return {
        "exp": exp_reward,
        "spirit_stones": spirit_stones_reward
    }


def calculate_friendship_bonus(friendship_level):
    """
    Tính toán lợi ích từ mức độ hảo cảm

    Parameters:
    -----------
    friendship_level: int
        Cấp độ hảo cảm (1-10)

    Returns:
    --------
    dict
        Các lợi ích (giảm giá giao dịch, tăng kinh nghiệm khi cùng làm nhiệm vụ)
    """
    # Giới hạn cấp độ hảo cảm
    friendship_level = max(1, min(10, friendship_level))

    # Tính các lợi ích
    trade_discount = 0.02 * friendship_level  # 2% mỗi cấp, tối đa 20%
    exp_bonus = 0.03 * friendship_level  # 3% mỗi cấp, tối đa 30%

    return {
        "trade_discount": trade_discount,
        "exp_bonus": exp_bonus
    }


def calculate_event_reward_multiplier(event_rarity):
    """
    Tính toán hệ số phần thưởng cho sự kiện

    Parameters:
    -----------
    event_rarity: str
        Độ hiếm của sự kiện (common, uncommon, rare, epic, legendary)

    Returns:
    --------
    float
        Hệ số nhân phần thưởng
    """
    # Hệ số theo độ hiếm
    rarity_multipliers = {
        "common": 1.0,
        "uncommon": 1.5,
        "rare": 2.0,
        "epic": 3.0,
        "legendary": 5.0
    }

    return rarity_multipliers.get(event_rarity.lower(), 1.0)


def calculate_breakthrough_chance(user_data):
    """
    Tính toán cơ hội đột phá cảnh giới

    Parameters:
    -----------
    user_data: dict
        Dữ liệu người dùng

    Returns:
    --------
    float
        Cơ hội đột phá (0.0 - 1.0)
    """
    # Lấy thông tin cảnh giới
    cultivation = user_data.get('cultivation', {})
    realm = cultivation.get('realm', 'Phàm Nhân')
    stage = cultivation.get('stage', 1)
    max_stage = cultivation.get('max_stage', 9)

    # Nếu chưa đạt cấp độ tối đa, không thể đột phá
    if stage < max_stage:
        return 0.0

    # Tìm chỉ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Cơ hội cơ bản giảm dần theo cảnh giới
    base_chance = 0.5 - realm_index * 0.05

    # Điều chỉnh theo các yếu tố khác
    # 1. Thời gian tu luyện ở cấp độ tối đa
    time_at_max = user_data.get('time_at_max_stage', 0)  # Giây
    time_bonus = min(0.2, time_at_max / 86400 * 0.01)  # +1% mỗi ngày, tối đa +20%

    # 2. Sử dụng đan dược
    breakthrough_pills = user_data.get('breakthrough_pills', 0)
    pill_bonus = min(0.3, breakthrough_pills * 0.05)  # +5% mỗi viên, tối đa +30%

    # 3. Hỗ trợ từ môn phái
    sect = user_data.get('sect', {})
    sect_bonus = 0.0
    if sect and sect.get('name', 'Không có') != 'Không có':
        sect_level = sect.get('level', 1)
        sect_bonus = min(0.1, sect_level * 0.01)  # +1% mỗi cấp môn phái, tối đa +10%

    # Tính tổng cơ hội
    total_chance = base_chance + time_bonus + pill_bonus + sect_bonus

    # Giới hạn cơ hội
    return max(0.05, min(0.8, total_chance))  # Tối thiểu 5%, tối đa 80%


def calculate_breakthrough_cost(realm):
    """
    Tính toán chi phí đột phá cảnh giới

    Parameters:
    -----------
    realm: str
        Cảnh giới hiện tại

    Returns:
    --------
    dict
        Chi phí đột phá (linh thạch, vật phẩm cần thiết)
    """
    # Tìm chỉ số cảnh giới
    realm_index = 0
    for i, r in enumerate(CULTIVATION_REALMS):
        if r['name'] == realm:
            realm_index = i
            break

    # Chi phí linh thạch tăng theo cấp bậc
    base_cost = 1000
    realm_multiplier = 3 ** realm_index

    spirit_stones_cost = base_cost * realm_multiplier

    # Vật phẩm cần thiết
    required_items = []

    # Từ cảnh giới thứ 3 trở đi cần thêm vật phẩm
    if realm_index >= 2:
        required_items.append({
            "item_id": 100 + realm_index,  # ID vật phẩm đột phá
            "quantity": realm_index
        })

    return {
        "spirit_stones": spirit_stones_cost,
        "required_items": required_items
    }


def calculate_skill_upgrade_cost(skill_level):
    """
    Tính toán chi phí nâng cấp kỹ năng

    Parameters:
    -----------
    skill_level: int
        Cấp độ kỹ năng hiện tại

    Returns:
    --------
    dict
        Chi phí nâng cấp (linh thạch, điểm kỹ năng)
    """
    # Chi phí tăng theo cấp độ
    base_spirit_stones = 200
    base_skill_points = 1

    level_multiplier = skill_level ** 1.5

    spirit_stones_cost = int(base_spirit_stones * level_multiplier)
    skill_points_cost = base_skill_points + (skill_level // 5)

    return {
        "spirit_stones": spirit_stones_cost,
        "skill_points": skill_points_cost
    }


def calculate_skill_effect(skill_data, user_level):
    """
    Tính toán hiệu quả của kỹ năng

    Parameters:
    -----------
    skill_data: dict
        Dữ liệu kỹ năng
    user_level: int
        Cấp độ người dùng

    Returns:
    --------
    dict
        Hiệu quả kỹ năng (sát thương, hồi phục, v.v.)
    """
    # Lấy thông tin kỹ năng
    skill_type = skill_data.get('type', 'attack')
    skill_level = skill_data.get('level', 1)
    skill_base_value = skill_data.get('base_value', 100)

    # Tính hiệu quả dựa trên loại kỹ năng
    if skill_type == "attack":
        # Kỹ năng tấn công
        base_damage = skill_base_value
        level_multiplier = 1 + skill_level * 0.1  # +10% mỗi cấp
        user_multiplier = 1 + user_level * 0.05  # +5% mỗi cấp người dùng

        damage = base_damage * level_multiplier * user_multiplier

        return {
            "damage": int(damage),
            "critical_chance": 0.1 + skill_level * 0.01  # +1% cơ hội chí mạng mỗi cấp
        }

    elif skill_type == "heal":
        # Kỹ năng hồi phục
        base_heal = skill_base_value
        level_multiplier = 1 + skill_level * 0.15  # +15% mỗi cấp
        user_multiplier = 1 + user_level * 0.03  # +3% mỗi cấp người dùng

        heal_amount = base_heal * level_multiplier * user_multiplier

        return {
            "heal_amount": int(heal_amount)
        }

    elif skill_type == "buff":
        # Kỹ năng tăng cường
        base_buff = skill_base_value / 100  # Chuyển thành phần trăm
        level_multiplier = 1 + skill_level * 0.05  # +5% mỗi cấp

        buff_value = base_buff * level_multiplier
        buff_duration = 30 + skill_level * 10  # 30 giây + 10 giây mỗi cấp

        return {
            "buff_value": buff_value,
            "buff_duration": buff_duration
        }

    elif skill_type == "debuff":
        # Kỹ năng suy yếu
        base_debuff = skill_base_value / 100  # Chuyển thành phần trăm
        level_multiplier = 1 + skill_level * 0.05  # +5% mỗi cấp

        debuff_value = base_debuff * level_multiplier
        debuff_duration = 20 + skill_level * 5  # 20 giây + 5 giây mỗi cấp

        return {
            "debuff_value": debuff_value,
            "debuff_duration": debuff_duration
        }

    # Mặc định trả về giá trị rỗng
    return {}


def calculate_equipment_stats(item_data, user_level):
    """
    Tính toán chỉ số của trang bị

    Parameters:
    -----------
    item_data: dict
        Dữ liệu vật phẩm
    user_level: int
        Cấp độ người dùng

    Returns:
    --------
    dict
        Chỉ số trang bị (power_bonus, health_bonus, v.v.)
    """
    # Lấy thông tin vật phẩm
    item_level = item_data.get('level', 1)
    item_rarity = item_data.get('rarity', 'common')
    item_type = item_data.get('type', 'weapon')

    # Hệ số theo độ hiếm
    rarity_multiplier = {
        'common': 1,
        'uncommon': 1.5,
        'rare': 2.5,
        'epic': 4,
        'legendary': 7,
        'mythic': 12
    }.get(item_rarity.lower(), 1)

    # Chỉ số cơ bản dựa trên loại trang bị
    base_stats = {
        'weapon': {'power_bonus': 50, 'health_bonus': 0},
        'armor': {'power_bonus': 20, 'health_bonus': 100},
        'accessory': {'power_bonus': 30, 'health_bonus': 50}
    }.get(item_type.lower(), {'power_bonus': 30, 'health_bonus': 30})

    # Tính toán chỉ số cuối cùng
    level_multiplier = (item_level / user_level) ** 0.8 if user_level > 0 else 1

    power_bonus = int(base_stats['power_bonus'] * rarity_multiplier * level_multiplier)
    health_bonus = int(base_stats['health_bonus'] * rarity_multiplier * level_multiplier)

    # Thêm thuộc tính ngẫu nhiên dựa trên độ hiếm
    additional_stats = {}

    if item_rarity.lower() in ['rare', 'epic', 'legendary', 'mythic']:
        # Thêm thuộc tính tốc độ tu luyện
        cultivation_speed_bonus = 0.05 * (rarity_multiplier - 1)
        additional_stats['cultivation_speed_bonus'] = cultivation_speed_bonus

    if item_rarity.lower() in ['epic', 'legendary', 'mythic']:
        # Thêm thuộc tính giảm thời gian hồi chiêu
        cooldown_reduction = 0.03 * (rarity_multiplier - 2)
        additional_stats['cooldown_reduction'] = cooldown_reduction

    if item_rarity.lower() in ['legendary', 'mythic']:
        # Thêm thuộc tính tăng tỷ lệ chí mạng
        critical_chance_bonus = 0.02 * (rarity_multiplier - 4)
        additional_stats['critical_chance_bonus'] = critical_chance_bonus

    # Kết hợp tất cả chỉ số
    stats = {
        'power_bonus': power_bonus,
        'health_bonus': health_bonus,
        **additional_stats
    }

    return stats
