import discord
from discord.ext import commands
import asyncio
from database.mongo_handler import MongoHandler
from utils.embed_utils import create_embed
from utils.text_utils import format_number


class Trading(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = MongoHandler()
        self.active_trades = {}

    @commands.command(name="trade", aliases=["giaodich"])
    async def trade(self, ctx, member: discord.Member = None):
        """Bắt đầu giao dịch với người chơi khác"""
        if not member:
            return await ctx.send("Vui lòng chỉ định người chơi để giao dịch.")

        if member.id == ctx.author.id:
            return await ctx.send("Bạn không thể giao dịch với chính mình.")

        if member.bot:
            return await ctx.send("Bạn không thể giao dịch với bot.")

        # Kiểm tra xem người chơi đã có giao dịch đang diễn ra không
        if ctx.author.id in self.active_trades or member.id in self.active_trades:
            return await ctx.send("Một trong hai người chơi đang có giao dịch đang diễn ra.")

        # Tạo ID giao dịch
        trade_id = f"{ctx.author.id}_{member.id}"

        # Tạo embed thông báo
        embed = create_embed(
            title="Yêu cầu giao dịch",
            description=f"{ctx.author.mention} muốn giao dịch với {member.mention}.\n"
                        f"{member.mention}, hãy phản hồi bằng cách nhấn nút bên dưới.",
            color=discord.Color.blue()
        )

        # Tạo các nút phản hồi
        accept_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Chấp nhận", custom_id="accept_trade")
        decline_button = discord.ui.Button(style=discord.ButtonStyle.red, label="Từ chối", custom_id="decline_trade")

        view = discord.ui.View()
        view.add_item(accept_button)
        view.add_item(decline_button)

        trade_msg = await ctx.send(embed=embed, view=view)

        # Chờ phản hồi
        try:
            def check(interaction):
                return interaction.user.id == member.id and interaction.message.id == trade_msg.id

            interaction = await self.bot.wait_for("interaction", check=check, timeout=60.0)

            if interaction.data["custom_id"] == "accept_trade":
                await self._start_trade_session(ctx, member, trade_id, trade_msg)
            else:
                await trade_msg.edit(
                    embed=create_embed(
                        title="Giao dịch bị từ chối",
                        description=f"{member.mention} đã từ chối yêu cầu giao dịch.",
                        color=discord.Color.red()
                    ),
                    view=None
                )

        except asyncio.TimeoutError:
            await trade_msg.edit(
                embed=create_embed(
                    title="Giao dịch hết hạn",
                    description="Yêu cầu giao dịch đã hết hạn.",
                    color=discord.Color.grey()
                ),
                view=None
            )

    async def _start_trade_session(self, ctx, member, trade_id, trade_msg):
        """Bắt đầu phiên giao dịch giữa hai người chơi"""
        # Khởi tạo thông tin giao dịch
        self.active_trades[ctx.author.id] = {
            "partner": member.id,
            "items": [],
            "spirit_stones": 0,
            "confirmed": False
        }

        self.active_trades[member.id] = {
            "partner": ctx.author.id,
            "items": [],
            "spirit_stones": 0,
            "confirmed": False
        }

        # Tạo embed giao dịch
        trade_embed = await self._create_trade_embed(ctx.author, member)

        # Tạo các nút điều khiển giao dịch
        add_item_button = discord.ui.Button(style=discord.ButtonStyle.blurple, label="Thêm vật phẩm",
                                            custom_id="add_item")
        add_ss_button = discord.ui.Button(style=discord.ButtonStyle.blurple, label="Thêm linh thạch",
                                          custom_id="add_ss")
        confirm_button = discord.ui.Button(style=discord.ButtonStyle.green, label="Xác nhận", custom_id="confirm")
        cancel_button = discord.ui.Button(style=discord.ButtonStyle.red, label="Hủy", custom_id="cancel")

        view = discord.ui.View()
        view.add_item(add_item_button)
        view.add_item(add_ss_button)
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await trade_msg.edit(embed=trade_embed, view=view)

        # Xử lý tương tác giao dịch
        while ctx.author.id in self.active_trades and member.id in self.active_trades:
            try:
                def check(interaction):
                    return (
                                interaction.user.id == ctx.author.id or interaction.user.id == member.id) and interaction.message.id == trade_msg.id

                interaction = await self.bot.wait_for("interaction", check=check, timeout=300.0)

                if interaction.data["custom_id"] == "add_item":
                    await self._handle_add_item(interaction, trade_msg)
                elif interaction.data["custom_id"] == "add_ss":
                    await self._handle_add_spirit_stones(interaction, trade_msg)
                elif interaction.data["custom_id"] == "confirm":
                    await self._handle_confirm(interaction, ctx.author, member, trade_msg)
                elif interaction.data["custom_id"] == "cancel":
                    await self._handle_cancel(interaction, trade_msg)
                    break

                # Cập nhật embed sau mỗi tương tác
                trade_embed = await self._create_trade_embed(ctx.author, member)
                await trade_msg.edit(embed=trade_embed, view=view)

                # Kiểm tra xem cả hai người chơi đã xác nhận chưa
                if (ctx.author.id in self.active_trades and member.id in self.active_trades and
                        self.active_trades[ctx.author.id]["confirmed"] and self.active_trades[member.id]["confirmed"]):
                    await self._complete_trade(ctx.author, member, trade_msg)
                    break

            except asyncio.TimeoutError:
                await trade_msg.edit(
                    embed=create_embed(
                        title="Giao dịch hết hạn",
                        description="Giao dịch đã hết hạn do không có hoạt động.",
                        color=discord.Color.grey()
                    ),
                    view=None
                )

                # Xóa thông tin giao dịch
                if ctx.author.id in self.active_trades:
                    del self.active_trades[ctx.author.id]
                if member.id in self.active_trades:
                    del self.active_trades[member.id]
                break

    async def _create_trade_embed(self, user1, user2):
        """Tạo embed hiển thị thông tin giao dịch"""
        embed = create_embed(
            title="Giao dịch đang diễn ra",
            description="Thêm vật phẩm hoặc linh thạch vào giao dịch và xác nhận khi hoàn tất.",
            color=discord.Color.blue()
        )

        # Thông tin giao dịch của người chơi 1
        user1_items = ""
        if not self.active_trades[user1.id]["items"]:
            user1_items = "Không có vật phẩm"
        else:
            for item in self.active_trades[user1.id]["items"]:
                user1_items += f"• {item['name']} (x{item['quantity']})\n"

        user1_ss = format_number(self.active_trades[user1.id]["spirit_stones"])
        user1_status = "✅" if self.active_trades[user1.id]["confirmed"] else "❌"

        embed.add_field(
            name=f"{user1.display_name} {user1_status}",
            value=f"**Vật phẩm:**\n{user1_items}\n**Linh thạch:** {user1_ss}",
            inline=True
        )

        # Thông tin giao dịch của người chơi 2
        user2_items = ""
        if not self.active_trades[user2.id]["items"]:
            user2_items = "Không có vật phẩm"
        else:
            for item in self.active_trades[user2.id]["items"]:
                user2_items += f"• {item['name']} (x{item['quantity']})\n"

        user2_ss = format_number(self.active_trades[user2.id]["spirit_stones"])
        user2_status = "✅" if self.active_trades[user2.id]["confirmed"] else "❌"

        embed.add_field(
            name=f"{user2.display_name} {user2_status}",
            value=f"**Vật phẩm:**\n{user2_items}\n**Linh thạch:** {user2_ss}",
            inline=True
        )

        return embed

    async def _handle_add_item(self, interaction, trade_msg):
        """Xử lý thêm vật phẩm vào giao dịch"""
        await interaction.response.send_message("Vui lòng nhập ID vật phẩm và số lượng (vd: 1 5):", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)

            # Xử lý đầu vào
            parts = msg.content.split()
            if len(parts) != 2:
                await interaction.followup.send(
                    "Định dạng không hợp lệ. Vui lòng nhập ID vật phẩm và số lượng (vd: 1 5).", ephemeral=True)
                return

            try:
                item_id = int(parts[0])
                quantity = int(parts[1])
            except ValueError:
                await interaction.followup.send("ID vật phẩm và số lượng phải là số nguyên.", ephemeral=True)
                return

            # Kiểm tra vật phẩm trong kho đồ
            user_data = await self.db.get_user(interaction.user.id)

            if not user_data or "inventory" not in user_data:
                await interaction.followup.send("Bạn không có vật phẩm nào trong kho đồ.", ephemeral=True)
                return

            # Tìm vật phẩm trong kho đồ
            item_found = False
            for inv_item in user_data["inventory"]:
                if inv_item["item_id"] == item_id:
                    item_found = True
                    if inv_item["quantity"] < quantity:
                        await interaction.followup.send(f"Bạn chỉ có {inv_item['quantity']} vật phẩm này.",
                                                        ephemeral=True)
                        return

                    # Lấy thông tin vật phẩm từ database
                    item_data = await self.db.get_item(item_id)
                    if not item_data:
                        await interaction.followup.send("Không tìm thấy thông tin vật phẩm.", ephemeral=True)
                        return

                    # Thêm vật phẩm vào giao dịch
                    self.active_trades[interaction.user.id]["items"].append({
                        "item_id": item_id,
                        "name": item_data["name"],
                        "quantity": quantity
                    })

                    # Reset trạng thái xác nhận
                    self.active_trades[interaction.user.id]["confirmed"] = False
                    partner_id = self.active_trades[interaction.user.id]["partner"]
                    if partner_id in self.active_trades:
                        self.active_trades[partner_id]["confirmed"] = False

                    await interaction.followup.send(f"Đã thêm {quantity} {item_data['name']} vào giao dịch.",
                                                    ephemeral=True)
                    break

            if not item_found:
                await interaction.followup.send("Không tìm thấy vật phẩm trong kho đồ của bạn.", ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("Hết thời gian nhập vật phẩm.", ephemeral=True)

    async def _handle_add_spirit_stones(self, interaction, trade_msg):
        """Xử lý thêm linh thạch vào giao dịch"""
        await interaction.response.send_message("Vui lòng nhập số lượng linh thạch muốn thêm:", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)

            # Xử lý đầu vào
            try:
                amount = int(msg.content)
                if amount <= 0:
                    await interaction.followup.send("Số lượng linh thạch phải lớn hơn 0.", ephemeral=True)
                    return
            except ValueError:
                await interaction.followup.send("Số lượng linh thạch phải là số nguyên.", ephemeral=True)
                return

            # Kiểm tra số dư linh thạch
            user_data = await self.db.get_user(interaction.user.id)

            if not user_data or user_data["spirit_stones"] < amount:
                await interaction.followup.send(
                    f"Bạn không đủ linh thạch. Số dư hiện tại: {format_number(user_data['spirit_stones'])}.",
                    ephemeral=True)
                return

            # Thêm linh thạch vào giao dịch
            self.active_trades[interaction.user.id]["spirit_stones"] = amount

            # Reset trạng thái xác nhận
            self.active_trades[interaction.user.id]["confirmed"] = False
            partner_id = self.active_trades[interaction.user.id]["partner"]
            if partner_id in self.active_trades:
                self.active_trades[partner_id]["confirmed"] = False

            await interaction.followup.send(f"Đã thêm {format_number(amount)} linh thạch vào giao dịch.",
                                            ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("Hết thời gian nhập số lượng linh thạch.", ephemeral=True)

    async def _handle_confirm(self, interaction, user1, user2, trade_msg):
        """Xử lý xác nhận giao dịch"""
        self.active_trades[interaction.user.id]["confirmed"] = True

        await interaction.response.send_message("Bạn đã xác nhận giao dịch.", ephemeral=True)

        # Kiểm tra xem cả hai người chơi đã xác nhận chưa
        partner_id = self.active_trades[interaction.user.id]["partner"]
        if partner_id in self.active_trades and self.active_trades[partner_id]["confirmed"]:
            await self._complete_trade(user1, user2, trade_msg)

    async def _handle_cancel(self, interaction, trade_msg):
        """Xử lý hủy giao dịch"""
        partner_id = self.active_trades[interaction.user.id]["partner"]

        # Xóa thông tin giao dịch
        if interaction.user.id in self.active_trades:
            del self.active_trades[interaction.user.id]
        if partner_id in self.active_trades:
            del self.active_trades[partner_id]

        await trade_msg.edit(
            embed=create_embed(
                title="Giao dịch đã hủy",
                description=f"{interaction.user.mention} đã hủy giao dịch.",
                color=discord.Color.red()
            ),
            view=None
        )

        await interaction.response.send_message("Bạn đã hủy giao dịch.", ephemeral=True)

    async def _complete_trade(self, user1, user2, trade_msg):
        """Hoàn tất giao dịch giữa hai người chơi"""
        # Lấy thông tin giao dịch
        user1_trade = self.active_trades[user1.id]
        user2_trade = self.active_trades[user2.id]

        # Thực hiện giao dịch
        try:
            # Cập nhật linh thạch
            await self.db.update_spirit_stones(user1.id, -user1_trade["spirit_stones"])
            await self.db.update_spirit_stones(user2.id, -user2_trade["spirit_stones"])
            await self.db.update_spirit_stones(user1.id, user2_trade["spirit_stones"])
            await self.db.update_spirit_stones(user2.id, user1_trade["spirit_stones"])

            # Cập nhật vật phẩm
            for item in user1_trade["items"]:
                await self.db.remove_item(user1.id, item["item_id"], item["quantity"])
                await self.db.add_item(user2.id, item["item_id"], item["quantity"])

            for item in user2_trade["items"]:
                await self.db.remove_item(user2.id, item["item_id"], item["quantity"])
                await self.db.add_item(user1.id, item["item_id"], item["quantity"])

            # Xóa thông tin giao dịch
            del self.active_trades[user1.id]
            del self.active_trades[user2.id]

            # Cập nhật thông báo
            await trade_msg.edit(
                embed=create_embed(
                    title="Giao dịch thành công",
                    description=f"Giao dịch giữa {user1.mention} và {user2.mention} đã hoàn tất.",
                    color=discord.Color.green()
                ),
                view=None
            )

        except Exception as e:
            # Xử lý lỗi
            await trade_msg.edit(
                embed=create_embed(
                    title="Lỗi giao dịch",
                    description=f"Đã xảy ra lỗi trong quá trình giao dịch: {str(e)}",
                    color=discord.Color.red()
                ),
                view=None
            )

            # Xóa thông tin giao dịch
            if user1.id in self.active_trades:
                del self.active_trades[user1.id]
            if user2.id in self.active_trades:
                del self.active_trades[user2.id]


def setup(bot):
    bot.add_cog(Trading(bot))
