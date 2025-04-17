import motor.motor_asyncio
import os
from dotenv import load_dotenv
import logging
from config import MONGO_DB_NAME, USERS_COLLECTION, SECTS_COLLECTION, ITEMS_COLLECTION, MONSTERS_COLLECTION

# Cấu hình logging
logger = logging.getLogger("tutien-bot.database")

# Load các biến môi trường
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')

# Biến toàn cục cho client và database
client = None
db = None

# Các collection
users_collection = None
sects_collection = None
items_collection = None
monsters_collection = None


async def connect_to_mongodb():
    """Kết nối đến MongoDB"""
    global client, db, users_collection, sects_collection, items_collection, monsters_collection

    try:
        # Tạo client MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

        # Kiểm tra kết nối
        await client.admin.command('ping')
        logger.info("Kết nối đến MongoDB thành công!")

        # Tạo/lấy database
        db = client[MONGO_DB_NAME]

        # Lấy các collection
        users_collection = db[USERS_COLLECTION]
        sects_collection = db[SECTS_COLLECTION]
        items_collection = db[ITEMS_COLLECTION]
        monsters_collection = db[MONSTERS_COLLECTION]

        # Tạo index cho các collection
        await users_collection.create_index("user_id", unique=True)
        await sects_collection.create_index("sect_id", unique=True)

        return True
    except Exception as e:
        logger.error(f"Lỗi kết nối đến MongoDB: {e}")
        return False


# USERS COLLECTION OPERATIONS
async def get_user(user_id):
    """Lấy thông tin người dùng từ database"""
    return await users_collection.find_one({"user_id": user_id})


async def create_user(user_id, username):
    """Tạo người dùng mới trong database"""
    user_data = {
        "user_id": user_id,
        "username": username,
        "realm_id": 0,  # Phàm Nhân
        "experience": 0,
        "linh_thach": 100,  # Số linh thạch ban đầu
        "health": 100,
        "attack": 10,
        "defense": 5,
        "sect_id": None,
        "inventory": [],
        "last_daily": None,
        "last_combat": None,
        "last_danhquai": None,
        "last_danhboss": None,
        "created_at": None,  # Sẽ được MongoDB tự động thêm
        "updated_at": None  # Sẽ được MongoDB tự động thêm
    }

    # Thêm người dùng vào database
    result = await users_collection.insert_one(user_data)

    # Trả về dữ liệu người dùng
    return await get_user(user_id)


async def update_user(user_id, update_data):
    """Cập nhật thông tin người dùng"""
    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def add_user_exp(user_id, exp_amount):
    """Thêm kinh nghiệm cho người dùng"""
    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"experience": exp_amount}}
    )
    return result.modified_count > 0


async def add_user_linh_thach(user_id, amount):
    """Thêm linh thạch cho người dùng"""
    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"linh_thach": amount}}
    )
    return result.modified_count > 0


async def get_user_or_create(user_id, username):
    """Lấy thông tin người dùng hoặc tạo mới nếu chưa tồn tại"""
    user = await get_user(user_id)
    if not user:
        user = await create_user(user_id, username)
    return user


# SECTS COLLECTION OPERATIONS
async def get_sect(sect_id):
    """Lấy thông tin môn phái từ database"""
    return await sects_collection.find_one({"sect_id": sect_id})


async def create_sect(owner_id, name, description):
    """Tạo môn phái mới"""
    # Tạo ID cho môn phái
    import uuid
    sect_id = str(uuid.uuid4())

    sect_data = {
        "sect_id": sect_id,
        "name": name,
        "description": description,
        "owner_id": owner_id,
        "members": [owner_id],
        "level": 1,
        "resources": 0,
        "created_at": None  # Sẽ được MongoDB tự động thêm
    }

    # Thêm môn phái vào database
    result = await sects_collection.insert_one(sect_data)

    # Cập nhật thông tin người dùng
    await update_user(owner_id, {"sect_id": sect_id})

    # Trả về dữ liệu môn phái
    return await get_sect(sect_id)


async def add_member_to_sect(sect_id, user_id):
    """Thêm thành viên vào môn phái"""
    result = await sects_collection.update_one(
        {"sect_id": sect_id},
        {"$addToSet": {"members": user_id}}
    )

    if result.modified_count > 0:
        # Cập nhật thông tin người dùng
        await update_user(user_id, {"sect_id": sect_id})
        return True
    return False


async def remove_member_from_sect(sect_id, user_id):
    """Xóa thành viên khỏi môn phái"""
    result = await sects_collection.update_one(
        {"sect_id": sect_id},
        {"$pull": {"members": user_id}}
    )

    if result.modified_count > 0:
        # Cập nhật thông tin người dùng
        await update_user(user_id, {"sect_id": None})
        return True
    return False

# Các hàm truy vấn khác có thể được thêm vào đây