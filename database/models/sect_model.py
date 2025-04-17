# database/models/sect_model.py
import datetime
from typing import Dict, List, Optional, Union, Any


class Sect:
    """Mô hình môn phái trong hệ thống Tu Tiên"""

    def __init__(self, sect_id: str, name: str, leader_id: int):
        # Thông tin cơ bản
        self.sect_id = sect_id
        self.name = name
        self.description = ""
        self.leader_id = leader_id
        self.created_at = datetime.datetime.utcnow()
        self.level = 1
        self.exp = 0
        self.max_exp = 1000

        # Tài nguyên
        self.resources = {
            "spirit_stones": 0,  # Linh thạch công quỹ
            "contribution_points": 0,  # Điểm cống hiến tích lũy
            "reputation": 0,  # Danh vọng môn phái
            "spiritual_energy": 0,  # Linh khí tích lũy
            "sect_materials": {}  # Nguyên liệu môn phái
        }

        # Thành viên
        self.members = []  # Danh sách ID thành viên
        self.elders = []  # Danh sách ID trưởng lão
        self.disciples = []  # Danh sách ID đệ tử
        self.applicants = []  # Danh sách ID người xin gia nhập

        # Cơ sở vật chất
        self.facilities = {
            "hall": {  # Đại điện
                "level": 1,
                "max_level": 10,
                "effects": ["Tăng số lượng thành viên tối đa"]
            },
            "treasury": {  # Kho báu
                "level": 1,
                "max_level": 10,
                "effects": ["Tăng sức chứa kho báu"]
            },
            "training_ground": {  # Bãi tập luyện
                "level": 1,
                "max_level": 10,
                "effects": ["Tăng tốc độ tu luyện"]
            },
            "alchemy_room": {  # Phòng luyện đan
                "level": 0,
                "max_level": 10,
                "effects": ["Cho phép luyện đan"]
            },
            "formation_hall": {  # Trận pháp đường
                "level": 0,
                "max_level": 10,
                "effects": ["Cho phép thiết lập trận pháp"]
            },
            "library": {  # Thư viện
                "level": 0,
                "max_level": 10,
                "effects": ["Cung cấp công pháp cơ bản"]
            },
            "spirit_field": {  # Linh điền
                "level": 0,
                "max_level": 10,
                "effects": ["Cho phép trồng linh dược"]
            },
            "beast_pavilion": {  # Linh thú các
                "level": 0,
                "max_level": 10,
                "effects": ["Cho phép nuôi linh thú"]
            },
            "defense_array": {  # Hộ phái đại trận
                "level": 0,
                "max_level": 10,
                "effects": ["Bảo vệ môn phái khỏi tấn công"]
            },
            "sect_shop": {  # Cửa hàng môn phái
                "level": 0,
                "max_level": 10,
                "effects": ["Cho phép mua bán vật phẩm đặc biệt"]
            }
        }

        # Công pháp môn phái
        self.techniques = []  # Danh sách công pháp độc quyền

        # Nhiệm vụ môn phái
        self.missions = []  # Danh sách nhiệm vụ

        # Lịch sử hoạt động
        self.activity_log = []  # Nhật ký hoạt động

        # Liên minh và kẻ thù
        self.allies = []  # Danh sách ID môn phái đồng minh
        self.enemies = []  # Danh sách ID môn phái thù địch

        # Cài đặt
        self.settings = {
            "join_requirement": {  # Yêu cầu gia nhập
                "min_realm": "Luyện Khí",  # Cảnh giới tối thiểu
                "min_level": 1,  # Cấp độ tối thiểu
                "approval_required": True  # Cần phê duyệt
            },
            "contribution_rates": {  # Tỷ lệ phân phối cống hiến
                "leader": 0.2,  # Trưởng môn
                "elders": 0.3,  # Trưởng lão
                "disciples": 0.5  # Đệ tử
            },
            "auto_accept": False,  # Tự động chấp nhận thành viên
            "public_visible": True,  # Hiển thị công khai
            "announcement": "",  # Thông báo môn phái
            "rules": ""  # Quy tắc môn phái
        }

        # Thông tin địa lý
        self.location = {
            "region": "Đông Thổ",  # Khu vực
            "coordinates": {"x": 0, "y": 0},  # Tọa độ
            "territory_size": 1,  # Kích thước lãnh thổ
            "environment": "Bình thường",  # Môi trường
            "spirit_veins": []  # Mạch linh khí
        }

        # Thống kê
        self.stats = {
            "total_members_ever": 1,  # Tổng số thành viên từng có
            "highest_level": 1,  # Cấp độ cao nhất đạt được
            "missions_completed": 0,  # Số nhiệm vụ đã hoàn thành
            "wars_won": 0,  # Số cuộc chiến thắng lợi
            "wars_lost": 0,  # Số cuộc chiến thất bại
            "treasures_found": 0,  # Số bảo vật tìm được
            "spirit_stones_earned": 0,  # Tổng linh thạch kiếm được
            "spirit_stones_spent": 0  # Tổng linh thạch đã tiêu
        }

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi đối tượng thành dictionary để lưu vào MongoDB"""
        return {
            "sect_id": self.sect_id,
            "name": self.name,
            "description": self.description,
            "leader_id": self.leader_id,
            "created_at": self.created_at,
            "level": self.level,
            "exp": self.exp,
            "max_exp": self.max_exp,
            "resources": self.resources,
            "members": self.members,
            "elders": self.elders,
            "disciples": self.disciples,
            "applicants": self.applicants,
            "facilities": self.facilities,
            "techniques": self.techniques,
            "missions": self.missions,
            "activity_log": self.activity_log,
            "allies": self.allies,
            "enemies": self.enemies,
            "settings": self.settings,
            "location": self.location,
            "stats": self.stats
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sect':
        """Tạo đối tượng Sect từ dictionary lấy từ MongoDB"""
        sect = cls(data["sect_id"], data["name"], data["leader_id"])
        sect.description = data.get("description", "")
        sect.created_at = data.get("created_at", datetime.datetime.utcnow())
        sect.level = data.get("level", 1)
        sect.exp = data.get("exp", 0)
        sect.max_exp = data.get("max_exp", 1000)
        sect.resources = data.get("resources", sect.resources)
        sect.members = data.get("members", [])
        sect.elders = data.get("elders", [])
        sect.disciples = data.get("disciples", [])
        sect.applicants = data.get("applicants", [])
        sect.facilities = data.get("facilities", sect.facilities)
        sect.techniques = data.get("techniques", [])
        sect.missions = data.get("missions", [])
        sect.activity_log = data.get("activity_log", [])
        sect.allies = data.get("allies", [])
        sect.enemies = data.get("enemies", [])
        sect.settings = data.get("settings", sect.settings)
        sect.location = data.get("location", sect.location)
        sect.stats = data.get("stats", sect.stats)
        return sect

    def add_member(self, user_id: int, position: str = "disciple") -> bool:
        """Thêm thành viên mới vào môn phái"""
        # Kiểm tra xem đã là thành viên chưa
        if user_id in self.members:
            return False

        # Thêm vào danh sách thành viên
        self.members.append(user_id)

        # Thêm vào danh sách theo chức vụ
        if position == "elder":
            self.elders.append(user_id)
        elif position == "disciple":
            self.disciples.append(user_id)
        elif position == "leader":
            self.leader_id = user_id

        # Cập nhật thống kê
        self.stats["total_members_ever"] += 1

        # Ghi log hoạt động
        self.log_activity(f"Thành viên mới {user_id} đã gia nhập môn phái với chức vụ {position}.")

        return True

    def remove_member(self, user_id: int) -> bool:
        """Xóa thành viên khỏi môn phái"""
        # Kiểm tra xem có phải là thành viên không
        if user_id not in self.members:
            return False

        # Không thể xóa trưởng môn
        if user_id == self.leader_id:
            return False

        # Xóa khỏi danh sách thành viên
        self.members.remove(user_id)

        # Xóa khỏi danh sách theo chức vụ
        if user_id in self.elders:
            self.elders.remove(user_id)
        if user_id in self.disciples:
            self.disciples.remove(user_id)

        # Ghi log hoạt động
        self.log_activity(f"Thành viên {user_id} đã rời khỏi môn phái.")

        return True

    def change_position(self, user_id: int, new_position: str) -> bool:
        """Thay đổi chức vụ của thành viên"""
        # Kiểm tra xem có phải là thành viên không
        if user_id not in self.members:
            return False

        # Xóa khỏi danh sách chức vụ cũ
        if user_id in self.elders:
            self.elders.remove(user_id)
        if user_id in self.disciples:
            self.disciples.remove(user_id)

        # Thêm vào danh sách chức vụ mới
        if new_position == "elder":
            self.elders.append(user_id)
        elif new_position == "disciple":
            self.disciples.append(user_id)
        elif new_position == "leader":
            # Nếu đổi thành trưởng môn, cần đổi trưởng môn cũ thành trưởng lão
            old_leader_id = self.leader_id
            if old_leader_id not in self.elders and old_leader_id in self.members:
                self.elders.append(old_leader_id)
            self.leader_id = user_id

        # Ghi log hoạt động
        self.log_activity(f"Thành viên {user_id} đã được thăng chức thành {new_position}.")

        return True

    def add_applicant(self, user_id: int) -> bool:
        """Thêm người xin gia nhập"""
        # Kiểm tra xem đã là thành viên hoặc đã xin gia nhập chưa
        if user_id in self.members or user_id in self.applicants:
            return False

        # Thêm vào danh sách xin gia nhập
        self.applicants.append(user_id)

        # Ghi log hoạt động
        self.log_activity(f"Người dùng {user_id} đã xin gia nhập môn phái.")

        return True

    def approve_applicant(self, user_id: int) -> bool:
        """Chấp nhận người xin gia nhập"""
        # Kiểm tra xem có trong danh sách xin gia nhập không
        if user_id not in self.applicants:
            return False

        # Xóa khỏi danh sách xin gia nhập
        self.applicants.remove(user_id)

        # Thêm vào danh sách thành viên
        return self.add_member(user_id, "disciple")

    def reject_applicant(self, user_id: int) -> bool:
        """Từ chối người xin gia nhập"""
        # Kiểm tra xem có trong danh sách xin gia nhập không
        if user_id not in self.applicants:
            return False

        # Xóa khỏi danh sách xin gia nhập
        self.applicants.remove(user_id)

        # Ghi log hoạt động
        self.log_activity(f"Đã từ chối đơn xin gia nhập của người dùng {user_id}.")

        return True

    def add_resources(self, resource_type: str, amount: int) -> bool:
        """Thêm tài nguyên vào môn phái"""
        if resource_type not in self.resources:
            return False

        self.resources[resource_type] += amount

        # Cập nhật thống kê nếu là linh thạch
        if resource_type == "spirit_stones":
            self.stats["spirit_stones_earned"] += amount

        return True

    def spend_resources(self, resource_type: str, amount: int) -> bool:
        """Chi tiêu tài nguyên của môn phái"""
        if resource_type not in self.resources:
            return False

        if self.resources[resource_type] < amount:
            return False

        self.resources[resource_type] -= amount

        # Cập nhật thống kê nếu là linh thạch
        if resource_type == "spirit_stones":
            self.stats["spirit_stones_spent"] += amount

        return True

    def upgrade_facility(self, facility_name: str) -> Dict[str, Any]:
        """Nâng cấp cơ sở vật chất"""
        result = {
            "success": False,
            "message": "",
            "cost": 0
        }

        # Kiểm tra xem có cơ sở này không
        if facility_name not in self.facilities:
            result["message"] = "Cơ sở không tồn tại."
            return result

        facility = self.facilities[facility_name]

        # Kiểm tra xem đã đạt cấp tối đa chưa
        if facility["level"] >= facility["max_level"]:
            result["message"] = "Cơ sở đã đạt cấp độ tối đa."
            return result

        # Tính chi phí nâng cấp
        base_cost = 1000
        level_multiplier = 2 ** facility["level"]
        cost = base_cost * level_multiplier

        result["cost"] = cost

        # Kiểm tra xem có đủ linh thạch không
        if self.resources["spirit_stones"] < cost:
            result["message"] = f"Không đủ linh thạch. Cần {cost} linh thạch."
            return result

        # Chi tiêu linh thạch
        self.spend_resources("spirit_stones", cost)

        # Nâng cấp cơ sở
        facility["level"] += 1

        # Ghi log hoạt động
        self.log_activity(f"Đã nâng cấp {facility_name} lên cấp {facility['level']} với chi phí {cost} linh thạch.")

        result["success"] = True
        result["message"] = f"Đã nâng cấp {facility_name} lên cấp {facility['level']}."

        return result

    def add_technique(self, technique_data: Dict[str, Any]) -> bool:
        """Thêm công pháp môn phái"""
        # Kiểm tra xem đã có công pháp này chưa
        for technique in self.techniques:
            if technique["id"] == technique_data["id"]:
                return False

        # Thêm công pháp mới
        self.techniques.append(technique_data)

        # Ghi log hoạt động
        self.log_activity(f"Đã thêm công pháp mới: {technique_data['name']}.")

        return True

    def remove_technique(self, technique_id: str) -> bool:
        """Xóa công pháp môn phái"""
        # Tìm và xóa công pháp
        for i, technique in enumerate(self.techniques):
            if technique["id"] == technique_id:
                self.techniques.pop(i)

                # Ghi log hoạt động
                self.log_activity(f"Đã xóa công pháp: {technique['name']}.")

                return True

        return False

    def add_mission(self, mission_data: Dict[str, Any]) -> bool:
        """Thêm nhiệm vụ môn phái"""
        # Thêm ID nếu chưa có
        if "id" not in mission_data:
            import uuid
            mission_data["id"] = str(uuid.uuid4())

        # Thêm thời gian tạo nếu chưa có
        if "created_at" not in mission_data:
            mission_data["created_at"] = datetime.datetime.utcnow()

        # Thêm nhiệm vụ mới
        self.missions.append(mission_data)

        # Ghi log hoạt động
        self.log_activity(f"Đã thêm nhiệm vụ mới: {mission_data['name']}.")

        return True

    def remove_mission(self, mission_id: str) -> bool:
        """Xóa nhiệm vụ môn phái"""
        # Tìm và xóa nhiệm vụ
        for i, mission in enumerate(self.missions):
            if mission["id"] == mission_id:
                self.missions.pop(i)

                # Ghi log hoạt động
                self.log_activity(f"Đã xóa nhiệm vụ: {mission['name']}.")

                return True

        return False

    def complete_mission(self, mission_id: str, user_id: int) -> Dict[str, Any]:
        """Hoàn thành nhiệm vụ môn phái"""
        result = {
            "success": False,
            "message": "",
            "rewards": {}
        }

        # Tìm nhiệm vụ
        mission = None
        for m in self.missions:
            if m["id"] == mission_id:
                mission = m
                break

        if not mission:
            result["message"] = "Nhiệm vụ không tồn tại."
            return result

        # Kiểm tra xem người dùng có phải là thành viên không
        if user_id not in self.members:
            result["message"] = "Chỉ thành viên môn phái mới có thể hoàn thành nhiệm vụ."
            return result

        # Kiểm tra xem nhiệm vụ đã hoàn thành chưa
        if "completed_by" in mission and user_id in mission["completed_by"]:
            result["message"] = "Bạn đã hoàn thành nhiệm vụ này rồi."
            return result

        # Đánh dấu nhiệm vụ đã hoàn thành
        if "completed_by" not in mission:
            mission["completed_by"] = []
        mission["completed_by"].append(user_id)

        # Cập nhật thống kê
        self.stats["missions_completed"] += 1

        # Xử lý phần thưởng
        rewards = mission.get("rewards", {})
        result["rewards"] = rewards

        # Ghi log hoạt động
        self.log_activity(f"Thành viên {user_id} đã hoàn thành nhiệm vụ: {mission['name']}.")

        result["success"] = True
        result["message"] = f"Đã hoàn thành nhiệm vụ: {mission['name']}."

        return result

    def gain_exp(self, amount: int) -> Dict[str, Any]:
        """Nhận kinh nghiệm cho môn phái và kiểm tra lên cấp"""
        result = {
            "exp_gained": amount,
            "level_up": False,
            "new_level": self.level
        }

        # Cộng kinh nghiệm
        self.exp += amount

        # Kiểm tra lên cấp
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1
            self.max_exp = int(self.max_exp * 1.5)
            result["level_up"] = True
            result["new_level"] = self.level

            # Cập nhật thống kê
            if self.level > self.stats["highest_level"]:
                self.stats["highest_level"] = self.level

            # Ghi log hoạt động
            self.log_activity(f"Môn phái đã lên cấp {self.level}!")

        return result

    def add_ally(self, sect_id: str) -> bool:
        """Thêm môn phái đồng minh"""
        # Kiểm tra xem đã là đồng minh chưa
        if sect_id in self.allies:
            return False

        # Kiểm tra xem có phải là kẻ thù không
        if sect_id in self.enemies:
            self.enemies.remove(sect_id)

        # Thêm vào danh sách đồng minh
        self.allies.append(sect_id)

        # Ghi log hoạt động
        self.log_activity(f"Đã kết minh với môn phái {sect_id}.")

        return True

    def remove_ally(self, sect_id: str) -> bool:
        """Xóa môn phái đồng minh"""
        # Kiểm tra xem có phải là đồng minh không
        if sect_id not in self.allies:
            return False

        # Xóa khỏi danh sách đồng minh
        self.allies.remove(sect_id)

        # Ghi log hoạt động
        self.log_activity(f"Đã hủy liên minh với môn phái {sect_id}.")

        return True

    def add_enemy(self, sect_id: str) -> bool:
        """Thêm môn phái thù địch"""
        # Kiểm tra xem đã là kẻ thù chưa
        if sect_id in self.enemies:
            return False

        # Kiểm tra xem có phải là đồng minh không
        if sect_id in self.allies:
            self.allies.remove(sect_id)

        # Thêm vào danh sách kẻ thù
        self.enemies.append(sect_id)

        # Ghi log hoạt động
        self.log_activity(f"Đã tuyên chiến với môn phái {sect_id}.")

        return True

    def remove_enemy(self, sect_id: str) -> bool:
        """Xóa môn phái thù địch"""
        # Kiểm tra xem có phải là kẻ thù không
        if sect_id not in self.enemies:
            return False

        # Xóa khỏi danh sách kẻ thù
        self.enemies.remove(sect_id)

        # Ghi log hoạt động
        self.log_activity(f"Đã hòa giải với môn phái {sect_id}.")

        return True

    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Cập nhật cài đặt môn phái"""
        # Cập nhật từng cài đặt
        for key, value in new_settings.items():
            if key in self.settings:
                if isinstance(self.settings[key], dict) and isinstance(value, dict):
                    # Nếu là dict, cập nhật từng giá trị con
                    for sub_key, sub_value in value.items():
                        if sub_key in self.settings[key]:
                            self.settings[key][sub_key] = sub_value
                else:
                    # Nếu không phải dict, cập nhật trực tiếp
                    self.settings[key] = value

        # Ghi log hoạt động
        self.log_activity("Đã cập nhật cài đặt môn phái.")

        return True

    def log_activity(self, message: str) -> None:
        """Ghi log hoạt động"""
        log_entry = {
            "timestamp": datetime.datetime.utcnow(),
            "message": message
        }

        # Thêm vào đầu danh sách để dễ truy xuất các log mới nhất
        self.activity_log.insert(0, log_entry)

        # Giới hạn số lượng log lưu trữ
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[:1000]

    def get_member_count(self) -> int:
        """Lấy số lượng thành viên"""
        return len(self.members)

    def get_elder_count(self) -> int:
        """Lấy số lượng trưởng lão"""
        return len(self.elders)

    def get_disciple_count(self) -> int:
        """Lấy số lượng đệ tử"""
        return len(self.disciples)

    def get_applicant_count(self) -> int:
        """Lấy số lượng người xin gia nhập"""
        return len(self.applicants)

    def get_facility_level(self, facility_name: str) -> int:
        """Lấy cấp độ của cơ sở"""
        if facility_name in self.facilities:
            return self.facilities[facility_name]["level"]
        return 0

    def get_max_members(self) -> int:
        """Lấy số lượng thành viên tối đa"""
        # Số lượng thành viên tối đa phụ thuộc vào cấp độ đại điện
        hall_level = self.facilities["hall"]["level"]
        return 20 + (hall_level - 1) * 10

    def is_member(self, user_id: int) -> bool:
        """Kiểm tra xem có phải là thành viên không"""
        return user_id in self.members

    def is_elder(self, user_id: int) -> bool:
        """Kiểm tra xem có phải là trưởng lão không"""
        return user_id in self.elders

    def is_leader(self, user_id: int) -> bool:
        """Kiểm tra xem có phải là trưởng môn không"""
        return user_id == self.leader_id

    def is_applicant(self, user_id: int) -> bool:
        """Kiểm tra xem có phải là người xin gia nhập không"""
        return user_id in self.applicants

    def can_join(self, user_realm: str, user_level: int) -> bool:
        """Kiểm tra xem có đủ điều kiện gia nhập không"""
        # Lấy yêu cầu gia nhập
        requirements = self.settings["join_requirement"]

        # Kiểm tra cảnh giới
        realm_levels = ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Hợp Thể", "Đại Thừa",
                        "Độ Kiếp", "Tiên Nhân"]
        min_realm_index = realm_levels.index(requirements["min_realm"]) if requirements[
                                                                               "min_realm"] in realm_levels else -1
        user_realm_index = realm_levels.index(user_realm) if user_realm in realm_levels else -1

        if user_realm_index < min_realm_index:
            return False

        # Kiểm tra cấp độ
        if user_level < requirements["min_level"]:
            return False

        # Kiểm tra số lượng thành viên
        if len(self.members) >= self.get_max_members():
            return False

        return True
