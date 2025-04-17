# database/models/user_model.py
import datetime
from typing import Dict, List, Optional, Union, Any


class User:
    """Mô hình người dùng trong hệ thống Tu Tiên"""

    def __init__(self, user_id: int, username: str):
        # Thông tin cơ bản
        self.user_id = user_id
        self.username = username
        self.avatar_url = None
        self.created_at = datetime.datetime.utcnow()
        self.last_active = datetime.datetime.utcnow()

        # Thông tin tu luyện
        self.cultivation = {
            "realm": "Luyện Khí",  # Cảnh giới tu luyện
            "realm_level": 1,  # Tiểu cảnh giới (1-9)
            "exp": 0,  # Kinh nghiệm tu luyện hiện tại
            "max_exp": 100,  # Kinh nghiệm cần để đột phá
            "cultivation_type": "Phàm",  # Loại căn cơ: Phàm, Linh, Thánh, Tiên, Thần
            "cultivation_base": 0,  # Căn cơ tu luyện (0-100)
            "meridians": {  # Trạng thái kinh mạch
                "opened": 0,  # Số kinh mạch đã khai thông (tối đa 12)
                "quality": "Phàm"  # Chất lượng kinh mạch: Phàm, Linh, Thánh, Tiên, Thần
            },
            "dantian": {  # Đan điền
                "capacity": 100,  # Dung lượng đan điền
                "current": 0,  # Lượng linh khí hiện tại
                "quality": "Phàm"  # Chất lượng đan điền: Phàm, Linh, Thánh, Tiên, Thần
            },
            "comprehension": {  # Ngộ tính và lĩnh ngộ
                "wood": 0,  # Mộc (0-100)
                "fire": 0,  # Hỏa (0-100)
                "earth": 0,  # Thổ (0-100)
                "metal": 0,  # Kim (0-100)
                "water": 0,  # Thủy (0-100)
                "wind": 0,  # Phong (0-100)
                "lightning": 0,  # Lôi (0-100)
                "ice": 0,  # Băng (0-100)
                "light": 0,  # Quang (0-100)
                "dark": 0,  # Ám (0-100)
                "space": 0,  # Không gian (0-100)
                "time": 0,  # Thời gian (0-100)
                "primary": None  # Ngộ tính chính
            },
            "techniques": {  # Công pháp đã học
                "cultivation": None,  # Công pháp tu luyện chính
                "body": None,  # Công pháp rèn thể
                "mental": None,  # Công pháp tu thần
                "sword": None,  # Kiếm pháp
                "saber": None,  # Đao pháp
                "fist": None,  # Quyền pháp
                "palm": None,  # Chưởng pháp
                "finger": None,  # Chỉ pháp
                "formation": None,  # Trận pháp
                "alchemy": None,  # Luyện đan
                "talisman": None,  # Phù lục
                "artifact": None  # Luyện khí
            },
            "breakthrough": {  # Thông tin đột phá
                "count": 0,  # Số lần đột phá thành công
                "failed": 0,  # Số lần đột phá thất bại
                "tribulation": 0,  # Số lần vượt qua thiên kiếp
                "last_attempt": None  # Thời gian đột phá gần nhất
            }
        }

        # Thuộc tính chiến đấu
        self.stats = {
            "hp": 100,  # Máu
            "max_hp": 100,  # Máu tối đa
            "mp": 100,  # Linh lực
            "max_mp": 100,  # Linh lực tối đa
            "physical_power": 10,  # Thân thể lực
            "spiritual_power": 10,  # Thần thức lực
            "attack": 10,  # Công kích
            "defense": 5,  # Phòng thủ
            "speed": 10,  # Tốc độ
            "crit_rate": 5,  # Tỷ lệ bạo kích (%)
            "crit_damage": 150,  # Sát thương bạo kích (%)
            "dodge": 5,  # Tỷ lệ né tránh (%)
            "accuracy": 100,  # Độ chính xác (%)
            "elemental": {  # Nguyên tố
                "wood": 0,  # Mộc (0-100)
                "fire": 0,  # Hỏa (0-100)
                "earth": 0,  # Thổ (0-100)
                "metal": 0,  # Kim (0-100)
                "water": 0,  # Thủy (0-100)
                "wind": 0,  # Phong (0-100)
                "lightning": 0,  # Lôi (0-100)
                "ice": 0,  # Băng (0-100)
                "light": 0,  # Quang (0-100)
                "dark": 0  # Ám (0-100)
            },
            "resistance": {  # Kháng tính
                "wood": 0,  # Kháng Mộc (0-100)
                "fire": 0,  # Kháng Hỏa (0-100)
                "earth": 0,  # Kháng Thổ (0-100)
                "metal": 0,  # Kháng Kim (0-100)
                "water": 0,  # Kháng Thủy (0-100)
                "wind": 0,  # Kháng Phong (0-100)
                "lightning": 0,  # Kháng Lôi (0-100)
                "ice": 0,  # Kháng Băng (0-100)
                "light": 0,  # Kháng Quang (0-100)
                "dark": 0  # Kháng Ám (0-100)
            }
        }

        # Tài nguyên
        self.resources = {
            "spirit_stones": 100,  # Linh thạch (tiền tệ chính)
            "low_stones": 0,  # Linh thạch hạ phẩm
            "mid_stones": 0,  # Linh thạch trung phẩm
            "high_stones": 0,  # Linh thạch thượng phẩm
            "spirit_herbs": 0,  # Linh dược
            "contribution": 0,  # Cống hiến môn phái
            "reputation": 0,  # Danh vọng
            "merit_points": 0,  # Công tích
            "bound_spirit_stones": 0,  # Linh thạch khóa
            "spiritual_energy": 0,  # Linh khí tự nhiên đã thu thập
            "cultivation_points": 0,  # Điểm tu luyện (dùng để nâng cấp công pháp)
            "talent_points": 0  # Điểm tài năng (dùng để nâng cấp thiên phú)
        }

        # Kho đồ
        self.inventory = {
            "capacity": 50,  # Sức chứa kho đồ
            "items": [],  # Danh sách vật phẩm [{"item_id": id, "quantity": số lượng, "bound": khóa}]
            "equipped": {  # Trang bị đang mặc
                "weapon": None,  # Vũ khí
                "armor": None,  # Áo giáp
                "helmet": None,  # Mũ
                "boots": None,  # Giày
                "belt": None,  # Đai
                "necklace": None,  # Dây chuyền
                "ring1": None,  # Nhẫn 1
                "ring2": None,  # Nhẫn 2
                "talisman": None,  # Bùa hộ mệnh
                "spirit_pet": None  # Linh thú
            }
        }

        # Kỹ năng
        self.skills = {
            "active": [],  # Kỹ năng chủ động [{"skill_id": id, "level": cấp độ, "exp": kinh nghiệm}]
            "passive": [],  # Kỹ năng bị động [{"skill_id": id, "level": cấp độ, "exp": kinh nghiệm}]
            "cultivation": [],  # Công pháp tu luyện [{"skill_id": id, "level": cấp độ, "exp": kinh nghiệm}]
            "crafting": [],  # Kỹ năng chế tạo [{"skill_id": id, "level": cấp độ, "exp": kinh nghiệm}]
            "equipped": {  # Kỹ năng đã trang bị (tối đa 5)
                "skill1": None,
                "skill2": None,
                "skill3": None,
                "skill4": None,
                "skill5": None
            }
        }

        # Thông tin môn phái
        self.sect = {
            "sect_id": None,  # ID môn phái
            "join_date": None,  # Ngày gia nhập
            "position": None,  # Chức vụ
            "contribution": 0,  # Cống hiến
            "weekly_contribution": 0,  # Cống hiến tuần
            "missions_completed": 0,  # Số nhiệm vụ môn phái đã hoàn thành
            "permissions": []  # Quyền hạn trong môn phái
        }

        # Thông tin xã hội
        self.social = {
            "friends": [],  # Danh sách bạn bè [{"user_id": id, "added_date": ngày thêm}]
            "reputation": {  # Danh vọng với các thế lực
                "general": 0,  # Danh vọng chung
                "sects": {},  # Danh vọng với các môn phái {"sect_id": giá trị}
                "cities": {},  # Danh vọng với các thành thị {"city_id": giá trị}
                "factions": {}  # Danh vọng với các thế lực {"faction_id": giá trị}
            },
            "titles": [],  # Danh hiệu đã đạt được
            "current_title": None,  # Danh hiệu đang sử dụng
            "achievements": [],  # Thành tựu đã đạt được
            "karma": 0,  # Nghiệp lực (âm: xấu, dương: tốt)
            "pvp": {  # Thông tin PvP
                "rank": None,  # Xếp hạng
                "points": 0,  # Điểm PvP
                "wins": 0,  # Số trận thắng
                "losses": 0,  # Số trận thua
                "streak": 0  # Chuỗi thắng hiện tại
            }
        }

        # Hoạt động
        self.activities = {
            "last_daily": None,  # Lần điểm danh cuối
            "daily_streak": 0,  # Chuỗi điểm danh
            "quests": {  # Nhiệm vụ
                "main": [],  # Nhiệm vụ chính tuyến
                "side": [],  # Nhiệm vụ phụ
                "daily": [],  # Nhiệm vụ hàng ngày
                "weekly": [],  # Nhiệm vụ hàng tuần
                "sect": []  # Nhiệm vụ môn phái
            },
            "completed_quests": [],  # Nhiệm vụ đã hoàn thành
            "exploration": {  # Khám phá
                "current_area": "Thôn Đào Hoa",  # Khu vực hiện tại
                "discovered_areas": ["Thôn Đào Hoa"],  # Khu vực đã khám phá
                "current_dungeon": None,  # Động phủ đang khám phá
                "dungeon_progress": {}  # Tiến độ động phủ {"dungeon_id": tầng}
            },
            "cooldowns": {  # Thời gian hồi
                "dungeon": None,  # Thời gian hồi động phủ
                "boss": None,  # Thời gian hồi boss
                "pvp": None,  # Thời gian hồi PvP
                "auction": None,  # Thời gian hồi đấu giá
                "cultivation": None  # Thời gian hồi tu luyện
            },
            "kills": {  # Số lượng đã tiêu diệt
                "monsters": {},  # Quái thường {"monster_id": số lượng}
                "bosses": {},  # Boss {"boss_id": số lượng}
                "players": 0  # Người chơi
            }
        }

        # Thống kê
        self.stats_record = {
            "pvp_wins": 0,  # Số trận PvP thắng
            "pvp_losses": 0,  # Số trận PvP thua
            "monster_kills_total": 0,  # Tổng số quái đã giết
            "boss_kills_total": 0,  # Tổng số boss đã giết
            "deaths": 0,  # Số lần chết
            "spirit_stones_earned": 0,  # Tổng linh thạch kiếm được
            "spirit_stones_spent": 0,  # Tổng linh thạch đã tiêu
            "items_crafted": 0,  # Số vật phẩm đã chế tạo
            "breakthroughs": 0,  # Số lần đột phá
            "quests_completed": 0,  # Số nhiệm vụ đã hoàn thành
            "dungeons_cleared": 0,  # Số động phủ đã hoàn thành
            "techniques_mastered": 0,  # Số công pháp đã thông thạo
            "highest_damage": 0,  # Sát thương cao nhất đã gây ra
            "total_cultivation_time": 0  # Tổng thời gian tu luyện (giây)
        }

        # Cài đặt người dùng
        self.settings = {
            "notifications": True,  # Bật/tắt thông báo
            "auto_cultivation": False,  # Tự động tu luyện
            "language": "vi",  # Ngôn ngữ
            "theme": "default",  # Giao diện
            "pvp_enabled": True,  # Cho phép PvP
            "trade_enabled": True,  # Cho phép giao dịch
            "friend_requests": True,  # Cho phép lời mời kết bạn
            "sect_invites": True  # Cho phép lời mời môn phái
        }

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "cultivation": self.cultivation,
            "stats": self.stats,
            "resources": self.resources,
            "inventory": self.inventory,
            "skills": self.skills,
            "sect": self.sect,
            "social": self.social,
            "activities": self.activities,
            "stats_record": self.stats_record,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Tạo đối tượng User từ dictionary lấy từ MongoDB"""
        user = cls(data["user_id"], data["username"])
        user.avatar_url = data.get("avatar_url")
        user.created_at = data.get("created_at", datetime.datetime.utcnow())
        user.last_active = data.get("last_active", datetime.datetime.utcnow())
        user.cultivation = data.get("cultivation", user.cultivation)
        user.stats = data.get("stats", user.stats)
        user.resources = data.get("resources", user.resources)
        user.inventory = data.get("inventory", user.inventory)
        user.skills = data.get("skills", user.skills)
        user.sect = data.get("sect", user.sect)
        user.social = data.get("social", user.social)
        user.activities = data.get("activities", user.activities)
        user.stats_record = data.get("stats_record", user.stats_record)
        user.settings = data.get("settings", user.settings)
        return user

    def add_item(self, item_id: str, quantity: int = 1, bound: bool = False) -> bool:
        """Thêm vật phẩm vào kho đồ"""
        # Kiểm tra sức chứa kho đồ
        current_items = sum(item["quantity"] for item in self.inventory["items"])
        if current_items + quantity > self.inventory["capacity"]:
            return False

        # Kiểm tra xem đã có vật phẩm này chưa và có cùng trạng thái khóa không
        for item in self.inventory["items"]:
            if item["item_id"] == item_id and item["bound"] == bound:
                item["quantity"] += quantity
                return True

        # Nếu chưa có, thêm mới
        self.inventory["items"].append({"item_id": item_id, "quantity": quantity, "bound": bound})
        return True

    def remove_item(self, item_id: str, quantity: int = 1, bound: bool = None) -> bool:
        """Xóa vật phẩm khỏi kho đồ"""
        # Nếu không chỉ định bound, ưu tiên xóa vật phẩm không khóa trước
        if bound is None:
            # Tìm vật phẩm không khóa
            for i, item in enumerate(self.inventory["items"]):
                if item["item_id"] == item_id and not item["bound"]:
                    if item["quantity"] > quantity:
                        item["quantity"] -= quantity
                        return True
                    elif item["quantity"] == quantity:
                        self.inventory["items"].pop(i)
                        return True
                    else:
                        remaining = quantity - item["quantity"]
                        self.inventory["items"].pop(i)
                        return self.remove_item(item_id, remaining, True)

            # Nếu không có vật phẩm không khóa, xóa vật phẩm khóa
            return self.remove_item(item_id, quantity, True)

        # Xóa vật phẩm với trạng thái khóa cụ thể
        for i, item in enumerate(self.inventory["items"]):
            if item["item_id"] == item_id and item["bound"] == bound:
                if item["quantity"] > quantity:
                    item["quantity"] -= quantity
                    return True
                elif item["quantity"] == quantity:
                    self.inventory["items"].pop(i)
                    return True
                else:
                    return False

        return False

    def has_item(self, item_id: str, quantity: int = 1, bound: bool = None) -> bool:
        """Kiểm tra xem có đủ vật phẩm không"""
        total = 0
        for item in self.inventory["items"]:
            if item["item_id"] == item_id:
                if bound is None or item["bound"] == bound:
                    total += item["quantity"]

        return total >= quantity

    def equip_item(self, item_id: str, slot: str) -> bool:
        """Trang bị vật phẩm"""
        # Kiểm tra xem có vật phẩm không
        if not self.has_item(item_id):
            return False

        # Kiểm tra slot hợp lệ
        valid_slots = ["weapon", "armor", "helmet", "boots", "belt", "necklace", "ring1", "ring2", "talisman",
                       "spirit_pet"]
        if slot not in valid_slots:
            return False

        # Tháo trang bị cũ nếu có
        old_item = self.inventory["equipped"].get(slot)
        if old_item:
            self.add_item(old_item, 1)

        # Trang bị mới
        self.remove_item(item_id, 1)
        self.inventory["equipped"][slot] = item_id
        return True

    def unequip_item(self, slot: str) -> bool:
        """Tháo trang bị"""
        # Kiểm tra slot hợp lệ
        valid_slots = ["weapon", "armor", "helmet", "boots", "belt", "necklace", "ring1", "ring2", "talisman",
                       "spirit_pet"]
        if slot not in valid_slots:
            return False

        # Kiểm tra xem có trang bị không
        item_id = self.inventory["equipped"].get(slot)
        if not item_id:
            return False

        # Tháo trang bị
        self.inventory["equipped"][slot] = None
        self.add_item(item_id, 1)
        return True

    def add_spirit_stones(self, amount: int, stone_type: str = "spirit_stones") -> None:
        """Thêm linh thạch"""
        valid_types = ["spirit_stones", "low_stones", "mid_stones", "high_stones", "bound_spirit_stones"]
        if stone_type in valid_types:
            self.resources[stone_type] += amount
            if stone_type == "spirit_stones":
                self.stats_record["spirit_stones_earned"] += amount

    def spend_spirit_stones(self, amount: int, stone_type: str = "spirit_stones") -> bool:
        """Chi tiêu linh thạch"""
        valid_types = ["spirit_stones", "low_stones", "mid_stones", "high_stones", "bound_spirit_stones"]
        if stone_type in valid_types and self.resources[stone_type] >= amount:
            self.resources[stone_type] -= amount
            if stone_type == "spirit_stones":
                self.stats_record["spirit_stones_spent"] += amount
            return True
        return False

    def convert_spirit_stones(self, from_type: str, to_type: str, amount: int) -> bool:
        """Chuyển đổi giữa các loại linh thạch"""
        conversion_rates = {
            "low_stones": {"spirit_stones": 10},
            "spirit_stones": {"low_stones": 0.1, "mid_stones": 100},
            "mid_stones": {"spirit_stones": 0.01, "high_stones": 100},
            "high_stones": {"mid_stones": 0.01}
        }

        if from_type not in conversion_rates or to_type not in conversion_rates[from_type]:
            return False

        rate = conversion_rates[from_type][to_type]
        converted_amount = int(amount * rate)

        if converted_amount <= 0:
            return False

        if self.resources[from_type] >= amount:
            self.resources[from_type] -= amount
            self.resources[to_type] += converted_amount
            return True

        return False

    def gain_exp(self, amount: int) -> Dict[str, Any]:
        """Nhận kinh nghiệm tu luyện và kiểm tra đột phá"""
        result = {
            "exp_gained": amount,
            "breakthrough": False,
            "realm_advancement": False,
            "new_realm": self.cultivation["realm"],
            "new_level": self.cultivation["realm_level"]
        }

        # Áp dụng hệ số ngộ tính dựa trên loại căn cơ
        cultivation_type_bonus = {
            "Phàm": 1.0,
            "Linh": 1.2,
            "Thánh": 1.5,
            "Tiên": 2.0,
            "Thần": 3.0
        }

        adjusted_amount = int(amount * cultivation_type_bonus.get(self.cultivation["cultivation_type"], 1.0))
        result["exp_gained"] = adjusted_amount

        # Cộng kinh nghiệm
        self.cultivation["exp"] += adjusted_amount

        # Kiểm tra đột phá
        while self.cultivation["exp"] >= self.cultivation["max_exp"]:
            # Trừ kinh nghiệm đã dùng để đột phá
            self.cultivation["exp"] -= self.cultivation["max_exp"]

            # Tăng tiểu cảnh giới
            self.cultivation["realm_level"] += 1
            self.cultivation["breakthrough"]["count"] += 1
            self.stats_record["breakthroughs"] += 1
            result["breakthrough"] = True

            # Tăng max_exp cho lần đột phá tiếp theo
            self.cultivation["max_exp"] = int(self.cultivation["max_exp"] * 1.5)

            # Cập nhật chỉ số
            self._update_stats_after_breakthrough()

            # Kiểm tra chuyển cảnh giới
            realm_data = self._check_realm_advancement()
            if realm_data:
                self.cultivation["realm"] = realm_data["name"]
                self.cultivation["realm_level"] = 1
                self.cultivation["max_exp"] = realm_data["base_exp"]
                result["realm_advancement"] = True
                result["new_realm"] = self.cultivation["realm"]
                result["new_level"] = self.cultivation["realm_level"]

                # Cập nhật chỉ số đặc biệt khi chuyển cảnh giới
                self._update_stats_after_realm_advancement(realm_data["name"])

        return result

    def _update_stats_after_breakthrough(self) -> None:
        """Cập nhật chỉ số sau khi đột phá tiểu cảnh giới"""
        # Tăng máu và linh lực tối đa
        self.stats["max_hp"] += 20
        self.stats["hp"] = self.stats["max_hp"]
        self.stats["max_mp"] += 20
        self.stats["mp"] = self.stats["max_mp"]

        # Tăng các chỉ số khác
        self.stats["physical_power"] += 2
        self.stats["spiritual_power"] += 2
        self.stats["attack"] += 2
        self.stats["defense"] += 1
        self.stats["speed"] += 1

    def _update_stats_after_realm_advancement(self, new_realm: str) -> None:
        """Cập nhật chỉ số sau khi chuyển cảnh giới"""
        # Tăng mạnh các chỉ số khi chuyển cảnh giới
        realm_multipliers = {
            "Luyện Khí": 1.0,
            "Trúc Cơ": 1.5,
            "Kim Đan": 2.0,
            "Nguyên Anh": 3.0,
            "Hóa Thần": 5.0,
            "Luyện Hư": 8.0,
            "Hợp Thể": 12.0,
            "Đại Thừa": 20.0,
            "Độ Kiếp": 30.0,
            "Tiên Nhân": 50.0
        }

        multiplier = realm_multipliers.get(new_realm, 1.0)

        # Tăng máu và linh lực tối đa
        self.stats["max_hp"] = int(self.stats["max_hp"] * multiplier)
        self.stats["hp"] = self.stats["max_hp"]
        self.stats["max_mp"] = int(self.stats["max_mp"] * multiplier)
        self.stats["mp"] = self.stats["max_mp"]

        # Tăng các chỉ số khác
        self.stats["physical_power"] = int(self.stats["physical_power"] * multiplier)
        self.stats["spiritual_power"] = int(self.stats["spiritual_power"] * multiplier)
        self.stats["attack"] = int(self.stats["attack"] * multiplier)
        self.stats["defense"] = int(self.stats["defense"] * multiplier)
        self.stats["speed"] = int(self.stats["speed"] * multiplier)

        # Tăng dung lượng đan điền
        self.cultivation["dantian"]["capacity"] = int(self.cultivation["dantian"]["capacity"] * multiplier)

        # Tăng tài nguyên khi đạt cảnh giới mới
        bonus_stones = {
            "Trúc Cơ": 1000,
            "Kim Đan": 5000,
            "Nguyên Anh": 20000,
            "Hóa Thần": 50000,
            "Luyện Hư": 100000,
            "Hợp Thể": 500000,
            "Đại Thừa": 1000000,
            "Độ Kiếp": 5000000,
            "Tiên Nhân": 10000000
        }

        if new_realm in bonus_stones:
            self.add_spirit_stones(bonus_stones[new_realm])

    def _check_realm_advancement(self) -> Optional[Dict[str, Any]]:
        """Kiểm tra điều kiện chuyển cảnh giới"""
        realm_data = {
            "Luyện Khí": {"max_level": 9, "next": "Trúc Cơ", "base_exp": 200},
            "Trúc Cơ": {"max_level": 9, "next": "Kim Đan", "base_exp": 500},
            "Kim Đan": {"max_level": 9, "next": "Nguyên Anh", "base_exp": 1000},
            "Nguyên Anh": {"max_level": 9, "next": "Hóa Thần", "base_exp": 2000},
            "Hóa Thần": {"max_level": 9, "next": "Luyện Hư", "base_exp": 5000},
            "Luyện Hư": {"max_level": 9, "next": "Hợp Thể", "base_exp": 10000},
            "Hợp Thể": {"max_level": 9, "next": "Đại Thừa", "base_exp": 20000},
            "Đại Thừa": {"max_level": 9, "next": "Độ Kiếp", "base_exp": 50000},
            "Độ Kiếp": {"max_level": 9, "next": "Tiên Nhân", "base_exp": 100000},
            "Tiên Nhân": {"max_level": 9, "next": None, "base_exp": 200000},
        }

        current_realm = self.cultivation["realm"]
        current_level = self.cultivation["realm_level"]

        # Kiểm tra xem có phải cảnh giới cao nhất không
        if current_realm not in realm_data or realm_data[current_realm]["next"] is None:
            return None

        # Kiểm tra xem đã đạt đến tầng cao nhất của cảnh giới chưa
        if current_level > realm_data[current_realm]["max_level"]:
            next_realm = realm_data[current_realm]["next"]
            return {
                "name": next_realm,
                "base_exp": realm_data[next_realm]["base_exp"]
            }

        return None

    def attempt_breakthrough(self) -> Dict[str, Any]:
        """Thử đột phá cảnh giới"""
        result = {
            "success": False,
            "message": "",
            "tribulation": False,
            "realm_advancement": False,
            "new_realm": self.cultivation["realm"],
            "new_level": self.cultivation["realm_level"]
        }

        # Kiểm tra xem có đủ kinh nghiệm để đột phá không
        if self.cultivation["exp"] < self.cultivation["max_exp"]:
            result["message"] = "Không đủ kinh nghiệm để đột phá."
            return result

        # Kiểm tra xem có đang ở cấp cao nhất của cảnh giới không
        realm_data = {
            "Luyện Khí": {"max_level": 9, "next": "Trúc Cơ", "tribulation": False},
            "Trúc Cơ": {"max_level": 9, "next": "Kim Đan", "tribulation": False},
            "Kim Đan": {"max_level": 9, "next": "Nguyên Anh", "tribulation": True},
            "Nguyên Anh": {"max_level": 9, "next": "Hóa Thần", "tribulation": True},
            "Hóa Thần": {"max_level": 9, "next": "Luyện Hư", "tribulation": True},
            "Luyện Hư": {"max_level": 9, "next": "Hợp Thể", "tribulation": True},
            "Hợp Thể": {"max_level": 9, "next": "Đại Thừa", "tribulation": True},
            "Đại Thừa": {"max_level": 9, "next": "Độ Kiếp", "tribulation": True},
            "Độ Kiếp": {"max_level": 9, "next": "Tiên Nhân", "tribulation": True},
            "Tiên Nhân": {"max_level": 9, "next": None, "tribulation": False},
        }

        current_realm = self.cultivation["realm"]
        current_level = self.cultivation["realm_level"]

        # Cập nhật thời gian đột phá gần nhất
        self.cultivation["breakthrough"]["last_attempt"] = datetime.datetime.utcnow()

        # Nếu đang ở cấp cao nhất của cảnh giới, cần vượt qua thiên kiếp
        if current_level >= realm_data[current_realm]["max_level"] and realm_data[current_realm]["next"] is not None:
            # Kiểm tra xem cần vượt qua thiên kiếp không
            if realm_data[current_realm]["tribulation"]:
                result["tribulation"] = True

                # Tính tỷ lệ thành công dựa trên căn cơ và kinh mạch
                base_success_rate = {
                    "Phàm": 0.3,
                    "Linh": 0.5,
                    "Thánh": 0.7,
                    "Tiên": 0.85,
                    "Thần": 0.95
                }

                # Tỷ lệ cơ bản dựa trên căn cơ
                success_rate = base_success_rate.get(self.cultivation["cultivation_type"], 0.3)

                # Điều chỉnh theo chất lượng kinh mạch
                meridian_bonus = {
                    "Phàm": 0,
                    "Linh": 0.05,
                    "Thánh": 0.1,
                    "Tiên": 0.15,
                    "Thần": 0.2
                }

                success_rate += meridian_bonus.get(self.cultivation["meridians"]["quality"], 0)

                # Điều chỉnh theo số kinh mạch đã khai thông
                success_rate += (self.cultivation["meridians"]["opened"] / 12) * 0.1

                # Điều chỉnh theo căn cơ tu luyện
                success_rate += (self.cultivation["cultivation_base"] / 100) * 0.2

                # Giới hạn tỷ lệ thành công
                success_rate = min(max(success_rate, 0.1), 0.95)

                # Xác định kết quả
                import random
                if random.random() <= success_rate:
                    # Thành công vượt qua thiên kiếp
                    self.cultivation["breakthrough"]["tribulation"] += 1

                    # Chuyển cảnh giới
                    next_realm = realm_data[current_realm]["next"]
                    self.cultivation["realm"] = next_realm
                    self.cultivation["realm_level"] = 1
                    self.cultivation["exp"] = 0

                    # Cập nhật max_exp cho cảnh giới mới
                    new_base_exp = {
                        "Luyện Khí": 100,
                        "Trúc Cơ": 200,
                        "Kim Đan": 500,
                        "Nguyên Anh": 1000,
                        "Hóa Thần": 2000,
                        "Luyện Hư": 5000,
                        "Hợp Thể": 10000,
                        "Đại Thừa": 20000,
                        "Độ Kiếp": 50000,
                        "Tiên Nhân": 100000,
                    }

                    self.cultivation["max_exp"] = new_base_exp.get(next_realm, 100)

                    # Cập nhật chỉ số
                    self._update_stats_after_realm_advancement(next_realm)

                    # Cập nhật kết quả
                    result["success"] = True
                    result["realm_advancement"] = True
                    result["new_realm"] = next_realm
                    result["new_level"] = 1
                    result["message"] = f"Bạn đã vượt qua thiên kiếp và tiến vào cảnh giới {next_realm}!"
                else:
                    # Thất bại khi vượt thiên kiếp
                    self.cultivation["breakthrough"]["failed"] += 1

                    # Mất một phần kinh nghiệm
                    self.cultivation["exp"] = int(self.cultivation["exp"] * 0.7)

                    # Có thể bị thương
                    self.stats["hp"] = max(1, int(self.stats["hp"] * 0.5))

                    result["message"] = "Bạn đã thất bại khi vượt qua thiên kiếp và bị thương nặng!"
            else:
                # Không cần thiên kiếp, chuyển cảnh giới trực tiếp
                next_realm = realm_data[current_realm]["next"]
                self.cultivation["realm"] = next_realm
                self.cultivation["realm_level"] = 1
                self.cultivation["exp"] = 0

                # Cập nhật max_exp cho cảnh giới mới
                new_base_exp = {
                    "Luyện Khí": 100,
                    "Trúc Cơ": 200,
                    "Kim Đan": 500,
                    "Nguyên Anh": 1000,
                    "Hóa Thần": 2000,
                    "Luyện Hư": 5000,
                    "Hợp Thể": 10000,
                    "Đại Thừa": 20000,
                    "Độ Kiếp": 50000,
                    "Tiên Nhân": 100000,
                }

                self.cultivation["max_exp"] = new_base_exp.get(next_realm, 100)

                # Cập nhật chỉ số
                self._update_stats_after_realm_advancement(next_realm)

                # Cập nhật kết quả
                result["success"] = True
                result["realm_advancement"] = True
                result["new_realm"] = next_realm
                result["new_level"] = 1
                result["message"] = f"Bạn đã tiến vào cảnh giới {next_realm}!"
        else:
            # Đột phá tiểu cảnh giới
            self.cultivation["realm_level"] += 1
            self.cultivation["exp"] -= self.cultivation["max_exp"]
            self.cultivation["max_exp"] = int(self.cultivation["max_exp"] * 1.2)
            self.cultivation["breakthrough"]["count"] += 1

            # Cập nhật chỉ số
            self._update_stats_after_breakthrough()

            # Cập nhật kết quả
            result["success"] = True
            result["new_level"] = self.cultivation["realm_level"]
            result[
                "message"] = f"Bạn đã đột phá thành công lên {self.cultivation['realm']} cảnh {self.cultivation['realm_level']}!"

        return result

    def cultivate(self, duration_minutes: int) -> Dict[str, Any]:
        """Tu luyện trong một khoảng thời gian để nhận kinh nghiệm"""
        result = {
            "exp_gained": 0,
            "spiritual_energy": 0,
            "breakthrough": False,
            "realm_advancement": False,
            "new_realm": self.cultivation["realm"],
            "new_level": self.cultivation["realm_level"],
            "events": []
        }

        # Kiểm tra xem có đang trong thời gian hồi không
        if self.activities["cooldowns"]["cultivation"] and self.activities["cooldowns"][
            "cultivation"] > datetime.datetime.utcnow():
            result["events"].append("Bạn đang trong thời gian hồi tu luyện.")
            return result

        # Tính toán kinh nghiệm nhận được
        base_exp_per_minute = {
            "Luyện Khí": 1,
            "Trúc Cơ": 2,
            "Kim Đan": 4,
            "Nguyên Anh": 8,
            "Hóa Thần": 16,
            "Luyện Hư": 32,
            "Hợp Thể": 64,
            "Đại Thừa": 128,
            "Độ Kiếp": 256,
            "Tiên Nhân": 512,
        }

        # Lấy kinh nghiệm cơ bản theo cảnh giới
        base_exp = base_exp_per_minute.get(self.cultivation["realm"], 1)

        # Điều chỉnh theo công pháp tu luyện
        technique_bonus = 1.0
        if self.cultivation["techniques"]["cultivation"]:
            # Giả sử có hàm để lấy thông tin công pháp
            technique_info = self._get_technique_info(self.cultivation["techniques"]["cultivation"])
            technique_bonus = technique_info.get("efficiency", 1.0)

        # Điều chỉnh theo chất lượng đan điền
        dantian_bonus = {
            "Phàm": 1.0,
            "Linh": 1.2,
            "Thánh": 1.5,
            "Tiên": 2.0,
            "Thần": 3.0
        }

        # Điều chỉnh theo số kinh mạch đã khai thông
        meridian_bonus = 1.0 + (self.cultivation["meridians"]["opened"] / 12) * 0.5

        # Tính tổng kinh nghiệm
        total_exp = int(base_exp * duration_minutes * technique_bonus *
                        dantian_bonus.get(self.cultivation["dantian"]["quality"], 1.0) *
                        meridian_bonus)

        # Tính linh khí thu thập được
        spiritual_energy = int(total_exp * 0.5)

        # Cập nhật tài nguyên
        self.resources["spiritual_energy"] += spiritual_energy

        # Cập nhật thống kê
        self.stats_record["total_cultivation_time"] += duration_minutes * 60

        # Đặt thời gian hồi (1/4 thời gian tu luyện)
        cooldown_minutes = max(5, int(duration_minutes / 4))
        self.activities["cooldowns"]["cultivation"] = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=cooldown_minutes)

        # Nhận kinh nghiệm và kiểm tra đột phá
        exp_result = self.gain_exp(total_exp)

        # Cập nhật kết quả
        result["exp_gained"] = exp_result["exp_gained"]
        result["spiritual_energy"] = spiritual_energy
        result["breakthrough"] = exp_result["breakthrough"]
        result["realm_advancement"] = exp_result["realm_advancement"]
        result["new_realm"] = exp_result["new_realm"]
        result["new_level"] = exp_result["new_level"]

        # Xử lý các sự kiện ngẫu nhiên khi tu luyện
        self._handle_cultivation_events(result, duration_minutes)

        return result

    def _handle_cultivation_events(self, result: Dict[str, Any], duration_minutes: int) -> None:
        """Xử lý các sự kiện ngẫu nhiên khi tu luyện"""
        import random

        # Tỷ lệ xảy ra sự kiện (càng tu luyện lâu càng cao)
        event_chance = min(0.5, 0.1 + (duration_minutes / 120) * 0.4)

        if random.random() <= event_chance:
            # Danh sách các sự kiện có thể xảy ra
            events = [
                {"type": "insight", "chance": 0.3, "message": "Bạn đã có được một chút lĩnh ngộ về đạo pháp!"},
                {"type": "resource", "chance": 0.2,
                 "message": "Bạn đã phát hiện một ít linh thạch trong khi tu luyện!"},
                {"type": "meridian", "chance": 0.1, "message": "Một kinh mạch của bạn đã được cải thiện!"},
                {"type": "technique", "chance": 0.1, "message": "Bạn đã hiểu thêm về công pháp đang tu luyện!"},
                {"type": "danger", "chance": 0.1, "message": "Bạn gặp nguy hiểm khi tu luyện, may mắn đã thoát được!"},
                {"type": "qi_deviation", "chance": 0.05,
                 "message": "Bạn bị tẩu hỏa nhập ma! Cần thời gian để hồi phục."},
                {"type": "enlightenment", "chance": 0.05, "message": "Bạn đã có được một đại lĩnh ngộ!"},
                {"type": "treasure", "chance": 0.02, "message": "Bạn đã phát hiện một bảo vật cổ xưa!"}
            ]

            # Tính tổng tỷ lệ
            total_chance = sum(event["chance"] for event in events)

            # Chuẩn hóa tỷ lệ
            normalized_events = []
            for event in events:
                normalized_events.append({
                    "type": event["type"],
                    "chance": event["chance"] / total_chance,
                    "message": event["message"]
                })

            # Chọn một sự kiện
            rand_val = random.random()
            cumulative_chance = 0
            selected_event = None

            for event in normalized_events:
                cumulative_chance += event["chance"]
                if rand_val <= cumulative_chance:
                    selected_event = event
                    break

            if selected_event:
                # Xử lý sự kiện đã chọn
                result["events"].append(selected_event["message"])

                if selected_event["type"] == "insight":
                    # Tăng ngẫu nhiên một loại ngộ tính
                    elements = ["wood", "fire", "earth", "metal", "water", "wind", "lightning", "ice", "light", "dark",
                                "space", "time"]
                    element = random.choice(elements)
                    self.cultivation["comprehension"][element] += random.randint(1, 3)
                    result["events"].append(f"Ngộ tính {element.capitalize()} tăng!")

                elif selected_event["type"] == "resource":
                    # Nhận linh thạch ngẫu nhiên
                    stones = random.randint(10, 100) * (10 ** (
                                ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể",
                                 "Đại Thừa", "Độ Kiếp", "Tiên Nhân"].index(self.cultivation["realm"]) // 2))
                    self.add_spirit_stones(stones)
                    result["events"].append(f"Nhận được {stones} linh thạch!")

                elif selected_event["type"] == "meridian":
                    # Cải thiện kinh mạch
                    if self.cultivation["meridians"]["opened"] < 12:
                        self.cultivation["meridians"]["opened"] += 1
                        result["events"].append(
                            f"Đã khai thông thêm 1 kinh mạch! ({self.cultivation['meridians']['opened']}/12)")

                elif selected_event["type"] == "technique":
                    # Cải thiện công pháp
                    if self.cultivation["techniques"]["cultivation"]:
                        self.resources["cultivation_points"] += random.randint(1, 5)
                        result["events"].append(f"Nhận được điểm tu luyện công pháp!")

                elif selected_event["type"] == "danger":
                    # Gặp nguy hiểm, mất một ít máu
                    damage = int(self.stats["max_hp"] * 0.2)
                    self.stats["hp"] = max(1, self.stats["hp"] - damage)
                    result["events"].append(f"Mất {damage} HP do gặp nguy hiểm!")

                elif selected_event["type"] == "qi_deviation":
                    # Tẩu hỏa nhập ma, bị thương nặng và không thể tu luyện trong một thời gian
                    self.stats["hp"] = max(1, int(self.stats["hp"] * 0.5))
                    self.activities["cooldowns"]["cultivation"] = datetime.datetime.utcnow() + datetime.timedelta(
                        hours=4)
                    result["events"].append("Bạn không thể tu luyện trong 4 giờ tới!")

                elif selected_event["type"] == "enlightenment":
                    # Đại lĩnh ngộ, tăng nhiều kinh nghiệm
                    bonus_exp = int(self.cultivation["max_exp"] * 0.2)
                    exp_result = self.gain_exp(bonus_exp)
                    result["exp_gained"] += exp_result["exp_gained"]
                    result["breakthrough"] = result["breakthrough"] or exp_result["breakthrough"]
                    result["realm_advancement"] = result["realm_advancement"] or exp_result["realm_advancement"]
                    result["new_realm"] = exp_result["new_realm"]
                    result["new_level"] = exp_result["new_level"]
                    result["events"].append(f"Nhận thêm {bonus_exp} kinh nghiệm từ đại lĩnh ngộ!")

                elif selected_event["type"] == "treasure":
                    # Tìm thấy bảo vật
                    # Giả sử có một danh sách các bảo vật theo cảnh giới
                    treasures_by_realm = {
                        "Luyện Khí": ["basic_cultivation_manual", "qi_gathering_pill", "minor_spirit_stone"],
                        "Trúc Cơ": ["foundation_pill", "meridian_cleansing_pill", "low_grade_talisman"],
                        "Kim Đan": ["golden_core_pill", "spirit_gathering_stone", "mid_grade_weapon"],
                        "Nguyên Anh": ["nascent_soul_elixir", "spiritual_beast_egg", "high_grade_armor"],
                        "Hóa Thần": ["divine_transformation_pill", "immortal_spring_water", "mystic_artifact"],
                        "Luyện Hư": ["void_refining_crystal", "heavenly_scripture", "immortal_grade_weapon"],
                        "Hợp Thể": ["fusion_core", "divine_beast_blood", "celestial_artifact"],
                        "Đại Thừa": ["great_dao_fragment", "immortal_essence", "godly_weapon"],
                        "Độ Kiếp": ["tribulation_immunity_charm", "heavenly_dao_insight", "divine_artifact"],
                        "Tiên Nhân": ["immortal_fruit", "dao_heart", "primordial_artifact"]
                    }

                    realm_treasures = treasures_by_realm.get(self.cultivation["realm"], ["basic_cultivation_manual"])
                    treasure_id = random.choice(realm_treasures)
                    self.add_item(treasure_id, 1)
                    result["events"].append(f"Nhận được bảo vật: {treasure_id}!")

    def _get_technique_info(self, technique_id: str) -> Dict[str, Any]:
        """Lấy thông tin về công pháp (giả định)"""
        # Trong thực tế, bạn sẽ truy vấn từ cơ sở dữ liệu hoặc từ một bộ dữ liệu tĩnh
        # Đây chỉ là một ví dụ đơn giản
        techniques = {
            "basic_qi_cultivation": {"name": "Vận Khí Quyết", "level": 1, "efficiency": 1.0},
            "foundation_establishment": {"name": "Trúc Cơ Quyết", "level": 2, "efficiency": 1.2},
            "golden_core_formation": {"name": "Kim Đan Quyết", "level": 3, "efficiency": 1.5},
            "nascent_soul_scripture": {"name": "Nguyên Anh Kinh", "level": 4, "efficiency": 2.0},
            "divine_transformation_manual": {"name": "Hóa Thần Quyết", "level": 5, "efficiency": 2.5},
            "void_refining_art": {"name": "Luyện Hư Công", "level": 6, "efficiency": 3.0},
            "fusion_dao": {"name": "Hợp Thể Đạo", "level": 7, "efficiency": 3.5},
            "great_dao_scripture": {"name": "Đại Thừa Kinh", "level": 8, "efficiency": 4.0},
            "tribulation_crossing_art": {"name": "Độ Kiếp Công", "level": 9, "efficiency": 4.5},
            "immortal_ascension_manual": {"name": "Thăng Tiên Quyết", "level": 10, "efficiency": 5.0}
        }

        return techniques.get(technique_id, {"name": "Không xác định", "level": 0, "efficiency": 1.0})

    def open_meridian(self) -> Dict[str, Any]:
        """Khai thông kinh mạch"""
        result = {
            "success": False,
            "message": ""
        }

        # Kiểm tra xem đã khai thông hết kinh mạch chưa
        if self.cultivation["meridians"]["opened"] >= 12:
            result["message"] = "Bạn đã khai thông tất cả kinh mạch!"
            return result

        # Chi phí khai thông kinh mạch tăng theo số lượng đã khai thông
        cost = (self.cultivation["meridians"]["opened"] + 1) * 100

        # Kiểm tra xem có đủ linh thạch không
        if self.resources["spirit_stones"] < cost:
            result["message"] = f"Không đủ linh thạch! Cần {cost} linh thạch để khai thông kinh mạch tiếp theo."
            return result

        # Tính tỷ lệ thành công
        base_success_rate = 0.9 - (self.cultivation["meridians"]["opened"] * 0.05)

        # Điều chỉnh theo căn cơ
        cultivation_type_bonus = {
            "Phàm": 0,
            "Linh": 0.05,
            "Thánh": 0.1,
            "Tiên": 0.15,
            "Thần": 0.2
        }

        success_rate = base_success_rate + cultivation_type_bonus.get(self.cultivation["cultivation_type"], 0)

        # Giới hạn tỷ lệ thành công
        success_rate = min(max(success_rate, 0.1), 0.95)

        # Chi tiêu linh thạch
        self.spend_spirit_stones(cost)

        # Xác định kết quả
        import random
        if random.random() <= success_rate:
            # Thành công khai thông kinh mạch
            self.cultivation["meridians"]["opened"] += 1

            # Tăng chỉ số
            self.stats["max_hp"] += 10
            self.stats["hp"] = self.stats["max_hp"]
            self.stats["max_mp"] += 20
            self.stats["mp"] = self.stats["max_mp"]

            result["success"] = True
            result["message"] = f"Khai thông thành công kinh mạch thứ {self.cultivation['meridians']['opened']}!"
        else:
            # Thất bại
            result["message"] = "Khai thông kinh mạch thất bại! Hãy thử lại sau."

        return result

    def upgrade_dantian(self) -> Dict[str, Any]:
        """Nâng cấp đan điền"""
        result = {
            "success": False,
            "message": ""
        }

        # Chi phí nâng cấp đan điền
        quality_levels = ["Phàm", "Linh", "Thánh", "Tiên", "Thần"]
        current_quality_index = quality_levels.index(self.cultivation["dantian"]["quality"])

        # Kiểm tra xem đã đạt chất lượng cao nhất chưa
        if current_quality_index >= len(quality_levels) - 1:
            result["message"] = "Đan điền của bạn đã đạt chất lượng cao nhất!"
            return result

        # Chi phí tăng theo cấp độ hiện tại
        base_cost = 1000
        cost = base_cost * (10 ** current_quality_index)

        # Kiểm tra xem có đủ linh thạch không
        if self.resources["spirit_stones"] < cost:
            result["message"] = f"Không đủ linh thạch! Cần {cost} linh thạch để nâng cấp đan điền."
            return result

        # Tính tỷ lệ thành công
        base_success_rate = 0.8 - (current_quality_index * 0.15)

        # Điều chỉnh theo căn cơ
        cultivation_type_bonus = {
            "Phàm": 0,
            "Linh": 0.05,
            "Thánh": 0.1,
            "Tiên": 0.15,
            "Thần": 0.2
        }

        success_rate = base_success_rate + cultivation_type_bonus.get(self.cultivation["cultivation_type"], 0)

        # Giới hạn tỷ lệ thành công
        success_rate = min(max(success_rate, 0.05), 0.9)

        # Chi tiêu linh thạch
        self.spend_spirit_stones(cost)

        # Xác định kết quả
        import random
        if random.random() <= success_rate:
            # Thành công nâng cấp đan điền
            next_quality = quality_levels[current_quality_index + 1]
            self.cultivation["dantian"]["quality"] = next_quality

            # Tăng dung lượng đan điền
            self.cultivation["dantian"]["capacity"] *= 2

            # Tăng chỉ số
            self.stats["max_mp"] *= 1.5
            self.stats["mp"] = self.stats["max_mp"]
            self.stats["spiritual_power"] *= 1.2

            result["success"] = True
            result["message"] = f"Nâng cấp đan điền thành công! Chất lượng mới: {next_quality}"
        else:
            # Thất bại
            result["message"] = "Nâng cấp đan điền thất bại! Hãy thử lại sau."

        return result

    def improve_cultivation_base(self, amount: int = 1) -> Dict[str, Any]:
        """Cải thiện căn cơ tu luyện"""
        result = {
            "success": False,
            "message": "",
            "improvement": 0
        }

        # Kiểm tra xem đã đạt căn cơ tối đa chưa
        if self.cultivation["cultivation_base"] >= 100:
            result["message"] = "Căn cơ tu luyện của bạn đã đạt mức tối đa!"
            return result

        # Chi phí cải thiện căn cơ
        cost_per_point = 100 * (1 + self.cultivation["cultivation_base"] / 20)
        total_cost = int(cost_per_point * amount)

        # Kiểm tra xem có đủ linh thạch không
        if self.resources["spirit_stones"] < total_cost:
            result["message"] = f"Không đủ linh thạch! Cần {total_cost} linh thạch để cải thiện căn cơ."
            return result

        # Chi tiêu linh thạch
        self.spend_spirit_stones(total_cost)

        # Tính điểm cải thiện thực tế
        actual_improvement = min(amount, 100 - self.cultivation["cultivation_base"])
        self.cultivation["cultivation_base"] += actual_improvement

        # Kiểm tra nâng cấp loại căn cơ
        self._check_cultivation_type_upgrade()

        result["success"] = True
        result["improvement"] = actual_improvement
        result[
            "message"] = f"Đã cải thiện căn cơ tu luyện thêm {actual_improvement} điểm! Hiện tại: {self.cultivation['cultivation_base']}/100"

        return result

    def _check_cultivation_type_upgrade(self) -> None:
        """Kiểm tra và nâng cấp loại căn cơ dựa trên điểm căn cơ"""
        cultivation_types = ["Phàm", "Linh", "Thánh", "Tiên", "Thần"]
        thresholds = [0, 20, 50, 80, 95]

        for i in range(len(cultivation_types) - 1, -1, -1):
            if self.cultivation["cultivation_base"] >= thresholds[i]:
                if cultivation_types[i] != self.cultivation["cultivation_type"]:
                    self.cultivation["cultivation_type"] = cultivation_types[i]
                break

    def learn_technique(self, technique_id: str) -> Dict[str, Any]:
        """Học một công pháp mới"""
        result = {
            "success": False,
            "message": ""
        }

        # Giả định có một hàm để lấy thông tin công pháp
        technique_info = self._get_technique_info(technique_id)

        # Kiểm tra xem đã học công pháp này chưa
        for category in self.skills:
            for skill in self.skills[category]:
                if skill["skill_id"] == technique_id:
                    result["message"] = f"Bạn đã học công pháp {technique_info['name']} rồi!"
                    return result

        # Kiểm tra yêu cầu cảnh giới
        realm_levels = ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể", "Đại Thừa",
                        "Độ Kiếp", "Tiên Nhân"]
        required_realm_index = technique_info["level"] - 1
        current_realm_index = realm_levels.index(self.cultivation["realm"]) if self.cultivation[
                                                                                   "realm"] in realm_levels else -1

        if current_realm_index < required_realm_index:
            result[
                "message"] = f"Cảnh giới không đủ để học công pháp này! Yêu cầu: {realm_levels[required_realm_index]}"
            return result

        # Xác định loại công pháp
        technique_type = "cultivation"  # Mặc định là công pháp tu luyện
        if "sword" in technique_id or "saber" in technique_id:
            technique_type = "active"
        elif "body" in technique_id:
            technique_type = "passive"
        elif "alchemy" in technique_id or "talisman" in technique_id or "artifact" in technique_id:
            technique_type = "crafting"

        # Thêm công pháp vào danh sách đã học
        self.skills[technique_type].append({
            "skill_id": technique_id,
            "level": 1,
            "exp": 0
        })

        # Nếu là công pháp tu luyện và chưa có công pháp tu luyện chính, đặt làm công pháp chính
        if technique_type == "cultivation" and not self.cultivation["techniques"]["cultivation"]:
            self.cultivation["techniques"]["cultivation"] = technique_id

        result["success"] = True
        result["message"] = f"Đã học thành công công pháp {technique_info['name']}!"

        return result

    def upgrade_technique(self, technique_id: str) -> Dict[str, Any]:
        """Nâng cấp một công pháp đã học"""
        result = {
            "success": False,
            "message": ""
        }

        # Tìm công pháp trong danh sách đã học
        found = False
        technique = None
        technique_type = None

        for category in self.skills:
            for skill in self.skills[category]:
                if skill["skill_id"] == technique_id:
                    technique = skill
                    technique_type = category
                    found = True
                    break
            if found:
                break

        if not found:
            result["message"] = "Bạn chưa học công pháp này!"
            return result

        # Kiểm tra cấp độ tối đa
        if technique["level"] >= 10:
            result["message"] = "Công pháp đã đạt cấp độ tối đa!"
            return result

        # Chi phí nâng cấp
        points_cost = technique["level"] * 10

        # Kiểm tra xem có đủ điểm tu luyện không
        if self.resources["cultivation_points"] < points_cost:
            result["message"] = f"Không đủ điểm tu luyện! Cần {points_cost} điểm."
            return result

        # Chi tiêu điểm tu luyện
        self.resources["cultivation_points"] -= points_cost

        # Nâng cấp công pháp
        technique["level"] += 1
        technique["exp"] = 0

        # Nếu đạt cấp độ 10, đánh dấu là đã thông thạo
        if technique["level"] == 10:
            self.stats_record["techniques_mastered"] += 1

        result["success"] = True
        result["message"] = f"Đã nâng cấp công pháp lên cấp {technique['level']}!"

        return result

    def set_primary_element(self, element: str) -> Dict[str, Any]:
        """Đặt nguyên tố chính cho tu luyện"""
        result = {
            "success": False,
            "message": ""
        }

        valid_elements = ["wood", "fire", "earth", "metal", "water", "wind", "lightning", "ice", "light", "dark",
                          "space", "time"]

        if element not in valid_elements:
            result["message"] = "Nguyên tố không hợp lệ!"
            return result

        # Đặt nguyên tố chính
        self.cultivation["comprehension"]["primary"] = element

        # Tăng ngộ tính cho nguyên tố đó
        self.cultivation["comprehension"][element] += 5

        result["success"] = True
        result["message"] = f"Đã đặt {element.capitalize()} làm nguyên tố chính!"

        return result

    def complete_daily(self) -> Dict[str, Any]:
        """Hoàn thành điểm danh hàng ngày"""
        result = {
            "success": False,
            "message": "",
            "rewards": {}
        }

        now = datetime.datetime.utcnow()
        last_daily = self.activities["last_daily"]

        # Nếu chưa từng điểm danh hoặc đã qua ngày mới
        if last_daily is None or (now - last_daily).days >= 1:
            # Kiểm tra xem có duy trì chuỗi điểm danh không
            if last_daily is not None and (now - last_daily).days == 1:
                self.activities["daily_streak"] += 1
            else:
                self.activities["daily_streak"] = 1

            self.activities["last_daily"] = now

            # Phần thưởng cơ bản
            spirit_stones = 100 * (1 + (self.activities["daily_streak"] // 7))
            exp = 50 * (1 + (self.activities["daily_streak"] // 7))

            # Phần thưởng đặc biệt cho các mốc
            special_rewards = {}
            if self.activities["daily_streak"] % 7 == 0:  # Mỗi 7 ngày
                special_rewards["weekly_chest"] = 1
            if self.activities["daily_streak"] % 30 == 0:  # Mỗi 30 ngày
                special_rewards["monthly_chest"] = 1
            if self.activities["daily_streak"] == 100:  # 100 ngày
                special_rewards["cultivation_manual"] = 1
            if self.activities["daily_streak"] == 365:  # 365 ngày
                special_rewards["legendary_pet_egg"] = 1

            # Cộng phần thưởng
            self.add_spirit_stones(spirit_stones)
            self.gain_exp(exp)

            # Thêm vật phẩm đặc biệt
            for item_id, quantity in special_rewards.items():
                self.add_item(item_id, quantity)

            result["success"] = True
            result["message"] = f"Điểm danh thành công! Chuỗi hiện tại: {self.activities['daily_streak']} ngày"
            result["rewards"] = {
                "spirit_stones": spirit_stones,
                "exp": exp,
                **special_rewards
            }
        else:
            result["message"] = "Bạn đã điểm danh hôm nay rồi!"

        return result

    def update_last_active(self) -> None:
        """Cập nhật thời gian hoạt động cuối"""
        self.last_active = datetime.datetime.utcnow()

    def join_sect(self, sect_id: str, position: str = "Đệ Tử") -> Dict[str, Any]:
        """Gia nhập môn phái"""
        result = {
            "success": False,
            "message": ""
        }

        # Kiểm tra xem đã ở trong môn phái nào chưa
        if self.sect["sect_id"]:
            result["message"] = f"Bạn đã là thành viên của môn phái! Hãy rời khỏi môn phái hiện tại trước."
            return result

        # Gia nhập môn phái mới
        self.sect["sect_id"] = sect_id
        self.sect["join_date"] = datetime.datetime.utcnow()
        self.sect["position"] = position
        self.sect["contribution"] = 0
        self.sect["weekly_contribution"] = 0
        self.sect["missions_completed"] = 0
        self.sect["permissions"] = ["join_activities", "use_sect_facilities"]

        result["success"] = True
        result["message"] = f"Đã gia nhập môn phái thành công!"

        return result

    def leave_sect(self) -> Dict[str, Any]:
        """Rời khỏi môn phái"""
        result = {
            "success": False,
            "message": ""
        }

        # Kiểm tra xem có trong môn phái không
        if not self.sect["sect_id"]:
            result["message"] = "Bạn không thuộc môn phái nào!"
            return result

        # Kiểm tra chức vụ (không cho phép trưởng môn rời đi)
        if self.sect["position"] == "Trưởng Môn":
            result["message"] = "Trưởng môn không thể rời khỏi môn phái! Hãy chuyển giao chức vụ trước."
            return result

        # Lưu lại tên môn phái cũ để hiển thị trong thông báo
        old_sect_id = self.sect["sect_id"]

        # Rời khỏi môn phái
        self.sect["sect_id"] = None
        self.sect["join_date"] = None
        self.sect["position"] = None
        self.sect["contribution"] = 0
        self.sect["weekly_contribution"] = 0
        self.sect["missions_completed"] = 0
        self.sect["permissions"] = []

        result["success"] = True
        result["message"] = f"Đã rời khỏi môn phái thành công!"

        return result

    def contribute_to_sect(self, spirit_stones: int) -> Dict[str, Any]:
        """Đóng góp linh thạch cho môn phái"""
        result = {
            "success": False,
            "message": "",
            "contribution_gained": 0
        }

        # Kiểm tra xem có trong môn phái không
        if not self.sect["sect_id"]:
            result["message"] = "Bạn không thuộc môn phái nào!"
            return result

        # Kiểm tra số lượng linh thạch
        if spirit_stones <= 0:
            result["message"] = "Số lượng linh thạch không hợp lệ!"
            return result

        # Kiểm tra xem có đủ linh thạch không
        if self.resources["spirit_stones"] < spirit_stones:
            result["message"] = "Không đủ linh thạch!"
            return result

        # Tính điểm cống hiến (1 linh thạch = 1 điểm cống hiến)
        contribution_points = spirit_stones

        # Chi tiêu linh thạch
        self.spend_spirit_stones(spirit_stones)

        # Cộng điểm cống hiến
        self.sect["contribution"] += contribution_points
        self.sect["weekly_contribution"] += contribution_points
        self.resources["contribution"] += contribution_points

        result["success"] = True
        result["contribution_gained"] = contribution_points
        result[
            "message"] = f"Đã đóng góp {spirit_stones} linh thạch cho môn phái, nhận được {contribution_points} điểm cống hiến!"

        return result

    def add_friend(self, friend_id: int) -> Dict[str, Any]:
        """Thêm bạn bè"""
        result = {
            "success": False,
            "message": ""
        }

        # Kiểm tra xem đã là bạn bè chưa
        for friend in self.social["friends"]:
            if friend["user_id"] == friend_id:
                result["message"] = "Người này đã là bạn của bạn rồi!"
                return result

        # Thêm vào danh sách bạn bè
        self.social["friends"].append({
            "user_id": friend_id,
            "added_date": datetime.datetime.utcnow()
        })

        result["success"] = True
        result["message"] = "Đã thêm bạn thành công!"

        return result

    def remove_friend(self, friend_id: int) -> Dict[str, Any]:
        """Xóa bạn bè"""
        result = {
            "success": False,
            "message": ""
        }

        # Tìm và xóa bạn bè
        for i, friend in enumerate(self.social["friends"]):
            if friend["user_id"] == friend_id:
                self.social["friends"].pop(i)
                result["success"] = True
                result["message"] = "Đã xóa bạn thành công!"
                return result

        result["message"] = "Không tìm thấy người này trong danh sách bạn bè!"
        return result

    def add_title(self, title: str) -> None:
        """Thêm danh hiệu"""
        if title not in self.social["titles"]:
            self.social["titles"].append(title)

    def set_title(self, title: str) -> Dict[str, Any]:
        """Đặt danh hiệu hiện tại"""
        result = {
            "success": False,
            "message": ""
        }

        # Kiểm tra xem có danh hiệu này không
        if title not in self.social["titles"] and title is not None:
            result["message"] = "Bạn không có danh hiệu này!"
            return result

        # Đặt danh hiệu
        self.social["current_title"] = title

        result["success"] = True
        if title:
            result["message"] = f"Đã đặt danh hiệu '{title}'!"
        else:
            result["message"] = "Đã gỡ bỏ danh hiệu!"

        return result

    def add_achievement(self, achievement_id: str) -> None:
        """Thêm thành tựu"""
        if achievement_id not in self.social["achievements"]:
            self.social["achievements"].append(achievement_id)

    def record_monster_kill(self, monster_id: str) -> None:
        """Ghi nhận giết quái"""
        if monster_id not in self.activities["kills"]["monsters"]:
            self.activities["kills"]["monsters"][monster_id] = 1
        else:
            self.activities["kills"]["monsters"][monster_id] += 1

        self.stats_record["monster_kills_total"] += 1

    def record_boss_kill(self, boss_id: str) -> None:
        """Ghi nhận giết boss"""
        if boss_id not in self.activities["kills"]["bosses"]:
            self.activities["kills"]["bosses"][boss_id] = 1
        else:
            self.activities["kills"]["bosses"][boss_id] += 1

        self.stats_record["boss_kills_total"] += 1

    def record_pvp_result(self, win: bool) -> None:
        """Ghi nhận kết quả PvP"""
        if win:
            self.stats_record["pvp_wins"] += 1
            self.social["pvp"]["wins"] += 1
            self.social["pvp"]["streak"] += 1
            self.social["pvp"]["points"] += 10 + min(self.social["pvp"]["streak"], 5)
        else:
            self.stats_record["pvp_losses"] += 1
            self.social["pvp"]["losses"] += 1
            self.social["pvp"]["streak"] = 0
            self.social["pvp"]["points"] = max(0, self.social["pvp"]["points"] - 5)

    def record_death(self) -> None:
        """Ghi nhận cái chết"""
        self.stats_record["deaths"] += 1

        # Mất một phần kinh nghiệm
        self.cultivation["exp"] = int(self.cultivation["exp"] * 0.9)

        # Hồi máu về 10%
        self.stats["hp"] = max(1, int(self.stats["max_hp"] * 0.1))

    def heal(self, amount: int = None) -> None:
        """Hồi máu"""
        if amount is None:
            # Hồi toàn bộ máu
            self.stats["hp"] = self.stats["max_hp"]
        else:
            # Hồi một lượng cụ thể
            self.stats["hp"] = min(self.stats["max_hp"], self.stats["hp"] + amount)

    def restore_mana(self, amount: int = None) -> None:
        """Hồi linh lực"""
        if amount is None:
            # Hồi toàn bộ linh lực
            self.stats["mp"] = self.stats["max_mp"]
        else:
            # Hồi một lượng cụ thể
            self.stats["mp"] = min(self.stats["max_mp"], self.stats["mp"] + amount)

    def use_item(self, item_id: str) -> Dict[str, Any]:
        """Sử dụng vật phẩm"""
        result = {
            "success": False,
            "message": "",
            "effects": []
        }

        # Kiểm tra xem có vật phẩm không
        if not self.has_item(item_id):
            result["message"] = "Bạn không có vật phẩm này!"
            return result

        # Giả định có một hàm để lấy thông tin vật phẩm
        item_info = self._get_item_info(item_id)

        # Kiểm tra loại vật phẩm
        if item_info["type"] != "consumable":
            result["message"] = "Vật phẩm này không thể sử dụng trực tiếp!"
            return result

        # Xử lý hiệu ứng của vật phẩm
        for effect in item_info.get("effects", []):
            effect_type = effect["type"]
            effect_value = effect["value"]

            if effect_type == "heal":
                old_hp = self.stats["hp"]
                self.heal(effect_value)
                result["effects"].append(f"Hồi {self.stats['hp'] - old_hp} HP")

            elif effect_type == "restore_mana":
                old_mp = self.stats["mp"]
                self.restore_mana(effect_value)
                result["effects"].append(f"Hồi {self.stats['mp'] - old_mp} MP")

            elif effect_type == "exp":
                exp_result = self.gain_exp(effect_value)
                result["effects"].append(f"Nhận {exp_result['exp_gained']} kinh nghiệm")

                if exp_result["breakthrough"]:
                    if exp_result["realm_advancement"]:
                        result["effects"].append(
                            f"Đột phá lên {exp_result['new_realm']} cảnh {exp_result['new_level']}!")
                    else:
                        result["effects"].append(
                            f"Đột phá lên {self.cultivation['realm']} cảnh {self.cultivation['realm_level']}!")

            elif effect_type == "spirit_stones":
                self.add_spirit_stones(effect_value)
                result["effects"].append(f"Nhận {effect_value} linh thạch")

            elif effect_type == "stat_boost":
                stat = effect["stat"]
                duration = effect.get("duration", 300)  # Mặc định 5 phút

                # Tăng chỉ số tạm thời (cần thêm logic để xử lý hiệu ứng tạm thời)
                if stat in self.stats:
                    self.stats[stat] += effect_value
                    result["effects"].append(f"Tăng {stat} lên {effect_value} trong {duration} giây")

            elif effect_type == "cultivation_boost":
                # Tăng tốc độ tu luyện (cần thêm logic để xử lý hiệu ứng tạm thời)
                duration = effect.get("duration", 3600)  # Mặc định 1 giờ
                result["effects"].append(f"Tăng tốc độ tu luyện {effect_value}x trong {duration} giây")

        # Xóa vật phẩm sau khi sử dụng
        self.remove_item(item_id, 1)

        result["success"] = True
        result["message"] = f"Đã sử dụng {item_info['name']}!"

        return result

    def _get_item_info(self, item_id: str) -> Dict[str, Any]:
        """Lấy thông tin về vật phẩm (giả định)"""
        # Trong thực tế, bạn sẽ truy vấn từ cơ sở dữ liệu hoặc từ một bộ dữ liệu tĩnh
        # Đây chỉ là một ví dụ đơn giản
        items = {
            "minor_healing_pill": {
                "name": "Tiểu Hồi Linh Đan",
                "type": "consumable",
                "effects": [{"type": "heal", "value": 100}]
            },
            "minor_mana_pill": {
                "name": "Tiểu Hồi Khí Đan",
                "type": "consumable",
                "effects": [{"type": "restore_mana", "value": 100}]
            },
            "exp_pill": {
                "name": "Tăng Ngộ Đan",
                "type": "consumable",
                "effects": [{"type": "exp", "value": 50}]
            },
            "spirit_stone_pouch": {
                "name": "Túi Linh Thạch",
                "type": "consumable",
                "effects": [{"type": "spirit_stones", "value": 100}]
            },
            "strength_potion": {
                "name": "Dược Tăng Lực",
                "type": "consumable",
                "effects": [{"type": "stat_boost", "stat": "physical_power", "value": 10, "duration": 300}]
            },
            "cultivation_elixir": {
                "name": "Linh Dược Tu Luyện",
                "type": "consumable",
                "effects": [{"type": "cultivation_boost", "value": 2, "duration": 3600}]
            }
        }

        return items.get(item_id, {"name": "Không xác định", "type": "unknown", "effects": []})

    def use_item(self, item_id: str) -> Dict[str, Any]:
        """Sử dụng vật phẩm"""
        result = {
            "success": False,
            "message": "",
            "item_name": "",
            "effects": [],
            "breakthrough": False,
            "realm_advancement": False,
            "new_realm": self.cultivation["realm"],
            "new_level": self.cultivation["realm_level"]
        }

        # Kiểm tra xem có vật phẩm không
        if not self.has_item(item_id):
            result["message"] = "Bạn không có vật phẩm này!"
            return result

        # Tìm thông tin vật phẩm trong database hoặc cache
        # Giả định có một hàm để lấy thông tin vật phẩm
        item_data = self._get_item_info(item_id)

        if not item_data:
            result["message"] = f"Không tìm thấy thông tin về vật phẩm có ID: {item_id}."
            return result

        # Lưu tên vật phẩm
        result["item_name"] = item_data["name"]

        # Kiểm tra loại vật phẩm
        item_type = item_data.get("item_type", "")

        if item_type not in ["consumable", "pill", "skill_book"]:
            result["message"] = "Vật phẩm này không thể sử dụng trực tiếp."
            return result

        # Kiểm tra yêu cầu cảnh giới
        if "required_realm" in item_data and item_data["required_realm"]:
            realm_levels = ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể",
                            "Đại Thừa", "Độ Kiếp", "Tiên Nhân"]
            required_realm_index = realm_levels.index(item_data["required_realm"]) if item_data[
                                                                                          "required_realm"] in realm_levels else -1
            current_realm_index = realm_levels.index(self.cultivation["realm"]) if self.cultivation[
                                                                                       "realm"] in realm_levels else -1

            if current_realm_index < required_realm_index:
                result[
                    "message"] = f"Cảnh giới không đủ để sử dụng vật phẩm này! Yêu cầu: {item_data['required_realm']}"
                return result

        # Kiểm tra yêu cầu cấp độ
        if "required_level" in item_data and item_data["required_level"] > 0:
            if self.cultivation["realm_level"] < item_data["required_level"]:
                result["message"] = f"Cấp độ không đủ để sử dụng vật phẩm này! Yêu cầu: {item_data['required_level']}"
                return result

        # Xử lý hiệu ứng của vật phẩm
        if item_type == "consumable" or item_type == "pill":
            # Xử lý tác dụng phụ của đan dược
            if item_type == "pill":
                # Kiểm tra tỷ lệ thành công
                import random
                success_rate = item_data.get("success_rate", 100)

                if random.random() * 100 > success_rate:
                    # Thất bại khi sử dụng đan dược
                    self.remove_item(item_id, 1)
                    result["message"] = f"Sử dụng {item_data['name']} thất bại! Đan dược không phát huy tác dụng."
                    return result

                # Xử lý tác dụng phụ
                side_effects = item_data.get("side_effects", [])
                if side_effects and random.random() < 0.3:  # 30% xảy ra tác dụng phụ
                    side_effect = random.choice(side_effects)
                    result["effects"].append(f"Tác dụng phụ: {side_effect}")

                    # Áp dụng tác dụng phụ (ví dụ: giảm máu, linh lực)
                    if "giảm máu" in side_effect.lower():
                        self.stats["hp"] = max(1, int(self.stats["hp"] * 0.9))  # Giảm 10% máu
                    elif "giảm linh lực" in side_effect.lower():
                        self.stats["mp"] = max(1, int(self.stats["mp"] * 0.9))  # Giảm 10% linh lực

            # Xử lý hiệu ứng chính
            for effect in item_data.get("effects", []):
                effect_type = effect.get("type", "")
                effect_value = effect.get("value", 0)

                if effect_type == "heal":
                    old_hp = self.stats["hp"]
                    self.stats["hp"] = min(self.stats["max_hp"], self.stats["hp"] + effect_value)
                    actual_heal = self.stats["hp"] - old_hp
                    result["effects"].append(f"Hồi {actual_heal} HP")

                elif effect_type == "restore_mana":
                    old_mp = self.stats["mp"]
                    self.stats["mp"] = min(self.stats["max_mp"], self.stats["mp"] + effect_value)
                    actual_restore = self.stats["mp"] - old_mp
                    result["effects"].append(f"Hồi {actual_restore} MP")

                elif effect_type == "exp":
                    exp_result = self.gain_exp(effect_value)
                    result["effects"].append(f"Nhận {exp_result['exp_gained']} kinh nghiệm")

                    # Cập nhật thông tin đột phá
                    result["breakthrough"] = exp_result["breakthrough"]
                    result["realm_advancement"] = exp_result["realm_advancement"]
                    result["new_realm"] = exp_result["new_realm"]
                    result["new_level"] = exp_result["new_level"]

                elif effect_type == "spirit_stones":
                    self.add_spirit_stones(effect_value)
                    result["effects"].append(f"Nhận {effect_value} linh thạch")

                elif effect_type == "stat_boost":
                    stat = effect.get("stat", "")
                    duration = effect.get("duration", 300)  # Mặc định 5 phút

                    # Tăng chỉ số tạm thời (cần thêm logic để xử lý hiệu ứng tạm thời)
                    if stat in self.stats:
                        self.stats[stat] += effect_value
                        result["effects"].append(f"Tăng {stat} lên {effect_value} trong {duration // 60} phút")

                elif effect_type == "cultivation_boost":
                    # Tăng tốc độ tu luyện (cần thêm logic để xử lý hiệu ứng tạm thời)
                    duration = effect.get("duration", 3600)  # Mặc định 1 giờ
                    result["effects"].append(f"Tăng tốc độ tu luyện {effect_value}x trong {duration // 60} phút")

        elif item_type == "skill_book":
            # Học kỹ năng mới
            skill_id = item_data.get("skill_id")
            skill_name = item_data.get("skill_name", "Không xác định")
            skill_type = item_data.get("skill_type", "active")

            if not skill_id:
                result["message"] = "Sách kỹ năng không hợp lệ!"
                return result

            # Kiểm tra xem đã học kỹ năng này chưa
            for category in self.skills:
                for skill in self.skills[category]:
                    if skill["skill_id"] == skill_id:
                        result["message"] = f"Bạn đã học kỹ năng {skill_name} rồi!"
                        return result

            # Thêm kỹ năng vào danh sách đã học
            if skill_type == "cultivation":
                self.skills["cultivation"].append({
                    "skill_id": skill_id,
                    "level": 1,
                    "exp": 0
                })
                result["effects"].append(f"Học được công pháp tu luyện: {skill_name}")
            elif skill_type == "crafting":
                self.skills["crafting"].append({
                    "skill_id": skill_id,
                    "level": 1,
                    "exp": 0
                })
                result["effects"].append(f"Học được kỹ năng chế tạo: {skill_name}")
            elif skill_type == "passive":
                self.skills["passive"].append({
                    "skill_id": skill_id,
                    "level": 1,
                    "exp": 0
                })
                result["effects"].append(f"Học được kỹ năng bị động: {skill_name}")
            else:
                self.skills["active"].append({
                    "skill_id": skill_id,
                    "level": 1,
                    "exp": 0
                })
                result["effects"].append(f"Học được kỹ năng chủ động: {skill_name}")

        # Xóa vật phẩm sau khi sử dụng
        self.remove_item(item_id, 1)

        result["success"] = True
        return result

    def _get_item_info(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin vật phẩm (giả định)"""
        # Trong thực tế, bạn sẽ truy vấn từ cơ sở dữ liệu hoặc từ một bộ dữ liệu tĩnh
        # Đây chỉ là một ví dụ đơn giản
        import json
        import os

        try:
            with open(os.path.join("data", "items.json"), "r", encoding="utf-8") as f:
                items_data = json.load(f)
                if item_id in items_data:
                    return items_data[item_id]
        except Exception:
            pass

        return None
