# database/models/item_model.py
from typing import Dict, List, Optional, Union, Any
from enum import Enum


class ItemType(Enum):
    EQUIPMENT = "equipment"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    TREASURE = "treasure"
    CULTIVATION_RESOURCE = "cultivation_resource"
    TALISMAN = "talisman"
    PILL = "pill"
    SPIRIT_STONE = "spirit_stone"
    SKILL_BOOK = "skill_book"
    QUEST_ITEM = "quest_item"


class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
    DIVINE = "divine"
    ARTIFACT = "artifact"


class EquipmentSlot(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    HELMET = "helmet"
    BOOTS = "boots"
    BELT = "belt"
    NECKLACE = "necklace"
    RING = "ring"
    TALISMAN = "talisman"
    SPIRIT_PET = "spirit_pet"


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


class Item:
    """Lớp cơ sở cho tất cả các vật phẩm"""

    def __init__(self, item_id: str, name: str, description: str, item_type: ItemType, rarity: ItemRarity):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.rarity = rarity
        self.value = 0  # Giá trị linh thạch
        self.stackable = True  # Có thể xếp chồng không
        self.tradeable = True  # Có thể giao dịch không
        self.bound = False  # Đã khóa vào người chơi chưa
        self.image_url = None  # URL hình ảnh
        self.required_level = 0  # Cảnh giới yêu cầu
        self.required_realm = None  # Cảnh giới yêu cầu
        self.weight = 1  # Trọng lượng (ảnh hưởng đến sức chứa kho đồ)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type.value,
            "rarity": self.rarity.value,
            "value": self.value,
            "stackable": self.stackable,
            "tradeable": self.tradeable,
            "bound": self.bound,
            "image_url": self.image_url,
            "required_level": self.required_level,
            "required_realm": self.required_realm,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Tạo đối tượng Item từ dictionary lấy từ MongoDB"""
        item = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemType(data["item_type"]),
            ItemRarity(data["rarity"])
        )
        item.value = data.get("value", 0)
        item.stackable = data.get("stackable", True)
        item.tradeable = data.get("tradeable", True)
        item.bound = data.get("bound", False)
        item.image_url = data.get("image_url")
        item.required_level = data.get("required_level", 0)
        item.required_realm = data.get("required_realm")
        item.weight = data.get("weight", 1)
        return item


class Equipment(Item):
    """Lớp đại diện cho trang bị"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity, slot: EquipmentSlot):
        super().__init__(item_id, name, description, ItemType.EQUIPMENT, rarity)
        self.slot = slot
        self.stats = {}  # Các chỉ số cộng thêm
        self.durability = 100  # Độ bền
        self.max_durability = 100  # Độ bền tối đa
        self.level = 1  # Cấp độ trang bị
        self.refinement = 0  # Độ tinh luyện
        self.sockets = 0  # Số ổ khảm
        self.gems = []  # Danh sách đá khảm
        self.set_id = None  # ID bộ trang bị
        self.element = ElementType.NONE  # Nguyên tố
        self.special_effects = []  # Hiệu ứng đặc biệt
        self.stackable = False  # Trang bị không thể xếp chồng

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "slot": self.slot.value,
            "stats": self.stats,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "level": self.level,
            "refinement": self.refinement,
            "sockets": self.sockets,
            "gems": self.gems,
            "set_id": self.set_id,
            "element": self.element.value,
            "special_effects": self.special_effects
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Equipment':
        """Tạo đối tượng Equipment từ dictionary lấy từ MongoDB"""
        equipment = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"]),
            EquipmentSlot(data["slot"])
        )
        equipment.value = data.get("value", 0)
        equipment.stackable = False
        equipment.tradeable = data.get("tradeable", True)
        equipment.bound = data.get("bound", False)
        equipment.image_url = data.get("image_url")
        equipment.required_level = data.get("required_level", 0)
        equipment.required_realm = data.get("required_realm")
        equipment.weight = data.get("weight", 1)
        equipment.stats = data.get("stats", {})
        equipment.durability = data.get("durability", 100)
        equipment.max_durability = data.get("max_durability", 100)
        equipment.level = data.get("level", 1)
        equipment.refinement = data.get("refinement", 0)
        equipment.sockets = data.get("sockets", 0)
        equipment.gems = data.get("gems", [])
        equipment.set_id = data.get("set_id")
        equipment.element = ElementType(data.get("element", "none"))
        equipment.special_effects = data.get("special_effects", [])
        return equipment

    def refine(self) -> bool:
        """Tinh luyện trang bị"""
        if self.refinement < 10:  # Giới hạn tinh luyện
            self.refinement += 1
            # Tăng chỉ số theo tinh luyện
            for stat in self.stats:
                self.stats[stat] = int(self.stats[stat] * 1.1)
            return True
        return False

    def repair(self) -> bool:
        """Sửa chữa trang bị"""
        if self.durability < self.max_durability:
            self.durability = self.max_durability
            return True
        return False

    def add_socket(self) -> bool:
        """Thêm ổ khảm"""
        if self.sockets < 3:  # Giới hạn ổ khảm
            self.sockets += 1
            return True
        return False

    def add_gem(self, gem_id: str) -> bool:
        """Khảm đá"""
        if len(self.gems) < self.sockets:
            self.gems.append(gem_id)
            return True
        return False

    def remove_gem(self, index: int) -> Optional[str]:
        """Tháo đá khảm"""
        if 0 <= index < len(self.gems):
            return self.gems.pop(index)
        return None


class Consumable(Item):
    """Lớp đại diện cho vật phẩm tiêu hao"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity):
        super().__init__(item_id, name, description, ItemType.CONSUMABLE, rarity)
        self.effects = []  # Các hiệu ứng khi sử dụng
        self.duration = 0  # Thời gian hiệu lực (giây)
        self.cooldown = 0  # Thời gian hồi (giây)
        self.use_limit = None  # Giới hạn số lần sử dụng (None = không giới hạn)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "effects": self.effects,
            "duration": self.duration,
            "cooldown": self.cooldown,
            "use_limit": self.use_limit
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Consumable':
        """Tạo đối tượng Consumable từ dictionary lấy từ MongoDB"""
        consumable = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"])
        )
        consumable.value = data.get("value", 0)
        consumable.stackable = data.get("stackable", True)
        consumable.tradeable = data.get("tradeable", True)
        consumable.bound = data.get("bound", False)
        consumable.image_url = data.get("image_url")
        consumable.required_level = data.get("required_level", 0)
        consumable.required_realm = data.get("required_realm")
        consumable.weight = data.get("weight", 1)
        consumable.effects = data.get("effects", [])
        consumable.duration = data.get("duration", 0)
        consumable.cooldown = data.get("cooldown", 0)
        consumable.use_limit = data.get("use_limit")
        return consumable


class Material(Item):
    """Lớp đại diện cho nguyên liệu"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity):
        super().__init__(item_id, name, description, ItemType.MATERIAL, rarity)
        self.material_type = None  # Loại nguyên liệu
        self.crafting_uses = []  # Danh sách công thức có thể sử dụng

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "material_type": self.material_type,
            "crafting_uses": self.crafting_uses
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        """Tạo đối tượng Material từ dictionary lấy từ MongoDB"""
        material = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"])
        )
        material.value = data.get("value", 0)
        material.stackable = data.get("stackable", True)
        material.tradeable = data.get("tradeable", True)
        material.bound = data.get("bound", False)
        material.image_url = data.get("image_url")
        material.required_level = data.get("required_level", 0)
        material.required_realm = data.get("required_realm")
        material.weight = data.get("weight", 1)
        material.material_type = data.get("material_type")
        material.crafting_uses = data.get("crafting_uses", [])
        return material


class Treasure(Item):
    """Lớp đại diện cho bảo vật"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity):
        super().__init__(item_id, name, description, ItemType.TREASURE, rarity)
        self.unique = True  # Bảo vật thường là độc nhất
        self.effects = []  # Hiệu ứng đặc biệt
        self.lore = ""  # Thông tin về lai lịch
        self.activation_requirements = {}  # Yêu cầu để kích hoạt
        self.active_abilities = []  # Khả năng chủ động
        self.passive_abilities = []  # Khả năng bị động

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "unique": self.unique,
            "effects": self.effects,
            "lore": self.lore,
            "activation_requirements": self.activation_requirements,
            "active_abilities": self.active_abilities,
            "passive_abilities": self.passive_abilities
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Treasure':
        """Tạo đối tượng Treasure từ dictionary lấy từ MongoDB"""
        treasure = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"])
        )
        treasure.value = data.get("value", 0)
        treasure.stackable = data.get("stackable", False)
        treasure.tradeable = data.get("tradeable", True)
        treasure.bound = data.get("bound", False)
        treasure.image_url = data.get("image_url")
        treasure.required_level = data.get("required_level", 0)
        treasure.required_realm = data.get("required_realm")
        treasure.weight = data.get("weight", 1)
        treasure.unique = data.get("unique", True)
        treasure.effects = data.get("effects", [])
        treasure.lore = data.get("lore", "")
        treasure.activation_requirements = data.get("activation_requirements", {})
        treasure.active_abilities = data.get("active_abilities", [])
        treasure.passive_abilities = data.get("passive_abilities", [])
        return treasure


class Pill(Consumable):
    """Lớp đại diện cho đan dược"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity):
        super().__init__(item_id, name, description, rarity)
        self.item_type = ItemType.PILL
        self.pill_type = None  # Loại đan dược
        self.side_effects = []  # Tác dụng phụ
        self.success_rate = 100  # Tỷ lệ thành công (%)
        self.quality = 0  # Chất lượng đan dược (0-100)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "pill_type": self.pill_type,
            "side_effects": self.side_effects,
            "success_rate": self.success_rate,
            "quality": self.quality
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pill':
        """Tạo đối tượng Pill từ dictionary lấy từ MongoDB"""
        pill = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"])
        )
        pill.value = data.get("value", 0)
        pill.stackable = data.get("stackable", True)
        pill.tradeable = data.get("tradeable", True)
        pill.bound = data.get("bound", False)
        pill.image_url = data.get("image_url")
        pill.required_level = data.get("required_level", 0)
        pill.required_realm = data.get("required_realm")
        pill.weight = data.get("weight", 1)
        pill.effects = data.get("effects", [])
        pill.duration = data.get("duration", 0)
        pill.cooldown = data.get("cooldown", 0)
        pill.use_limit = data.get("use_limit")
        pill.pill_type = data.get("pill_type")
        pill.side_effects = data.get("side_effects", [])
        pill.success_rate = data.get("success_rate", 100)
        pill.quality = data.get("quality", 0)
        return pill


class SkillBook(Item):
    """Lớp đại diện cho sách kỹ năng"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity):
        super().__init__(item_id, name, description, ItemType.SKILL_BOOK, rarity)
        self.skill_id = None  # ID kỹ năng được học
        self.skill_name = None  # Tên kỹ năng
        self.skill_description = None  # Mô tả kỹ năng
        self.skill_type = None  # Loại kỹ năng
        self.one_time_use = True  # Chỉ sử dụng một lần

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "skill_description": self.skill_description,
            "skill_type": self.skill_type,
            "one_time_use": self.one_time_use
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillBook':
        """Tạo đối tượng SkillBook từ dictionary lấy từ MongoDB"""
        skill_book = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"])
        )
        skill_book.value = data.get("value", 0)
        skill_book.stackable = data.get("stackable", True)
        skill_book.tradeable = data.get("tradeable", True)
        skill_book.bound = data.get("bound", False)
        skill_book.image_url = data.get("image_url")
        skill_book.required_level = data.get("required_level", 0)
        skill_book.required_realm = data.get("required_realm")
        skill_book.weight = data.get("weight", 1)
        skill_book.skill_id = data.get("skill_id")
        skill_book.skill_name = data.get("skill_name")
        skill_book.skill_description = data.get("skill_description")
        skill_book.skill_type = data.get("skill_type")
        skill_book.one_time_use = data.get("one_time_use", True)
        return skill_book


class SpiritStone(Item):
    """Lớp đại diện cho linh thạch"""

    def __init__(self, item_id: str, name: str, description: str, rarity: ItemRarity):
        super().__init__(item_id, name, description, ItemType.SPIRIT_STONE, rarity)
        self.stone_type = "normal"  # Loại linh thạch
        self.value_multiplier = 1  # Hệ số giá trị
        self.energy_content = 100  # Lượng linh khí chứa trong đó

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        data = super().to_dict()
        data.update({
            "stone_type": self.stone_type,
            "value_multiplier": self.value_multiplier,
            "energy_content": self.energy_content
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpiritStone':
        """Tạo đối tượng SpiritStone từ dictionary lấy từ MongoDB"""
        spirit_stone = cls(
            data["item_id"],
            data["name"],
            data["description"],
            ItemRarity(data["rarity"])
        )
        spirit_stone.value = data.get("value", 0)
        spirit_stone.stackable = data.get("stackable", True)
        spirit_stone.tradeable = data.get("tradeable", True)
        spirit_stone.bound = data.get("bound", False)
        spirit_stone.image_url = data.get("image_url")
        spirit_stone.required_level = data.get("required_level", 0)
        spirit_stone.required_realm = data.get("required_realm")
        spirit_stone.weight = data.get("weight", 1)
        spirit_stone.stone_type = data.get("stone_type", "normal")
        spirit_stone.value_multiplier = data.get("value_multiplier", 1)
        spirit_stone.energy_content = data.get("energy_content", 100)
        return spirit_stone
