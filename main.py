import discord
from discord.ext import commands
import asyncio
import os
import json
import random
from gtts import gTTS
import re 
import time  # Rất quan trọng cho daily, use, inv

# ====================================================================
# KHAI BÁO BIẾN TOÀN CỤC (CRITICAL FIX)
# ====================================================================
# PHẢI KHAI BÁO CÁC BIẾN TOÀN CỤC NÀY TRƯỚC KHI CHẠY load_data() VÀ CÁC LỆNH KHÁC
FILE_USERS = "users.json"
FILE_GLOBAL = "global_data.json"
users = {}
global_data = {
    "admin_list": [],  # Sẽ được nạp từ Railway ENV
    "last_pet_id": 0
}
anime_list = []
custom_graphics = {} 
# ====================================================================
# PHẦN 1/10: KHỞI TẠO BOT VÀ THIẾT LẬP CƠ BẢN (FIXED)
# ====================================================================

# Định nghĩa Intents (Cần thiết cho Discord v2.0+)
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True        
intents.presences = True # Cho các tác vụ như 'get_member'

# Khởi tạo Bot với tiền tố CHỈ LÀ "b"
bot = commands.Bot(command_prefix=["b"], intents=intents, help_command=None) 
# ====================================================================
# PHẦN 2: CẤU HÌNH DATA VÀ HÀM TRỢ GIÚP (FIXED)
# ====================================================================

# --- CẤU HÌNH ITEMS (ID SỐ 001 - 499) ---
CONSUMABLES_ITEMS = {
    "001": {"name": "🎁 Hộp quà", "price": 500, "sell_price": 250, "desc": "Mở ra phần thưởng ngẫu nhiên."},
    "002": {"name": "💎 Đá quý", "price": 2000, "sell_price": 1000, "desc": "Nguyên liệu nâng cấp."},
    "003": {"name": "💎 Rương Đá Thần", "price": 0, "sell_price": 500, "desc": "Mở ra 1 loại Đá Buff ngẫu nhiên."}, 
    "004": {"name": "🎫 Lượt Boss Thêm", "price": 500, "sell_price": 250, "desc": "Cấp thêm 1 lượt săn Boss/Hunt."},
    "005": {"name": "🎟️ Vé EXP Pet", "price": 300, "sell_price": 150, "desc": "Tăng 50 EXP ngay lập tức cho Pet."},
}
PET_ITEMS = {
    "101": {"name": "🐾 Pet ngẫu nhiên", "price": 1000, "sell_price": 500, "desc": "Nhận một Pet ngẫu nhiên."},
    "102": {"name": "🍖 Thức ăn", "price": 100, "sell_price": 50, "desc": "Tăng EXP cho Pet."},
    "103": {"name": "🧪 Nước Tẩy LT", "price": 10000, "sell_price": 5000, "desc": "Gỡ Pet khỏi người dùng, biến Pet thành item Pet ngẫu nhiên (101)."},
}
PERMANENT_EQUIPMENT = {
    "201": {"name": "⚔️ Kiếm Gỗ", "price": 300, "sell_price": 150, "bonus": {"atk": 1}, "slot": "weapon", "desc": "+1 ATK."},
    "202": {"name": "🛡️ Khiên Sắt", "price": 400, "sell_price": 200, "bonus": {"hp": 5}, "slot": "armor", "desc": "+5 HP."},
    "203": {"name": "🔮 Ngọc Tăng Tốc", "price": 600, "sell_price": 300, "bonus": {"speed": 2}, "slot": "accessory", "desc": "+2 SPD."},
    "204": {"name": "💎 Ngọc Sức Mạnh", "price": 800, "sell_price": 400, "bonus": {"atk": 2}, "slot": "accessory", "desc": "+2 ATK."},
    "205": {"name": "🍀 Tứ Diệp Thảo", "price": 1000, "sell_price": 500, "bonus": {"luck": 10}, "slot": "accessory", "desc": "+10 LUCK."},
    "206": {"name": "💨 Giày Né Đòn", "price": 1200, "sell_price": 600, "bonus": {"dodge": 5}, "slot": "armor", "desc": "+5 Dodge."},
}
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
RING_SHOP = {
    "401": {"name": "Nhẫn Đồng", "cost": 50000, "emoji": "💍", "ring_img_key": "basic_ring_img"},
    "402": {"name": "Nhẫn Bạc", "cost": 250000, "emoji": "💍", "ring_img_key": "silver_ring_img"},
    "403": {"name": "Nhẫn Kim Cương", "cost": 1000000, "emoji": "💎", "ring_img_key": "diamond_ring_img"},
}
ALL_SHOP_ITEMS = {**CONSUMABLES_ITEMS, **PET_ITEMS, **PERMANENT_EQUIPMENT, **HUNT_BUFFS}

# --- CẤU HÌNH CÁC SHOP VÀ TÊN LỆNH ---
SHOP_CONFIGS = {
    "shop": {"title": "💰 Cửa Hàng Tiền Tệ (Shop)", "color": 0x33FF66, "items": ["001", "002", "004", "005"]},
    "petshop": {"title": "🐾 Cửa Hàng Vật Nuôi (Pet Shop)", "color": 0x9966FF, "items": ["101", "102", "103"]},
    "equipshop": {"title": "⚔️ Cửa Hàng Trang Bị (Equipment Shop)", "color": 0xFF9933, "items": ["201", "202", "203", "204", "205", "206"]},
    "buffshop": {"title": "✨ Cửa Hàng Buff (Buff Shop)", "color": 0x33CCFF, "items": ["301", "302", "303", "304", "305", "306", "307", "308"]},
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


# --- HÀM QUẢN LÝ DATA VÀ TÍCH HỢP RAILWAY (FIXED) ---
def load_data():
    global users, global_data, anime_list, custom_graphics
    
    if os.path.exists(FILE_USERS):
        with open(FILE_USERS, 'r') as f:
            users.update(json.load(f)) # Sử dụng update để giữ lại users rỗng nếu load lỗi
    
    if os.path.exists(FILE_GLOBAL):
        with open(FILE_GLOBAL, 'r') as f:
            global_data.update(json.load(f))

    
    # TÍCH HỢP 1: ADMIN_IDS TỪ RAILWAY
    admin_env = os.getenv("ADMIN_IDS")
    if admin_env:
        # Lưu ý: ID phải là chuỗi (string) trong JSON khi lưu
        admin_list_str = [id.strip() for id in admin_env.split(',') if id.strip()]
        global_data["admin_list"] = admin_list_str
    elif "admin_list" not in global_data:
        print("CẢNH BÁO: Không tìm thấy biến môi trường ADMIN_IDS. Sử dụng danh sách Admin trống.")
        global_data["admin_list"] = []

    # TÍCH HỢP 2: ANIME_LIST_CONFIG TỪ RAILWAY
    anime_config_env = os.getenv("ANIME_LIST_CONFIG")
    if anime_config_env:
        try:
            # Gán trực tiếp vào biến toàn cục anime_list
            globals()['anime_list'] = json.loads(anime_config_env)
            print(f"✅ Đã tải thành công {len(anime_list)} Anime từ Railway.")
        except json.JSONDecodeError:
            print("❌ LỖI: Biến ANIME_LIST_CONFIG không phải là JSON hợp lệ.")

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
    """Sử dụng hàm này thay vì tự gọi open()"""
    if data_dict is users:
        file_name = FILE_USERS
    elif data_dict is global_data:
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
    """Đảm bảo save_data() được gọi trong hàm này."""
    user = get_user(user_id)
    user["balance"] = user.get("balance", 0) + amount
    save_data(users) # Lưu users sau khi cập nhật

def is_admin(user_id):
    """Trả về True nếu user_id có trong danh sách admin_list (nạp từ ENV)."""
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
# PHẦN 3: LỆNH KINH TẾ VÀ SHOP (FIXED)
# ====================================================================

@bot.command(name="balance", aliases=["bal", "money", "Bal", "Money", "cf"]) # ADD ALIAS CF
async def balance_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = get_user(member.id)
    await ctx.send(f"💸 **{member.display_name}** hiện có **{user['balance']:,} xu**.")

@bot.command(name="daily", aliases=["Daily"])
async def daily_cmd(ctx):
    uid = str(ctx.author.id)
    user = get_user(uid)
    cooldown = 24 * 3600 
    
    if time.time() - user["last_daily"] >= cooldown:
        reward = 500
        update_balance(uid, reward) # update_balance đã tự gọi save_data(users)
        user["last_daily"] = time.time()
        save_data(users) # Cần lưu lại last_daily
        await ctx.send(f"✅ **{ctx.author.display_name}** đã nhận **{reward:,} xu** hàng ngày!")
    else:
        remaining = int(cooldown - (time.time() - user["last_daily"]))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await ctx.send(f"⏳ Bạn phải chờ thêm **{hours} giờ {minutes} phút** nữa để nhận quà hàng ngày.")

@bot.command(name="shop", aliases=["s", "bshop", "bpetshop", "bequipshop", "bbuffshop", 
                                  "S", "Bshop", "Bpetshop", "Bequipshop", "Bbuffshop", "itemshop", "shoppet"]) # ADD ALIASES TRÁNH TRÙNG P.9/10
async def shop_cmd(ctx):
    """Hiển thị các cửa hàng dựa trên lệnh gọi (bshop, bpetshop, etc.)."""
    
    command_name = ctx.invoked_with
    if command_name.startswith('b'):
        command_name = command_name[1:]

    # FIX: Chuyển alias của P.9/10 sang P.3
    if command_name in ["itemshop", "shoppet"]:
         command_name = "shop" # Mặc định chuyển về shop chính

    # --- HIỂN THỊ DANH MỤC SHOP (Nếu người dùng chỉ gõ bshop/bs) ---
    if command_name in ["shop", "s", "itemshop", "shoppet"]:
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

    item_id = item_id.zfill(3) 
    item_data = ALL_SHOP_ITEMS.get(item_id)
    
    if not item_data:
        return await ctx.send("❌ ID vật phẩm không hợp lệ hoặc không có trong cửa hàng.")

    user = get_user(ctx.author.id)
    cost = item_data["price"] * count

    if user["balance"] < cost:
        return await ctx.send(f"❌ Bạn không đủ **{cost:,} xu** để mua {count}x {item_data['name']}.")

    update_balance(ctx.author.id, -cost) # update_balance đã tự gọi save_data
    
    new_items = []
    for _ in range(count):
        unique_id = str(time.time()) + str(random.randint(100, 999))
        new_items.append({
            "shop_id": item_id,
            "name": item_data["name"],
            "unique_id": unique_id,
        })
    
    user["inventory"].extend(new_items)
    save_data(users) # Cần lưu lại inventory

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
    
    items_in_inv = [item for item in user["inventory"] if item.get("shop_id") == shop_id]
    
    if len(items_in_inv) < count:
        return await ctx.send(f"❌ Bạn chỉ có **{len(items_in_inv)}x** {item_data['name']} trong túi.")
        
    # Xóa vật phẩm khỏi túi đồ
    items_removed = 0
    i = 0
    while items_removed < count and i < len(user["inventory"]):
        if user["inventory"][i].get("shop_id") == shop_id:
            user["inventory"].pop(i)
            items_removed += 1
        else:
            i += 1
            
    total_sell_price = item_data["sell_price"] * count
    update_balance(ctx.author.id, total_sell_price) # update_balance đã tự gọi save_data
    save_data(users) # Cần lưu lại inventory sau khi xóa item
    
    await ctx.send(f"✅ Đã bán thành công **{count}x {item_data['name']}** với giá **{total_sell_price:,} xu**!")


@bot.command(name="ringshop", aliases=["rshop", "Ringshop", "Rshop"]) 
async def ring_shop_cmd(ctx):
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
        
    update_balance(ctx.author.id, -cost) # update_balance đã tự gọi save_data
    user["ring"] = item_id
    save_data(users)

    await ctx.send(f"✅ **{ctx.author.display_name}** đã mua và trang bị thành công {item_data['emoji']} **{item_data['name']}** với giá **{cost:,} xu**!")


@bot.command(name="customshop", aliases=["cshop", "Cshop"]) 
async def custom_shop_cmd(ctx, shop_type: str = None):
    if not custom_graphics:
        return await ctx.send("❌ Cửa hàng tùy chỉnh hiện đang trống.")
        
    shop_type = (shop_type or "all").lower()
    items_to_display = []
    
    current_id_counter = 501
    all_graphics_items = []
    
    # Tạo danh sách item với ID số 5xx
    for key, items in custom_graphics.items():
        if isinstance(items, list):
            for item in items:
                item_id = str(current_id_counter).zfill(3)
                item["id"] = item_id
                all_graphics_items.append(item)
                current_id_counter += 1

    # Phân loại để hiển thị
    if shop_type in ["bg", "backgrounds", "all"]:
        items_to_display.extend([i for i in all_graphics_items if 'backgrounds' in i.get('data', {}).get('type', '') or i['id'].startswith('50')])
    if shop_type in ["bn", "banners", "all"]:
        items_to_display.extend([i for i in all_graphics_items if 'banners' in i.get('data', {}).get('type', '') or i['id'].startswith('51')])
    if shop_type in ["em", "emojis", "all"]:
        items_to_display.extend([i for i in all_graphics_items if 'emojis' in i.get('data', {}).get('type', '') or i['id'].startswith('52')])
        
    if not items_to_display:
        return await ctx.send("❌ Không tìm thấy mặt hàng cho loại shop này.")
        
    embed = discord.Embed(
        title=f"🎨 Cửa Hàng Đồ Họa Tùy Chỉnh ({shop_type.upper()})",
        description="Mua các mặt hàng này sẽ thêm chúng vào túi đồ (inventory) của bạn. ID: 501-599",
        color=discord.Color.blue()
    )
    
    for item in items_to_display:
        item_type = item.get('data', {}).get('type', 'Item').title()
        
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
    current_id_counter = 501
    for key, items in custom_graphics.items():
        if isinstance(items, list):
            for item in items:
                item_id_internal = str(current_id_counter).zfill(3)
                if item_id_internal == item_id:
                    item_data = item
                    item_data["id"] = item_id_internal 
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
        
    update_balance(ctx.author.id, -cost) # update_balance đã tự gọi save_data
    
    user["inventory"].append({
        "shop_id": item_id,
        "name": f"[{item_type.title()}] {item_data['name']}",
        "unique_id": str(time.time()) + str(random.randint(100, 999)),
        "data": item_data 
    })
    save_data(users)
    
    await ctx.send(f"✅ **{ctx.author.display_name}** đã mua thành công **{item_data['name']}** ({item_id}) với giá **{cost:,} xu**!")
      # ====================================================================
# PHẦN 4: LỆNH TÚI ĐỒ VÀ SỬ DỤNG ITEM (FIXED)
# ====================================================================

@bot.command(name="inv", aliases=["items", "Inv", "Items", "inventory"]) # ADD ALIAS INVENTORY
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
        
        if shop_id.startswith("2"): 
            is_equipped = False
            for pet in user.get("pets", []):
                if pet.get("equipped_item") == unique_id:
                    is_equipped = True
                    break
            equipment.append((item, is_equipped))
        elif shop_id.startswith("5"): 
            custom_items.append(item)
        else:
            item_counts[shop_id] = item_counts.get(shop_id, 0) + 1

    # --- 2. FIELD: VẬT PHẨM TIÊU THỤ (Consumables & Pet Items & Buffs) ---
    consumable_text = ""
    # FIX: Cần đếm số lượng item tiêu thụ chính xác (item_counts)
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
    # FIX: Cần đếm số lượng item trang bị chính xác (equipment)
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
        # Nhóm các item tùy chỉnh theo shop_id
        custom_counts[item['shop_id']] = custom_counts.get(item['shop_id'], 0) + 1
        
    for shop_id, count in custom_counts.items():
        # Lấy tên item tùy chỉnh (Cần tìm lại item_data nếu muốn tên chính xác hơn)
        # Tạm thời dùng tên đã lưu trong inventory
        item_name = next((item.get("name") for item in custom_items if item.get("shop_id") == shop_id), "Custom Item")
        custom_text += f"`[{shop_id}]` **{item_name}** x{count}\n"

    if custom_text:
        inv_embed.add_field(name="🎨 Đồ Họa (Set: `bsetbg/bsetgif <URL>`)", 
                            value=custom_text, 
                            inline=False)
    else:
        inv_embed.add_field(name="🎨 Đồ Họa", 
                            value="*Chưa có đồ họa tùy chỉnh nào...*", 
                            inline=False)

    # --- 5. FIELD: BUFF HIỆN TẠI ---
    buff_text = ""
    current_time = time.time()
    if user.get("buffs"):
        # Lọc buff hết hạn (cần làm lại ở đây vì hunt_cmd chỉ lọc, inv_cmd nên hiển thị trạng thái hiện tại)
        active_buffs = {k: v for k, v in user["buffs"].items() if v["end_time"] > current_time}
        user["buffs"] = active_buffs # Cập nhật xóa buff hết hạn trong data

        for buff_type, buff_data in active_buffs.items():
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
    else:
        inv_embed.add_field(name="✨ Buff Đang Kích Hoạt", 
                            value="*Không có buff nào đang hoạt động.*", 
                            inline=False)


    inv_embed.set_footer(text="ID 6 chữ số: unique_id của Trang bị (Dùng để Equip/Unequip)")
    save_data(users) # Lưu lại data sau khi lọc buff
    await ctx.send(embed=inv_embed)


@bot.command(name="use", aliases=["Use"]) 
async def use_cmd(ctx, shop_id: str = None, pet_id: int = None):
    """Sử dụng vật phẩm (ID 3 chữ số)."""
    if shop_id is None:
        return await ctx.send("❌ Cú pháp: `buse <ID> [Pet_ID]`")
        
    shop_id = shop_id.zfill(3)
    user = get_user(ctx.author.id)
    
    # Tìm index và item_entry
    item_index = -1
    for i, item in enumerate(user["inventory"]):
        if item.get("shop_id") == shop_id:
            item_index = i
            break
            
    if item_index == -1:
        return await ctx.send(f"❌ Bạn không có vật phẩm với ID `{shop_id}` trong túi.")
        
    item_entry = user["inventory"][item_index]
    item_name = item_entry['name']
    item_data = ALL_SHOP_ITEMS.get(shop_id, {})
    
    # Xóa item khỏi túi đồ (trừ khi là item cần giữ lại)
    # Tạm thời xóa. Nếu logic không sử dụng, sẽ hoàn trả lại.
    user["inventory"].pop(item_index) 
    res = ""
    
    # 1. BUFFS (3xx)
    if shop_id.startswith("3"): 
        if item_data["type"] not in ["loot_rate", "exp_rate", "luck_rate"]:
            res = f"❌ Không thể sử dụng vật phẩm buff không xác định này."
            user["inventory"].append(item_entry) # Hoàn trả
        else:
            buff_type = item_data["type"]
            buff_value = item_data["value"]
            duration = item_data["duration"]
            current_time = time.time()
            
            # Ghi đè buff nếu buff mới mạnh hơn (hoặc đơn giản là reset thời gian)
            user["buffs"][buff_type] = {
                "value": buff_value,
                "end_time": current_time + duration
            }
            duration_display = f"{duration // 3600} giờ" if duration % 3600 == 0 else f"{duration // 60} phút"
            res = f"✨ Đã kích hoạt **{item_name}**! **{item_data['desc'].split(' trong ')[0]}** trong **{duration_display}**."
            
    # 2. PET ITEMS (1xx)
    elif shop_id == "101": 
        user["inventory"].append(item_entry) # Hoàn trả lại item đã bị xóa
        return await ctx.send(f"❌ Vui lòng sử dụng lệnh `brollpet` để mở **{item_name}**.")
    
    elif shop_id == "103": 
        if pet_id is None or pet_id <= 0: 
            user["inventory"].append(item_entry) # Hoàn trả
            return await ctx.send("❌ Cú pháp: `buse 103 <Pet_ID>`")
        
        target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
        if not target_pet: 
            user["inventory"].append(item_entry) # Hoàn trả
            return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
        user["pets"].remove(target_pet)
        
        pet_item_data = ALL_SHOP_ITEMS["101"]
        # Tạo item mới thay vì hoàn trả item cũ
        unique_id_new = str(time.time()) + str(random.randint(100, 999))
        user["inventory"].append({"shop_id": "101", "name": pet_item_data["name"], "unique_id": unique_id_new})
        res = f"🧪 Đã sử dụng **{item_name}**. Pet **{target_pet['name']}** đã được gỡ bỏ và bạn nhận lại **1x {pet_item_data['name']}**."

    # 3. CONSUMABLES (0xx)
    elif shop_id == "004": 
        user["boss_runs"] = user.get("boss_runs", 0) + 1
        res = f"🎫 Đã sử dụng **{item_name}**. Bạn nhận thêm **1 lượt** săn Boss/Hunt. Tổng lượt hiện có: **{user['boss_runs']}**."
        
    elif shop_id == "005": 
        if pet_id is None or pet_id <= 0: 
            user["inventory"].append(item_entry) # Hoàn trả
            return await ctx.send("❌ Cú pháp: `buse 005 <Pet_ID>`")
        
        target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
        if not target_pet: 
            user["inventory"].append(item_entry) # Hoàn trả
            return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
        exp_gain = 50
        target_pet["exp"] += exp_gain
        res = f"🎟️ Pet **{target_pet['name']}** nhận được **{exp_gain} EXP**! Tổng EXP hiện tại: {target_pet['exp']}."

    # 4. CÁC ITEMS KHÁC (Cần giữ lại nếu item không bị xóa)
    else:
        user["inventory"].append(item_entry)
        res = f"❌ Vật phẩm **{item_name}** không thể sử dụng bằng lệnh `buse` hoặc chưa có logic xử lý."
    
    save_data(users)
    await ctx.send(res)


@bot.command(name="equip", aliases=["Equip"])
async def equip_cmd(ctx, unique_id: str = None, pet_id: int = None):
    """Trang bị vật phẩm (ID 6 số) cho Pet (ID số)."""
    if unique_id is None or pet_id is None:
        return await ctx.send("❌ Cú pháp: `bequip <ID_6_số> <Pet_ID>`.")
    
    unique_id = unique_id[:6] # Chỉ lấy 6 ký tự đầu
    user = get_user(ctx.author.id)
    
    # 1. Tìm Trang bị trong túi đồ
    item_to_equip = next((item for item in user["inventory"] if item.get("unique_id", "").startswith(unique_id)), None)
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
    if pet_id is None:
        return await ctx.send("❌ Cú pháp: `bunequip <Pet_ID>`.")
        
    user = get_user(ctx.author.id)
    target_pet = next((p for p in user["pets"] if p.get("id") == pet_id), None)
    
    if not target_pet:
        return await ctx.send(f"❌ Không tìm thấy Pet với ID **{pet_id}**.")
        
    equipped_unique_id = target_pet.get("equipped_item")
    if not equipped_unique_id:
        return await ctx.send(f"❌ Pet **{target_pet['name']}** không có trang bị nào.")
        
    equipped_item = next((item for item in user["inventory"] if item.get("unique_id") == equipped_unique_id), None)
    item_name = equipped_item["name"] if equipped_item else "Trang bị không rõ"
    
    target_pet["equipped_item"] = None
    save_data(users)
    await ctx.send(f"✅ Đã gỡ **{item_name}** khỏi Pet **{target_pet['name']}**.")
  # ====================================================================
# PHẦN 5: LỆNH PET VÀ HUNTING (FIXED)
# ====================================================================

@bot.command(name="rollpet", aliases=["rp", "Rollpet", "Rp"])
async def random_pet_cmd(ctx):
    uid = ctx.author.id; user = get_user(uid)
    
    pet_item = next((item for item in user.get("inventory", []) if item.get("shop_id") == "101"), None) 
    if not pet_item: return await ctx.send("❌ Bạn không có **🐾 Pet ngẫu nhiên** (ID: 101) trong túi. Dùng `bbuy 101` để mua.")
    
    # Xóa 1 Pet ngẫu nhiên khỏi túi
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


@bot.command(name="pets", aliases=["z", "Pets", "Z", "zoo"]) # ADD ALIAS ZOO
async def pets_cmd(ctx):
    user = get_user(ctx.author.id)
    pets = user.get("pets")
    
    if not pets:
        return await ctx.send("❌ Bạn chưa sở hữu Pet nào. Dùng `brollpet`.")
        
    embed = discord.Embed(
        title=f"🐾 Bộ Sưu Tập Pet của {ctx.author.display_name}",
        color=discord.Color.blue()
    )
    
    for pet in pets:
        item_unique_id = pet.get("equipped_item")
        item_name = "Không"
        
        if item_unique_id:
            # FIX: Lấy item bằng unique_id chính xác
            equipped_item = next((item for item in user["inventory"] if item.get("unique_id") == item_unique_id), None)
            if equipped_item:
                item_name = equipped_item["name"]
        
        stats = pet["stats"]
        rarity_display = PET_RARITIES.get(pet['rarity'], {}).get('name', pet['rarity'])
        name_line = f"[{pet['id']}] **{pet['name']}** (Lv.{pet['level']}) - *{rarity_display}*"
        info_line = f"HP/ATK/SPD: {stats['hp']}/{stats['atk']}/{stats['speed']}\nEXP: {pet['exp']}\nTrang bị: *{item_name}*"
        
        embed.add_field(name=name_line, value=info_line, inline=True)
        
    await ctx.send(embed=embed)


@bot.command(name="hunt", aliases=["Hunt"])
@commands.cooldown(1, 60, commands.BucketType.user) # ADD COOLDOWN (60 giây)
async def hunt_cmd(ctx):
    uid = str(ctx.author.id)
    user = get_user(uid)
    
    if user["boss_runs"] <= 0:
        # Nếu hết lượt, xóa cooldown để người dùng có thể thử lại
        hunt_cmd.reset_cooldown(ctx) 
        return await ctx.send("❌ Bạn đã hết lượt săn Boss/Hunt. Dùng `bbuy 004` để mua thêm lượt.")
        
    if not user["pets"]:
        hunt_cmd.reset_cooldown(ctx)
        return await ctx.send("❌ Bạn cần ít nhất một Pet để tham gia săn Boss. Dùng `brollpet`.")

    # 1. TÍNH TOÁN BUFFS VÀ STATS
    current_time = time.time()
    active_buffs = {k: v for k, v in user["buffs"].items() if v["end_time"] > current_time}
    user["buffs"] = active_buffs 
    
    base_win_rate = 0.5
    luck_buff = active_buffs.get("luck_rate", {}).get("value", 1.0)
    final_win_rate = base_win_rate * luck_buff

    strongest_pet = max(user["pets"], key=lambda p: p["stats"]["hp"] + p["stats"]["atk"] + p["stats"]["speed"])
    
    # 2. XỬ LÝ KẾT QUẢ HUNT
    user["boss_runs"] -= 1
    save_data(users)
    
    result_text = f"**{ctx.author.display_name}** và Pet **{strongest_pet['name']}** đã tham gia săn Boss!"
    
    if random.random() < final_win_rate: # WIN
        reward_money = random.randint(1000, 3000)
        reward_exp = random.randint(50, 150)
        
        loot_buff = active_buffs.get("loot_rate", {}).get("value", 1.0)
        final_reward_money = int(reward_money * loot_buff)
        
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
        
    save_data(users) # Cần lưu lại EXP và buff đã lọc
    await ctx.send(f"{result_text}\n\n{res}\n\n*Lượt còn lại:* **{user['boss_runs']}**")

# Xử lý lỗi cooldown cho lệnh hunt
@hunt_cmd.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        seconds = int(error.retry_after)
        await ctx.send(f"⏰ Bạn vừa đi săn rồi. Hãy chờ **{seconds}** giây nữa để tiếp tục!")
      # ====================================================================
# PHẦN 6: LỆNH TƯƠNG TÁC (SOCIAL & ROLEPLAY) - ĐÃ FIX LỖI ALIAS
# ====================================================================

SOCIAL_ACTIONS = {
    "hit": {"past": "đánh", "desc": "đã tung cú đấm chí mạng vào", "emoji": "💥", "aliases": ["dam"]}, 
    "hug": {"past": "ôm", "desc": "đã ôm chặt lấy", "emoji": "🫂", "aliases": ["om"]}, 
    "kiss": {"past": "hôn", "desc": "đã tặng một nụ hôn e thẹn cho", "emoji": "💖", "aliases": ["hon"]}, 
    "pat": {"past": "xoa đầu", "desc": "đã xoa đầu đầy cưng chiều", "emoji": "😊", "aliases": []}, 
    "slap": {"past": "tát", "desc": "đã tát một cái đau điếng vào", "emoji": "💢", "aliases": ["tat"]}, 
    "cuddle": {"past": "rúc vào", "desc": "đã rúc vào người", "emoji": "💞", "aliases": []}, 
    "poke": {"past": "chọc", "desc": "đã chọc vào má", "emoji": "👉", "aliases": []}, 
    "yeu": {"past": "yêu", "desc": "đã gửi tình yêu đến", "emoji": "❤️", "aliases": ["love"]},
    "chui": {"past": "chửi", "desc": "đã chửi mắng thậm tệ", "emoji": "🤬", "aliases": []},
    # Lệnh cá nhân (có cùng giá trị past là "tự nhận là" -> dễ gây lỗi alias)
    "ngu": {"past": "tự nhận là", "desc": "đã tự nhận mình là", "emoji": "😴", "is_self": True, "aliases": []},
    "khon": {"past": "tự nhận là", "desc": "đã tự nhận mình là", "emoji": "💡", "is_self": True, "aliases": []},
}
MARRIAGE_FEE = 10000

# Hàm trợ giúp lấy member (giữ nguyên)
async def get_member(ctx, target_str):
    if not target_str:
        return None
    try:
        member_id = int(target_str.strip('<@!>'))
        if ctx.guild:
            member = ctx.guild.get_member(member_id)
            if member:
                return member
            try:
                return await ctx.guild.fetch_member(member_id)
            except discord.NotFound:
                pass
        return await bot.fetch_user(member_id) 
    except (ValueError, discord.NotFound):
        return None


# HÀM CALLBACK CHUNG
async def interact_cmd(ctx, target: str = None): 
    
    invoked_name = ctx.invoked_with.lower()
    if invoked_name.startswith('b'):
        action_name = invoked_name[1:]
    else:
        action_name = invoked_name
        
    action_data = SOCIAL_ACTIONS.get(action_name)
    
    # FIX: Thêm logic để xử lý lệnh 'troll' thủ công (nếu action_name là 'troll')
    if action_name == "troll":
        action_data = {"past": "troll", "desc": "đã troll", "emoji": "😈", "aliases": []}

    if not action_data: return 

    is_self_action = action_data.get("is_self", False)

    if is_self_action:
        # Xử lý lệnh tự tương tác (ngu, khon)
        display_name = action_name.capitalize()
        embed = discord.Embed(
            description=f"{action_data['emoji']} **{ctx.author.display_name}** {action_data['desc']} **{display_name}**.",
            color=discord.Color.blue()
        )
        return await ctx.send(embed=embed)


    if target is None:
        return await ctx.send(f"❌ Cú pháp: `b{action_name} <@người dùng>`.")

    member_target = await get_member(ctx, target)
    if not member_target:
        return await ctx.send("❌ Người dùng không hợp lệ.")
        
    if member_target.id == ctx.author.id:
        return await ctx.send("❌ Bạn không thể tự thực hiện hành động này.")


    # Lấy URL GIF
    author_data = get_user(ctx.author.id)
    gif_url = get_action_image_url(author_data, f"{action_name}_gif")

    embed = discord.Embed(
        description=f"{action_data['emoji']} **{ctx.author.display_name}** {action_data['desc']} **{member_target.display_name}**!",
        color=discord.Color.red() if action_name in ["hit", "slap", "chui"] else discord.Color.green()
    )
    embed.set_image(url=gif_url)
    await ctx.send(embed=embed)


# Tạo lệnh tương tác và aliases cho từng hành động (ĐÃ SỬA LỖI VỀ ALIAS TỰ NHẬN LÀ)
for action, data in SOCIAL_ACTIONS.items():
    aliases = []
    # CHỈ THÊM data["past"] VÀO ALIASES NẾU NÓ KHÔNG PHẢI LÀ LỆNH TỰ TƯƠNG TÁC
    # để tránh trùng lặp "tự nhận là" giữa ngu và khon
    if not data.get("is_self", False):
        aliases.append(data["past"])
        aliases.append(data["past"].capitalize())
    
    # Thêm tên lệnh viết hoa và aliases tùy chỉnh
    aliases.append(action.capitalize())
    aliases.extend(data.get("aliases", []))
    
    # Đảm bảo aliases không bị trùng lặp
    aliases = list(set(aliases)) 
    
    bot.command(name=action, aliases=aliases)(interact_cmd)


# --- BỔ SUNG LỆNH 'TROLL' RIÊNG BIỆT (ĐÃ FIX LỖI TRÙNG TÊN) ---
@bot.command(name="troll", aliases=["Troll"])
async def troll_cmd_fix(ctx, target: str = None):
    # Định nghĩa dữ liệu troll tạm thời và gọi hàm tương tác chung
    SOCIAL_ACTIONS["troll"] = {"past": "troll", "desc": "đã troll", "emoji": "😈", "aliases": []}
    await interact_cmd(ctx, target)
    # Xóa key tạm thời để không ảnh hưởng đến vòng lặp
    if "troll" in SOCIAL_ACTIONS:
        del SOCIAL_ACTIONS["troll"] 


# --- CÁC LỆNH HÔN NHÂN/TÌNH YÊU (Giữ nguyên) ---

@bot.command(name="propose", aliases=["Propose"]) 
async def propose_cmd(ctx, target: str = None):
    member_target = await get_member(ctx, target)
    if not member_target or member_target.id == ctx.author.id: return await ctx.send("❌ Người dùng không hợp lệ.")

    author_data = get_user(ctx.author.id)
    if author_data["married_to"]: return await ctx.send("❌ Bạn đã kết hôn rồi.")
    if not author_data.get("ring"): return await ctx.send("❌ Bạn cần mua nhẫn cưới (Ring) trước khi cầu hôn! Dùng `bringshop`.")

    embed = discord.Embed(
        title="💖 LỜI CẦU HÔN NGỌT NGÀO",
        description=f"**{member_target.mention}**, **{ctx.author.display_name}** đang cầu hôn bạn! Dùng `baccept {ctx.author.mention}` để đồng ý.",
        color=discord.Color.light_grey()
    )
    embed.set_image(url=DEFAULT_IMAGE_LINKS["propose_gif"])
    embed.set_footer(text=f"Người cầu hôn đã chuẩn bị nhẫn {RING_SHOP.get(author_data['ring'], {}).get('name', 'Bí ẩn')}!")
    
    await ctx.send(member_target.mention, embed=embed)


@bot.command(name="accept", aliases=["Accept"]) 
async def accept_cmd(ctx, proposer: str = None):
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
    update_balance(ctx.author.id, -MARRIAGE_FEE) # update_balance đã tự gọi save_data
    save_data(users) # Lưu lại data của người cầu hôn
    
    embed = discord.Embed(
        title="💍 KẾT HÔN THÀNH CÔNG!",
        description=f"🎉 **{member_proposer.display_name}** và **{ctx.author.display_name}** đã chính thức về chung một nhà! Chúc mừng hạnh phúc!",
        color=discord.Color.purple()
    )
    embed.set_image(url=DEFAULT_IMAGE_LINKS["accept_gif"])
    await ctx.send(f"{member_proposer.mention} {ctx.author.mention}", embed=embed)


@bot.command(name="divorce", aliases=["Divorce"]) 
async def divorce_cmd(ctx):
    user = get_user(ctx.author.id)
    spouse_id = user["married_to"]
    
    if not spouse_id: return await ctx.send("❌ Bạn chưa kết hôn.")
    
    spouse = await get_member(ctx, str(spouse_id))

    # Xóa trạng thái kết hôn của cả hai
    user["married_to"] = None
    spouse_data = get_user(spouse_id)
    if spouse_data:
        spouse_data["married_to"] = None
        
    save_data(users)

    spouse_name = spouse.display_name if spouse else "người bạn đời cũ (không tìm thấy)"
    await ctx.send(f"💔 **{ctx.author.display_name}** và **{spouse_name}** đã ly hôn. Hẹn gặp lại kiếp sau.")


@bot.command(name="wife", aliases=["husband", "spouse", "Wife", "Husband", "Spouse"]) 
async def check_spouse_cmd(ctx):
    user = get_user(ctx.author.id)
    spouse_id = user["married_to"]
    
    if not spouse_id: return await ctx.send("❌ Bạn chưa kết hôn.")
    
    spouse = await get_member(ctx, str(spouse_id))
    if spouse:
        await ctx.send(f"❤️ Người bạn đời hiện tại của **{ctx.author.display_name}** là **{spouse.display_name}**.")
    else:
        await ctx.send("⚠️ Bạn đã kết hôn, nhưng không tìm thấy người bạn đời đó trong server này nữa.")
        
      # ====================================================================
# PHẦN 7: LỆNH TÙY CHỈNH (CUSTOMIZATION) (FIXED)
# ====================================================================

# Hàm kiểm tra URL cơ bản (Đã có sẵn ở P.1)
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
  # ====================================================================
# PHẦN 8/10: LỆNH ADMIN VÀ UTILITY (FIXED)
# ====================================================================

# LỆNH ADMIN (Đã fix logic để dùng global_data)
@bot.command(name="addadmin")
@commands.check(lambda ctx: str(ctx.author.id) == str(ctx.guild.owner.id)) 
async def addadmin_cmd(ctx, member: discord.Member):
    """Thêm một thành viên vào danh sách Admin của bot."""
    member_id_str = str(member.id)
    admin_list = global_data.get("admin_list", [])
    
    if member_id_str not in admin_list:
        admin_list.append(member_id_str)
        global_data["admin_list"] = admin_list
        save_data(global_data)
        await ctx.send(f"✅ Đã thêm **{member.display_name}** vào danh sách Admin bot. (Dùng ENV/JSON)")
    else:
        await ctx.send(f"❌ **{member.display_name}** đã là Admin rồi.")

@bot.command(name="deladmin", aliases=["removeadmin"])
@commands.check(lambda ctx: str(ctx.author.id) == str(ctx.guild.owner.id)) 
async def deladmin_cmd(ctx, member: discord.Member):
    """Xóa một thành viên khỏi danh sách Admin của bot."""
    member_id_str = str(member.id)
    admin_list = global_data.get("admin_list", [])

    if member_id_str in admin_list:
        admin_list.remove(member_id_str)
        global_data["admin_list"] = admin_list
        save_data(global_data)
        await ctx.send(f"✅ Đã xóa **{member.display_name}** khỏi danh sách Admin bot.")
    else:
        await ctx.send(f"❌ **{member.display_name}** không có trong danh sách Admin.")

# LỆNH PHÁT NHẠC (PLAY) (FIXED: Thêm xử lý lỗi và xóa file)
@bot.command(name="play", aliases=["tts"])
async def play_cmd(ctx, *, source: str = None):
    if source is None:
        return await ctx.send(f"❌ Cú pháp: `{ctx.prefix}play <URL file âm thanh>` hoặc `{ctx.prefix}play <văn bản TTS>`.")

    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("❌ Bạn phải tham gia vào kênh thoại (Voice Channel) để sử dụng lệnh này.")

    channel = ctx.author.voice.channel
    vc = ctx.voice_client
    tts_filename = f"tts_{ctx.author.id}.mp3"
    
    try:
        if vc is None:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)
        
        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.5)

        # Xử lý TTS
        if not (is_valid_url(source) and (source.endswith(('.mp3', '.mp4', '.ogg', '.wav')) or "youtube" in source or "youtu.be" in source)):
            tts = gTTS(source, lang='vi')
            tts.save(tts_filename)
            vc.play(discord.FFmpegPCMAudio(tts_filename), after=lambda e: print('Done playing TTS', e))
            await ctx.send(f"🗣️ Đã phát TTS: **{source}**")
            
        # Xử lý URL
        else:
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            vc.play(discord.FFmpegPCMAudio(source, **FFMPEG_OPTIONS), after=lambda e: print('Done playing URL', e))
            await ctx.send(f"🎶 Đã bắt đầu phát nhạc từ URL: **{source}**")

        # Chờ phát xong
        while vc.is_playing() or vc.is_paused():
            await asyncio.sleep(1)
            
    except Exception as e:
        await ctx.send(f"❌ Đã xảy ra lỗi trong quá trình phát: {e}")
        
    finally:
        # Đảm bảo file được xóa và bot ngắt kết nối
        if os.path.exists(tts_filename):
            os.remove(tts_filename)
        if vc and vc.is_connected():
            await vc.disconnect()

# LỆNH DỪNG (STOP)
@bot.command(name="stop", aliases=["leave", "disconnect"])
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


# LỆNH TRỢ GIÚP (HELP) - Cập nhật aliases theo P.6
@bot.command(name="help", aliases=["commands", "h", "bhelp", "b"]) 
async def help_cmd(ctx):
    """Hiển thị danh sách các lệnh."""
    prefix = ctx.prefix
    
    embed = discord.Embed(
        title="🌸 Sổ Tay Lệnh Của Tớ 🌸",
        description=f"Hihi, tớ là Bot dễ thương nhất trong server này! Bạn dùng `{prefix}tênlệnh` nha.",
        color=discord.Color.pink()
    )
    
    embed.add_field(
        name="🎶 Nhóm Nhạc & Giọng Nói", 
        value=f"• `{prefix}play` / `{prefix}tts` (Link/Text): Tớ hát cho bạn nghe, hoặc đọc văn bản siêu nhanh.\n"
              f"• `{prefix}stop` / `{prefix}leave`: Dừng tớ lại và tớ sẽ tạm biệt bạn.", 
        inline=False
    )
                    
    # Cập nhật theo SOCIAL_ACTIONS (P.6)
    embed.add_field(
        name="🧸 Nhóm Tương Tác Cưng Chiều", 
        value=f"**Tình cảm:** `{prefix}hug`, `{prefix}kiss`, `{prefix}yeu`, `{prefix}propose`\n"
              f"**Trêu chọc:** `{prefix}hit`, `{prefix}slap`, `{prefix}chui`, `{prefix}troll`\n"
              f"**Tự nhận:** `{prefix}ngu`, `{prefix}khon`", 
        inline=False
    )
    
    # Cập nhật theo logic P.3, P.4, P.5
    embed.add_field(
        name="🕹️ Nhóm Game & Kinh Tế",
        value=f"• `{prefix}balance` / `{prefix}cf`: Kiểm tra tiền.\n"
              f"• `{prefix}shop` / `{prefix}bpetshop`: Xem các cửa hàng (Mua: `{prefix}buy <ID>`).\n"
              f"• `{prefix}inv`: Xem túi đồ.\n"
              f"• `{prefix}rollpet`: Mở Pet ngẫu nhiên.\n"
              f"• `{prefix}hunt`: Đi săn Boss/Loot (Cooldown 60s).\n"
              f"• `{prefix}pets` / `{prefix}zoo`: Xem danh sách Pet và Stats.\n"
              f"• `{prefix}equip`/`{prefix}unequip`: Trang bị/Gỡ đồ cho Pet.",
        inline=False
    )

    embed.add_field(
        name="⚙️ Nhóm Tiện Ích & Quản Lý",
        value=f"• `{prefix}help` / `{prefix}b`: Xem lại menu này.\n"
              f"• `{prefix}profile`: Xem Profile và ảnh nền.\n"
              f"• `{prefix}setbg`/`{prefix}setgif`: Đặt ảnh/GIF tùy chỉnh.\n"
              f"• `{prefix}addadmin <@user>`: Quản lý quyền Admin (chỉ Chủ Server).",
        inline=False
    )

    embed.set_footer(text="Cảm ơn bạn đã sử dụng tớ nha! ❤️")
    
    await ctx.send(embed=embed)
  # ====================================================================
# PHẦN 9/10: HỆ THỐNG GAME VÀ KINH TẾ (HOÀN CHỈNH - GỠ BỎ TRÙNG LẶP)
# ====================================================================

# ⚠️ LƯU Ý: TOÀN BỘ LOGIC CỦA PHẦN NÀY ĐÃ ĐƯỢC CHUYỂN HOẶC TÍCH HỢP VÀO
#           CÁC PHẦN 2, 3, 4, 5 ĐỂ TRÁNH TRÙNG LẶP VÀ LỖI DỮ LIỆU.

# CÁC LỆNH ĐÃ ĐƯỢC XỬ LÝ (TRÁNH TRÙNG LẶP):
# - `bcf` (balance) -> Đã xử lý ở P.3
# - `bitemshop` (shop) -> Đã xử lý ở P.3
# - `bbuy` (buy) -> Đã xử lý ở P.3

@bot.command(name="shoppet_dummy", aliases=["shpt"])
async def shoppet_dummy_cmd(ctx):
    """Giữ lại lệnh này để giữ cấu trúc 10 phần, nhưng sử dụng lệnh Shop chính."""
    await ctx.send("✅ Lệnh `bshoppet` (Cửa hàng Pet) đã được tích hợp vào lệnh `bshop` hoặc `bpetshop`!")
  
        await ctx.send(f"❌ Đã xảy ra lỗi: {error}")

if __name__ == "__main__":
    try:
        # Nếu bạn dùng os.getenv, hãy đảm bảo biến môi trường được thiết lập
        if TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("⚠️ CẢNH BÁO: Vui lòng thay 'YOUR_BOT_TOKEN_HERE' bằng token bot thực tế của bạn.")
        bot.run(TOKEN)
    except discord.HTTPException as e:
        print(f"❌ LỖI KẾT NỐI DISCORD: Vui lòng kiểm tra Token và Intents. Chi tiết: {e}")
    except Exception as e:
        print(f"❌ LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT: {e}")
      # ====================================================================
# PHẦN 10: CHẠY BOT (ĐÃ FIX LỖI TOKEN CHO RAILWAY)
# ====================================================================

# CÁC LỆNH ĐÃ ĐƯỢC XỬ LÝ (TRÁNH TRÙNG LẶP):
# - `binv` (inv) -> Đã xử lý ở P.4
# - `bhunt` (hunt) -> Đã xử lý ở P.5 (có cooldown)
# - `bzoo` (pets) -> Đã xử lý ở P.5

@bot.command(name="sleep")
async def sleep_cmd(ctx):
    """Xem cooldown của bạn."""
    # Logic này chỉ là placeholder
    await ctx.send("😴 Lệnh `bsleep` sẽ được sử dụng để giảm cooldown cho các lệnh khác trong phiên bản hoàn chỉnh!")


# ====================================================================
# CHẠY BOT (Dùng Biến Môi Trường DISCORD_TOKEN)
# ====================================================================

@bot.event
async def on_ready():
    # Giả sử hàm load_data() đã được định nghĩa ở các phần trước
    try:
        load_data() # Gọi hàm load data khi bot sẵn sàng
        print(f'✅ Bot đã sẵn sàng: {bot.user.name} (ID: {bot.user.id})')
        print(f'Số lượng người dùng đã tải: {len(users)}')
    except NameError:
        print("⚠️ CẢNH BÁO: Hàm load_data/biến users chưa được định nghĩa. Bot vẫn chạy nhưng không có data.")
    except Exception as e:
        print(f"❌ LỖI KHI TẢI DỮ LIỆU: {e}")
        
    await bot.change_presence(activity=discord.Game(name=f"bhelp | Chúc mọi người vui vẻ!"))
    print('-------------------------------------------')

# Thêm logic để xử lý sự kiện khi lệnh không tồn tại (tránh lỗi)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Không cần phản hồi cho lỗi này để tránh làm phiền
        pass
    else:
        # In các lỗi khác ra console để debug
        print(f"❌ LỖI LỆNH: {error}")
        await ctx.send(f"❌ Đã xảy ra lỗi: {error}")

if __name__ == "__main__":
    # Đọc Token từ Biến Môi Trường DISCORD_TOKEN (Chuẩn Railway)
    TOKEN = os.getenv('DISCORD_TOKEN') 
    
    if TOKEN:
        try:
            print("Đang khởi động bot...")
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ LỖI KẾT NỐI: Token Bot không hợp lệ. Vui lòng kiểm tra lại biến DISCORD_TOKEN.")
        except discord.HTTPException as e:
            print(f"❌ LỖI KẾT NỐI DISCORD: Vui lòng kiểm tra Token và Intents. Chi tiết: {e}")
        except Exception as e:
            print(f"❌ LỖI KHÔNG XÁC ĐỊNH KHI CHẠY BOT: {e}")
    else:
        print("❌ LỖI CẤU HÌNH: Không tìm thấy biến môi trường DISCORD_TOKEN. Vui lòng thiết lập biến này trên Railway.")
    
# --- KẾT THÚC FILE main.py ---
        
