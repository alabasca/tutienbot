# Cấu hình chung cho bot

# Cấu hình Discord
BOT_PREFIX = "!"
ACTIVITY_NAME = "Tu Tiên | !help"

# Cấu hình MongoDB
MONGO_DB_NAME = "tutien_bot"
USERS_COLLECTION = "users"
SECTS_COLLECTION = "sects"
ITEMS_COLLECTION = "items"
MONSTERS_COLLECTION = "monsters"

# Cấu hình hệ thống Tu Luyện
EXP_PER_MESSAGE = 1  # Kinh nghiệm nhận được từ mỗi tin nhắn
EXP_PER_MINUTE_VOICE = 2  # Kinh nghiệm nhận được mỗi phút voice chat
VOICE_CHECK_INTERVAL = 60  # Kiểm tra voice chat mỗi 60 giây

# Cấu hình hệ thống Combat
COMBAT_COOLDOWN = 1800  # 30 phút (tính bằng giây)
DANHQUAI_COOLDOWN = 600  # 10 phút (tính bằng giây)
DANHBOSS_COOLDOWN = 900  # 15 phút (tính bằng giây)

# Cấu hình phần thưởng
QUAI_MIN_REWARD = 5  # Linh thạch tối thiểu từ đánh quái
QUAI_MAX_REWARD = 20  # Linh thạch tối đa từ đánh quái
BOSS_MIN_REWARD = 50  # Linh thạch tối thiểu từ đánh boss
BOSS_MAX_REWARD = 200  # Linh thạch tối đa từ đánh boss
COMBAT_WIN_REWARD = 30  # Linh thạch khi thắng PvP

# Cấu hình điểm danh hàng ngày
DAILY_REWARD = 50  # Linh thạch nhận được khi điểm danh

# Màu sắc Embed
EMBED_COLOR = 0x3498db  # Màu xanh dương
EMBED_COLOR_SUCCESS = 0x2ecc71  # Màu xanh lá
EMBED_COLOR_ERROR = 0xe74c3c  # Màu đỏ
EMBED_COLOR_WARNING = 0xf39c12  # Màu vàng

# Một số emoji hữu ích
EMOJI_LINH_THACH = "💎"
EMOJI_EXP = "✨"
EMOJI_HEALTH = "❤️"
EMOJI_ATTACK = "⚔️"
EMOJI_DEFENSE = "🛡️"
EMOJI_LEVEL_UP = "🔼"

# Danh sách cảnh giới tu luyện
CULTIVATION_REALMS = [
    {"id": 0, "name": "Phàm Nhân", "exp_required": 0},
    # Luyện Khí (9 tầng)
    {"id": 1, "name": "Luyện Khí Tầng 1", "exp_required": 100},
    {"id": 2, "name": "Luyện Khí Tầng 2", "exp_required": 250},
    {"id": 3, "name": "Luyện Khí Tầng 3", "exp_required": 450},
    {"id": 4, "name": "Luyện Khí Tầng 4", "exp_required": 700},
    {"id": 5, "name": "Luyện Khí Tầng 5", "exp_required": 1000},
    {"id": 6, "name": "Luyện Khí Tầng 6", "exp_required": 1500},
    {"id": 7, "name": "Luyện Khí Tầng 7", "exp_required": 2100},
    {"id": 8, "name": "Luyện Khí Tầng 8", "exp_required": 3000},
    {"id": 9, "name": "Luyện Khí Tầng 9", "exp_required": 4000},
    # Trúc Cơ (3 tầng)
    {"id": 10, "name": "Trúc Cơ Sơ Kỳ", "exp_required": 6000},
    {"id": 11, "name": "Trúc Cơ Trung Kỳ", "exp_required": 9000},
    {"id": 12, "name": "Trúc Cơ Viên Mãn", "exp_required": 13000},
    # Kim Đan (3 tầng)
    {"id": 13, "name": "Kim Đan Sơ Kỳ", "exp_required": 20000},
    {"id": 14, "name": "Kim Đan Trung Kỳ", "exp_required": 30000},
    {"id": 15, "name": "Kim Đan Viên Mãn", "exp_required": 45000},
    # Nguyên Anh (3 tầng)
    {"id": 16, "name": "Nguyên Anh Sơ Kỳ", "exp_required": 70000},
    {"id": 17, "name": "Nguyên Anh Trung Kỳ", "exp_required": 100000},
    {"id": 18, "name": "Nguyên Anh Viên Mãn", "exp_required": 150000},
    # Hóa Thần (3 tầng)
    {"id": 19, "name": "Hóa Thần Sơ Kỳ", "exp_required": 230000},
    {"id": 20, "name": "Hóa Thần Trung Kỳ", "exp_required": 350000},
    {"id": 21, "name": "Hóa Thần Viên Mãn", "exp_required": 500000},
    # Luyện Hư (3 tầng)
    {"id": 22, "name": "Luyện Hư Sơ Kỳ", "exp_required": 800000},
    {"id": 23, "name": "Luyện Hư Trung Kỳ", "exp_required": 1200000},
    {"id": 24, "name": "Luyện Hư Viên Mãn", "exp_required": 1800000},
    # Đại Thừa (3 tầng)
    {"id": 25, "name": "Đại Thừa Sơ Kỳ", "exp_required": 3000000},
    {"id": 26, "name": "Đại Thừa Trung Kỳ", "exp_required": 5000000},
    {"id": 27, "name": "Đại Thừa Viên Mãn", "exp_required": 8000000},
    # Diễn Chủ Vạn Giới
    {"id": 28, "name": "Diễn Chủ Vạn Giới", "exp_required": 15000000}
]

# Hệ số sức mạnh theo cảnh giới
def get_power_multiplier(realm_id):
    base_multiplier = 1.0
    for i in range(realm_id):
        if i < 10:  # Luyện Khí
            base_multiplier += 0.2
        elif i < 13:  # Trúc Cơ
            base_multiplier += 0.5
        elif i < 16:  # Kim Đan
            base_multiplier += 1.0
        elif i < 19:  # Nguyên Anh
            base_multiplier += 2.0
        elif i < 22:  # Hóa Thần
            base_multiplier += 3.0
        elif i < 25:  # Luyện Hư
            base_multiplier += 5.0
        elif i < 28:  # Đại Thừa
            base_multiplier += 8.0
        else:  # Diễn Chủ Vạn Giới
            base_multiplier += 15.0
    return base_multiplier