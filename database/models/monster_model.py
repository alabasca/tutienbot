# database/models/monster_model.py
from typing import Dict, List, Optional, Union, Any
from enum import Enum


class MonsterType(Enum):
    BEAST = "beast"
    DEMON = "demon"
    SPIRIT = "spirit"
    UNDEAD = "undead"
    ELEMENTAL = "elemental"
    HUMAN = "human"
    DIVINE = "divine"
    DEVIL = "devil"
    CONSTRUCT = "construct"
    PLANT = "plant"


class MonsterRank(Enum):
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    SS = "SS"
    SSS = "SSS"
    LEGENDARY = "LEGENDARY"
    MYTHIC = "MYTHIC"
    DIVINE = "DIVINE"


class ElementType(Enum):
    NONE = "none"
    WOOD = "wood"
    FIRE = "fire"
    EARTH = "earth"
    METAL = "metal"
    WATER = "water"
    WIND = "wind"
    LIGHTNING = "lightning"
    ICE = "ice"
    LIGHT = "light"
    DARK = "dark"
    SPACE = "space"
    TIME = "time"


class Monster:
    """Lớp đại diện cho quái vật"""

    def __init__(self, monster_id: str, name: str, monster_type: MonsterType, rank: MonsterRank):
        self.monster_id = monster_id
        self.name = name
        self.description = ""
        self.monster_type = monster_type
        self.rank = rank
        self.level = 1
        self.realm = "Luyện Khí"  # Cảnh giới tương đương
        self.realm_level = 1  # Tiểu cảnh giới

        # Thuộc tính chiến đấu
        self.stats = {
            "hp": 100,
            "max_hp": 100,
            "mp": 50,
            "max_mp": 50,
            "attack": 10,
            "defense": 5,
            "speed": 10,
            "crit_rate": 5,
            "crit_damage": 150,
            "dodge": 5,
            "accuracy": 100,
            "elemental": {
                "wood": 0,
                "fire": 0,
                "earth": 0,
                "metal": 0,
                "water": 0,
                "wind": 0,
                "lightning": 0,
                "ice": 0,
                "light": 0,
                "dark": 0
            },
            "resistance": {
                "wood": 0,
                "fire": 0,
                "earth": 0,
                "metal": 0,
                "water": 0,
                "wind": 0,
                "lightning": 0,
                "ice": 0,
                "light": 0,
                "dark": 0
            }
        }

        # Kỹ năng
        self.skills = []

        # Phần thưởng
        self.drops = []

        # Kinh nghiệm và linh thạch khi đánh bại
        self.exp_reward = 10
        self.spirit_stone_reward = 5

        # Thuộc tính đặc biệt
        self.element = ElementType.NONE
        self.abilities = []
        self.weaknesses = []
        self.resistances = []
        self.immunities = []

        # Thông tin hiển thị
        self.image_url = None
        self.spawn_areas = []
        self.spawn_rate = 100  # Tỷ lệ xuất hiện (1-100)
        self.aggression = "neutral"  # hostile, neutral, passive
        self.size = "medium"  # tiny, small, medium, large, huge, colossal

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        return {
            "monster_id": self.monster_id,
            "name": self.name,
            "description": self.description,
            "monster_type": self.monster_type.value,
            "rank": self.rank.value,
            "level": self.level,
            "realm": self.realm,
            "realm_level": self.realm_level,
            "stats": self.stats,
            "skills": self.skills,
            "drops": self.drops,
            "exp_reward": self.exp_reward,
            "spirit_stone_reward": self.spirit_stone_reward,
            "element": self.element.value,
            "abilities": self.abilities,
            "weaknesses": self.weaknesses,
            "resistances": self.resistances,
            "immunities": self.immunities,
            "image_url": self.image_url,
            "spawn_areas": self.spawn_areas,
            "spawn_rate": self.spawn_rate,
            "aggression": self.aggression,
            "size": self.size
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Monster':
        """Tạo đối tượng Monster từ dictionary lấy từ MongoDB"""
        monster = cls(
            data["monster_id"],
            data["name"],
            MonsterType(data["monster_type"]),
            MonsterRank(data["rank"])
        )
        monster.description = data.get("description", "")
        monster.level = data.get("level", 1)
        monster.realm = data.get("realm", "Luyện Khí")
        monster.realm_level = data.get("realm_level", 1)
        monster.stats = data.get("stats", monster.stats)
        monster.skills = data.get("skills", [])
        monster.drops = data.get("drops", [])
        monster.exp_reward = data.get("exp_reward", 10)
        monster.spirit_stone_reward = data.get("spirit_stone_reward", 5)
        monster.element = ElementType(data.get("element", "none"))
        monster.abilities = data.get("abilities", [])
        monster.weaknesses = data.get("weaknesses", [])
        monster.resistances = data.get("resistances", [])
        monster.immunities = data.get("immunities", [])
        monster.image_url = data.get("image_url")
        monster.spawn_areas = data.get("spawn_areas", [])
        monster.spawn_rate = data.get("spawn_rate", 100)
        monster.aggression = data.get("aggression", "neutral")
        monster.size = data.get("size", "medium")
        return monster

    def scale_to_level(self, target_level: int) -> None:
        """Điều chỉnh chỉ số theo cấp độ"""
        if target_level <= 0 or target_level == self.level:
            return

        # Tính hệ số tăng
        level_multiplier = target_level / self.level

        # Cập nhật cấp độ
        self.level = target_level

        # Cập nhật chỉ số
        self.stats["max_hp"] = int(self.stats["max_hp"] * level_multiplier)
        self.stats["hp"] = self.stats["max_hp"]
        self.stats["max_mp"] = int(self.stats["max_mp"] * level_multiplier)
        self.stats["mp"] = self.stats["max_mp"]
        self.stats["attack"] = int(self.stats["attack"] * level_multiplier)
        self.stats["defense"] = int(self.stats["defense"] * level_multiplier)
        self.stats["speed"] = int(self.stats["speed"] * level_multiplier)

        # Cập nhật phần thưởng
        self.exp_reward = int(self.exp_reward * level_multiplier)
        self.spirit_stone_reward = int(self.spirit_stone_reward * level_multiplier)

    def scale_to_realm(self, target_realm: str, target_realm_level: int = 1) -> None:
        """Điều chỉnh chỉ số theo cảnh giới"""
        realm_levels = ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể", "Đại Thừa",
                        "Độ Kiếp", "Tiên Nhân"]

        # Kiểm tra cảnh giới hợp lệ
        if target_realm not in realm_levels:
            return

        # Tính chỉ số tăng dựa trên cảnh giới
        current_realm_index = realm_levels.index(self.realm)
        target_realm_index = realm_levels.index(target_realm)

        # Nếu cùng cảnh giới, chỉ điều chỉnh theo tiểu cảnh giới
        if current_realm_index == target_realm_index:
            level_multiplier = target_realm_level / self.realm_level
        else:
            # Nếu khác cảnh giới, áp dụng hệ số mạnh mẽ hơn
            realm_multiplier = 2 ** (target_realm_index - current_realm_index)
            level_multiplier = realm_multiplier * (target_realm_level / self.realm_level)

        # Cập nhật cảnh giới
        self.realm = target_realm
        self.realm_level = target_realm_level

        # Cập nhật chỉ số
        self.stats["max_hp"] = int(self.stats["max_hp"] * level_multiplier)
        self.stats["hp"] = self.stats["max_hp"]
        self.stats["max_mp"] = int(self.stats["max_mp"] * level_multiplier)
        self.stats["mp"] = self.stats["max_mp"]
        self.stats["attack"] = int(self.stats["attack"] * level_multiplier)
        self.stats["defense"] = int(self.stats["defense"] * level_multiplier)
        self.stats["speed"] = int(self.stats["speed"] * level_multiplier)

        # Cập nhật phần thưởng
        self.exp_reward = int(self.exp_reward * level_multiplier)
        self.spirit_stone_reward = int(self.spirit_stone_reward * level_multiplier)

    def add_skill(self, skill_data: Dict[str, Any]) -> None:
        """Thêm kỹ năng cho quái vật"""
        self.skills.append(skill_data)

    def add_drop(self, item_id: str, chance: float, min_quantity: int = 1, max_quantity: int = 1) -> None:
        """Thêm vật phẩm rơi ra khi đánh bại"""
        drop = {
            "item_id": item_id,
            "chance": chance,  # Tỷ lệ rơi (0-1)
            "min_quantity": min_quantity,
            "max_quantity": max_quantity
        }
        self.drops.append(drop)

    def get_combat_power(self) -> int:
        """Tính sức mạnh chiến đấu tổng hợp"""
        stats = self.stats

        # Công thức tính sức mạnh (có thể điều chỉnh)
        power = (
                stats["max_hp"] * 0.5 +
                stats["attack"] * 2 +
                stats["defense"] * 1.5 +
                stats["speed"] * 1 +
                stats["crit_rate"] * 0.5 +
                (stats["crit_damage"] - 100) * 0.1
        )

        # Điều chỉnh theo cấp độ và cảnh giới
        realm_bonus = {
            "Luyện Khí": 1,
            "Trúc Cơ": 2,
            "Kim Đan": 4,
            "Nguyên Anh": 8,
            "Hóa Thần": 16,
            "Luyện Hư": 32,
            "Hợp Thể": 64,
            "Đại Thừa": 128,
            "Độ Kiếp": 256,
            "Tiên Nhân": 512
        }

        power *= realm_bonus.get(self.realm, 1)
        power *= (0.9 + 0.1 * self.realm_level)

        return int(power)

    def get_random_drops(self) -> List[Dict[str, Any]]:
        """Tính toán vật phẩm rơi ra dựa trên tỷ lệ"""
        import random

        result = []

        for drop in self.drops:
            # Kiểm tra xem có rơi ra không
            if random.random() <= drop["chance"]:
                # Tính số lượng
                quantity = random.randint(drop["min_quantity"], drop["max_quantity"])

                if quantity > 0:
                    result.append({
                        "item_id": drop["item_id"],
                        "quantity": quantity
                    })

        return result


class Boss(Monster):
    """Lớp đại diện cho boss"""

    def __init__(self, monster_id: str, name: str, monster_type: MonsterType, rank: MonsterRank):
        super().__init__(monster_id, name, monster_type, rank)

        # Thuộc tính đặc biệt của boss
        self.is_boss = True
        self.respawn_time = 86400  # Thời gian hồi sinh (giây), mặc định 1 ngày
        self.phases = 1  # Số giai đoạn chiến đấu
        self.phase_triggers = []  # Điều kiện kích hoạt giai đoạn mới
        self.phase_abilities = {}  # Khả năng đặc biệt theo giai đoạn
        self.minions = []  # Quái vật đi kèm
        self.special_mechanics = []  # Cơ chế đặc biệt
        self.defeat_count = 0  # Số lần bị đánh bại
        self.last_defeat = None  # Thời gian bị đánh bại gần nhất

        # Tăng chỉ số cơ bản cho boss
        self.stats["max_hp"] *= 5
        self.stats["hp"] = self.stats["max_hp"]
        self.stats["attack"] *= 2
        self.stats["defense"] *= 2

        # Tăng phần thưởng
        self.exp_reward *= 10
        self.spirit_stone_reward *= 10

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "is_boss": self.is_boss,
            "respawn_time": self.respawn_time,
            "phases": self.phases,
            "phase_triggers": self.phase_triggers,
            "phase_abilities": self.phase_abilities,
            "minions": self.minions,
            "special_mechanics": self.special_mechanics,
            "defeat_count": self.defeat_count,
            "last_defeat": self.last_defeat
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Boss':
        """Tạo đối tượng Boss từ dictionary lấy từ MongoDB"""
        boss = cls(
            data["monster_id"],
            data["name"],
            MonsterType(data["monster_type"]),
            MonsterRank(data["rank"])
        )
        boss.description = data.get("description", "")
        boss.level = data.get("level", 1)
        boss.realm = data.get("realm", "Luyện Khí")
        boss.realm_level = data.get("realm_level", 1)
        boss.stats = data.get("stats", boss.stats)
        boss.skills = data.get("skills", [])
        boss.drops = data.get("drops", [])
        boss.exp_reward = data.get("exp_reward", 10)
        boss.spirit_stone_reward = data.get("spirit_stone_reward", 5)
        boss.element = ElementType(data.get("element", "none"))
        boss.abilities = data.get("abilities", [])
        boss.weaknesses = data.get("weaknesses", [])
        boss.resistances = data.get("resistances", [])
        boss.immunities = data.get("immunities", [])
        boss.image_url = data.get("image_url")
        boss.spawn_areas = data.get("spawn_areas", [])
        boss.spawn_rate = data.get("spawn_rate", 100)
        boss.aggression = data.get("aggression", "hostile")
        boss.size = data.get("size", "large")
        boss.respawn_time = data.get("respawn_time", 86400)
        boss.phases = data.get("phases", 1)
        boss.phase_triggers = data.get("phase_triggers", [])
        boss.phase_abilities = data.get("phase_abilities", {})
        boss.minions = data.get("minions", [])
        boss.special_mechanics = data.get("special_mechanics", [])
        boss.defeat_count = data.get("defeat_count", 0)
        boss.last_defeat = data.get("last_defeat")
        return boss

    def add_minion(self, minion_id: str, count: int = 1) -> None:
        """Thêm quái vật đi kèm"""
        self.minions.append({
            "minion_id": minion_id,
            "count": count
        })

    def add_phase_trigger(self, hp_percent: int, phase: int) -> None:
        """Thêm điều kiện kích hoạt giai đoạn mới"""
        self.phase_triggers.append({
            "hp_percent": hp_percent,
            "phase": phase
        })

    def add_phase_ability(self, phase: int, ability: Dict[str, Any]) -> None:
        """Thêm khả năng đặc biệt cho giai đoạn"""
        if str(phase) not in self.phase_abilities:
            self.phase_abilities[str(phase)] = []

        self.phase_abilities[str(phase)].append(ability)

    def record_defeat(self) -> None:
        """Ghi nhận bị đánh bại"""
        import datetime

        self.defeat_count += 1
        self.last_defeat = datetime.datetime.utcnow()

    def is_available(self) -> bool:
        """Kiểm tra xem boss đã hồi sinh chưa"""
        if self.last_defeat is None:
            return True

        import datetime

        # Tính thời gian đã trôi qua kể từ lần bị đánh bại gần nhất
        time_passed = (datetime.datetime.utcnow() - self.last_defeat).total_seconds()

        return time_passed >= self.respawn_time

    def get_time_until_respawn(self) -> int:
        """Lấy thời gian còn lại đến khi hồi sinh (giây)"""
        if self.last_defeat is None:
            return 0

        import datetime

        # Tính thời gian đã trôi qua kể từ lần bị đánh bại gần nhất
        time_passed = (datetime.datetime.utcnow() - self.last_defeat).total_seconds()

        # Tính thời gian còn lại
        time_remaining = max(0, self.respawn_time - time_passed)

        return int(time_remaining)

    def get_current_phase(self, current_hp_percent: int) -> int:
        """Xác định giai đoạn hiện tại dựa trên phần trăm máu"""
        current_phase = 1

        for trigger in sorted(self.phase_triggers, key=lambda x: x["hp_percent"], reverse=True):
            if current_hp_percent <= trigger["hp_percent"]:
                current_phase = trigger["phase"]
                break

        return current_phase

    def get_phase_abilities(self, phase: int) -> List[Dict[str, Any]]:
        """Lấy danh sách khả năng đặc biệt của giai đoạn"""
        return self.phase_abilities.get(str(phase), [])
