import discord
from discord.ext import commands
import asyncio
import json
import os
import logging
from dotenv import load_dotenv

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tutien-bot")

# Load các biến môi trường
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Khởi tạo bot với intent đầy đủ
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


# Tải các module
async def load_modules():
    # Core modules
    await bot.load_extension("modules.core.cultivation")
    await bot.load_extension("modules.core.combat")
    await bot.load_extension("modules.core.monster")
    await bot.load_extension("modules.core.inventory")

    # Social modules
    await bot.load_extension("modules.social.sect")

    # Activities modules
    await bot.load_extension("modules.activities.daily")

    # Utility modules
    await bot.load_extension("modules.utility.help")
    await bot.load_extension("modules.utility.error_handler")

    logger.info("Đã tải xong tất cả các module")


@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} đã kết nối đến Discord!')
    # Tạo activity cho bot
    await bot.change_presence(activity=discord.Game(name="Tu Tiên | !help"))

    # Tải modules
    await load_modules()

    # Ensure database connection
    from database.mongo_handler import connect_to_mongodb
    await connect_to_mongodb()
    logger.info("Đã kết nối đến MongoDB")


@bot.event
async def on_message(message):
    # Nếu tin nhắn từ bot, bỏ qua
    if message.author.bot:
        return

    # Sử lý kinh nghiệm từ chat
    if message.content and not message.content.startswith('!'):
        from modules.core.cultivation import add_chat_exp
        await add_chat_exp(bot, message)

    # Cho phép xử lý commands
    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member, before, after):
    # Nếu là bot, bỏ qua
    if member.bot:
        return

    # Nếu người dùng tham gia voice chat
    if before.channel is None and after.channel is not None:
        from modules.core.cultivation import start_voice_tracking
        await start_voice_tracking(bot, member, after.channel)

    # Nếu người dùng rời voice chat
    elif before.channel is not None and after.channel is None:
        from modules.core.cultivation import end_voice_tracking
        await end_voice_tracking(bot, member, before.channel)

@bot.event
async def on_monster_kill(user_id, monster_level):
    """Chuyển tiếp sự kiện giết quái vật đến các module"""
    bot.dispatch('monster_kill', user_id, monster_level)

@bot.event
async def on_item_collect(user_id, item_id, quantity):
    """Chuyển tiếp sự kiện thu thập vật phẩm đến các module"""
    bot.dispatch('item_collect', user_id, item_id, quantity)

@bot.event
async def on_cultivation(user_id, seconds):
    """Chuyển tiếp sự kiện tu luyện đến các module"""
    bot.dispatch('cultivation', user_id, seconds)

@bot.event
async def on_sect_contribution(user_id, amount):
    """Chuyển tiếp sự kiện đóng góp môn phái đến các module"""
    bot.dispatch('sect_contribution', user_id, amount)

@bot.event
async def on_pvp_win(user_id):
    """Chuyển tiếp sự kiện thắng PvP đến các module"""
    bot.dispatch('pvp_win', user_id)

# Chạy bot
if __name__ == "__main__":
    # Tạo thư mục logs nếu chưa tồn tại
    os.makedirs("logs", exist_ok=True)

    # Chạy bot
    bot.run(TOKEN)