import re
import random
import unicodedata
from typing import List, Dict, Any, Tuple


def normalize_text(text: str) -> str:
    """Chuẩn hóa văn bản, loại bỏ dấu và chuyển sang chữ thường"""
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    return text.lower()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Cắt ngắn văn bản nếu quá dài"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_number(number: int) -> str:
    """Định dạng số có dấu phân cách hàng nghìn"""
    return f"{number:,}"


def format_time(seconds: int) -> str:
    """Định dạng thời gian từ số giây"""
    if seconds < 60:
        return f"{seconds} giây"

    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} phút {seconds} giây"

    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} giờ {minutes} phút {seconds} giây"

    days, hours = divmod(hours, 24)
    return f"{days} ngày {hours} giờ {minutes} phút {seconds} giây"


def progress_bar(current: int, total: int, length: int = 20, fill: str = "█", empty: str = "░") -> str:
    """Tạo thanh tiến trình"""
    percent = current / total
    filled_length = int(length * percent)
    bar = fill * filled_length + empty * (length - filled_length)
    percentage = int(100 * percent)
    return f"[{bar}] {percentage}%"


def generate_random_quote() -> str:
    """Tạo câu nói ngẫu nhiên về tu tiên"""
    quotes = [
        "Thiên đạo vô tình, tu tiên vô định.",
        "Đắc đạo thành tiên, vô ưu vô phiền.",
        "Thương hải tang điền, đạo tâm bất biến.",
        "Rèn tâm tu tính, đạo pháp tự nhiên.",
        "Thể ngộ thiên cơ, tâm minh lý thông.",
        "Vạn pháp quy không, đạo tâm thường tồn.",
        "Tu tiên thành tiên, cách trời một bước.",
        "Một ngày tu đạo, một ngày gần tiên.",
        "Tu thân dưỡng tính, ngộ đạo thành tiên.",
        "Thiên địa có định số, tu tiên phá thường lệ."
    ]
    return random.choice(quotes)


def realm_description(realm_id: int, realm_name: str) -> str:
    """Tạo mô tả cho cảnh giới tu luyện"""
    descriptions = {
        0: "Phàm nhân không có linh lực, tu luyện từ con số không.",
        1: "Bắt đầu tích tụ linh khí, cảm nhận được năng lượng thiên địa.",
        2: "Linh khí bắt đầu vận chuyển trong cơ thể, tăng cường thể chất.",
        3: "Linh khí thành lạc, tuần hoàn trong kinh mạch cơ bản.",
        4: "Linh khí đầy tràn, thể chất cường hóa đáng kể.",
        5: "Linh khí đã đủ sâu, bắt đầu chuyển hóa thành lạc.",
        # Các cấp độ cao hơn
        10: "Đan điền thành hình, linh khí tinh thuần, bắt đầu trúc cơ.",
        13: "Kim đan hình thành, linh khí đặc hóa, nội lực thâm hậu.",
        16: "Nguyên anh thành hình, có thể xuất du ngoài thể xác.",
        19: "Thần thức thoát phàm, bước vào cảnh giới Hóa Thần.",
        22: "Luyện hư ngưng không, có thể chạm đến mức không thời vô tận.",
        25: "Đại thừa viên mãn, lĩnh ngộ thiên đạo, thấu hiểu quy luật.",
        28: "Diễn chủ vạn giới, có thể sáng tạo và khống chế thế giới riêng."
    }

    # Tìm mô tả phù hợp hoặc tạo mô tả mặc định
    if realm_id in descriptions:
        return descriptions[realm_id]

    # Mô tả mặc định dựa trên phạm vi
    if 1 <= realm_id <= 9:  # Luyện Khí
        return f"Tu luyện {realm_name}, linh khí ngày càng tinh thuần."
    elif 10 <= realm_id <= 12:  # Trúc Cơ
        return f"Cảnh giới {realm_name}, đan điền vững chắc, linh lực dồi dào."
    elif 13 <= realm_id <= 15:  # Kim Đan
        return f"Cảnh giới {realm_name}, Kim Đan ngưng tụ, sức mạnh tăng vọt."
    elif 16 <= realm_id <= 18:  # Nguyên Anh
        return f"Cảnh giới {realm_name}, Nguyên Anh thành hình, có thể xuất hồn du ngoại."
    elif 19 <= realm_id <= 21:  # Hóa Thần
        return f"Cảnh giới {realm_name}, thần thức thoát phàm, bắt đầu chạm đến thiên đạo."
    elif 22 <= realm_id <= 24:  # Luyện Hư
        return f"Cảnh giới {realm_name}, luyện hư ngưng không, thâm nhập không gian pháp tắc."
    elif 25 <= realm_id <= 27:  # Đại Thừa
        return f"Cảnh giới {realm_name}, lĩnh ngộ thiên đạo, thấu hiểu quy luật vạn vật."
    else:
        return f"Đạt tới cảnh giới {realm_name}, sức mạnh không thể đo đếm."


def generate_battle_message(attacker: str, defender: str, damage: int, is_crit: bool = False) -> str:
    """Tạo thông báo chiến đấu ngẫu nhiên"""
    attack_messages = [
        f"{attacker} tung một đòn đánh vào {defender}, gây ra {damage} sát thương",
        f"{attacker} tấn công {defender}, gây ra {damage} sát thương",
        f"{attacker} vung kiếm về phía {defender}, gây ra {damage} sát thương",
        f"{attacker} phóng chưởng vào {defender}, gây ra {damage} sát thương",
        f"{attacker} sử dụng công pháp, gây ra {damage} sát thương cho {defender}"
    ]

    crit_messages = [
        f"{attacker} tung một đòn chí mạng vào {defender}, gây ra {damage} sát thương",
        f"{attacker} tìm thấy điểm yếu của {defender}, gây ra {damage} sát thương chí mạng",
        f"{attacker} tung đòn bí kíp, gây ra {damage} sát thương chí mạng vào {defender}",
        f"{attacker} bất ngờ đánh trúng huyệt đạo của {defender}, gây ra {damage} sát thương chí mạng",
        f"{attacker} triển khai thế công tuyệt vời, gây ra {damage} sát thương chí mạng cho {defender}"
    ]

    message = random.choice(crit_messages if is_crit else attack_messages)
    return message


def generate_cultivation_message(user: str, exp_gain: int, source: str) -> str:
    """Tạo thông báo tu luyện ngẫu nhiên"""
    messages = [
        f"{user} đã tu luyện thành công, thu được {exp_gain} điểm kinh nghiệm từ {source}",
        f"{user} cảm nhận linh khí quanh mình, tích lũy thêm {exp_gain} điểm kinh nghiệm từ {source}",
        f"{user} tĩnh tâm tu luyện, thu được {exp_gain} điểm kinh nghiệm từ {source}",
        f"{user} tâm thần hợp nhất, lĩnh ngộ được {exp_gain} điểm kinh nghiệm từ {source}",
        f"{user} vận chuyển công pháp, tích lũy thêm {exp_gain} điểm kinh nghiệm từ {source}"
    ]

    message = random.choice(messages)
    return message


def generate_breakthrough_message(user: str, old_realm: str, new_realm: str) -> str:
    """Tạo thông báo đột phá cảnh giới ngẫu nhiên"""
    messages = [
        f"Sau khoảnh khắc tĩnh tâm, {user} cảm thấy một luồng năng lượng mạnh mẽ chảy trong người. Chúc mừng, {user} đã đột phá từ {old_realm} lên {new_realm}!",
        f"Linh khí bùng nổ! {user} đã vượt qua rào cản, đột phá từ {old_realm} lên {new_realm}!",
        f"Thiên địa rung chuyển, vạn vật cúi đầu. {user} đã đột phá từ {old_realm} lên {new_realm}!",
        f"Trong khoảnh khắc ngộ đạo, {user} đã phá vỡ xiềng xích, tiến từ {old_realm} lên {new_realm}!",
        f"Ánh sáng bao phủ, linh khí hội tụ. {user} đã đột phá từ {old_realm} lên {new_realm}!"
    ]

    message = random.choice(messages)
    return message


def generate_item_description(item_type: str, item_quality: str, element: str = None) -> str:
    """Tạo mô tả vật phẩm ngẫu nhiên dựa trên loại và chất lượng"""
    # Tên các chất liệu
    materials = {
        "weapon": ["sắt", "thép", "đồng", "bạc", "vàng", "bạch kim", "hắc thiết", "huyền thiết"],
        "armor": ["vải", "da", "lông thú", "lân xà", "vảy rồng", "thiết giáp", "linh tơ", "kim loại"],
        "accessory": ["gỗ", "đá", "thủy tinh", "pha lê", "ngọc bích", "mã não", "kim cương", "cổ ngọc"],
    }

    # Tên các thuộc tính
    qualities = {
        "common": ["phổ thông", "thông thường", "tầm thường", "bình dân"],
        "uncommon": ["không phổ biến", "khá tốt", "chất lượng", "đáng chú ý"],
        "rare": ["hiếm có", "quý giá", "cao cấp", "tinh xảo"],
        "epic": ["sử thi", "tuyệt phẩm", "huyền thoại", "vô song"],
        "legendary": ["thần thánh", "chí tôn", "bất tử", "cổ xưa"]
    }

    # Các đặc tính phụ thuộc vào nguyên tố
    element_qualities = {
        "fire": ["nóng bỏng", "bùng cháy", "đốt cháy", "rực lửa"],
        "water": ["mát lạnh", "thấm nhuần", "thanh khiết", "linh động"],
        "earth": ["vững chắc", "nặng nề", "kiên cố", "bền bỉ"],
        "metal": ["sắc bén", "sáng chói", "cứng rắn", "lạnh lẽo"],
        "wood": ["sinh sôi", "dẻo dai", "linh hoạt", "tự nhiên"],
        "light": ["rạng rỡ", "tinh khiết", "chói lọi", "thanh cao"],
        "dark": ["u ám", "bí ẩn", "thâm sâu", "huyền bí"],
        "thunder": ["mạnh mẽ", "dữ dội", "bùng nổ", "nhanh nhẹn"],
        "wind": ["nhẹ nhàng", "linh hoạt", "tự do", "nhanh nhẹn"]
    }

    # Chọn các thành phần ngẫu nhiên
    material = random.choice(materials.get(item_type, ["không rõ"]))
    quality_adj = random.choice(qualities.get(item_quality, ["không rõ"]))
    element_adj = ""

    if element and element in element_qualities:
        element_adj = random.choice(element_qualities[element])
        element_desc = f", {element_adj}, toát ra khí tức {element}"
    else:
        element_desc = ""

    # Tạo mô tả dựa trên loại vật phẩm
    if item_type == "weapon":
        return f"Vũ khí {quality_adj} được chế tạo từ {material}{element_desc}."
    elif item_type == "armor":
        return f"Áo giáp {quality_adj} được làm từ {material}{element_desc}."
    elif item_type == "accessory":
        return f"Phụ kiện {quality_adj} được chế tác từ {material}{element_desc}."
    elif item_type == "consumable":
        return f"Vật phẩm tiêu hao {quality_adj}, tỏa ra năng lượng{element_desc}."
    else:
        return f"Vật phẩm {quality_adj}{element_desc}."


def generate_monster_encounter_message(player: str, monster: str, location: str = None) -> str:
    """Tạo thông báo gặp quái vật ngẫu nhiên"""
    if not location:
        locations = ["rừng rậm", "hang động", "thung lũng", "núi cao", "hẻm núi", "đầm lầy", "sa mạc", "bờ biển"]
        location = random.choice(locations)

    messages = [
        f"Trong lúc đi qua {location}, {player} đã chạm trán với {monster}!",
        f"{player} phát hiện {monster} đang ẩn nấp trong {location}!",
        f"Khi đang tu luyện tại {location}, {player} bị {monster} tấn công!",
        f"{monster} bất ngờ xuất hiện trước mặt {player} tại {location}!",
        f"Trong chuyến thám hiểm ở {location}, {player} gặp phải {monster}!"
    ]

    message = random.choice(messages)
    return message


def get_vietnamese_date() -> str:
    """Lấy ngày tháng theo định dạng tiếng Việt"""
    import datetime

    now = datetime.datetime.now()
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday = weekdays[now.weekday()]

    return f"{weekday}, ngày {now.day} tháng {now.month} năm {now.year}"