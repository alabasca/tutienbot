import discord
from discord.ext import commands
import asyncio
from database.mongo_handler import MongoHandler
from utils.embed_utils import create_leaderboard_embed
from utils.text_utils import format_number
import config


class Rankings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = MongoHandler()

    @commands.command(name="rankings", aliases=["bxh", "bangxephang"])
    async def rankings(self, ctx, category="power", page=1):
        """Hiển thị bảng xếp hạng người chơi"""
        # Kiểm tra danh mục hợp lệ
        valid_categories = ["power", "cultivation", "spirit", "contribution", "pvp"]
        if category.lower() not in valid_categories:
            return await ctx.send(f"Danh mục không hợp lệ. Các danh mục có sẵn: {', '.join(valid_categories)}")

        # Chuyển đổi trang thành số nguyên
        try:
            page = int(page)
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        # Lấy dữ liệu xếp hạng
        leaderboard_data = await self._get_leaderboard_data(category.lower())

        # Tạo tiêu đề bảng xếp hạng
        title = self._get_leaderboard_title(category.lower())

        # Tạo embed
        embed = create_leaderboard_embed(leaderboard_data, title, page)

        # Gửi embed
        message = await ctx.send(embed=embed)

        # Thêm reaction để chuyển trang nếu có nhiều trang
        if len(leaderboard_data) > 10:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "➡️":
                        page += 1
                        if page * 10 > len(leaderboard_data):
                            page = 1
                    elif str(reaction.emoji) == "⬅️":
                        page -= 1
                        if page < 1:
                            page = (len(leaderboard_data) + 9) // 10

                    # Cập nhật embed
                    embed = create_leaderboard_embed(leaderboard_data, title, page)
                    await message.edit(embed=embed)

                    # Xóa reaction của người dùng
                    await message.remove_reaction(reaction, user)

                except asyncio.TimeoutError:
                    break

    async def _get_leaderboard_data(self, category):
        """Lấy dữ liệu xếp hạng dựa trên danh mục"""
        if category == "power":
            # Xếp hạng theo sức mạnh chiến đấu
            users = await self.db.get_all_users()
            leaderboard = []

            for user in users:
                if 'combat_power' in user:
                    leaderboard.append({
                        'user_id': user['_id'],
                        'username': user.get('username', 'Không xác định'),
                        'value': user['combat_power']
                    })

            # Sắp xếp theo sức mạnh giảm dần
            leaderboard.sort(key=lambda x: x['value'], reverse=True)
            return leaderboard

        elif category == "cultivation":
            # Xếp hạng theo cảnh giới tu luyện
            users = await self.db.get_all_users()
            leaderboard = []

            for user in users:
                if 'cultivation' in user:
                    # Tính toán giá trị xếp hạng dựa trên cảnh giới và cấp độ
                    realm_value = self._get_realm_value(user['cultivation'].get('realm', 'Phàm Nhân'))
                    stage_value = user['cultivation'].get('stage', 1)
                    progress_value = user['cultivation'].get('progress', 0) / user['cultivation'].get('max_progress',
                                                                                                      100)

                    total_value = realm_value * 1000 + stage_value * 10 + progress_value

                    leaderboard.append({
                        'user_id': user['_id'],
                        'username': user.get('username', 'Không xác định'),
                        'value': total_value,
                        'display_value': f"{user['cultivation'].get('realm', 'Phàm Nhân')} cấp {stage_value}"
                    })

            # Sắp xếp theo giá trị giảm dần
            leaderboard.sort(key=lambda x: x['value'], reverse=True)

            # Thay đổi giá trị hiển thị
            for entry in leaderboard:
                if 'display_value' in entry:
                    entry['value'] = entry['display_value']

            return leaderboard

        elif category == "spirit":
            # Xếp hạng theo số lượng linh thạch
            users = await self.db.get_all_users()
            leaderboard = []

            for user in users:
                if 'spirit_stones' in user:
                    leaderboard.append({
                        'user_id': user['_id'],
                        'username': user.get('username', 'Không xác định'),
                        'value': user['spirit_stones']
                    })

            # Sắp xếp theo số lượng linh thạch giảm dần
            leaderboard.sort(key=lambda x: x['value'], reverse=True)
            return leaderboard

        elif category == "contribution":
            # Xếp hạng theo đóng góp môn phái
            users = await self.db.get_all_users()
            leaderboard = []

            for user in users:
                if 'contribution' in user and user.get('sect', {}).get('name', 'Không có') != 'Không có':
                    leaderboard.append({
                        'user_id': user['_id'],
                        'username': user.get('username', 'Không xác định'),
                        'value': user['contribution'],
                        'sect': user.get('sect', {}).get('name', 'Không có')
                    })

            # Sắp xếp theo đóng góp giảm dần
            leaderboard.sort(key=lambda x: x['value'], reverse=True)

            # Thêm tên môn phái vào tên người dùng
            for entry in leaderboard:
                if 'sect' in entry:
                    entry['username'] = f"{entry['username']} [{entry['sect']}]"

            return leaderboard

        elif category == "pvp":
            # Xếp hạng theo thành tích PvP
            users = await self.db.get_all_users()
            leaderboard = []

            for user in users:
                if 'pvp' in user:
                    wins = user['pvp'].get('wins', 0)
                    losses = user['pvp'].get('losses', 0)
                    total = wins + losses

                    # Tính tỷ lệ thắng
                    win_rate = wins / total if total > 0 else 0

                    leaderboard.append({
                        'user_id': user['_id'],
                        'username': user.get('username', 'Không xác định'),
                        'value': wins,
                        'display_value': f"{wins}W {losses}L ({win_rate:.2%})"
                    })

            # Sắp xếp theo số trận thắng giảm dần
            leaderboard.sort(key=lambda x: x['value'], reverse=True)

            # Thay đổi giá trị hiển thị
            for entry in leaderboard:
                if 'display_value' in entry:
                    entry['value'] = entry['display_value']

            return leaderboard

        return []

    def _get_leaderboard_title(self, category):
        """Lấy tiêu đề bảng xếp hạng dựa trên danh mục"""
        if category == "power":
            return "Bảng xếp hạng Sức mạnh"
        elif category == "cultivation":
            return "Bảng xếp hạng Tu vi"
        elif category == "spirit":
            return "Bảng xếp hạng Linh thạch"
        elif category == "contribution":
            return "Bảng xếp hạng Công hiến"
        elif category == "pvp":
            return "Bảng xếp hạng PvP"
        return "Bảng xếp hạng"

    def _get_realm_value(self, realm):
        """Chuyển đổi cảnh giới thành giá trị số để so sánh"""
        realms = {
            "Phàm Nhân": 1,
            "Luyện Khí": 2,
            "Trúc Cơ": 3,
            "Kim Đan": 4,
            "Nguyên Anh": 5,
            "Hóa Thần": 6,
            "Hợp Thể": 7,
            "Đại Thừa": 8,
            "Độ Kiếp": 9,
            "Tán Tiên": 10
        }

        return realms.get(realm, 0)

    @commands.command(name="rank", aliases=["myrank", "hangcuatoi"])
    async def my_rank(self, ctx, category="power"):
        """Hiển thị thứ hạng của bản thân trong các bảng xếp hạng"""
        # Kiểm tra danh mục hợp lệ
        valid_categories = ["power", "cultivation", "spirit", "contribution", "pvp"]
        if category.lower() not in valid_categories:
            return await ctx.send(f"Danh mục không hợp lệ. Các danh mục có sẵn: {', '.join(valid_categories)}")

        # Lấy dữ liệu xếp hạng
        leaderboard_data = await self._get_leaderboard_data(category.lower())

        # Tìm thứ hạng của người dùng
        user_rank = None
        user_data = None

        for i, entry in enumerate(leaderboard_data):
            if entry['user_id'] == ctx.author.id:
                user_rank = i + 1
                user_data = entry
                break

        # Nếu không tìm thấy người dùng trong bảng xếp hạng
        if user_rank is None:
            return await ctx.send(
                f"Bạn chưa có thứ hạng trong bảng xếp hạng {self._get_leaderboard_title(category.lower())}.")

        # Tạo embed hiển thị thứ hạng
        embed = discord.Embed(
            title=f"Thứ hạng của {ctx.author.display_name}",
            description=f"Trong {self._get_leaderboard_title(category.lower())}",
            color=discord.Color.blue()
        )

        # Thêm thông tin thứ hạng
        embed.add_field(
            name="Thứ hạng",
            value=f"#{user_rank}/{len(leaderboard_data)}",
            inline=True
        )

        # Thêm giá trị
        value_display = user_data['value']
        if isinstance(value_display, (int, float)) and not isinstance(value_display, str):
            value_display = format_number(value_display)

        embed.add_field(
            name=self._get_category_name(category.lower()),
            value=value_display,
            inline=True
        )

        # Thêm thông tin người chơi xung quanh
        nearby_players = ""

        # Lấy 2 người chơi trên và 2 người chơi dưới
        start_idx = max(0, user_rank - 3)
        end_idx = min(len(leaderboard_data), user_rank + 2)

        for i in range(start_idx, end_idx):
            entry = leaderboard_data[i]
            rank = i + 1

            # Định dạng giá trị
            value_display = entry['value']
            if isinstance(value_display, (int, float)) and not isinstance(value_display, str):
                value_display = format_number(value_display)

            # Đánh dấu người dùng hiện tại
            if rank == user_rank:
                nearby_players += f"**#{rank}. {entry['username']} - {value_display}**\n"
            else:
                nearby_players += f"#{rank}. {entry['username']} - {value_display}\n"

        embed.add_field(
            name="Xếp hạng xung quanh",
            value=nearby_players if nearby_players else "Không có dữ liệu",
            inline=False
        )

        # Thêm gợi ý
        embed.set_footer(text=f"Sử dụng lệnh 'rankings {category}' để xem bảng xếp hạng đầy đủ")

        await ctx.send(embed=embed)

    def _get_category_name(self, category):
        """Lấy tên hiển thị của danh mục"""
        if category == "power":
            return "Sức mạnh"
        elif category == "cultivation":
            return "Tu vi"
        elif category == "spirit":
            return "Linh thạch"
        elif category == "contribution":
            return "Công hiến"
        elif category == "pvp":
            return "Thành tích PvP"
        return "Giá trị"

    @commands.command(name="sectrank", aliases=["bangxephangmonphai"])
    async def sect_rank(self, ctx, page=1):
        """Hiển thị bảng xếp hạng môn phái"""
        # Chuyển đổi trang thành số nguyên
        try:
            page = int(page)
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        # Lấy dữ liệu xếp hạng môn phái
        leaderboard_data = await self._get_sect_leaderboard()

        # Tạo embed
        embed = create_leaderboard_embed(leaderboard_data, "Bảng xếp hạng Môn phái", page)

        # Gửi embed
        message = await ctx.send(embed=embed)

        # Thêm reaction để chuyển trang nếu có nhiều trang
        if len(leaderboard_data) > 10:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "➡️":
                        page += 1
                        if page * 10 > len(leaderboard_data):
                            page = 1
                    elif str(reaction.emoji) == "⬅️":
                        page -= 1
                        if page < 1:
                            page = (len(leaderboard_data) + 9) // 10

                    # Cập nhật embed
                    embed = create_leaderboard_embed(leaderboard_data, "Bảng xếp hạng Môn phái", page)
                    await message.edit(embed=embed)

                    # Xóa reaction của người dùng
                    await message.remove_reaction(reaction, user)

                except asyncio.TimeoutError:
                    break

    async def _get_sect_leaderboard(self):
        """Lấy dữ liệu xếp hạng môn phái"""
        # Lấy tất cả môn phái
        sects = await self.db.get_all_sects()
        leaderboard = []

        for sect in sects:
            # Tính tổng sức mạnh của môn phái
            total_power = 0
            member_count = 0

            # Lấy danh sách thành viên
            members = sect.get('members', [])
            for member_id in members:
                user = await self.db.get_user(member_id)
                if user:
                    total_power += user.get('combat_power', 0)
                    member_count += 1

            # Thêm vào danh sách xếp hạng
            leaderboard.append({
                'sect_id': sect['_id'],
                'username': sect.get('name', 'Không xác định'),
                'value': total_power,
                'display_value': f"{format_number(total_power)} ({member_count} thành viên)"
            })

        # Sắp xếp theo sức mạnh giảm dần
        leaderboard.sort(key=lambda x: x['value'], reverse=True)

        # Thay đổi giá trị hiển thị
        for entry in leaderboard:
            if 'display_value' in entry:
                entry['value'] = entry['display_value']

        return leaderboard


def setup(bot):
    bot.add_cog(Rankings(bot))
