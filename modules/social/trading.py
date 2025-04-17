# modules/social/trading.py
import discord
from discord.ext import commands
import asyncio
import datetime
import logging
from typing import Dict, List, Optional, Union, Any

from database.mongo_handler import MongoHandler
from database.models.user_model import User
from utils.embed_utils import create_embed, create_success_embed, create_error_embed
from utils.text_utils import format_number

# Cấu hình logging
logger = logging.getLogger("tutien-bot.trading")


class TradingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mongo_handler = MongoHandler()
        self.items_cache = {}
        self.load_items_data()

        # Lưu trữ các giao dịch đang diễn ra
        # {trade_id: {
        #   "initiator": user_id,
        #   "
