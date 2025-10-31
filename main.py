# ====================================================================
# PHẦN 1: KHỞI TẠO VÀ CẤU HÌNH CƠ BẢN
# ====================================================================
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from gtts import gTTS
import asyncio
import random
import time
import json
import os

# Cấu hình Intents
intents = discord.Intents.default()
intents.message_content = True 

# Khởi tạo Bot và Tiền tố
bot = commands.Bot(command_prefix="b", intents=intents, help_command=None)

# Biến toàn cục để lưu trữ data
FILE_USERS = "users_data.json"
FILE_GLOBAL = "global_data.json"
users = {}
global_data = {}
anime_list = [] # Config Anime từ Railway
custom_graphics = {} # Config Đồ họa từ Railway

# TOKEN của Bot - LẤY TỪ BIẾN MÔI TRƯỜNG HOẶC ĐIỀN VÀO ĐÂY!
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR_DISCORD_TOKEN_HERE" 
# ====================================================================
# PHẦN 2: CẤU HÌNH DATA VÀ HÀM TRỢ GIÚP
# ====================================================================

# --- CẤU HÌNH ITEMS (ID SỐ 001 - 499) ---

# 1. CONSUMABLES (001 - 099)
CONSUMABLES_ITEMS = {
    "001": {"name": "🎁 Hộp quà", "price": 500, "sell_price": 250, "desc": "Mở ra phần thưởng ngẫu nhiên."},
    "002": {"name": "💎 Đá quý", "price": 2000, "sell_price": 1000, "desc": "Nguyên liệu nâng cấp."},
    "003": {"name": "💎 Rương Đá Thần", "price": 0, "sell_price": 500, "desc": "Mở ra 1 loại Đá Buff ngẫu nhiên."}, 
    "004": {"name": "🎫 Lượt Boss Thêm", "price": 500, "sell_price": 250, "desc": "Cấp thêm 1 lượt săn Boss/Hunt."},
    "005": {"name": "🎟️ Vé EXP Pet", "price": 300, "sell_price": 150, "desc": "Tăng 50 EXP ngay lập tức cho Pet."},
}

# 2. PET ITEMS (100 - 199)
PET_ITEMS = {
    "101": {"name": "🐾 Pet ngẫu nhiên", "price": 1000, "sell_price": 500, "desc": "Nhận một Pet ngẫu nhiên."},
    "102": {"name": "🍖 Thức ăn", "price": 100, "sell_price": 50, "desc": "Tăng EXP cho Pet."},
    "103": {"name": "🧪 Nước Tẩy LT", "price": 10000, "sell_price": 5000, "desc": "Gỡ Pet khỏi người dùng, biến Pet thành item Pet ngẫu nhiên (101)."},
}

# 3. EQUIPMENT ITEMS (200 - 299)
PERMANENT_EQUIPMENT = {
    "201": {"name": "⚔️ Kiếm Gỗ", "price": 300, "sell_price": 150, "bonus": {"atk": 1}, "slot": "weapon", "desc": "+1 ATK."},
    "202": {"name": "🛡️ Khiên Sắt", "price": 400, "sell_price": 200, "bonus": {"hp": 5}, "slot": "armor", "desc": "+5 HP."},
    "203": {"name": "🔮 Ngọc Tăng Tốc", "price": 600, "sell_price": 300, "bonus": {"speed": 2}, "slot": "accessory", "desc": "+2 SPD."},
    "204": {"name": "💎 Ngọc Sức Mạnh", "price": 800, "sell_price": 400, "bonus": {"atk": 2}, "slot": "accessory", "desc": "+2 ATK."},
    "205": {"name": "🍀 Tứ Diệp Thảo", "price": 1000, "sell_price": 500, "bonus": {"luck": 10}, "slot": "accessory", "desc": "+10 LUCK."},
    "206": {"name": "💨 Giày Né Đòn", "price": 1200, "sell_price": 600, "bonus": {"dodge": 5}, "slot": "armor", "desc": "+5 Dodge."},
}

# 4. BUFF ITEMS (300 - 399) - ĐA CẤP ĐỘ
HUNT_BUFFS = {
    "301": {"name": "Đá Tỉ Lệ (Minor)", "price": 1500, "sell_price": 750, "type": "loot_rate", "value": 1.2, "duration": 900, "desc": "Tỉ lệ rơi đồ tăng x1.2 trong 15 phút."},
    "302": {"name": "Đá Tỉ Lệ (Standard)", "price": 3000, "sell_price": 1500, "type": "loot_rate", "value": 1.5, "duration": 3600, "desc": "Tỉ lệ rơi đồ tăng x1.5 trong 1 giờ."},
    "303": {"name": "Đá Tỉ Lệ (Major)", "price": 8000, "sell_price": 4000, "type": "loot_rate", "value": 2.0, "duration": 10800, "desc": "Tỉ lệ rơi đồ tăng x2.0 trong 3 giờ."},
    "304": {"name": "Đá Nhân EXP (Minor)", "price": 1500, "sell_price": 750, "type": "exp_rate", "value": 1.5, "duration": 900, "desc": "EXP Pet nhận được tăng x1.5 trong 15 phút."},
    "305": {"name": "Đá Nhân EXP (Standard)", "price": 3000, "sell_price": 1500, "type": "exp_rate", "value": 2.0, "duration": 3600, "desc": "EXP Pet nhận được tăng x2.0 trong 1 giờ."},
    "306": {"name": "Đá Nhân EXP (Major)", "price": 8000, "sell_price": 4000, "type": "exp_rate", "value": 3.0, "duration": 10800, "desc": "EXP Pet nhận được tăng x3.0 trong 3 giờ."},
    "307": {"name": "Đá May Mắn (Standard)", "price": 2500, "sell_price": 1250, "type": "luck_rate", "value": 1.5, "duration": 3600, "desc": "Tỉ lệ thắng boss tăng x1.5 trong 1 giờ."},
    "308": {"name": "Đá May Mắn (Major)", "price": 6000, "sell_price": 3000, "type": "luck_rate", "value": 2.0, "duration": 7200, "desc": "Tỉ lệ thắng boss tăng x2.0 trong 2 giờ."},
}

# 5. RING ITEMS (400 - 499)
RING_SHOP = {
    "401": {"name": "Nhẫn Đồng", "cost": 50000, "emoji": "💍", "ring_img_key": "basic_ring_img"},
    "402": {"name": "Nhẫn Bạc", "cost": 250000, "emoji": "💍", "ring_img_key": "silver_ring_img"},
    "403": {"name": "Nhẫn Kim Cương", "cost": 1000000, "emoji": "💎", "ring_img_key": "diamond_ring_img"},
}

# Hợp nhất tất cả Item vào một Dict lớn để tra cứu nhanh (trừ Ring Shop)
ALL_SHOP_ITEMS = {**CONSUMABLES_ITEMS, **PET_ITEMS, **PERMANENT_EQUIPMENT, **HUNT_BUFFS}


# --- CẤU HÌNH CÁC SHOP VÀ TÊN LỆNH ---
SHOP_CONFIGS = {
    "shop": {
        "title": "💰 Cửa Hàng Tiền Tệ (Shop)", 
        "color": 0x33FF66, 
        "items": ["001", "002", "004", "005"] 
    },
    "petshop": {
        "title": "🐾 Cửa Hàng Vật Nuôi (Pet Shop)", 
        "color": 0x9966FF, 
        "items": ["101", "102", "103"] 
    },
    "equipshop": {
        "title": "⚔️ Cửa Hàng Trang Bị (Equipment Shop)", 
        "color": 0xFF9933, 
        "items": ["201", "202", "203", "204", "205", "206"] 
    },
    "buffshop": {
        "title": "✨ Cửa Hàng Buff (Buff Shop)", 
        "color": 0x33CCFF, 
        "items": ["301", "302", "303", "304", "305", "306", "307", "308"] 
    },
}

# --- PET VÀ RARITY CONFIGS ---
PET_RARITIES = {
    "Common": {"rate": 60, "name": "Thường"},
    "Uncommon": {"rate": 25, "name": "Hiếm"},
    "Rare": {"rate": 10, "name": "Rất Hiếm"},
    "Epic": {"rate": 4, "name": "Sử Thi"},
    "Legendary": {"rate": 1, "name": "Huyền Thoại"},
}
PET_CONFIGS = {
    "MeoMeo": {"hp": 15, "atk": 3, "speed": 10, "rarity": "Common"},
    "GauGau": {"hp": 20, "atk": 2, "speed": 8, "rarity": "Uncommon"},
    "ThoNgoc": {"hp": 12, "atk": 4, "speed": 12, "rarity": "Rare"},
    "RongLua": {"hp": 30, "atk": 5, "speed": 5, "rarity": "Epic"},
    "Phoenix": {"hp": 40, "atk": 8, "speed": 15, "rarity": "Legendary"},
    "DauDat": {"hp": 10, "atk": 1, "speed": 1, "rarity": "Common"},
}


# --- GIF VÀ BACKGROUND ANIME ---
DEFAULT_IMAGE_LINKS = {
    "profile_bg": "https://i.pinimg.com/originals/1f/2a/3c/1f2a3c30d3d520869d80d2d3c907d88c.jpg", 
    "propose_gif": "https://i.gifer.com/S6eA.gif",           
    "accept_gif": "https://i.gifer.com/C9zR.gif",            
    "hit_gif": "https://i.gifer.com/K1U.gif",                
    "hug_gif": "https://i.gifer.com/8Qj9.gif",               
    "kiss_gif": "https://i.gifer.com/97yX.gif",              
    "pat_gif": "https://i.gifer.com/I6Pj.gif",               
    "slap_gif": "https://i.gifer.com/95oE.gif",              
    "cuddle_gif": "https://i.gifer.com/L1dF.gif",            
    "poke_gif": "https://i.gifer.com/5J3c.gif",              
    "default_interact_gif": "https://i.gifer.com/7s1H.gif",  
    "basic_ring_img": "https://i.gifer.com/YwN.gif",          
    "silver_ring_img": "https://i.gifer.com/H66I.gif",        
    "diamond_ring_img": "https://i.gifer.com/origin/26/26e6d5e160e1d1f7e0344d5c192f4476.gif", 
}


# --- HÀM QUẢN LÝ DATA VÀ TÍCH HỢP RAILWAY ---
def load_data():
    global users, global_data, anime_list, custom_graphics
    if os.path.exists(FILE_USERS):
        with open(FILE_USERS, 'r') as f:
            users = json.load(f)
    if os.path.exists(FILE_GLOBAL):
        with open(FILE_GLOBAL, 'r') as f:
            global_data = json.load(f)
    
    # TÍCH HỢP 1: ADMIN_IDS TỪ RAILWAY
    admin_env = os.getenv("ADMIN_IDS")
    if admin_env:
        admin_list = [id.strip() for id in admin_env.split(',') if id.strip()]
        global_data["admin_list"] = admin_list
    elif "admin_list" not in global_data:
        print("CẢNH BÁO: Không tìm thấy biến môi trường ADMIN_IDS. Sử dụng danh sách Admin trống.")
        global_data["admin_list"] = []

    # TÍCH HỢP 2: ANIME_LIST_CONFIG TỪ RAILWAY
    anime_config_env = os.getenv("ANIME_LIST_CONFIG")
    if anime_config_env:
        try:
            anime_list = json.loads(anime_config_env)
            print(f"✅ Đã tải thành công {len(anime_list)} Anime từ Railway.")
        except json.JSONDecodeError:
            print("❌ LỖI: Biến ANIME_LIST_CONFIG không phải là JSON hợp lệ.")
            anime_list = []
    else:
        anime_list = []

    # TÍCH HỢP 3: CUSTOM_GRAPHICS_CONFIG TỪ RAILWAY
    graphics_config_env = os.getenv("CUSTOM_GRAPHICS_CONFIG")
    if graphics_config_env:
        try:
            loaded_graphics = json.loads(graphics_config_env)
            custom_graphics.update(loaded_graphics)
            print(f"✅ Đã tải thành công Cấu hình đồ họa tùy chỉnh từ Railway.")
        except json.JSONDecodeError:
            print("❌ LỖI: Biến CUSTOM_GRAPHICS_CONFIG không phải là JSON hợp lệ.")
    
    if "last_pet_id" not in global_data:
        global_data["last_pet_id"] = 0
        
def save_data(data_dict):
    if data_dict == users:
        file_name = FILE_USERS
    elif data_dict == global_data:
        file_name = FILE_GLOBAL
    else:
        return
    
    with open(file_name, 'w') as f:
        json.dump(data_dict, f, indent=4)

def get_user(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "balance": 1000,
            "inventory": [],
            "pets": [],
            "last_daily": 0,
            "boss_runs": 3,
            "buffs": {},
            "married_to": None,
            "ring": None,         
            "custom_bg": None,    
            "custom_gif": None,   
        }
    return users[user_id]

def update_balance(user_id, amount):
    user = get_user(user_id)
    user["balance"] = user.get("balance", 0) + amount
    save_data(users)

def is_admin(user_id):
    return str(user_id) in global_data.get("admin_list", [])

def get_action_image_url(user_data, action_key):
    """Lấy URL GIF/Ảnh theo thứ tự ưu tiên."""
    if user_data.get("custom_gif"):
        return user_data["custom_gif"]
    if action_key in DEFAULT_IMAGE_LINKS:
        return DEFAULT_IMAGE_LINKS[action_key]
    return DEFAULT_IMAGE_LINKS.get("default_interact_gif")

def get_random_pet_by_rarity():
    """Tạo Pet ngẫu nhiên dựa trên tỉ lệ."""
    total_rate = sum(r["rate"] for r in PET_RARITIES.values())
    rand_val = random.randint(1, total_rate)
    cumulative_rate = 0
    selected_rarity = None
    
    for r_name, r_data in PET_RARITIES.items():
        cumulative_rate += r_data["rate"]
        if rand_val <= cumulative_rate:
            selected_rarity = r_name
            break
            
    available_pets = [name for name, config in PET_CONFIGS.items() if config["rarity"] == selected_rarity]
    if not available_pets:
        selected_rarity = "Common" # Fallback
        available_pets = [name for name, config in PET_CONFIGS.items() if config["rarity"] == "Common"]

    pet_name = random.choice(available_pets)
    return pet_name, selected_rarity
# ====================================================================
# PHẦN 3: LỆNH KINH TẾ VÀ SHOP
# ====================================================================

@bot.command(name="balance", aliases=["bal", "money", "Bal", "Money"])
async def balance_cmd(ctx, member: discord.Member = None):
    # Logic cũ
    member = member or ctx.author
    user = get_user(member.id)
    await ctx.send(f"💸 **{member.display_name}** hiện có **{user['balance']:,} xu**.")

@bot.command(name="daily", aliases=["Daily"])
async def daily_cmd(ctx):
    # Logic cũ
    uid = str(ctx.author.id)
    user = get_user(uid)
    cooldown = 24 * 3600 # 24 giờ
    
    if time.time() - user["last_daily"] >= cooldown:
        reward = 500
        update_balance(uid, reward)
        user["last_daily"] = time.time()
        save_data(users)
        await ctx.send(f"✅ **{ctx.author.display_name}** đã nhận **{reward:,} xu** hàng ngày!")
    else:
        remaining = int(cooldown - (time.time() - user["last_daily"]))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await ctx.send(f"⏳ Bạn phải chờ thêm **{hours} giờ {minutes} phút** nữa để nhận quà hàng ngày.")

@bot.command(name="shop", aliases=["s", "bshop", "bpetshop", "bequipshop", "bbuffshop", 
                                  "S", "Bshop", "Bpetshop", "Bequipshop", "Bbuffshop"]) 
async def shop_cmd(ctx):
    """Hiển thị các cửa hàng dựa trên lệnh gọi (bshop, bpetshop, etc.)."""
    
    command_name = ctx.invoked_with
    if command_name.startswith('b'):
        command_name = command_name[1:]

    # --- HIỂN THỊ DANH MỤC SHOP (Nếu người dùng chỉ gõ bshop/bs) ---
    if command_name in ["shop", "s"]:
        embed = discord.Embed(
            title="🛒 Danh Mục Cửa Hàng Anime",
            description="Chào mừng đến với chợ đen Anime! Dùng prefix 'b' + tên shop để mở (Ví dụ: `bpetshop`)",
            color=0xDDDDDD
        )
        for key, config in SHOP_CONFIGS.items():
            embed.add_field(name=config['title'], value=f"**Lệnh:** `b{key}`", inline=True)
        
        embed.set_thumbnail(url=DEFAULT_IMAGE_LINKS.get("default_interact_gif")) 
        return await ctx.send(embed=embed)

    shop_config = SHOP_CONFIGS.get(command_name)
    if not shop_config:
        return await ctx.send("❌ Cửa hàng không tồn tại.")

    # --- HIỂN THỊ CHI TIẾT SHOP (ĐÃ LÀM ĐẸP) ---
    shop_embed = discord.Embed(
        title=shop_config['title'],
        description=f"Sử dụng: `bbuy <ID> [số lượng]` | Ví dụ: `bbuy {shop_config['items'][0]}`",
        color=shop_config['color']
    )
    
    if command_name == "petshop":
         shop_embed.set_thumbnail(url="https://i.gifer.com/P0b.gif") 
    elif command_name == "equipshop":
         shop_embed.set_thumbnail(url="https://i.gifer.com/7YfL.gif") 
    
    item_source = ALL_SHOP_ITEMS 

    for item_id in shop_config["items"]:
        item = item_source.get(item_id)
        if item:
            price = f"{item['price']:,} xu"
            name = item['name']
            desc = item['desc']
            
            shop_embed.add_field(
                name=f"[{item_id}] **{name}**",
                value=f"`Giá:` **{price}**\n*Mô tả: {desc}*",
                inline=False 
            )
            
    await ctx.send(embed=shop_embed)

@bot.command(name="buy", aliases=["Buy"])
async def buy_cmd(ctx, item_id: str = None, count: int = 1):
    """Mua vật phẩm bằng ID (001-499)."""
    if item_id is None or count <= 0:
        return await ctx.send("❌ Cú pháp: `bbuy <ID> [số lượng]`")

    item_id = item_id.zfill(3) # Đảm bảo ID là 3 chữ số
    item_data = ALL_SHOP_ITEMS.get(item_id)
    
    if not item_data:
        return await ctx.send("❌ ID vật phẩm không hợp lệ hoặc không có trong cửa hàng.")

    user = get_user(ctx.author.id)
    cost = item_data["price"] * count

    if user["balance"] < cost:
        return await ctx.send(f"❌ Bạn không đủ **{cost:,} xu** để mua {count}x {item_data['name']}.")

    # Trừ tiền
    update_balance(ctx.author.id, -cost)

    # Thêm vào túi đồ
    new_items = []
    for _ in range(count):
        unique_id = str(time.time()) + str(random.randint(100, 999))
        new_items.append({
            "shop_id": item_id,
            "name": item_data["name"],
            "unique_id": unique_id,
        })
    
    user["inventory"].extend(new_items)
    save_data(users)

    await ctx.send(f"✅ **{ctx.author.display_name}** đã mua thành công **{count}x {item_data['name']}** với giá **{cost:,} xu**!")


@bot.command(name="sell", aliases=["Sell"])
async def sell_cmd(ctx, shop_id: str = None, count: int = 1):
    """Bán vật phẩm (dùng ID 3 chữ số)."""
    if shop_id is None or count <= 0:
        return await ctx.send("❌ Cú pháp: `bsell <ID> [số lượng]`")
    
    shop_id = shop_id.zfill(3)
    item_data = ALL_SHOP_ITEMS.get(shop_id)

    if not item_data or item_data.get("sell_price") is None or item_data.get("sell_price") == 0:
        return await ctx.send("❌ ID vật phẩm không hợp lệ hoặc không thể bán.")

    user = get_user(ctx.author.id)
    
    # Đếm số lượng vật phẩm trong túi đồ
    items_in_inv = [item for item in user["inventory"] if item.get("shop_id") == shop_id]
    
    if len(items_in_inv) < count:
        return await ctx.send(f"❌ Bạn chỉ có **{len(items_in_inv)}x** {item_data['name']} trong túi.")
        
    # Xóa vật phẩm khỏi túi đồ
    for _ in range(count):
        # Tìm và xóa item đầu tiên có shop_id tương ứng
        item_to_remove = next((item for item in user["inventory"] if item.get("shop_id") == shop_id), None)
        if item_to_remove:
            user["inventory"].remove(item_to_remove)
            
    # Tính tiền và cộng vào balance
    total_sell_price = item_data["sell_price"] * count
    update_balance(ctx.author.id, total_sell_price)
    save_data(users)
    
    await ctx.send(f"✅ Đã bán thành công **{count}x {item_data['name']}** với giá **{total_sell_price:,} xu**!")


@bot.command(name="ringshop", aliases=["rshop", "Ringshop", "Rshop"]) 
async def ring_shop_cmd(ctx):
    # Logic cũ + cập nhật ID
    shop_embed = discord.Embed(
        title="💍 Cửa Hàng Nhẫn Cưới Anime",
        description="Mua nhẫn để cầu hôn. (Chỉ cần mua 1 lần)",
        color=discord.Color.gold()
    )
    shop_embed.set_thumbnail(url=DEFAULT_IMAGE_LINKS.get(RING_SHOP['403']['ring_img_key']))

    for item_id, item_data in RING_SHOP.items():
        name = item_data['name']
        cost = f"{item_data['cost']:,} xu"
        emoji = item_data['emoji']
        shop_embed.add_field(
            name=f"{emoji} {name} (`{item_id}`)",
            value=f"**Giá:** {cost}",
            inline=True
        )
    
    shop_embed.set_footer(text="Sử dụng: bbuyring <id_nhẫn> | Ví dụ: bbuyring 403")
    await ctx.send(embed=shop_embed)


@bot.command(name="buyring", aliases=["Buyring"]) 
async def buy_ring_cmd(ctx, item_id: str = None):
    # Logic cũ + cập nhật ID
    if item_id is None:
        return await ctx.send("❌ Cú pháp: `bbuyring <id_nhẫn>`. Dùng `bringshop` để xem ID.")

    item_id = item_id.zfill(3)
    item_data = RING_SHOP.get(item_id)
    if not item_data:
        return await ctx.send("❌ ID nhẫn không hợp lệ.")

    user = get_user(ctx.author.id)
    cost = item_data["cost"]

    if user["balance"] < cost:
        return await ctx.send(f"❌ Bạn không đủ **{cost:,} xu** để mua {item_data['name']}.")

    if user["ring"] == item_id:
        return await ctx.send(f"❌ Bạn đã sở hữu và đang trang bị {item_data['name']} rồi.")
        
    update_balance(ctx.author.id, -cost)
    user["ring"] = item_id
    save_data(users)

    await ctx.send(f"✅ **{ctx.author.display_name}** đã mua và trang bị thành công {item_data['emoji']} **{item_data['name']}** với giá **{cost:,} xu**!")


@bot.command(name="customshop", aliases=["cshop", "Cshop"]) 
async def custom_shop_cmd(ctx, shop_type: str = None):
    # Logic cũ + cập nhật ID (ID 5xx cho Custom Graphics)
    if not custom_graphics:
        return await ctx.send("❌ Cửa hàng tùy chỉnh hiện đang trống.")
        
    shop_type = (shop_type or "all").lower()
    items_to_display = []
    
    # Lấy ID 5xx để đảm bảo không trùng
    current_id_counter = 501
    all_graphics_items = []
    
    # Tạo danh sách item với ID số 5xx
    for key, items in custom_graphics.items():
        if isinstance(items, list):
            for item in items:
                # Gán ID số 3 chữ số (501, 502, ...)
                item_id = str(current_id_counter).zfill(3)
                item["id"] = item_id
                all_graphics_items.append(item)
                current_id_counter += 1

    # Phân loại để hiển thị
    if shop_type in ["bg", "backgrounds", "all"]:
        items_to_display.extend([i for i in all_graphics_items if 'bg' in i['id'].lower()])
    if shop_type in ["bn", "banners", "all"]:
        items_to_display.extend([i for i in all_graphics_items if 'bn' in i['id'].lower()])
    if shop_type in ["em", "emojis", "all"]:
        items_to_display.extend([i for i in all_graphics_items if 'em' in i['id'].lower()])
        
    if not items_to_display:
        return await ctx.send("❌ Không tìm thấy mặt hàng cho loại shop này.")
        
    embed = discord.Embed(
        title=f"🎨 Cửa Hàng Đồ Họa Tùy Chỉnh ({shop_type.upper()})",
        description="Mua các mặt hàng này sẽ thêm chúng vào túi đồ (inventory) của bạn. ID: 501-599",
        color=discord.Color.blue()
    )
    
    for item in items_to_display:
        item_type = ""
        if item['id'].startswith('50'): item_type = "BG" # Ví dụ
        elif item['id'].startswith('51'): item_type = "Banner" # Ví dụ
        
        value_text = f"**Giá:** {item.get('price', 0):,} xu\n"
        if item_type == "Emoji":
            value_text += f"**Code:** `{item.get('code', '')}`"
            
        embed.add_field(
            name=f"[{item['id']}] {item['name']}",
            value=value_text,
            inline=True
        )
        
    embed.set_footer(text="Sử dụng: bbuycustom <ID_item> | Ví dụ: bbuycustom 501")
    await ctx.send(embed=embed)


@bot.command(name="buycustom", aliases=["Buycustom"]) 
async def buy_custom_cmd(ctx, item_id: str = None):
    """Mua các vật phẩm từ cửa hàng đồ họa tùy chỉnh (ID 5xx)."""
    if item_id is None:
        return await ctx.send("❌ Cú pháp: `bbuycustom <ID_item>`. Dùng `bcustomshop` để xem ID.")
        
    item_id = item_id.zfill(3)
    item_data = None
    item_type = ""
    
    # Logic tìm item tương tự như bcustomshop để lấy item_data
    all_graphics_items = []
    current_id_counter = 501
    for key, items in custom_graphics.items():
        if isinstance(items, list):
            for item in items:
                item_id_internal = str(current_id_counter).zfill(3)
                if item_id_internal == item_id:
                    item_data = item
                    item_data["id"] = item_id_internal # Gán lại ID
                    item_type = key[:-1] if key.endswith('s') else key
                    break
                current_id_counter += 1
            if item_data: break
                
    if not item_data:
        return await ctx.send("❌ ID vật phẩm tùy chỉnh không hợp lệ.")
        
    user = get_user(ctx.author.id)
    cost = item_data.get("price", 0)
    
    if user["balance"] < cost:
        return await ctx.send(f"❌ Bạn không đủ **{cost:,} xu** để mua {item_data['name']}.")
        
    update_balance(ctx.author.id, -cost)
    
    user["inventory"].append({
        "shop_id": item_id,
        "name": f"[{item_type.title()}] {item_data['name']}",
        "unique_id": str(time.time()) + str(random.randint(100, 999)),
        "data": item_data 
    })
    save_data(users)
    
    await ctx.send(f"✅ **{ctx.author.display_name}** đã mua thành công **{item_data['name']}** ({item_id}) với giá **{cost:,} xu**!")
  # ====================================================================
# PHẦN 4: LỆNH TÚI ĐỒ VÀ SỬ DỤNG ITEM
# ====================================================================

@bot.command(name="inv", aliases=["items", "Inv", "Items"]) 
async def inv_cmd(ctx):
    """Hiển thị Túi đồ (Inventory) của người dùng (ĐÃ LÀM ĐẸP)."""
    uid = str(ctx.author.id)
    user = get_user(uid)
    
    inv_embed = discord.Embed(
        title=f"🎒 Túi Đồ của {ctx.author.display_name}",
        description=f"Tổng số dư: **{user['balance']:,} xu**",
        color=0x00BFFF 
    )
    inv_embed.set_thumbnail(url=ctx.author.display_avatar.url)
    
    # --- 1. PHÂN LOẠI VẬT PHẨM ---
    item_counts = {}
    equipment = []
    custom_items = []
    
    for item in user.get("inventory", []):
        shop_id = item.get("shop_id")
        unique_id = item.get("unique_id")
        
        if shop_id.startswith("2"): # 2xx: Equipment
            is_equipped = False
            for pet in user.get("pets", []):
                if pet.get("equipped_item") == unique_id:
                    is_equipped = True
                    break
            equipment.append((item, is_equipped))
        elif shop_id.startswith("5"): # 5xx: Custom Graphics
            custom_items.append(item)
        else:
            item_counts[shop_id] = item_counts.get(shop_id, 0) + 1

    # --- 2. FIELD: VẬT PHẨM TIÊU THỤ (Consumables & Pet Items & Buffs) ---
    consumable_text = ""
    for shop_id, count in item_counts.items():
        item_data = ALL_SHOP_ITEMS.get(shop_id, {"name": "Item Không rõ"})
        item_name = item_data['name']
        consumable_text += f"`[{shop_id}]` **{item_name}** x{count}\n"
        
    if consumable_text:
        inv_embed.add_field(name="📦 Vật Phẩm Tiêu Thụ (Dùng: `buse <ID>`)", 
                            value=consumable_text, 
                            inline=False)
    else:
        inv_embed.add_field(name="📦 Vật Phẩm Tiêu Thụ", 
                            value="*Kho chứa trống rỗng...*", 
                            inline=False)

    # --- 3. FIELD: TRANG BỊ (Equipment - 2xx) ---
    equip_text = ""
    for item, is_equipped in equipment:
        status = " (✅ Đã Trang Bị)" if is_equipped else " (❌ Chưa Trang Bị)"
        equip_text += f"`[{item['shop_id']}]` **{item['name']}** - ID: `{item['unique_id'][:6]}`{status}\n"
    
    if equip_text:
        inv_embed.add_field(name="⚔️ Trang Bị (Equip: `bequip <ID_6_số> <Pet_ID>`)", 
                            value=equip_text, 
                            inline=False)
    else:
        inv_embed.add_field(name="⚔️ Trang Bị", 
                            value="*Chưa có trang bị nào...*", 
                            inline=False)

    # --- 4. FIELD: ĐỒ HỌA TÙY CHỈNH (Custom Graphics - 5xx) ---
    custom_text = ""
    custom_counts = {}
    for item in custom_items:
        custom_counts[item['shop_id']] = custom_counts.get(item['shop_id'], 0) + 1
        
    for shop_id, count in custom_counts.items():
        # Lấy tên item tùy chỉnh (Đây là một cách đơn giản, nếu bạn muốn tên đẹp hơn, cần logic tìm item từ custom_graphics)
        item_name = item.get("name", "Custom Item")
        custom_text += f"`[{shop_id}]` **{item_name}** x{count}\n"

    if custom_text:
        inv_embed.add_field(name="🎨 Đồ Họa (Set: `bsetbg/bsetgif <URL>`)", 
                            value=custom_text, 
                            inline=False)

    # --- 5. FIELD: BUFF HIỆN TẠI ---
    buff_text = ""
    current_time = time.time()
    if user.get("buffs"):
        for buff_type, buff_data in user["buffs"].items():
            if buff_data["end_time"] > current_time:
                remaining_time = int(buff_data["end_time"] - current_time)
                name_map = {"loot_rate": "Tỉ Lệ Rơi Đồ", "exp_rate": "Nhân EXP Pet", "luck_rate": "May Mắn Boss"}
                buff_name = name_map.get(buff_type, buff_type.title())
                duration_display = f"{remaining_time // 3600} giờ {(remaining_time % 3600) // 60} phút"
                
                buff_text += f"⚡ **{buff_name}** (x{buff_data['value']})\n"
                buff_text += f"   *Còn lại:* **{duration_display}**\n"
    
    if buff_text:
        inv_embed.add_field(name="✨ Buff Đang Kích Hoạt", 
                            value=buff_text, 
                            inline=False)

    inv_embed.set_footer(text="ID 6 chữ số: unique_id của Trang bị (Dùng để Equip/Unequip)")
    await ctx.send(embed=inv_embed)


@bot.command(name="use", aliases=["Use"]) 
async def use_cmd(ctx, shop_id: str = None, pet_id: int = None):
    """Sử dụng vật phẩm (ID 3 chữ số)."""
    if shop_id is None:
        return await ctx.send("❌ Cú pháp: `buse <ID> [Pet_ID]`")
        
    shop_id = shop_id.zfill(3)
    user = get_user(ctx.author.id)
    item_entry = next((item for item in user["inventory"] if item.get("shop_id") == shop_id), None)

    if not item_entry:
        return await ctx.send(f"❌ Bạn không có vật phẩm với ID `{shop_id}` trong túi.")
        
    item_name = item_entry['name']
    item_data = ALL_SHOP_ITEMS.get(shop_id, {})
    
    # Xóa item khỏi túi đồ (trừ khi là item cần giữ lại)
    user["inventory"].remove(item_entry) 
    res = ""
    
    # 1. BUFFS (3xx)
    if shop_id.startswith("3"): 
        if item_data["type"] not in ["loot_rate", "exp_rate", "luck_rate"]:
            res = f"❌ Không thể sử dụng vật phẩm buff không xác định này."
        else:
            buff_type = item_data["type"]
            buff_value = item_data["value"]
            duration = item_data["duration"]
            current_time = time.time()
            
            user["buffs"][buff_type] = {
                "value": buff_value,
                "end_time": current_time + duration
            }
            duration_display = f"{duration // 3600} giờ" if duration % 3600 == 0 else f"{duration // 60} phút"
            res = f"✨ Đã kích hoạt **{item_name}**! **{item_data['desc'].split(' trong ')[0]}** trong **{duration_display}**."
            
    # 2. PET ITEMS (1xx)
    elif shop_id == "101": # Pet ngẫu nhiên (chỉ là item, phải dùng brollpet)
        user["inventory"].append(item_entry) # Hoàn trả lại item đã bị xóa
        return await ctx.send(f"❌ Vui lòng sử dụng lệnh `brollpet` để mở **{item_name}**.")
    
    elif shop_id == "103": # Nước Tẩy LT
        if pet_id is None or pet_id <= 0: return await ctx.send("❌ Cú pháp: `buse 103 <Pet_ID>`")
        
        target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
        if not target_pet: return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
        user["pets"].remove(target_pet)
        
        # Tạo lại item Pet ngẫu nhiên (101) và thêm vào túi
        pet_item_data = ALL_SHOP_ITEMS["101"]
        user["inventory"].append({"shop_id": "101", "name": pet_item_data["name"], "unique_id": str(time.time()) + str(random.randint(100, 999))})
        res = f"🧪 Đã sử dụng **{item_name}**. Pet **{target_pet['name']}** đã được gỡ bỏ và bạn nhận lại **1x {pet_item_data['name']}**."

    # 3. CONSUMABLES (0xx)
    elif shop_id == "004": # Lượt Boss Thêm
        user["boss_runs"] = user.get("boss_runs", 0) + 1
        res = f"🎫 Đã sử dụng **{item_name}**. Bạn nhận thêm **1 lượt** săn Boss/Hunt. Tổng lượt hiện có: **{user['boss_runs']}**."
        
    elif shop_id == "005": # Vé EXP Pet
        if pet_id is None or pet_id <= 0: return await ctx.send("❌ Cú pháp: `buse 005 <Pet_ID>`")
        
        target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
        if not target_pet: return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
        exp_gain = 50
        target_pet["exp"] += exp_gain
        # (Thêm logic Level Up nếu cần)
        res = f"🎟️ Pet **{target_pet['name']}** nhận được **{exp_gain} EXP**! Tổng EXP hiện tại: {target_pet['exp']}."

    # 4. CÁC ITEMS KHÁC (Cần giữ lại nếu item không bị xóa)
    else:
        # Trong trường hợp item không có logic sử dụng ở đây, trả lại item
        user["inventory"].append(item_entry)
        res = f"❌ Vật phẩm **{item_name}** không thể sử dụng bằng lệnh `buse` hoặc chưa có logic xử lý."
    
    save_data(users)
    await ctx.send(res)


@bot.command(name="equip", aliases=["Equip"])
async def equip_cmd(ctx, unique_id: str = None, pet_id: int = None):
    """Trang bị vật phẩm (ID 6 số) cho Pet (ID số)."""
    # Logic cũ
    if unique_id is None or pet_id is None:
        return await ctx.send("❌ Cú pháp: `bequip <ID_6_số> <Pet_ID>`.")
    
    user = get_user(ctx.author.id)
    
    # 1. Tìm Trang bị trong túi đồ
    item_to_equip = next((item for item in user["inventory"] if item.get("unique_id", "")[:6] == unique_id), None)
    if not item_to_equip:
        return await ctx.send(f"❌ Không tìm thấy Trang bị với ID `{unique_id}`.")
        
    item_data = ALL_SHOP_ITEMS.get(item_to_equip["shop_id"])
    if not item_data or item_to_equip["shop_id"] not in PERMANENT_EQUIPMENT:
        return await ctx.send(f"❌ Vật phẩm `{item_to_equip['name']}` không phải là trang bị.")

    # 2. Tìm Pet
    target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
    if not target_pet:
        return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
    # 3. Trang bị (Logic chỉ cho phép 1 món)
    if target_pet.get("equipped_item") == item_to_equip["unique_id"]:
        return await ctx.send(f"❌ Trang bị này đã được gắn cho Pet **{target_pet['name']}**.")
        
    # Gỡ món đồ cũ nếu có
    old_item_unique_id = target_pet.get("equipped_item")
    if old_item_unique_id:
        old_item = next((item for item in user["inventory"] if item.get("unique_id") == old_item_unique_id), None)
        if old_item:
            await ctx.send(f"⚠️ Đã gỡ **{old_item['name']}** khỏi Pet **{target_pet['name']}**.")
    
    target_pet["equipped_item"] = item_to_equip["unique_id"]
    save_data(users)
    await ctx.send(f"✅ Đã trang bị **{item_to_equip['name']}** cho Pet **{target_pet['name']}**!")


@bot.command(name="unequip", aliases=["un", "Unequip", "Un"])
async def unequip_cmd(ctx, pet_id: int = None):
    """Gỡ trang bị khỏi Pet (Dùng Pet ID)."""
    # Logic cũ
    if pet_id is None:
        return await ctx.send("❌ Cú pháp: `bunequip <Pet_ID>`.")
        
    user = get_user(ctx.author.id)
    target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
    
    if not target_pet:
        return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
    equipped_unique_id = target_pet.get("equipped_item")
    if not equipped_unique_id:
        return await ctx.send(f"❌ Pet **{target_pet['name']}** không có trang bị nào.")
        
    # Tìm thông tin item để hiển thị tên
    equipped_item = next((item for item in user["inventory"] if item.get("unique_id") == equipped_unique_id), None)
    item_name = equipped_item["name"] if equipped_item else "Trang bị không rõ"
    
    target_pet["equipped_item"] = None
    save_data(users)
    await ctx.send(f"✅ Đã gỡ **{item_name}** khỏi Pet **{target_pet['name']}**.")
                                                                       # ====================================================================
# PHẦN 5: LỆNH PET VÀ HUNTING
# ====================================================================

@bot.command(name="rollpet", aliases=["rp", "Rollpet", "Rp"])
async def random_pet_cmd(ctx):
    uid = ctx.author.id; user = get_user(uid)
    
    # Cập nhật ID item Pet ngẫu nhiên từ 101
    pet_item = next((item for item in user.get("inventory", []) if item.get("shop_id") == "101"), None) 
    if not pet_item: return await ctx.send("❌ Bạn không có **🐾 Pet ngẫu nhiên** (ID: 101) trong túi. Dùng `bbuy 101` để mua.")
    
    user["inventory"].remove(pet_item)
    
    pet_name, rarity_name = get_random_pet_by_rarity() 
    pet_config = PET_CONFIGS[pet_name]
    
    global_data["last_pet_id"] = global_data.get("last_pet_id", 0) + 1
    new_pet_id = global_data["last_pet_id"]
    
    new_pet = {
        "id": new_pet_id,
        "name": pet_name,
        "rarity": rarity_name,
        "level": 1,
        "exp": 0,
        "stats": pet_config,
        "equipped_item": None,
    }
    user["pets"].append(new_pet)
    save_data(users)
    save_data(global_data)

    embed = discord.Embed(
        title=f"🎉 CHÚC MỪNG! Pet Mới!",
        description=f"🎉 Bạn nhận được Pet **{pet_name}** mới! (Rarity: **{PET_RARITIES[rarity_name]['name']}**)",
        color=0xFF00FF
    )
    embed.add_field(name="ID Pet", value=new_pet_id, inline=True)
    embed.add_field(name="HP/ATK/SPD", value=f"{new_pet['stats']['hp']}/{new_pet['stats']['atk']}/{new_pet['stats']['speed']}", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="pets", aliases=["z", "Pets", "Z"])
async def pets_cmd(ctx):
    # Logic cũ
    user = get_user(ctx.author.id)
    pets = user.get("pets")
    
    if not pets:
        return await ctx.send("❌ Bạn chưa sở hữu Pet nào.")
        
    embed = discord.Embed(
        title=f"🐾 Bộ Sưu Tập Pet của {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    
    for pet in pets:
        item_unique_id = pet.get("equipped_item")
        item_name = "Không"
        
        if item_unique_id:
            equipped_item = next((item for item in user["inventory"] if item.get("unique_id") == item_unique_id), None)
            if equipped_item:
                item_name = equipped_item["name"]
        
        stats = pet["stats"]
        name_line = f"[{pet['id']}] **{pet['name']}** (Lv.{pet['level']})"
        info_line = f"HP/ATK/SPD: {stats['hp']}/{stats['atk']}/{stats['speed']}\nEXP: {pet['exp']}\nTrang bị: *{item_name}*"
        
        embed.add_field(name=name_line, value=info_line, inline=True)
        
    await ctx.send(embed=embed)


@bot.command(name="hunt", aliases=["Hunt"])
async def hunt_cmd(ctx):
    # Logic cũ (Sẽ cần cập nhật logic Buff)
    uid = str(ctx.author.id)
    user = get_user(uid)
    
    if user["boss_runs"] <= 0:
        return await ctx.send("❌ Bạn đã hết lượt săn Boss/Hunt. Dùng `bbuy 004` để mua thêm lượt.")
        
    if not user["pets"]:
        return await ctx.send("❌ Bạn cần ít nhất một Pet để tham gia săn Boss. Dùng `brollpet`.")

    # 1. TÍNH TOÁN BUFFS VÀ STATS
    current_time = time.time()
    active_buffs = {k: v for k, v in user["buffs"].items() if v["end_time"] > current_time}
    user["buffs"] = active_buffs # Cập nhật xóa buff hết hạn
    
    # Áp dụng Luck Buff (307, 308)
    base_win_rate = 0.5
    luck_buff = active_buffs.get("luck_rate", {}).get("value", 1.0)
    final_win_rate = base_win_rate * luck_buff

    # Lấy tổng Stats (Đơn giản hóa: dùng Stats của Pet mạnh nhất)
    strongest_pet = max(user["pets"], key=lambda p: p["stats"]["hp"] + p["stats"]["atk"] + p["stats"]["speed"])
    pet_power = strongest_pet["stats"]["hp"] + strongest_pet["stats"]["atk"] + strongest_pet["stats"]["speed"]
    
    # 2. XỬ LÝ KẾT QUẢ HUNT
    user["boss_runs"] -= 1
    save_data(users)
    
    # Giả định Boss có độ khó tương đương Pet Power (cho đơn giản)
    
    result_text = f"**{ctx.author.display_name}** và Pet **{strongest_pet['name']}** đã tham gia săn Boss!"
    
    if random.random() < final_win_rate: # WIN
        reward_money = random.randint(1000, 3000)
        reward_exp = random.randint(50, 150)
        
        # Áp dụng Loot Rate Buff (301, 302, 303)
        loot_buff = active_buffs.get("loot_rate", {}).get("value", 1.0)
        final_reward_money = int(reward_money * loot_buff)
        
        # Áp dụng EXP Rate Buff (304, 305, 306)
        exp_buff = active_buffs.get("exp_rate", {}).get("value", 1.0)
        final_reward_exp = int(reward_exp * exp_buff)

        update_balance(uid, final_reward_money)
        strongest_pet["exp"] = strongest_pet.get("exp", 0) + final_reward_exp
        
        res = f"✅ **CHIẾN THẮNG!** Boss đã bị đánh bại!\n"
        res += f"💰 Nhận được **{final_reward_money:,} xu** (Loot x{loot_buff:.1f})\n"
        res += f"✨ Pet **{strongest_pet['name']}** nhận được **{final_reward_exp} EXP** (EXP x{exp_buff:.1f})"
    else: # LOSE
        res = f"❌ **THẤT BẠI!** Boss quá mạnh...\n"
        res += f"Pet **{strongest_pet['name']}** không nhận được gì."
        
    await ctx.send(f"{result_text}\n\n{res}\n\n*Lượt còn lại:* **{user['boss_runs']}**")
  # ====================================================================
# PHẦN 6: LỆNH TƯƠNG TÁC (SOCIAL & ROLEPLAY) - CODE ĐÃ SỬA LỖI
# ====================================================================

SOCIAL_ACTIONS = {
    # Key phải là chữ thường để khớp với lệnh gọi.
    "hit": {"past": "đánh", "desc": "đã tung cú đấm chí mạng vào", "emoji": "💥"}, 
    "hug": {"past": "ôm", "desc": "đã ôm chặt lấy", "emoji": "🫂"}, 
    "kiss": {"past": "hôn", "desc": "đã tặng một nụ hôn e thẹn cho", "emoji": "💖"}, 
    "pat": {"past": "xoa đầu", "desc": "đã xoa đầu đầy cưng chiều", "emoji": "😊"}, 
    "slap": {"past": "tát", "desc": "đã tát một cái đau điếng vào", "emoji": "💢"}, 
    "cuddle": {"past": "rúc vào", "desc": "đã rúc vào người", "emoji": "💞"}, 
    "poke": {"past": "chọc", "desc": "đã chọc vào má", "emoji": "👉"}, 
}
MARRIAGE_FEE = 10000

# Hàm trợ giúp lấy member
async def get_member(ctx, target_str):
    if not target_str:
        return None
    try:
        member_id = int(target_str.strip('<@!>'))
        # Đảm bảo lệnh chạy được trong DMs (nếu bot cho phép)
        if ctx.guild:
            return await ctx.guild.fetch_member(member_id)
        else:
            return await bot.fetch_user(member_id)
    except:
        return None

# HÀM CALLBACK CHUNG - KHÔNG DÙNG DECORATOR @bot.command() Ở ĐÂY!
async def interact_cmd(ctx, target: str = None): 
    """
    Xử lý tất cả các lệnh tương tác (hug, kiss, hit, etc.).
    Action được lấy từ tên lệnh đã gọi (ctx.invoked_with).
    """
    
    # Lấy tên lệnh đã gọi (hug, kiss, hit, ...) và chuyển về chữ thường
    # Ví dụ: nếu user gõ bHUG, ctx.invoked_with là HUG.
    invoked_name = ctx.invoked_with.lower()
    
    # Xử lý các tiền tố 'b' (ví dụ: bhug -> hug)
    if invoked_name.startswith('b'):
        action_name = invoked_name[1:]
    else:
        action_name = invoked_name
        
    action_data = SOCIAL_ACTIONS.get(action_name)
    
    if not action_data:
        # Nếu lệnh gọi không phải là lệnh tương tác (hoặc không khớp alias), thoát
        return 

    if target is None:
        return await ctx.send(f"❌ Cú pháp: `b{action_name} <@người dùng>`.")

    member_target = await get_member(ctx, target)
    if not member_target or member_target.id == ctx.author.id:
        return await ctx.send("❌ Người dùng không hợp lệ hoặc bạn không thể tự thực hiện hành động này.")

    # Lấy URL GIF
    author_data = get_user(ctx.author.id)
    gif_url = get_action_image_url(author_data, f"{action_name}_gif")

    embed = discord.Embed(
        description=f"{action_data['emoji']} **{ctx.author.display_name}** {action_data['desc']} **{member_target.display_name}**!",
        color=discord.Color.red() if action_name in ["hit", "slap"] else discord.Color.green()
    )
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)


# Tạo lệnh tương tác và aliases cho từng hành động
for action, data in SOCIAL_ACTIONS.items():
    # Thêm aliases: hug, ôm, Hug, Ôm
    aliases = [data["past"], action.capitalize(), data["past"].capitalize()]
    
    # Gán hàm interact_cmd làm callback cho từng lệnh mới.
    # LƯU Ý: Không được định nghĩa @bot.command() ngay trên hàm interact_cmd
    bot.command(name=action, aliases=aliases)(interact_cmd)


# --- CÁC LỆNH HÔN NHÂN/TÌNH YÊU ---

@bot.command(name="propose", aliases=["Propose"]) 
async def propose_cmd(ctx, target: str = None):
    # Logic cũ
    member_target = await get_member(ctx, target)
    if not member_target: return await ctx.send("❌ Người dùng không hợp lệ.")
    if member_target.id == ctx.author.id: return await ctx.send("❌ Bạn không thể tự cầu hôn chính mình.")

    author_data = get_user(ctx.author.id)
    if author_data["married_to"]: return await ctx.send("❌ Bạn đã kết hôn rồi.")
    if not author_data.get("ring"): return await ctx.send("❌ Bạn cần mua nhẫn cưới (Ring) trước khi cầu hôn! Dùng `bringshop`.")

    embed = discord.Embed(
        title="💖 LỜI CẦU HÔN NGỌT NGÀO",
        description=f"**{member_target.mention}**, **{ctx.author.display_name}** đang cầu hôn bạn! Dùng `baccept {ctx.author.mention}` để đồng ý.",
        color=discord.Color.light_grey()
    )
    embed.set_image(url=DEFAULT_IMAGE_LINKS["propose_gif"])
    embed.set_footer(text=f"Người cầu hôn đã chuẩn bị nhẫn {RING_SHOP.get(author_data['ring'])['name']}!")
    
    await ctx.send(member_target.mention, embed=embed)


@bot.command(name="accept", aliases=["Accept"]) 
async def accept_cmd(ctx, proposer: str = None):
    # Logic cũ
    member_proposer = await get_member(ctx, proposer)
    if not member_proposer: return await ctx.send("❌ Người dùng cầu hôn không hợp lệ.")

    proposer_data = get_user(member_proposer.id)
    target_data = get_user(ctx.author.id)
    
    if target_data["married_to"]: return await ctx.send("❌ Bạn đã kết hôn rồi.")
    if proposer_data["married_to"]: return await ctx.send("❌ Người này đã kết hôn với người khác.")
    if proposer_data["ring"] is None: return await ctx.send("❌ Người này chưa mua nhẫn.")
    
    if target_data["balance"] < MARRIAGE_FEE: 
        return await ctx.send(f"❌ **{ctx.author.display_name}** cần **{MARRIAGE_FEE:,} xu** phí kết hôn.")

    # Cập nhật trạng thái
    target_data["married_to"] = member_proposer.id
    proposer_data["married_to"] = ctx.author.id
    update_balance(ctx.author.id, -MARRIAGE_FEE)
    save_data(users)
    
    embed = discord.Embed(
        title="💍 KẾT HÔN THÀNH CÔNG!",
        description=f"🎉 **{member_proposer.display_name}** và **{ctx.author.display_name}** đã chính thức về chung một nhà! Chúc mừng hạnh phúc!",
        color=discord.Color.purple()
    )
    embed.set_image(url=DEFAULT_IMAGE_LINKS["accept_gif"])
    await ctx.send(f"{member_proposer.mention} {ctx.author.mention}", embed=embed)


@bot.command(name="divorce", aliases=["Divorce"]) 
async def divorce_cmd(ctx):
    # Logic cũ
    user = get_user(ctx.author.id)
    spouse_id = user["married_to"]
    
    if not spouse_id: return await ctx.send("❌ Bạn chưa kết hôn.")
    
    spouse = await get_member(ctx, str(spouse_id))
    if not spouse: return await ctx.send("❌ Không tìm thấy người bạn đời của bạn.")

    # Xóa trạng thái kết hôn của cả hai
    user["married_to"] = None
    spouse_data = get_user(spouse_id)
    if spouse_data:
        spouse_data["married_to"] = None
        
    save_data(users)
    await ctx.send(f"💔 **{ctx.author.display_name}** và **{spouse.display_name}** đã ly hôn. Hẹn gặp lại kiếp sau.")


@bot.command(name="wife", aliases=["husband", "spouse", "Wife", "Husband", "Spouse"]) 
async def check_spouse_cmd(ctx):
    # Logic cũ
    user = get_user(ctx.author.id)
    spouse_id = user["married_to"]
    
    if not spouse_id: return await ctx.send("❌ Bạn chưa kết hôn.")
    
    spouse = await get_member(ctx, str(spouse_id))
    if spouse:
        await ctx.send(f"❤️ Người bạn đời hiện tại của **{ctx.author.display_name}** là **{spouse.display_name}**.")
    else:
        await ctx.send("⚠️ Bạn đã kết hôn, nhưng không tìm thấy người bạn đời đó trong server này nữa.")
      # ====================================================================
# PHẦN 7: LỆNH TÙY CHỈNH (CUSTOMIZATION)
# ====================================================================

# Hàm kiểm tra URL cơ bản
def is_valid_url(url):
    return url.startswith("http") and ("." in url)

@bot.command(name="setbg", aliases=["setgif", "customize", "Setbg", "Setgif", "Customize"])
async def set_custom_image_cmd(ctx, type_to_set: str = None, link: str = None):
    """Đặt URL ảnh nền (profile) hoặc GIF tùy chỉnh (tương tác)."""
    if type_to_set is None or link is None:
        return await ctx.send("❌ Cú pháp: `bsetbg bg <URL_ảnh>` hoặc `bsetbg gif <URL_gif>`")

    user = get_user(ctx.author.id)
    type_to_set = type_to_set.lower()

    if not is_valid_url(link):
        return await ctx.send("❌ URL không hợp lệ.")

    if type_to_set == "bg":
        user["custom_bg"] = link
        res = f"✅ Đã đặt ảnh nền (Background) Profile tùy chỉnh thành công!"
    elif type_to_set == "gif":
        user["custom_gif"] = link
        res = f"✅ Đã đặt GIF tương tác (Social GIF) tùy chỉnh thành công!"
    else:
        return await ctx.send("❌ Loại tùy chỉnh không hợp lệ. Chọn `bg` (Background) hoặc `gif` (Social GIF).")

    save_data(users)
    await ctx.send(res)


@bot.command(name="profile", aliases=["p", "info", "Profile", "P", "Info"])
async def profile_cmd(ctx, target: str = None):
    """Hiển thị thông tin Profile và Stats của người dùng."""
    member = ctx.author
    if target:
        member = await get_member(ctx, target)
        if not member:
            return await ctx.send("❌ Người dùng không hợp lệ.")
            
    user_data = get_user(member.id)
    
    # 1. Lấy BG tùy chỉnh hoặc BG mặc định
    profile_bg_url = user_data.get("custom_bg") or DEFAULT_IMAGE_LINKS["profile_bg"]
    
    profile_embed = discord.Embed(
        title=f"🌸 Profile Anime của {member.display_name}",
        color=discord.Color.magenta()
    )
    profile_embed.set_thumbnail(url=member.display_avatar.url)
    
    # 2. Thông tin cơ bản
    info_text = f"💰 **Số dư:** {user_data.get('balance', 0):,} xu\n"
    
    # 3. Thông tin Hôn nhân
    spouse_id = user_data.get("married_to")
    if spouse_id:
        spouse = await get_member(ctx, str(spouse_id))
        spouse_name = spouse.display_name if spouse else "Không còn trong server"
        info_text += f"❤️ **Kết hôn với:** {spouse_name}"
        ring_id = user_data.get("ring")
        if ring_id:
            info_text += f" ({RING_SHOP.get(ring_id, {}).get('name', 'Nhẫn bí ẩn')})"
    else:
        info_text += f"💔 **Tình trạng:** Độc thân"
        
    profile_embed.add_field(name="✨ Thông tin Cơ Bản", value=info_text, inline=False)
    
    # 4. Thông tin Game
    game_text = f"🐾 **Tổng số Pet:** {len(user_data.get('pets', []))}\n"
    game_text += f"🎫 **Lượt Boss còn:** {user_data.get('boss_runs', 0)}\n"
    
    profile_embed.add_field(name="🕹️ Thông tin Game", value=game_text, inline=False)

    # Đặt ảnh BG tùy chỉnh
    profile_embed.set_image(url=profile_bg_url)
    
    await ctx.send(embed=profile_embed)
  # ... (Các lệnh Admin ở trên giữ nguyên) ...
# @bot.command(name="deladmin", aliases=["removeadmin", "Deladmin", "Removeadmin"]) ... (giữ nguyên)
# @bot.command(name="help", aliases=["commands", "hlep", "Help", "Commands"]) ... (giữ nguyên)

# ====================================================================
# LỆNH PHÁT NHẠC MỚI (PLAY)
# ====================================================================

@bot.command(name="play", aliases=["p", "bplay", "btts", "Play", "P", "Bplay", "Btts"])
async def play_cmd(ctx, *, source: str = None):
    """
    Phát file âm thanh từ URL hoặc chuyển Text sang Speech (TTS).
    Cú pháp: bplay <URL> hoặc bplay <Văn bản>
    """
    if source is None:
        return await ctx.send("❌ Cú pháp: `bplay <URL file âm thanh>` hoặc `bplay <văn bản TTS>`.")

    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("❌ Bạn phải tham gia vào kênh thoại (Voice Channel) để sử dụng lệnh này.")

    channel = ctx.author.voice.channel
    vc = ctx.voice_client

    # 1. Kết nối hoặc Di chuyển đến kênh thoại
    if vc is None:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)
    
    # Dừng nhạc cũ nếu đang phát
    if vc.is_playing():
        vc.stop()
        await asyncio.sleep(0.5)

    try:
        if is_valid_url(source) and (source.endswith(('.mp3', '.mp4', '.ogg', '.wav')) or "youtube" in source or "youtu.be" in source):
            # --- PHÁT NHẠC TỪ URL (Sử dụng youtube-dl/yt-dlp qua FFmpeg) ---
            
            # Cấu hình FFmpeg (Dùng ytdl để xử lý link trực tiếp)
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            
            # Sử dụng ytdl để lấy stream URL chất lượng tốt nhất
            try:
                # Nếu bạn đã cài đặt yt-dlp và discord.py[voice] đầy đủ
                # Tuy nhiên, để đơn giản, tôi sẽ dùng trực tiếp URL nếu là file MP3/MP4.
                
                # Cảnh báo: Discord.py chỉ hỗ trợ file stream trực tiếp.
                # Phát URL trực tiếp:
                vc.play(discord.FFmpegPCMAudio(source, **FFMPEG_OPTIONS), 
                        after=lambda e: print('Done playing URL', e))
                
                await ctx.send(f"🎶 Đã bắt đầu phát nhạc từ URL: **{source}**")
                
            except Exception as e:
                return await ctx.send(f"❌ Lỗi khi phát từ URL (FFmpeg): {e}")
            
        else:
            # --- CHUYỂN TEXT SANG SPEECH (TTS) ---
            tts = gTTS(source, lang='vi')
            filename = f"tts_{ctx.author.id}.mp3"
            tts.save(filename)

            vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: print('Done playing TTS', e))
            await ctx.send(f"🗣️ Đã phát TTS: **{source}**")

            # Chờ phát xong và xóa file
            while vc.is_playing():
                await asyncio.sleep(1)
            os.remove(filename)
            
        # Chờ phát xong nếu là URL (giữ kết nối)
        if is_valid_url(source):
            await asyncio.sleep(1) # Chờ 1 giây trước khi ngắt nếu không có loop/queue
            # Nếu muốn bot không ngắt ngay:
            # await asyncio.sleep(60) # Giữ kết nối trong 1 phút sau khi phát xong
            
        # Luôn ngắt kết nối sau khi phát xong (để tránh bot bị treo trong kênh thoại)
        await vc.disconnect()
        
    except Exception as e:
        if vc and vc.is_connected():
            await vc.disconnect()
        await ctx.send(f"❌ Đã xảy ra lỗi trong quá trình phát: {e}")
        
        # Xóa file TTS nếu có lỗi
        tts_filename = f"tts_{ctx.author.id}.mp3"
        if os.path.exists(tts_filename):
            os.remove(tts_filename)
            

@bot.command(name="stop", aliases=["leave", "disconnect", "Stop", "Leave", "Disconnect"])
async def stop_cmd(ctx):
    """Dừng phát nhạc và ngắt kết nối bot khỏi kênh thoại."""
    vc = ctx.voice_client
    if vc and vc.is_connected():
        if vc.is_playing():
            vc.stop()
        await vc.disconnect()
        await ctx.send("🛑 Đã dừng phát nhạc và ngắt kết nối khỏi kênh thoại.")
    else:
        await ctx.send("❌ Bot hiện không ở trong kênh thoại nào.")
      # ====================================================================
# PHẦN 9: LỆNH ANIME/MEDIA (Từ Railway)
# ====================================================================

@bot.command(name="animelist", aliases=["al", "Animelist", "Al"])
async def animelist_cmd(ctx):
    """Hiển thị danh sách Anime được cấu hình qua Railway."""
    global anime_list
    
    if not anime_list:
        return await ctx.send("❌ Danh sách Anime trống. Vui lòng cấu hình biến môi trường `ANIME_LIST_CONFIG` trên Railway.")
        
    embed = discord.Embed(
        title="🎬 Danh Sách Anime (Cấu hình từ Railway)",
        color=discord.Color.purple()
    )
    
    display_list = anime_list[:5] if len(anime_list) > 5 else anime_list
    
    for anime in display_list:
        title = anime.get("title", "Không rõ tên")
        genre = anime.get("genre", "Không rõ thể loại")
        rating = anime.get("rating", "N/A")
        
        embed.add_field(
            name=f"[{anime.get('id', 'N/A')}] {title}",
            value=f"**Thể loại:** {genre}\n**Rating:** {rating}/10",
            inline=True
        )
        
    if len(anime_list) > 5:
        embed.set_footer(text=f"Và {len(anime_list) - 5} anime khác... | Tổng cộng: {len(anime_list)}.")
        
    first_anime_url = anime_list[0].get("image_url")
    if first_anime_url:
        embed.set_thumbnail(url=first_anime_url)
        
    await ctx.send(embed=embed)
  # ====================================================================
# PHẦN 10: START BOT
# ====================================================================

@bot.event
async def on_ready():
    load_data()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bot đã sẵn sàng: {bot.user.name}")
    print("--------------------------------------------------")

if __name__ == '__main__':
    # Kiểm tra Token từ Biến môi trường
    if DISCORD_TOKEN == "YOUR_DISCORD_TOKEN_HERE":
        print("LỖI: Vui lòng thay thế DISCORD_TOKEN trong code hoặc thiết lập biến môi trường DISCORD_TOKEN.")
    else:
        bot.run(DISCORD_TOKEN)
      
