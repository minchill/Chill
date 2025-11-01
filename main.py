================================
PHẦN 1/10: KHỞI TẠO BOT VÀ IMPORTS CẦN THIẾT
================================
import discord
from discord.ext import commands
import asyncio
import os 
import json
import random
from gtts import gTTS 
import re 
from discord import ui 

# Định nghĩa Intents (Rất quan trọng cho Discord v2.0+)
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True        
intents.presences = True      

# Khởi tạo Bot với tiền tố CHỈ LÀ "b"
bot = commands.Bot(command_prefix=["b"], intents=intents) 

# Tên file lưu trữ dữ liệu
CURRENCY_FILE = "currency.json"
INVENTORY_FILE = "inventory.json"
PET_FILE = "pets.json"
ADMIN_FILE = "admin_list.txt"
================================
PHẦN 2/10: CẤU TRÚC DỮ LIỆU GAME (TƯƠNG TÁC, SHOP)
================================
# Cấu trúc dữ liệu cho các lệnh tương tác
INTERACT_ACTIONS = {
    "yeu": {"text": "đã bày tỏ tình yêu với", "color": discord.Color.red()},
    "hon": {"text": "đã trao một nụ hôn nồng cháy cho", "color": discord.Color.pink()},
    "om": {"text": "đã ôm thật chặt", "color": discord.Color.orange()},
    "dam": {"text": "đã đấm thật mạnh vào mặt", "color": discord.Color.dark_red()},
    "tat": {"text": "đã tát một cái đau điếng vào", "color": discord.Color.gold()},
    "chui": {"text": "đã chửi mắng thậm tệ", "color": discord.Color.dark_grey()},
    "troll": {"text": "đã troll", "color": discord.Color.blue()},
    "ngu": {"text": "cảm thấy mình thật", "color": discord.Color.light_grey(), "self_action": True},
    "khon": {"text": "cảm thấy mình thật", "color": discord.Color.green(), "self_action": True},
}

# Cấu trúc dữ liệu vật phẩm (Shop)
SHOP_ITEMS = {
    "hop_qua": { 
        "name": "Hộp Quà May Mắn", "description": "Mở ra ngẫu nhiên nhận tiền hoặc vật phẩm hiếm.",
        "price": 2000, "category": "utility"
    },
    "ve_san": { 
        "name": "Vé Đi Săn", "description": "Cần thiết để dùng lệnh bhunt.",
        "price": 800, "category": "consumable"
    },
    "ve_boss": { 
        "name": "Vé Boss", "description": "Dùng để tham gia săn boss hàng ngày.",
        "price": 5000, "category": "consumable"
    },
    "thuoc_hoi_suc": {
        "name": "Thuốc Hồi Sức", "description": "Hồi phục sức khỏe cho thú cưng.",
        "price": 1200, "category": "consumable"
    }
}

# Cấu trúc dữ liệu Pet (Shop Pet)
PET_STATS = {
    "meo_muop": {"name": "Mèo Mướp", "rarity": "Thường", "price": 10000, "hp": 10, "dmg": 2},
    "cho_alaska": {"name": "Chó Alaska", "rarity": "Hiếm", "price": 50000, "hp": 25, "dmg": 5},
    "ho_trang": {"name": "Hổ Trắng", "rarity": "Thần Thoại", "price": 100000, "hp": 50, "dmg": 10}
}
================================
PHẦN 3/10: CẤU TRÚC DỮ LIỆU MENU PHÂN TRANG (CHO DROPDOWN)
================================
# CẤU TRÚC DANH MỤC MENU (ĐỂ TẠO CÁC TRANG CỦA DROPDOWN)
MENU_CATEGORIES = {
    "home": {
        "title": "🏡 Trang Chủ | Tổng quan Bot",
        "emoji": "🏡",
        "description": "Thông tin cơ bản về bot và hướng dẫn sử dụng menu.\n**Tiền tố (Prefix) hiện tại:** `b`",
        "fields": [
            ("💰 Tiền tệ & Túi đồ", "`bcf`, `binv`", True),
            ("🎮 Game & Thú cưng", "`bhunt`, `bsleep`, `bzoo`", True),
            ("🎶 Âm nhạc & TTS", "`bplay` (hoặc `btts`), `bstop`", True),
            ("🤝 Tương tác/Emote", "`byeu`, `bhon`, `bdam`, `btat`...", True),
            ("⚙️ Tiện ích & Admin", "`bping`, `bhelp`, `baddadmin`", True),
            ("🛒 Mua sắm", "Dùng dropdown để chọn Shop.", True),
        ]
    },
    "economy": {
        "title": "💰 Danh mục Kinh Tế & Tài Chính",
        "emoji": "💵",
        "description": "Các lệnh liên quan đến tiền bạc và giao dịch.",
        "fields": [
            ("Xem Số Dư", "`bcf` hoặc `bbalance`", True),
            ("Xem Túi đồ", "`binv` hoặc `binventory`", True),
            ("Đi Săn (Game)", "`bhunt` (Cần Vé, CD: 60s)", True),
            ("Cửa hàng Vật phẩm", "Dùng dropdown để chuyển đến Item Shop.", True),
            ("Mua Vật phẩm", "`bbuy <ID> <số lượng>`", True),
            ("Hệ thống", "Đang được phát triển thêm...", True),
        ]
    },
    "item_shop": {
        "title": "🛒 Item Shop | Chợ Trời Vật Phẩm",
        "emoji": "🛍️",
        "description": f"Dùng `bbuy <ID> <số lượng>` để mua. Ví dụ: `bbuy ve_san 1`.",
    },
    "pet_shop": {
        "title": "🦁 Pet Shop | Cửa Hàng Thú Cưng",
        "emoji": "🐾",
        "description": "Các thú cưng hiện có. Lệnh mua pet (buypet) đang được xây dựng.",
    }
}
================================
PHẦN 4/10: LỆNH TƯƠNG TÁC (INTERACT) VÀ HÀM HỖ TRỢ
================================
# LỆNH TƯƠNG TÁC
@bot.command(name="yeu", aliases=["hon", "om", "dam", "tat", "chui", "troll", "ngu", "khon"])
async def interact_cmd(ctx, member: discord.Member = None):
    action = ctx.invoked_with
    details = INTERACT_ACTIONS.get(action)
    
    if details.get("self_action"):
        embed = discord.Embed(
            description=f"**{ctx.author.display_name}** {details['text']} **{action}**! 😅",
            color=details['color']
        )
        await ctx.send(embed=embed)
    elif member is None:
        await ctx.send(f"❌ Bạn cần nhắc tên thành viên (`@{action}`) để {details['text']} ai đó!")
    elif member == ctx.author:
        await ctx.send("❌ Không thể dùng lệnh tương tác với chính mình theo cách này.")
    else:
        embed = discord.Embed(
            description=f"**{ctx.author.display_name}** {details['text']} **{member.display_name}**!",
            color=details['color']
        )
        await ctx.send(embed=embed)

# HÀM KIỂM TRA URL HỢP LỆ (DÙNG CHO PHẦN 7)
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' 
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
        r'localhost|' 
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
        r'(?::\d+)?(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None
================================
PHẦN 5/10: HÀM HỖ TRỢ ĐỌC/GHI DỮ LIỆU (GAME/ADMIN)
================================
# HÀM HỖ TRỢ ADMIN
def get_admin_list():
    try:
        with open(ADMIN_FILE, "r") as f:
            return [int(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_admin_list(admin_ids):
    with open(ADMIN_FILE, "w") as f:
        for admin_id in admin_ids:
            f.write(f"{admin_id}\n")

# HÀM HỖ TRỢ GAME/KINH TẾ
def load_data(file_name):
    """Tải dữ liệu từ file JSON."""
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    return data

def save_data(data, file_name):
    """Lưu dữ liệu vào file JSON."""
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)

def ensure_user_exists(user_id):
    """Đảm bảo người dùng có số dư tiền tệ mặc định."""
    currency_data = load_data(CURRENCY_FILE)
    if str(user_id) not in currency_data:
        currency_data[str(user_id)] = 0 # Số dư ban đầu là 0
        save_data(currency_data, CURRENCY_FILE)
        ================================
PHẦN 6/10: EVENT HANDLERS VÀ LỆNH ADMIN
================================
# Event Bot đã sẵn sàng
@bot.event
async def on_ready():
    print(f'🤖 Bot đã sẵn sàng! Đăng nhập dưới tên: {bot.user.name}')
    print(f'ID Bot: {bot.user.id}')
    await bot.change_presence(activity=discord.Game(name=f"dùng bhelp"))

# Event xử lý lỗi lệnh
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Thiếu đối số:** Bạn cần cung cấp đầy đủ thông tin. Gõ `{ctx.prefix}help` để xem cú pháp.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ **Không có quyền:** Bạn không có đủ quyền hạn để sử dụng lệnh này.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ **Không tìm thấy thành viên:** Vui lòng nhắc tên thành viên hợp lệ.")
    elif isinstance(error, commands.CommandOnCooldown):
        if ctx.command.name != 'hunt':
             seconds = int(error.retry_after)
             await ctx.send(f"⏰ Bạn đang trong thời gian chờ. Thử lại sau **{seconds}** giây.")
    else:
        print(f"Lỗi: {error}") 
        await ctx.send(f"❌ Đã xảy ra lỗi không xác định: `{error}`")

# LỆNH ADMIN
@bot.command(name="addadmin")
@commands.check(lambda ctx: ctx.author == ctx.guild.owner) 
async def addadmin_cmd(ctx, member: discord.Member):
    admin_ids = get_admin_list()
    if member.id not in admin_ids:
        admin_ids.append(member.id)
        save_admin_list(admin_ids)
        await ctx.send(f"✅ Đã thêm **{member.display_name}** vào danh sách Admin bot.")
    else:
        await ctx.send(f"❌ **{member.display_name}** đã là Admin rồi.")

@bot.command(name="deladmin", aliases=["removeadmin"])
@commands.check(lambda ctx: ctx.author == ctx.guild.owner) 
async def deladmin_cmd(ctx, member: discord.Member):
    admin_ids = get_admin_list()
    if member.id in admin_ids:
        admin_ids.remove(member.id)
        save_admin_list(admin_ids)
        await ctx.send(f"✅ Đã xóa **{member.display_name}** khỏi danh sách Admin bot.")
    else:
        await ctx.send(f"❌ **{member.display_name}** không có trong danh sách Admin.")
        ================================
PHẦN 7/10: LỆNH PHÁT NHẠC (PLAY/TTS)
================================
# LỆNH PHÁT NHẠC (PLAY/TTS) - ĐÃ FIX LỖI ALIAS 'p'
@bot.command(name="play", aliases=["bplay", "btts", "Play", "Bplay", "Btts"]) 
async def play_cmd(ctx, *, source: str = None):
    """Phát nhạc hoặc đọc văn bản TTS."""
    if source is None:
        return await ctx.send(f"❌ Cú pháp: `{ctx.prefix}play <URL file âm thanh>` hoặc `{ctx.prefix}play <văn bản TTS>`.")
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("❌ Bạn phải tham gia vào kênh thoại (Voice Channel) để sử dụng lệnh này.")

    channel = ctx.author.voice.channel
    vc = ctx.voice_client
    if vc is None:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)
    if vc.is_playing():
        vc.stop()
        await asyncio.sleep(0.5)

    try:
        if is_valid_url(source) and (source.endswith(('.mp3', '.mp4', '.ogg', '.wav')) or "youtube" in source or "youtu.be" in source):
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            vc.play(discord.FFmpegPCMAudio(source, **FFMPEG_OPTIONS), after=lambda e: print('Done playing URL', e))
            await ctx.send(f"🎶 Đã bắt đầu phát nhạc từ URL: **{source}**")
        else:
            tts = gTTS(source, lang='vi')
            filename = f"tts_{ctx.author.id}.mp3"
            tts.save(filename)
            vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: print('Done playing TTS', e))
            await ctx.send(f"🗣️ Đã phát TTS: **{source}**")
            while vc.is_playing():
                await asyncio.sleep(1)
            os.remove(filename)
            
        await vc.disconnect()
    except Exception as e:
        if vc and vc.is_connected(): await vc.disconnect()
        await ctx.send(f"❌ Đã xảy ra lỗi trong quá trình phát: {e}")
        tts_filename = f"tts_{ctx.author.id}.mp3"
        if os.path.exists(tts_filename): os.remove(tts_filename)
        
# LỆNH DỪNG (STOP)
@bot.command(name="stop", aliases=["leave", "disconnect"])
async def stop_cmd(ctx):
    """Dừng phát nhạc và ngắt kết nối bot khỏi kênh thoại."""
    vc = ctx.voice_client
    if vc and vc.is_connected():
        if vc.is_playing(): vc.stop()
        await vc.disconnect()
        await ctx.send("🛑 Đã dừng phát nhạc và ngắt kết nối khỏi kênh thoại.")
    else:
        await ctx.send("❌ Bot hiện không ở trong kênh thoại nào.")
              ================================
PHẦN 8/10: HÀM HỖ TRỢ MENU VÀ LỚP VIEW (DROPDOWN/BUTTONS)
================================
# HÀM HỖ TRỢ TẠO EMBED CHO MENU PHÂN TRANG
def get_menu_embed(category_id, prefix):
    """Tạo Embed dựa trên ID danh mục."""
    
    if category_id == "item_shop":
        fields = []
        for item_id, item_details in SHOP_ITEMS.items():
            price_formatted = f"{item_details['price']:,}" 
            item_info = (f"**Giá:** {price_formatted} xu 💰\n"
                         f"**Mô tả:** {item_details['description']}")
            fields.append((f"✨ {item_details['name']} (`{item_id}`)", item_info, True))
    elif category_id == "pet_shop":
        fields = []
        for pet_id, pet_details in PET_STATS.items():
            price_formatted = f"{pet_details['price']:,}"
            pet_info = (f"**Độ hiếm:** {pet_details['rarity']}\n"
                        f"**HP/DMG:** {pet_details['hp']}/{pet_details['dmg']}")
            fields.append((f"✨ {pet_details['name']} (Giá: {price_formatted} xu)", pet_info, True))
    else:
        fields = MENU_CATEGORIES.get(category_id, MENU_CATEGORIES["home"])["fields"]
        
    category_info = MENU_CATEGORIES.get(category_id, MENU_CATEGORIES["home"])
    
    embed = discord.Embed(
        title=category_info["emoji"] + " " + category_info["title"],
        description=category_info["description"].replace("`b`", f"`{prefix}`"),
        color=discord.Color.from_rgb(47, 49, 54)
    )
    
    for name, value, inline in fields:
        embed.add_field(name=name, value=value.replace("`b`", f"`{prefix}`"), inline=inline)
        
    embed.set_footer(text=f"Được phát triển bởi Mực Team | Prefix: {prefix}")
    return embed


# LỚP VIEW (MENU TƯƠNG TÁC PHÂN TRANG)
class PaginatorSelect(discord.ui.Select):
    """Dropdown (Select Menu) để chọn danh mục lệnh."""
    def __init__(self, prefix):
        options = [
            discord.SelectOption(label="Trang Chủ (Tổng quan)", value="home", emoji="🏡"),
            discord.SelectOption(label="Kinh Tế & Tài Chính", value="economy", emoji="💵"),
            discord.SelectOption(label="Item Shop", value="item_shop", emoji="🛍️"),
            discord.SelectOption(label="Pet Shop", value="pet_shop", emoji="🦁"),
        ]
        super().__init__(placeholder="Chọn danh mục lệnh...", options=options, custom_id="category_select")
        self.prefix = prefix
        
    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        new_embed = get_menu_embed(selected_category, self.prefix)
        await interaction.response.edit_message(embed=new_embed, view=self.view)

class HelpShopView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=180) 
        self.ctx = ctx
        self.prefix = ctx.prefix
        self.message = None # Khởi tạo thuộc tính message
        
        # Thêm Dropdown (Row 0)
        self.add_item(PaginatorSelect(self.prefix))
        
        # Thêm nút bấm chuyển trang (Row 1)
        self.add_item(discord.ui.Button(label="<<", style=discord.ButtonStyle.grey, custom_id="first_page", disabled=True, row=1))
        self.add_item(discord.ui.Button(label="<", style=discord.ButtonStyle.grey, custom_id="prev_page", disabled=True, row=1))
        self.add_item(discord.ui.Button(label="Home", style=discord.ButtonStyle.blurple, custom_id="home_page", emoji="🏠", row=1)) 
        self.add_item(discord.ui.Button(label=">", style=discord.ButtonStyle.grey, custom_id="next_page", disabled=True, row=1))
        self.add_item(discord.ui.Button(label=">>", style=discord.ButtonStyle.grey, custom_id="last_page", disabled=True, row=1))
        
    async def on_timeout(self):
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"Lỗi khi xử lý timeout cho HelpShopView: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Bạn không phải là người gọi lệnh này.", ephemeral=True)
            return False
        return True
        
    @discord.ui.button(label="Home", style=discord.ButtonStyle.blurple, custom_id="home_page", emoji="🏠", row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_embed = get_menu_embed("home", self.prefix)
        await interaction.response.edit_message(embed=new_embed, view=self)
        ================================
PHẦN 9/10: LỆNH HELP VÀ KINH TẾ CƠ BẢN
================================
# LỆNH GỌI MENU TƯƠNG TÁC (THAY THẾ LỆNH HELP CŨ)
@bot.command(name="help", aliases=["commands", "h", "bhelp", "b"]) 
async def help_cmd(ctx):
    """Hiển thị menu tương tác theo danh mục."""
    embed = get_menu_embed("home", ctx.prefix)
    view = HelpShopView(ctx)
    # Gán đối tượng tin nhắn cho thuộc tính .message của View
    view.message = await ctx.send(embed=embed, view=view)

# Vô hiệu hóa lệnh shop cũ, khuyến khích dùng menu
@bot.command(name="itemshop", aliases=["shop", "sh"])
async def itemshop_cmd(ctx):
    """Vui lòng dùng lệnh bhelp và chọn Item Shop trong menu dropdown."""
    await ctx.send(f"⚠️ Vui lòng gõ **`{ctx.prefix}help`** và chọn **Item Shop** trong menu thả xuống để có trải nghiệm tốt nhất!")

@bot.command(name="shoppet", aliases=["shpt"])
async def shoppet_cmd(ctx):
    """Vui lòng dùng lệnh bhelp và chọn Pet Shop trong menu dropdown."""
    await ctx.send(f"⚠️ Vui lòng gõ **`{ctx.prefix}help`** và chọn **Pet Shop** trong menu thả xuống để có trải nghiệm tốt nhất!")


# LỆNH XEM SỐ DƯ (bcf)
@bot.command(name="cf", aliases=["balance"])
async def cf_cmd(ctx, member: discord.Member = None):
    """Xem số dư tiền tệ (cashflow) của bạn hoặc người khác."""
    if member is None: member = ctx.author
    ensure_user_exists(member.id)
    currency_data = load_data(CURRENCY_FILE)
    balance = currency_data.get(str(member.id), 0)
    
    embed = discord.Embed(
        title=f"💰 Ví Tiền của {member.display_name}",
        description=f"Số dư hiện tại: **{balance:,}** xu 🌟",
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Gõ {ctx.prefix}help và chọn Item Shop.")
    await ctx.send(embed=embed)
    ================================
PHẦN 10/10: LỆNH MUA SẮM VÀ GAME (BUY, INV, HUNT, ZOO) VÀ CHẠY BOT
================================
# LỆNH MUA VẬT PHẨM (bbuy)
@bot.command(name="buy")
async def buy_cmd(ctx, item_id: str = None, quantity: int = 1):
    """Mua một vật phẩm từ cửa hàng."""
    prefix = ctx.prefix
    if item_id is None:
        return await ctx.send(f"❌ Bạn cần chỉ rõ ID vật phẩm muốn mua. Gõ `{prefix}help` để xem ID.")
        
    item_id = item_id.lower()
    if item_id not in SHOP_ITEMS:
        return await ctx.send(f"❌ ID vật phẩm `{item_id}` không hợp lệ. Gõ `{prefix}help` để xem.")
        
    item = SHOP_ITEMS[item_id]; user_id = str(ctx.author.id)
    
    if quantity <= 0: return await ctx.send("❌ Số lượng phải lớn hơn 0.")
    price = item['price']
    
    if price <= 0: return await ctx.send("❌ Vật phẩm này hiện không thể mua được.")
        
    total_cost = price * quantity
    ensure_user_exists(user_id); currency_data = load_data(CURRENCY_FILE)
    current_balance = currency_data.get(user_id, 0)
    
    if current_balance < total_cost:
        return await ctx.send(f"❌ Bạn không đủ tiền! Bạn cần **{total_cost:,}** xu nhưng chỉ có **{current_balance:,}** xu.")
        
    # Trừ tiền và thêm vào Inventory
    currency_data[user_id] -= total_cost; save_data(currency_data, CURRENCY_FILE)
    inventory_data = load_data(INVENTORY_FILE)
    if user_id not in inventory_data: inventory_data[user_id] = {}
    inventory_data[user_id][item_id] = inventory_data[user_id].get(item_id, 0) + quantity
    save_data(inventory_data, INVENTORY_FILE)

    await ctx.send(f"✅ **{ctx.author.display_name}** đã mua thành công **{quantity}x {item['name']}** với tổng giá **{total_cost:,}** xu!")

# LỆNH TÚI ĐỒ (binv)
@bot.command(name="inv", aliases=["inventory"])
async def inv_cmd(ctx):
    """Hiển thị vật phẩm trong túi đồ của bạn."""
    user_id = str(ctx.author.id); inventory_data = load_data(INVENTORY_FILE)
    if user_id not in inventory_data or not inventory_data[user_id]:
        return await ctx.send("🎒 Túi đồ của bạn hiện đang trống trơn.")
    embed = discord.Embed(title=f"🎒 Túi Đồ của {ctx.author.display_name}", color=discord.Color.teal())
    item_list = ""
    for item_id, quantity in inventory_data[user_id].items():
        item_name = SHOP_ITEMS.get(item_id, {}).get("name", item_id)
        item_list += f"• **{item_name}**: x{quantity:,}\n"
    embed.description = item_list
    embed.set_footer(text=f"Dùng bhelp để xem cửa hàng.")
    await ctx.send(embed=embed)

# LỆNH ĐI SĂN (bhunt) - ĐÃ THÊM LOGIC TRỪ VÉ SĂN
@bot.command(name="hunt")
@commands.cooldown(1, 60, commands.BucketType.user) # Cooldown 60 giây
async def hunt_cmd(ctx):
    """Đi săn để kiếm tiền và có cơ hội bắt pet. Cần 1 Vé Đi Săn."""
    user_id = str(ctx.author.id); TICKET_ID = "ve_san"
    inventory_data = load_data(INVENTORY_FILE); user_inv = inventory_data.get(user_id, {})
    
    if user_inv.get(TICKET_ID, 0) < 1:
        hunt_cmd.reset_cooldown(ctx)
        return await ctx.send(f"❌ Bạn không có **Vé Đi Săn**! Mua vé bằng lệnh `{ctx.prefix}buy ve_san 1`.")

    # TRỪ VÉ ĐI SĂN
    user_inv[TICKET_ID] -= 1
    if user_inv[TICKET_ID] == 0: del user_inv[TICKET_ID]
    inventory_data[user_id] = user_inv; save_data(inventory_data, INVENTORY_FILE)
    
    # XỬ LÝ PHẦN THƯỞNG
    earned_money = random.randint(500, 2000)
    currency_data = load_data(CURRENCY_FILE); ensure_user_exists(user_id)
    currency_data[user_id] += earned_money; save_data(currency_data, CURRENCY_FILE)
    
    if random.randint(1, 10) == 1:
        pet_info = PET_STATS[random.choice(list(PET_STATS.keys()))]
        await ctx.send(f"🎉 **{ctx.author.display_name}** đã dùng 1 Vé Đi Săn, bắt được **{pet_info['name']}** hiếm! Kiếm được **{earned_money:,}** xu.")
    else:
        await ctx.send(f"🌾 **{ctx.author.display_name}** đã dùng 1 Vé Đi Săn, nhưng chỉ kiếm được **{earned_money:,}** xu. Thử lại sau nhé!")

@hunt_cmd.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = int(error.retry_after)
        await ctx.send(f"⏰ Bạn vừa đi săn rồi. Chờ **{seconds}** giây nữa để đi săn tiếp.")

# LỆNH NGỦ/COOLDOWN (bsleep)
@bot.command(name="sleep")
async def sleep_cmd(ctx):
    await ctx.send("😴 Lệnh `bsleep` sẽ được sử dụng để giảm cooldown cho các lệnh khác trong phiên bản hoàn chỉnh!")

# LỆNH KHO SỞ THÚ (bzoo)
@bot.command(name="zoo")
async def zoo_cmd(ctx):
    await ctx.send("🐾 Lệnh `bzoo` sẽ hiển thị danh sách thú cưng bạn sở hữu (chưa hoàn thành logic đọc dữ liệu).")

# ====================================================================
# CHẠY BOT (Dùng Token Bot của bạn)
# ====================================================================
# BẠN CẦN THAY THẾ "YOUR_BOT_TOKEN_HERE" BẰNG TOKEN BOT THỰC TẾ CỦA BẠN
# bot.run("YOUR_BOT_TOKEN_HERE")
