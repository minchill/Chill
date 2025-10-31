import discord
from discord.ext import commands, tasks
import os
import json
import random
import asyncio
import tempfile
import time
from datetime import datetime
from gtts import gTTS
import aiohttp
import io
from discord import FFmpegPCMAudio 

# --- CẤU HÌNH BOT (CHỈ DÙNG TIỀN TỐ 'b') ---
TOKEN = os.getenv("DISCORD_TOKEN") 

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# Ghi đè lệnh help mặc định của discord
bot = commands.Bot(command_prefix=['b'], intents=intents, help_command=None) 

# ----------------- DATA (JSON) -----------------
DATA_FILE = "user_data.json"

def load_data(file_name=DATA_FILE):
    """Tải dữ liệu từ file JSON."""
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if 'global_data' not in data:
                    data['global_data'] = {"last_daily_shop_update": 0, "shop_items": {}, "daily_quest": {}}
                return data
            except json.JSONDecodeError:
                return {"global_data": {"last_daily_shop_update": 0, "shop_items": {}, "daily_quest": {}}}
    return {"global_data": {"last_daily_shop_update": 0, "shop_items": {}, "daily_quest": {}}}

def save_data(data, file_name=DATA_FILE):
    """Lưu dữ liệu vào file JSON."""
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Tải dữ liệu và tách users/global_data
data_store = load_data()
users = {k: v for k, v in data_store.items() if k != 'global_data'}
global_data = data_store.get('global_data', {"last_daily_shop_update": 0, "shop_items": {}, "daily_quest": {}})

# Biến đếm ID toàn cục (Dùng để gán ID duy nhất cho Pet/Item)
global_pet_id_counter = 1
for user_id, user_data in users.items():
    for pet in user_data.get('pets', []):
        if pet.get('id'):
            global_pet_id_counter = max(global_pet_id_counter, pet['id'] + 1)
          # ----------------- DỮ LIỆU NGẪU NHIÊN & CẤU HÌNH PET -----------------
PET_NAMES = ["Mèo Thần Tốc", "Cún Lửa", "Rồng Cỏ", "Thỏ Điện", "Gấu Nước"]
PET_ELEMENTS = ["Lửa", "Nước", "Cỏ", "Điện", "Đất", "Gió"]
SKILLS = ["Tấn Công Mạnh", "Phòng Thủ Kín", "Hồi Máu", "Tốc Độ Cao", "Bảo Vệ"]
RARITY_CHANCES = {"Phổ Biến": 0.50, "Hiếm": 0.30, "Sử Thi": 0.15, "Thần Thoại": 0.05}
CHEST_NAME = "💎 Rương Đá Thần" 

# --- CẤU HÌNH ITEM TRANG BỊ Vĩnh viễn (ĐÃ CẬP NHẬT) ---
PERMANENT_EQUIPMENT = {
    "R1": {"name": "⚔️ Kiếm Gỗ", "price": 2500, "sell_price": 1250, "bonus": {"ATK": 5, "HP": 0, "DEF": 0, "SPD": 0, "LUCK": 0, "EVASION": 0}},
    "R2": {"name": "🛡️ Khiên Sắt", "price": 5000, "sell_price": 2500, "bonus": {"ATK": 0, "HP": 50, "DEF": 5, "SPD": 0, "LUCK": 0, "EVASION": 0}},
    "R3": {"name": "🔮 Ngọc Tăng Tốc", "price": 10000, "sell_price": 5000, "bonus": {"ATK": 0, "HP": 0, "DEF": 0, "SPD": 5, "LUCK": 0, "EVASION": 0}},
    "R4": {"name": "💎 Ngọc Sức Mạnh", "price": 10000, "sell_price": 5000, "bonus": {"ATK": 10, "HP": 0, "DEF": 0, "SPD": 0, "LUCK": 0, "EVASION": 0}},
    "R5": {"name": "🍀 Tứ Diệp Thảo", "price": 15000, "sell_price": 7500, "bonus": {"ATK": 0, "HP": 0, "DEF": 0, "SPD": 0, "LUCK": 5, "EVASION": 0}},
    "R6": {"name": "💨 Giày Né Đòn", "price": 15000, "sell_price": 7500, "bonus": {"ATK": 0, "HP": 0, "DEF": 0, "SPD": 0, "LUCK": 0, "EVASION": 5}}
}

# --- CẤU HÌNH CÁC VẬT PHẨM CỐ ĐỊNH (BASE) ---
BASE_SHOP_ITEMS = {
    "1": {"name": "🎁 Hộp quà", "price": 500, "sell_price": 250},
    "2": {"name": "🐾 Pet ngẫu nhiên", "price": 1000, "sell_price": 500},
    "3": {"name": "🍖 Thức ăn", "price": 200, "sell_price": 100}, 
    "4": {"name": "💎 Đá quý", "price": 2000, "sell_price": 1000},
    "5": {"name": CHEST_NAME, "price": 3000, "sell_price": 1500}
}
HUNT_BUFFS = {
    "6": {"name": "Đá Tăng Tỉ Lệ", "duration": 1800, "type": "catch_chance", "value": 0.15, "desc": "Tăng 15% tỉ lệ bắt Pet (30 phút).", "price": 5000, "sell_price": 2500},
    "7": {"name": "Đá Nhân EXP", "duration": 1800, "type": "exp_multiplier", "value": 2.0, "desc": "Nhân đôi EXP Pet nhận được (30 phút).", "price": 5000, "sell_price": 2500},
    "8": {"name": "Đá Bùa May Mắn", "duration": 3600, "type": "hidden_chance", "value": 0.05, "desc": "Tăng 5% cơ hội bắt Pet Ẩn (1 giờ).", "price": 10000, "sell_price": 5000}
}
for id, item in HUNT_BUFFS.items(): BASE_SHOP_ITEMS[id] = item

# --- CẤU HÌNH QUESTS ---
QUESTS_CONFIG = {
    "q1": {"desc": "Sử dụng lệnh `bh` (hunt) 5 lần.", "reward_coin": 1000, "reward_item_id": "3", "target_count": 5, "command": "hunt"},
    "q2": {"desc": "Chiến thắng `bpve` 2 lần.", "reward_coin": 1500, "reward_item_id": "4", "target_count": 2, "command": "pve"},
    "q3": {"desc": "Mua 1 vật phẩm từ `bshop`.", "reward_coin": 500, "reward_item_id": "1", "target_count": 1, "command": "buy"},
}

# --- CẤU HÌNH AUTO FIGHT & BOSS ---
WILD_PET_CONFIG = {"EXP_BASE": 100, "COIN_BASE": 150, "COOLDOWN": 120}
BOSS_CONFIG = {
    "COOLDOWN": 3600, "BOSS_NAMES": ["King Lửa", "Thủy Tộc Giận DỮ", "Lãnh Chúa Gió"],
    "REWARD_ITEM_ID": "5", "EXP_BASE": 500, "COIN_BASE": 1000, "POWER_MULTIPLIER": 1.5 
}

# --- CÁC HÀM HỖ TRỢ DỮ LIỆU TOÀN CỤC & SHOP ---

def save_global_data():
    """Lưu dữ liệu toàn cục."""
    data_store = load_data()
    data_store['global_data'] = global_data
    save_data(data_store)

def update_daily_shop():
    """Cập nhật các vật phẩm ngẫu nhiên và cố định hàng ngày."""
    current_day = datetime.now().day
    if global_data.get('last_daily_shop_update_day') != current_day:
        
        # Chọn 3-5 item trang bị ngẫu nhiên
        available_items = list(PERMANENT_EQUIPMENT.keys())
        num_items = random.randint(3, 5)
        
        # Lấy ID của item trang bị
        random_item_ids = random.sample(available_items, min(num_items, len(available_items)))
        
        shop_items = {}
        for item_id in random_item_ids:
            # Dùng ID gốc của item trang bị (R1, R2, v.v.)
            PERMANENT_EQUIPMENT[item_id]["id"] = item_id # Gán ID cho dễ tra cứu
            shop_items[item_id] = PERMANENT_EQUIPMENT[item_id]
            
        global_data['shop_items'] = shop_items
        global_data['last_daily_shop_update_day'] = current_day
        
        # Cập nhật Quest hàng ngày
        update_daily_quest()
        
        save_global_data()
        print("Daily shop and quest updated.")
    
    # Kết hợp các item cố định và item ngẫu nhiên
    current_shop = BASE_SHOP_ITEMS.copy()
    current_shop.update(global_data.get('shop_items', {}))
    return current_shop

def update_daily_quest():
    """Thiết lập nhiệm vụ hàng ngày mới."""
    selected_quest_id = random.choice(list(QUESTS_CONFIG.keys()))
    quest_data = QUESTS_CONFIG[selected_quest_id].copy()
    quest_data["id"] = selected_quest_id
    global_data["daily_quest"] = quest_data
    
    # Reset tiến trình quest cho tất cả người dùng
    for user_id in users:
        users[user_id]["quest_progress"] = 0
        users[user_id]["quest_claimed"] = False
    save_data(users)

def progress_quest(uid, command_name, count=1):
    """Cập nhật tiến trình Quest cho người dùng."""
    user = get_user(uid)
    current_quest = global_data.get("daily_quest")
    
    if current_quest and not user.get("quest_claimed") and current_quest.get("command") == command_name:
        user["quest_progress"] = user.get("quest_progress", 0) + count
        user["quest_progress"] = min(user["quest_progress"], current_quest["target_count"])
        save_data(users)
        return True # Đã cập nhật
    return False

# --- CÁC HÀM HỖ TRỢ PET & STATS (ĐÃ CẬP NHẬT) ---

def get_next_pet_id():
    global global_pet_id_counter
    new_id = global_pet_id_counter
    global_pet_id_counter += 1
    return new_id

def exp_for_level(level):
    return 100 * level + 50 * (level ** 2)

def pet_exp_for_level(level):
    return 50 + 20 * (level ** 2)

def get_base_stats(rarity):
    """Tính Stats cơ bản của Pet dựa trên cấp độ 1 và độ hiếm (ĐÃ THÊM LUCK/EVASION)."""
    base_hp = 100
    base_atk = 10
    base_def = 5
    base_spd = 5
    base_luck = 1 # Chỉ số May Mắn
    base_evasion = 1 # Chỉ số Né Tránh
    
    # Bonus theo độ hiếm
    rarity_bonus = {"Phổ Biến": 1.0, "Hiếm": 1.1, "Sử Thi": 1.25, "Thần Thoại": 1.5, "Đấng Cứu Thế": 2.0}
    multiplier = rarity_bonus.get(rarity, 1.0)
    
    return {
        "HP": int(base_hp * multiplier),
        "ATK": int(base_atk * multiplier),
        "DEF": int(base_def * multiplier),
        "SPD": int(base_spd * multiplier),
        "LUCK": int(base_luck * multiplier),
        "EVASION": int(base_evasion * multiplier)
    }

def get_final_stats(pet):
    """Tính Stats cuối cùng của Pet (Base + Level Bonus + Item Bonus) (ĐÃ CẬP NHẬT)."""
    base_stats = get_base_stats(pet.get("rarity", "Phổ Biến"))
    level = pet.get("level", 1)
    
    final_stats = {
        "HP": base_stats["HP"] + (level * 5),
        "ATK": base_stats["ATK"] + (level * 2),
        "DEF": base_stats["DEF"] + (level * 1),
        "SPD": base_stats["SPD"] + (level * 1),
        "LUCK": base_stats["LUCK"] + (level * 0.5), # Tăng ít hơn
        "EVASION": base_stats["EVASION"] + (level * 0.5) # Tăng ít hơn
    }
    
    # --- Cộng Stats từ Item Trang Bị ---
    # Phải kiểm tra nếu Pet có owner_id (tránh lỗi khi tạo wild pet/boss)
    uid = pet.get('owner_id')
    if uid:
        user = get_user(uid)
        inv = user.get("inventory", [])
        
        for unique_id in pet.get("equipped_items", []):
            equipped_item_data = next((item for item in inv if item.get("unique_id") == unique_id), None)
            
            if equipped_item_data:
                shop_id = equipped_item_data["shop_id"]
                item_config = PERMANENT_EQUIPMENT.get(shop_id) or global_data.get('shop_items', {}).get(shop_id)
                
                if item_config and item_config.get("bonus"):
                    for stat, bonus in item_config["bonus"].items():
                        final_stats[stat] = final_stats.get(stat, 0) + bonus
                        
    # Tính Lực chiến (Power) dựa trên chỉ số mới (Chỉ số LUCK/EVASION chỉ tính 1/3)
    power = final_stats["ATK"] + final_stats["DEF"] + final_stats["SPD"] + (final_stats["HP"] // 10) + (final_stats["LUCK"] // 3) + (final_stats["EVASION"] // 3)
    final_stats["POWER"] = int(power)
    
    # Đảm bảo LUCK và EVASION là số nguyên
    final_stats["LUCK"] = int(final_stats["LUCK"])
    final_stats["EVASION"] = int(final_stats["EVASION"])
    
    return final_stats


def get_user(uid):
    """Lấy dữ liệu người dùng theo ID, nếu chưa có sẽ tạo mới."""
    key = str(uid)
    if key not in users:
        users[key] = {
            "coin": 0, "pets": [], "inventory": [], "last_daily": None,
            "level": 1, "exp": 0, "buffs": {}, 
            "quest_progress": 0, "quest_claimed": False
        }
    
    # Đảm bảo Pet có ID và equipped_items
    for pet in users[key].get("pets", []):
        if 'id' not in pet: pet['id'] = get_next_pet_id()
        if 'equipped_items' not in pet: pet['equipped_items'] = [] # Danh sách unique_id của item
        if 'owner_id' not in pet: pet['owner_id'] = uid
    
    return users[key]

def update_balance(uid, amount):
    user = get_user(uid)
    user["coin"] = user.get("coin", 0) + amount
    save_data(users)

def get_balance(uid):
    return get_user(uid).get("coin", 0)

def add_exp(uid, exp, ctx=None):
    user = get_user(uid)
    user['exp'] = user.get('exp', 0) + exp
    
    while user['exp'] >= exp_for_level(user['level']):
        user['exp'] -= exp_for_level(user['level'])
        user['level'] += 1
        if ctx:
            asyncio.create_task(ctx.send(f"🎉 **{ctx.author.display_name}** đạt Cấp độ **{user['level']}**!"))

def random_roll_rarity():
    r = random.random()
    cumulative = 0
    for rarity, chance in RARITY_CHANCES.items():
        cumulative += chance
        if r < cumulative:
            return rarity
    return "Phổ Biến"

def add_pet_exp(pet, exp):
    messages = []
    pet["exp"] = pet.get("exp", 0) + exp
    
    while pet["exp"] >= pet_exp_for_level(pet["level"]):
        pet["exp"] -= pet_exp_for_level(pet["level"])
        pet["level"] += 1
        messages.append(f"⬆️ **{pet['name']}** lên Lv **{pet['level']}**!")
        
    return messages
  # ----------------- 3.1 CÁC LỆNH ECONOMY & MUA BÁN -----------------

## LỆNH BAL
@bot.command(name="bal")
async def balance_cmd(ctx):
    balance = get_balance(ctx.author.id)
    await ctx.send(f"💰 Số dư của **{ctx.author.display_name}**: **{balance:,}** xu.")

## LỆNH DAILY
@bot.command(name="daily")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily_cmd(ctx):
    uid = ctx.author.id
    reward = 500
    item_id = "5" 
    item_data = BASE_SHOP_ITEMS.get(item_id, {"name": CHEST_NAME})
    
    user = get_user(uid)
    user["inventory"].append({"shop_id": item_id, "name": item_data["name"], "unique_id": str(time.time()) + str(random.randint(0, 1000))})
    update_balance(uid, reward)
    save_data(users)
    
    await ctx.send(f"🎁 **{ctx.author.display_name}** nhận **{reward}** xu và hòm: **{item_data['name']}**!")

@daily_cmd.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        h = secs // 3600; m = (secs%3600)//60; s = secs%60
        await ctx.send(f"⏰ Lệnh daily tái tạo sau **{h}g {m}p {s}s**.")

## LỆNH HUNT (RÚT GỌN: h - Cập nhật Logic Luck)
@bot.command(name="hunt", aliases=["h"])
@commands.cooldown(1, 60, commands.BucketType.user)
async def hunt_cmd(ctx):
    uid = ctx.author.id
    user = get_user(uid)
    
    # --- XỬ LÝ BUFF --- (Giữ nguyên)
    base_catch_chance = 0.30; base_exp_multiplier = 1.0; base_hidden_chance = 0.01 
    active_buffs = {}; current_time = int(time.time())
    
    for buff_id, buff_data in list(user["buffs"].items()):
        if buff_data["end_time"] > current_time:
            active_buffs[buff_id] = buff_data
            if buff_data["type"] == "catch_chance": base_catch_chance += buff_data["value"]
            elif buff_data["type"] == "exp_multiplier": base_exp_multiplier = buff_data["value"]
            elif buff_data["type"] == "hidden_chance": base_hidden_chance += buff_data["value"]
        else:
            del user["buffs"][buff_id]
            
    # --- Áp dụng Pet Luck vào tỉ lệ bắt Pet ---
    # Lấy Pet Slot 1 (hoặc Pet có LUCK cao nhất)
    player_pet = next((p for p in user.get("pets", []) if p.get("slot", 0) == 1), None)
    luck_bonus = 0
    if player_pet:
        pet_stats = get_final_stats(player_pet)
        # Mỗi 10 điểm LUCK tăng 1% tỉ lệ bắt
        luck_bonus = pet_stats['LUCK'] / 100.0 
    
    save_data(users)
    buff_msg = " [Buff đang hoạt động: " + ", ".join(d['name'] for d in active_buffs.values()) + "]" if active_buffs else ""

    # --- TIẾN HÀNH HUNT ---
    final_catch_chance = min(1.0, base_catch_chance + luck_bonus)
    
    if random.random() < final_catch_chance:
        progress_quest(uid, "hunt") # Cập nhật Quest
        
        rarity = random_roll_rarity(); is_hidden = False
        pet_name = random.choice(PET_NAMES)
        
        pet_data = {"id": get_next_pet_id(), "name": pet_name, "rarity": rarity, "skill": random.choice(SKILLS), "level": 1, "exp": 0,
               "element": random.choice(PET_ELEMENTS), "is_hidden": is_hidden, "slot": 0, "evolution": 0, "owner_id": uid, "equipped_items": []}
        
        user["pets"].append(pet_data)
        initial_exp = int(random.randint(5, 20) * base_exp_multiplier)
        level_up_messages = add_pet_exp(pet_data, initial_exp)
        save_data(users)
        
        response = f"🎉 Bạn bắt được Pet **{pet_name}** ({rarity})! [ID: {pet_data['id']}]"
        response += f"\n(Pet nhận {initial_exp} EXP khởi điểm! Tỉ lệ bắt: {final_catch_chance*100:.1f}%)"
        if level_up_messages: response += " " + " ".join(level_up_messages)
        await ctx.send(response + buff_msg)
    else:
        update_balance(uid, 50)
        await ctx.send(f"💔 Không thấy pet. Nhận 50 xu an ủi. (Tỉ lệ bắt: {final_catch_chance*100:.1f}%)" + buff_msg)
        
    await balance_cmd(ctx)
    
@hunt_cmd.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        await ctx.send(f"⏰ Lệnh hunt tái tạo sau **{secs}s**.")

## LỆNH SHOP (shop)
@bot.command(name="shop")
async def shop_cmd(ctx):
    current_shop = update_daily_shop() 
    
    shop_list = "\n".join([f"• **{item['name']}** (ID: {id}) — {item['price']:,} xu" 
                           for id, item in current_shop.items()])
    
    embed = discord.Embed(
        title="🛍️ Cửa Hàng (Cập nhật hàng ngày)", 
        description=f"Dùng `bbuy <ID món>` để mua đồ:\n\n{shop_list}", 
        color=0xffa500
    )
    embed.set_footer(text="Ví dụ: bbuy 3 (mua Thức ăn)")
    await ctx.send(embed=embed)

## LỆNH BUY (buy - Cập nhật Quest)
@bot.command(name="buy")
async def buy_cmd(ctx, item_id: str = None):
    current_shop = update_daily_shop()
    if not item_id or item_id not in current_shop:
        return await ctx.send("🛒 Mua: `bbuy <ID món>` (Xem bshop để biết ID).")
        
    item_data = current_shop[item_id]
    price = item_data["price"]
    item_name = item_data["name"]
    uid = ctx.author.id; user = get_user(uid)
    
    if user["coin"] < price:
        return await ctx.send("💰 Bạn không đủ xu để mua món này.")
        
    user["coin"] -= price
    user["inventory"].append({"shop_id": item_id, "name": item_name, "unique_id": str(time.time()) + str(random.randint(0, 1000))})
    
    progress_quest(uid, "buy") # Cập nhật Quest
    save_data(users)
    
    await ctx.send(f"✅ Đã mua **{item_name}** (Shop ID: {item_id}) với giá **{price:,} xu**. Kiểm tra túi đồ bằng `binv`.")

## LỆNH SELL (Bán đồ theo ID duy nhất)
@bot.command(name="sell")
async def sell_cmd(ctx, unique_id: str = None):
    if not unique_id: return await ctx.send("💰 Bán: `bsell <ID món trong túi>` (Xem ID trong `binv`).")
        
    uid = ctx.author.id; user = get_user(uid); inv = user.get("inventory", [])
    item_to_sell_data = next((item for item in inv if item.get("unique_id") == unique_id), None)
    
    if not item_to_sell_data: return await ctx.send(f"❌ Bạn không có vật phẩm có ID **{unique_id}** trong túi đồ.")
    
    # Kiểm tra xem item có đang được pet nào trang bị không
    for pet in user["pets"]:
        if unique_id in pet.get("equipped_items", []):
            return await ctx.send(f"❌ Vật phẩm **{item_to_sell_data['name']}** đang được Pet **{pet['name']}** trang bị. Dùng `bunequip <ID pet> <ID túi>` trước khi bán.")

    shop_id = item_to_sell_data["shop_id"]
    shop_item_data = BASE_SHOP_ITEMS.get(shop_id) or PERMANENT_EQUIPMENT.get(shop_id) or global_data.get('shop_items', {}).get(shop_id)
    sell_price = shop_item_data.get("sell_price", 100) if shop_item_data else 100
    
    user["inventory"].remove(item_to_sell_data)
    update_balance(uid, sell_price)
    save_data(users)
    
    await ctx.send(f"✅ Đã bán **{item_to_sell_data['name']}** (ID: {unique_id}) với giá **{sell_price:,} xu**.")
    await balance_cmd(ctx)


## LỆNH INVENTORY (inv, hiển thị ID duy nhất)
@bot.command(name="inv", aliases=["items"])
async def inv_cmd(ctx):
    inventory = get_user(ctx.author.id).get("inventory", [])
    if not inventory: return await ctx.send("🎒 Túi đồ trống rỗng.")
        
    item_list = []
    for item in inventory:
        # Kiểm tra xem item có đang được trang bị không
        equipped_to = ""
        for pet in get_user(ctx.author.id)["pets"]:
            if item.get("unique_id") in pet.get("equipped_items", []):
                equipped_to = f" (Trang bị cho Pet ID: {pet['id']})"
                break
                
        item_list.append(f"• **{item['name']}** (Shop ID: {item['shop_id']}) - ID Túi: `{item['unique_id']}`{equipped_to}")
    
    embed = discord.Embed(
        title=f"🎒 Túi đồ của {ctx.author.display_name} ({len(inventory)} món)", 
        description=f"Dùng `b equip <ID túi> <ID pet>` | `b use <ID túi>` | `b sell <ID túi>`:\n\n" + "\n".join(item_list[:20]), # Giới hạn 20 món
        color=0x40E0D0
    )
    if len(inventory) > 20: embed.set_footer(text=f"Và {len(inventory) - 20} món khác...")
    await ctx.send(embed=embed)
  # ----------------- 3.2 CÁC LỆNH SỬ DỤNG ITEM, PET & MINIGAMES -----------------

## LỆNH USE ITEM 
@bot.command(name="use")
async def use_cmd(ctx, unique_id: str = None):
    # Logic giữ nguyên
    if not unique_id: return await ctx.send("🎁 Dùng: `b use <ID món trong túi>` (Xem ID trong `binv`).")
    uid = ctx.author.id; user = get_user(uid); inv = user.get("inventory", [])
    item_to_use = next((item for item in inv if item.get("unique_id") == unique_id), None)
    if not item_to_use: return await ctx.send(f"❌ Bạn không có vật phẩm có ID túi **{unique_id}**.")

    shop_id = item_to_use["shop_id"]; item_name = item_to_use["name"]
    
    if shop_id in PERMANENT_EQUIPMENT or shop_id in global_data.get('shop_items', {}):
        return await ctx.send(f"❌ Vật phẩm **{item_name}** là trang bị. Dùng `b equip <ID túi> <ID pet>`.")

    user["inventory"].remove(item_to_use)
    res = ""
    
    if shop_id == "5": # Rương Đá Thần
        stone_id = random.choice(list(HUNT_BUFFS.keys()))
        stone_data = BASE_SHOP_ITEMS[stone_id]
        user["inventory"].append({"shop_id": stone_id, "name": stone_data["name"], "unique_id": str(time.time()) + str(random.randint(0, 1000))})
        res = f"📦 Mở **{CHEST_NAME}** và nhận được **{stone_data['name']}**! Dùng `b use <ID>` để kích hoạt buff."
    
    elif shop_id in ["6", "7", "8"]: # Đá Buff
        buff_info = HUNT_BUFFS[shop_id]
        current_time = int(time.time()); end_time = current_time + buff_info["duration"]
        user["buffs"][buff_info["type"]] = {"end_time": end_time, "value": buff_info["value"], "name": buff_info["name"]}
        duration_str = f"{buff_info['duration'] // 60} phút" if buff_info['duration'] < 3600 else f"{buff_info['duration'] // 3600} giờ"
        res = f"✨ Đã kích hoạt **{item_name}**! {buff_info['desc']} (Hiệu lực {duration_str})."
    
    elif shop_id == "2": # Pet ngẫu nhiên
        new_pet_name = random.choice(PET_NAMES)
        pet = {"id": get_next_pet_id(), "name": new_pet_name, "rarity": random_roll_rarity(), "skill": random.choice(SKILLS), 
               "level":1, "exp": 0, "element": random.choice(PET_ELEMENTS), "is_hidden": False, "slot": 0, "evolution": 0, "owner_id": uid, "equipped_items": []} 
        user["pets"].append(pet)
        res = f"🎉 Bạn nhận Pet **{new_pet_name}** [ID: {pet['id']}]!"
    
    elif shop_id == "3": # Thức ăn
        FEED_EXP = 100
        if not user["pets"]:
            user["inventory"].append(item_to_use); save_data(users)
            return await ctx.send("🐾 Bạn không có pet để cho ăn.")
            
        p = random.choice(user["pets"])
        level_up_messages = add_pet_exp(p, FEED_EXP)
        res = f"🍖 Đã cho **{p['name']}** ăn. +**{FEED_EXP} EXP**."
        if level_up_messages: res += " " + " ".join(level_up_messages)
            
    elif shop_id == "1": # Hộp quà
        reward = random.randint(100, 300)
        update_balance(uid, reward)
        res = f"🎁 Mở hộp quà: +{reward} 💰"
        
    else:
        res = f"✅ Đã sử dụng **{item_name}** (Shop ID: {shop_id})."
    
    save_data(users)
    await ctx.send(res)


## LỆNH ZOO (z - Cập nhật hiển thị Stats mới)
@bot.command(name="zoo", aliases=["z","pet"])
async def zoo_cmd(ctx):
    uid = ctx.author.id; pets = get_user(uid).get("pets", [])
    if not pets: return await ctx.send("🐾 Bạn chưa có pet nào.")
    
    embed = discord.Embed(title=f"🦴 Kho Pet của {ctx.author.display_name} ({len(pets)} pet)", color=0xFEE3F5)
    for i, p in enumerate(pets, start=1):
        stats = get_final_stats(p)
        slot = f" [SLOT {p.get('slot')}]" if p.get("slot") else ""
        exp_to_next = pet_exp_for_level(p['level'])
        
        equipped_names = [next(item['name'] for item in get_user(uid)['inventory'] if item['unique_id'] == iid) for iid in p.get('equipped_items', [])]
        equipped_str = f" | Trang bị: {', '.join(equipped_names)}" if equipped_names else ""
        
        embed.add_field(
            name=f"#{i} {p['name']}{slot} (ID Pet: {p.get('id', 'N/A')})", 
            value=f"✨ {p['rarity']} | Lv {p['level']} | P: **{stats['POWER']}**\n"
                  f"📊 HP: {stats['HP']} | ATK: {stats['ATK']} | DEF: {stats['DEF']}\n"
                  f"🍀 LUCK: {stats['LUCK']} | 💨 EVASION: {stats['EVASION']} | SPD: {stats['SPD']}\n"
                  f"EXP: {p.get('exp', 0)}/{exp_to_next}{equipped_str}", 
            inline=False
        )
        
    embed.set_footer(text="Dùng bteam add/remove <số thứ tự> để chỉnh đội hình. Dùng b equip/unequip.")
    await ctx.send(embed=embed)

## LỆNH EQUIP / UNEQUIP (Trang bị và Gỡ bỏ trang bị)
@bot.command(name="equip")
async def equip_cmd(ctx, unique_id: str = None, pet_id: int = None):
    if not unique_id or pet_id is None: 
        return await ctx.send("❌ Cú pháp: `b equip <ID túi> <ID pet>` (Xem ID túi bằng `binv`, ID pet bằng `bz`).")
        
    uid = ctx.author.id; user = get_user(uid); inv = user.get("inventory", [])
    item_to_equip = next((item for item in inv if item.get("unique_id") == unique_id), None)
    pet = next((p for p in user.get("pets", []) if p.get("id") == pet_id), None)
    
    if not item_to_equip: return await ctx.send(f"❌ Không tìm thấy item với ID túi `{unique_id}`.")
    if not pet: return await ctx.send(f"❌ Không tìm thấy Pet với ID `{pet_id}`.")
    
    shop_id = item_to_equip["shop_id"]
    item_config = PERMANENT_EQUIPMENT.get(shop_id) or global_data.get('shop_items', {}).get(shop_id)
    
    if not item_config or 'bonus' not in item_config:
        return await ctx.send(f"❌ Item **{item_to_equip['name']}** không phải là trang bị (không có chỉ số bonus).")

    if unique_id in pet.get("equipped_items", []):
        return await ctx.send(f"❌ Item này đã được trang bị cho Pet **{pet['name']}** rồi.")
        
    if unique_id in [i for p in user["pets"] for i in p.get("equipped_items", [])]:
        return await ctx.send(f"❌ Item này đã được Pet khác trang bị. Dùng `bunequip` trước.")

    # Trang bị
    pet["equipped_items"] = pet.get("equipped_items", []) + [unique_id]
    save_data(users)
    await ctx.send(f"✅ Đã trang bị **{item_to_equip['name']}** cho Pet **{pet['name']}** (ID: {pet_id}).")

@bot.command(name="unequip", aliases=["un"])
async def unequip_cmd(ctx, pet_id: int = None, unique_id: str = None):
    if pet_id is None or unique_id is None:
        return await ctx.send("❌ Cú pháp: `b unequip <ID pet> <ID túi>`.")
        
    uid = ctx.author.id; user = get_user(uid)
    pet = next((p for p in user.get("pets", []) if p.get("id") == pet_id), None)
    item_to_unequip = next((item for item in user.get("inventory", []) if item.get("unique_id") == unique_id), None)

    if not pet: return await ctx.send(f"❌ Không tìm thấy Pet với ID `{pet_id}`.")
    if not item_to_unequip: return await ctx.send(f"❌ Không tìm thấy Item với ID túi `{unique_id}`.")

    if unique_id in pet.get("equipped_items", []):
        pet["equipped_items"].remove(unique_id)
        save_data(users)
        await ctx.send(f"✅ Đã gỡ **{item_to_unequip['name']}** khỏi Pet **{pet['name']}** (ID: {pet_id}).")
    else:
        await ctx.send(f"❌ Item **{item_to_unequip['name']}** không được trang bị cho Pet **{pet['name']}**.")

## LỆNH QUEST (Nhiệm vụ hàng ngày)
@bot.command(name="quest")
async def quest_cmd(ctx):
    current_quest = global_data.get("daily_quest")
    if not current_quest:
        update_daily_shop()
        current_quest = global_data.get("daily_quest")
        
    if not current_quest:
        return await ctx.send("❌ Hiện tại chưa có nhiệm vụ nào được thiết lập. Vui lòng chờ 24h từ lần chạy bot gần nhất.")

    uid = ctx.author.id; user = get_user(uid)
    
    if user.get("quest_claimed"):
        status = "✅ ĐÃ NHẬN THƯỞNG!"
    else:
        progress = user.get("quest_progress", 0)
        target = current_quest["target_count"]
        status = f"Đã hoàn thành: **{progress}/{target}**"
        if progress >= target:
            status += " (Sẵn sàng nhận thưởng!)"

    reward_item_data = BASE_SHOP_ITEMS.get(current_quest["reward_item_id"]) or PERMANENT_EQUIPMENT.get(current_quest["reward_item_id"])
    reward_item_name = reward_item_data["name"] if reward_item_data else "Vật phẩm bí ẩn"

    embed = discord.Embed(
        title="📜 Nhiệm Vụ Hàng Ngày", 
        description=f"**Mô tả:** {current_quest['desc']}",
        color=0x9B59B6
    )
    embed.add_field(name="💰 Phần Thưởng", value=f"{current_quest['reward_coin']:,} xu + **{reward_item_name}**", inline=False)
    embed.add_field(name="🎯 Tình Trạng", value=status, inline=False)
    embed.set_footer(text="Dùng bclaim để nhận thưởng khi hoàn thành.")
    await ctx.send(embed=embed)

@bot.command(name="claim")
async def claim_cmd(ctx):
    current_quest = global_data.get("daily_quest")
    if not current_quest: return await ctx.send("❌ Hiện tại không có nhiệm vụ để nhận thưởng.")

    uid = ctx.author.id; user = get_user(uid)
    
    if user.get("quest_claimed"):
        return await ctx.send("❌ Bạn đã nhận thưởng nhiệm vụ hôm nay rồi.")
        
    progress = user.get("quest_progress", 0)
    target = current_quest["target_count"]
    
    if progress < target:
        return await ctx.send(f"❌ Bạn cần hoàn thành nhiệm vụ **{progress}/{target}** trước khi nhận thưởng.")
        
    # Thưởng
    reward_coin = current_quest["reward_coin"]
    reward_item_id = current_quest["reward_item_id"]
    reward_item_data = BASE_SHOP_ITEMS.get(reward_item_id) or PERMANENT_EQUIPMENT.get(reward_item_id)
    reward_item_name = reward_item_data["name"] if reward_item_data else "Vật phẩm bí ẩn"
    
    update_balance(uid, reward_coin)
    user["inventory"].append({"shop_id": reward_item_id, "name": reward_item_name, "unique_id": str(time.time()) + str(random.randint(0, 1000))})
    user["quest_claimed"] = True
    add_exp(uid, 10, ctx=ctx)
    save_data(users)
    
    await ctx.send(f"🎉 **CHÚC MỪNG!** Bạn đã hoàn thành và nhận thưởng nhiệm vụ: **{reward_coin:,} xu** và **{reward_item_name}**!")

## LỆNH BLACKJACK (BBJ) - Dùng Icon để tương tác
@bot.command(name="bj", aliases=["bbj"])
async def bbj_cmd(ctx, amount: int = None):
    # ------------------ KHỞI TẠO & CƯỢC ------------------
    uid = ctx.author.id
    if amount is None or amount <= 0: return await ctx.send("❌ Cú pháp: `bbj <số xu cược>`.")
    if get_balance(uid) < amount: return await ctx.send("💰 Bạn không đủ xu để cược.")
    
    def get_card_value(card):
        if card in ["K", "Q", "J"]: return 10
        if card == "A": return 11
        return int(card)
        
    def calculate_score(hand):
        score = sum(get_card_value(card) for card in hand)
        aces = hand.count("A")
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score
    
    deck = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"] * 4
    random.shuffle(deck)
    def deal_card(): return deck.pop()
        
    player_hand = [deal_card(), deal_card()]
    dealer_hand = [deal_card(), deal_card()]
    
    # ------------------ HÀM HIỂN THỊ EMBED ------------------
    def create_embed(game_state, hide_dealer=True):
        player_score = calculate_score(player_hand)
        dealer_display = dealer_hand[0] + ", [?]" if hide_dealer else ", ".join(dealer_hand)
        dealer_score = "?" if hide_dealer else calculate_score(dealer_hand)
        
        embed = discord.Embed(
            title="♠️ BLACKJACK ♣️",
            description=f"**Cược:** {amount:,} xu",
            color=0x2ECC71
        )
        embed.add_field(name=f"Bạn ({player_score})", value=f"Bài: {', '.join(player_hand)}", inline=False)
        embed.add_field(name=f"Bot ({dealer_score})", value=f"Bài: {dealer_display}", inline=False)
        
        if game_state == "playing":
            embed.set_footer(text="Nhấn ➕ (Rút) hoặc ✋ (Dừng) | ❌ (Thoát)")
        elif game_state == "end":
             embed.set_footer(text="Trò chơi đã kết thúc!")
             
        return embed
        
    # ------------------ GỬI TIN NHẮN VÀ THÊM REACTIONS ------------------
    game_message = await ctx.send(embed=create_embed("playing"))
    await game_message.add_reaction("➕")
    await game_message.add_reaction("✋")
    await game_message.add_reaction("❌")
    
    # ------------------ VÒNG LẶP CHỜ TƯƠNG TÁC ------------------
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == game_message.id and str(reaction.emoji) in ["➕", "✋", "❌"]

    while calculate_score(player_hand) < 21:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await game_message.edit(embed=create_embed("end"), content="⏰ Hết giờ! Trò chơi bị hủy.")
            return

        await game_message.remove_reaction(reaction.emoji, user)

        if str(reaction.emoji) == "❌":
            await game_message.edit(embed=create_embed("end"), content="💔 Trò chơi bị hủy.")
            return
            
        elif str(reaction.emoji) == "✋":
            break
            
        elif str(reaction.emoji) == "➕":
            player_hand.append(deal_card())
            player_score = calculate_score(player_hand)
            await game_message.edit(embed=create_embed("playing"))
            if player_score > 21: break
                
    # ------------------ XỬ LÝ KẾT QUẢ CUỐI CÙNG ------------------
    player_score = calculate_score(player_hand); dealer_score = calculate_score(dealer_hand)
    result_msg = ""
    
    if player_score > 21:
        result_msg = "💥 **Bust!** Bạn bị quá 21 điểm. Thua cược."
        update_balance(uid, -amount)
    else:
        while dealer_score < 17:
            dealer_hand.append(deal_card())
            dealer_score = calculate_score(dealer_hand)

        if dealer_score > 21:
            result_msg = "🎉 **DEALER BUST!** Bot bị quá 21 điểm. Bạn thắng!"
            update_balance(uid, amount)
        elif player_score > dealer_score:
            result_msg = "🎉 **BLACKJACK!** Bạn có điểm cao hơn. Bạn thắng!"
            update_balance(uid, amount)
        elif player_score < dealer_score:
            result_msg = "💔 **DEALER THẮNG!** Bot có điểm cao hơn. Thua cược."
            update_balance(uid, -amount)
        else:
            result_msg = "🤝 **PUSH!** Hòa điểm. Không ai mất tiền."
            
    final_embed = create_embed("end", hide_dealer=False)
    await game_message.edit(embed=final_embed, content=f"{result_msg}\n")
    
    await balance_cmd(ctx)
  # ----------------- CÁC LỆNH BATTLE & TEAM -----------------

def simple_battle(pet1, pet2, exp_bonus=1.0):
    """Mô phỏng trận đấu 1v1 đơn giản dựa trên Stats (ĐÃ THÊM EVASION)."""
    stats1 = get_final_stats(pet1); stats2 = get_final_stats(pet2)
    hp1 = stats1["HP"]; hp2 = stats2["HP"]
    
    # Tỉ lệ Né tránh (Evasion) = EVASION / (EVASION + 100) (tối đa 50%)
    evasion_chance1 = stats1["EVASION"] / (stats1["EVASION"] + 100)
    evasion_chance2 = stats2["EVASION"] / (stats2["EVASION"] + 100)
    
    # Tỉ lệ Sát thương chí mạng (Critical) = LUCK / 200 (tối đa 50%)
    crit_chance1 = stats1["LUCK"] / 200.0
    crit_chance2 = stats2["LUCK"] / 200.0
    
    # Giới hạn tỉ lệ né/crit tối đa (ví dụ 50%)
    evasion_chance1 = min(0.5, evasion_chance1)
    evasion_chance2 = min(0.5, evasion_chance2)
    crit_chance1 = min(0.5, crit_chance1)
    crit_chance2 = min(0.5, crit_chance2)
    
    # Chiến đấu theo lượt (tối đa 20 lượt)
    for _ in range(20):
        # Lượt Pet 1 tấn công Pet 2
        if random.random() > evasion_chance2: # Pet 2 không né
            damage1 = max(1, stats1["ATK"] - stats2["DEF"])
            if random.random() < crit_chance1: # Chí mạng
                damage1 = damage1 * 2
            hp2 -= damage1
            if hp2 <= 0: return pet1, pet2 # Pet 1 thắng
        
        # Lượt Pet 2 tấn công Pet 1
        if random.random() > evasion_chance1: # Pet 1 không né
            damage2 = max(1, stats2["ATK"] - stats1["DEF"])
            if random.random() < crit_chance2: # Chí mạng
                damage2 = damage2 * 2
            hp1 -= damage2
            if hp1 <= 0: return pet2, pet1 # Pet 2 thắng

    # Nếu hòa sau 20 lượt, Pet nào còn HP cao hơn thắng
    if hp1 > hp2: return pet1, pet2
    if hp2 > hp1: return pet2, pet1
    return None, None # Hòa

## LỆNH PVP (1v1, cược xu - Chỉ dùng Pet SLOT 1)
@bot.command(name="pvp")
async def pvp_cmd(ctx, member: discord.Member, amount: int):
    # Logic giữ nguyên (1v1, cược xu, chỉ dùng Pet SLOT 1)
    if member.id == ctx.author.id: return await ctx.send("❌ Không thể thách đấu chính mình.")
    if amount <= 0: return await ctx.send("❌ Số xu cược phải lớn hơn 0.")
    if get_balance(ctx.author.id) < amount or get_balance(member.id) < amount: return await ctx.send("❌ Một trong hai người không đủ xu để cược.")
        
    u1 = get_user(ctx.author.id); u2 = get_user(member.id)
    pet1 = next((p for p in u1.get("pets",[]) if p.get("slot",0)==1), None)
    pet2 = next((p for p in u2.get("pets",[]) if p.get("slot",0)==1), None)
    if not pet1 or not pet2: return await ctx.send("❌ Cả hai cần có pet ở **SLOT 1** trong đội hình (dùng bteam add).")
        
    winner, loser = simple_battle(pet1, pet2)
    
    if winner is None:
        await ctx.send("🤝 Hòa! Không ai mất xu.")
        return
        
    is_author_winner = winner.get('owner_id') == ctx.author.id
    winner_id = ctx.author.id if is_author_winner else member.id
    winner_name = ctx.author.display_name if is_author_winner else member.display_name
    
    if is_author_winner:
        update_balance(ctx.author.id, amount); update_balance(member.id, -amount); color = 0x00ff00
    else:
        update_balance(ctx.author.id, -amount); update_balance(member.id, amount); color = 0xff0000
        
    stats1 = get_final_stats(pet1); stats2 = get_final_stats(pet2)
    embed = discord.Embed(title="⚔️ Kết quả Thách Đấu Pet (1v1)", color=color)
    embed.add_field(name=f"{ctx.author.display_name} (Pet: {pet1['name']})", value=f"P: {stats1['POWER']} | ATK: {stats1['ATK']} | EVASION: {stats1['EVASION']}", inline=False)
    embed.add_field(name=f"{member.display_name} (Pet: {pet2['name']})", value=f"P: {stats2['POWER']} | ATK: {stats2['ATK']} | EVASION: {stats2['EVASION']}", inline=False)
    embed.set_footer(text=f"Người thắng: {winner_name} nhận {amount} xu.")
    
    await ctx.send(embed=embed)


## LỆNH PVP LINH HOẠT (Team Fight)
def team_battle(team1, team2):
    """Mô phỏng trận đấu Team vs Team đơn giản (Sum Stats)."""
    # Sum of all key stats
    total_stats1 = {"HP": 0, "ATK": 0, "DEF": 0, "SPD": 0, "LUCK": 0, "EVASION": 0}
    for pet in team1:
        stats = get_final_stats(pet)
        for key in total_stats1: total_stats1[key] += stats[key]
        
    total_stats2 = {"HP": 0, "ATK": 0, "DEF": 0, "SPD": 0, "LUCK": 0, "EVASION": 0}
    for pet in team2:
        stats = get_final_stats(pet)
        for key in total_stats2: total_stats2[key] += stats[key]
        
    # Mô phỏng chiến đấu: Tỉ lệ thắng dựa trên tổng Power
    # Power = ATK + DEF + (HP/10) + (SPD) + (LUCK/3) + (EVASION/3)
    power1 = total_stats1["ATK"] + total_stats1["DEF"] + (total_stats1["HP"] // 10) + total_stats1["SPD"] + (total_stats1["LUCK"] // 3) + (total_stats1["EVASION"] // 3)
    power2 = total_stats2["ATK"] + total_stats2["DEF"] + (total_stats2["HP"] // 10) + total_stats2["SPD"] + (total_stats2["LUCK"] // 3) + (total_stats2["EVASION"] // 3)
    
    win_chance = power1 / (power1 + power2)
    
    if random.random() < win_chance: return 1, power1, power2 # Team 1 thắng
    if random.random() < (1 - win_chance): return 2, power1, power2 # Team 2 thắng
    return 0, power1, power2 # Hòa

@bot.command(name="fight")
async def fight_cmd(ctx, member: discord.Member):
    if member.id == ctx.author.id: return await ctx.send("❌ Không thể chiến với chính mình.")
        
    u1 = get_user(ctx.author.id); u2 = get_user(member.id)
    team1 = sorted([p for p in u1.get("pets",[]) if p.get("slot",0)>0], key=lambda x: x.get("slot"))[:3]
    team2 = sorted([p for p in u2.get("pets",[]) if p.get("slot",0)>0], key=lambda x: x.get("slot"))[:3]
    
    if not team1 or not team2: return await ctx.send("❌ Cả hai cần có ít nhất 1 Pet trong đội hình (dùng bteam add).")
        
    winner_team_index, power1, power2 = team_battle(team1, team2)
    WIN = 300; LOSE = -100
    
    if winner_team_index == 1:
        update_balance(ctx.author.id, WIN); update_balance(member.id, LOSE)
        winner_id = ctx.author.id; winner_team = team1; res = f"🎉 **Bạn thắng!** Nhận {WIN} xu."; color = 0x00ff00
    elif winner_team_index == 2:
        update_balance(ctx.author.id, LOSE); update_balance(member.id, WIN)
        winner_id = member.id; winner_team = team2; res = f"💔 Đội đối thủ mạnh hơn. Bạn bị trừ {abs(LOSE)} xu."; color = 0xff0000
    else:
        res = "🤝 Hòa! Không ai đổi xu và không pet nào lên cấp."; color = 0xffff00; winner_id = None; winner_team = []
        
    exp_gain_msg = ""
    if winner_id:
        winner_user_data = get_user(winner_id)
        for pet_in_team in winner_team:
            original_pet = next((p for p in winner_user_data["pets"] if p.get("id") == pet_in_team.get("id")), None)
            if original_pet:
                exp_gained = random.randint(50, 150)
                level_up_messages = add_pet_exp(original_pet, exp_gained)
                exp_gain_msg += f"\n🏆 Pet **{original_pet['name']}** nhận **{exp_gained} EXP**!"
                if level_up_messages: exp_gain_msg += " " + " ".join(level_up_messages)
        save_data(users) 
    
    em = discord.Embed(title=f"⚔️ Kết quả chiến trận Pet ({len(team1)}v{len(team2)})", description=res, color=color)
    em.add_field(name=f"{ctx.author.display_name} ({len(team1)} Pet)", value=f"Tổng Lực Chiến: **{int(power1)}**", inline=True)
    em.add_field(name=f"{member.display_name} ({len(team2)} Pet)", value=f"Tổng Lực Chiến: **{int(power2)}**", inline=True)
    
    if exp_gain_msg: em.add_field(name="✨ Pet Nhận EXP", value=exp_gain_msg, inline=False)
    await ctx.send(embed=em)

## LỆNH AUTO FIGHT (PVE - Cập nhật Logic Luck/Battle)
@bot.command(name="pve", aliases=["af"])
@commands.cooldown(1, WILD_PET_CONFIG["COOLDOWN"], commands.BucketType.user)
async def pve_cmd(ctx):
    uid = ctx.author.id; user = get_user(uid)
    player_pet = next((p for p in user.get("pets", []) if p.get("slot", 0) == 1), None)
    if not player_pet: return await ctx.send("❌ Bạn cần có Pet ở **SLOT 1** trong đội hình để chiến đấu.")
        
    # Tạo Pet hoang dã (dựa trên cấp độ của người chơi)
    player_level = player_pet['level']
    wild_level = random.randint(player_level - 5, player_level + 5); wild_level = max(1, wild_level)
    wild_name = random.choice(PET_NAMES)
    wild_rarity = random.choice(list(RARITY_CHANCES.keys()))
    
    # Pet hoang dã không có owner_id
    wild_pet_data = {"id": 0, "name": wild_name, "rarity": wild_rarity, "level": wild_level, 
                     "owner_id": 0, "equipped_items": []} # Pet tạm thời
    
    winner, loser = simple_battle(player_pet, wild_pet_data)
    
    if winner and winner.get('owner_id') == uid:
        progress_quest(uid, "pve") # Cập nhật Quest
        
        # Áp dụng LUCK để tăng thưởng
        player_stats = get_final_stats(player_pet)
        luck_multiplier = 1 + (player_stats['LUCK'] / 50.0) # Ví dụ: 50 LUCK = x2 thưởng
        
        coin_gain = int((WILD_PET_CONFIG["COIN_BASE"] + random.randint(0, 50)) * luck_multiplier)
        exp_gain = int((WILD_PET_CONFIG["EXP_BASE"] + random.randint(0, 50)) * luck_multiplier)
        update_balance(uid, coin_gain); level_up_messages = add_pet_exp(player_pet, exp_gain)
        add_exp(uid, 5, ctx=ctx); save_data(users)
        
        wild_stats = get_final_stats(wild_pet_data)
        
        res_msg = f"🎉 **Chiến Thắng!** Pet **{player_pet['name']}** (P: {player_stats['POWER']}) đã đánh bại **{wild_name}** (P: {wild_stats['POWER']})!"
        res_msg += f"\n💰 Bạn nhận **{coin_gain:,}** xu. 🏆 Pet nhận **{exp_gain} EXP**."
        if level_up_messages: res_msg += " " + " ".join(level_up_messages)
        await ctx.send(res_msg)
    else:
        coin_lose = random.randint(50, 100); exp_lose = random.randint(10, 30)
        update_balance(uid, -coin_lose); player_pet["exp"] = max(0, player_pet["exp"] - exp_lose)
        save_data(users)
        
        wild_stats = get_final_stats(wild_pet_data)
        res_msg = f"💔 **Thất Bại!** Pet **{player_pet['name']}** (P: {player_stats['POWER']}) đã bị **{wild_name}** (P: {wild_stats['POWER']}) đánh bại."
        res_msg += f"\n📉 Bạn bị trừ **{coin_lose}** xu. Pet mất **{exp_lose} EXP**."
        await ctx.send(res_msg)

@pve_cmd.error
async def pve_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        await ctx.send(f"⏰ Lệnh PVE tái tạo sau **{secs} giây**.")

## LỆNH AUTO FIGHT BOSS (boss - Cập nhật Logic Battle)
@bot.command(name="boss", aliases=["bfboss"])
@commands.cooldown(1, BOSS_CONFIG["COOLDOWN"], commands.BucketType.user)
async def boss_cmd(ctx):
    uid = ctx.author.id; user = get_user(uid)
    player_pet = next((p for p in user.get("pets", []) if p.get("slot", 0) == 1), None)
    if not player_pet: return await ctx.send("❌ Bạn cần có Pet ở **SLOT 1** để thách đấu Boss.")
        
    boss_name = random.choice(BOSS_CONFIG["BOSS_NAMES"])
    boss_level = max(10, player_pet['level'] + 5)
    
    boss_rarity = "Thần Thoại"
    boss_pet_data = {"id": 0, "name": boss_name, "rarity": boss_rarity, "level": boss_level, 
                     "owner_id": 0, "equipped_items": []} # Pet tạm thời
    
    # Nhân Stats Boss lên (Giả lập Boss mạnh hơn)
    boss_stats = get_final_stats(boss_pet_data)
    boss_stats["HP"] = int(boss_stats["HP"] * BOSS_CONFIG["POWER_MULTIPLIER"])
    boss_stats["ATK"] = int(boss_stats["ATK"] * BOSS_CONFIG["POWER_MULTIPLIER"])
    
    # Boss vẫn bị đánh bại như pet thường
    winner, loser = simple_battle(player_pet, boss_pet_data) 
    
    if winner and winner.get('owner_id') == uid:
        item_data = BASE_SHOP_ITEMS[BOSS_CONFIG["REWARD_ITEM_ID"]]
        coin_gain = BOSS_CONFIG["COIN_BASE"] + random.randint(100, 500)
        exp_gain = BOSS_CONFIG["EXP_BASE"] + random.randint(100, 300)
        
        update_balance(uid, coin_gain)
        user["inventory"].append({"shop_id": BOSS_CONFIG["REWARD_ITEM_ID"], "name": item_data["name"], "unique_id": str(time.time()) + str(random.randint(0, 1000))})
        level_up_messages = add_pet_exp(player_pet, exp_gain)
        add_exp(uid, 20, ctx=ctx); save_data(users)
        
        res_msg = f"👑 **ĐẠI THẮNG BOSS!** Pet **{player_pet['name']}** đã hạ gục Boss **{boss_name}** (P: {boss_stats['POWER']})!"
        res_msg += f"\n💰 Bạn nhận **{coin_gain:,}** xu. 🎁 Nhận **{item_data['name']}**."
        res_msg += f"🏆 Pet nhận **{exp_gain} EXP**."
        if level_up_messages: res_msg += " " + " ".join(level_up_messages)
        await ctx.send(res_msg)
    else:
        coin_lose = random.randint(200, 400); exp_lose = random.randint(50, 100)
        update_balance(uid, -coin_lose); player_pet["exp"] = max(0, player_pet["exp"] - exp_lose)
        save_data(users)
        
        res_msg = f"💔 **THẤT BẠI TRƯỚC BOSS!** Boss **{boss_name}** (P: {boss_stats['POWER']}) quá mạnh."
        res_msg += f"\n📉 Bạn bị trừ **{coin_lose}** xu. Pet mất **{exp_lose} EXP**."
        await ctx.send(res_msg)

@boss_cmd.error
async def boss_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        h = secs // 3600; m = (secs%3600)//60; s = secs%60
        await ctx.send(f"⏰ Lệnh Boss tái tạo sau **{h}g {m}p {s}s**.")


# --- LỆNH TEAM (GROUP) ---
@bot.group(name="team")
async def team_group(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("❌ Cú pháp: `bteam <add/remove/show>`.")

@team_group.command(name="add")
async def team_add(ctx, pet_number: int = None, slot: int = 1):
    uid = ctx.author.id; user = get_user(uid); pets = user.get("pets", [])
    if pet_number is None or slot not in [1, 2, 3]: 
        return await ctx.send("❌ Cú pháp: `bteam add <số thứ tự pet> <slot 1/2/3>` (Xem số thứ tự trong `bz`).")
    if pet_number <= 0 or pet_number > len(pets): 
        return await ctx.send("❌ Số thứ tự pet không hợp lệ.")
        
    pet = pets[pet_number - 1]
    
    # Loại bỏ pet cũ ở slot nếu có
    for p in pets:
        if p.get("slot") == slot:
            p["slot"] = 0
            break
            
    # Thêm pet mới vào slot
    pet["slot"] = slot
    save_data(users)
    await ctx.send(f"✅ Pet **{pet['name']}** đã được đặt vào **SLOT {slot}**.")

@team_group.command(name="remove")
async def team_remove(ctx, slot: int = 1):
    uid = ctx.author.id; user = get_user(uid); pets = user.get("pets", [])
    if slot not in [1, 2, 3]: return await ctx.send("❌ Slot không hợp lệ (1, 2 hoặc 3).")
        
    pet_in_slot = next((p for p in pets if p.get("slot") == slot), None)
    
    if pet_in_slot:
        pet_in_slot["slot"] = 0
        save_data(users)
        await ctx.send(f"✅ Pet **{pet_in_slot['name']}** đã được gỡ khỏi **SLOT {slot}**.")
    else:
        await ctx.send(f"❌ SLOT {slot} đã trống.")

@team_group.command(name="show")
async def team_show(ctx):
    uid = ctx.author.id; pets = get_user(uid).get("pets", [])
    team = sorted([p for p in pets if p.get("slot", 0) > 0], key=lambda x: x.get("slot"))
    
    if not team: return await ctx.send("🐾 Đội hình của bạn đang trống. Dùng `bteam add <stt pet> <slot>`.")
    
    team_list = ""
    for p in team:
        stats = get_final_stats(p)
        team_list += f"**SLOT {p['slot']}**: {p['name']} (Lv {p['level']} | P: {stats['POWER']})\n"
        
    embed = discord.Embed(title=f"⚔️ Đội Hình Chiến Đấu của {ctx.author.display_name}", description=team_list, color=0x5865F2)
    await ctx.send(embed=embed)

# --- LỆNH PROFILE ---
@bot.command(name="profile")
async def profile_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    user = get_user(member.id)
    
    total_pets = len(user.get("pets", []))
    total_inventory = len(user.get("inventory", []))
    
    embed = discord.Embed(
        title=f"👤 Hồ Sơ Pet Master: {member.display_name}",
        color=0x3498DB
    )
    
    # Thông tin cơ bản
    embed.add_field(name="💰 Xu hiện tại", value=f"{user.get('coin', 0):,} xu", inline=True)
    embed.add_field(name="✨ Cấp độ Master", value=f"Lv {user.get('level', 1)}", inline=True)
    embed.add_field(name="🐾 Pet đã sở hữu", value=f"{total_pets} Pet", inline=True)
    embed.add_field(name="🎒 Túi đồ", value=f"{total_inventory} món", inline=True)
    
    # Team hiện tại
    team = sorted([p for p in user.get("pets", []) if p.get("slot", 0) > 0], key=lambda x: x.get("slot"))
    team_names = ", ".join([p["name"] for p in team]) if team else "Chưa thiết lập"
    embed.add_field(name="⚔️ Đội hình", value=team_names, inline=False)
    
    # Buffs đang hoạt động
    active_buffs_str = ""
    current_time = int(time.time())
    
    for buff_id, buff_data in user.get("buffs", {}).items():
        if buff_data["end_time"] > current_time:
            time_left = buff_data["end_time"] - current_time
            h = time_left // 3600; m = (time_left % 3600) // 60
            active_buffs_str += f"• **{buff_data['name']}** (Còn: {h}g {m}p)\n"
            
    if active_buffs_str:
        embed.add_field(name="✨ Buff Hoạt Động", value=active_buffs_str, inline=False)

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id}")
    await ctx.send(embed=embed)
  # ----------------- CÁC LỆNH UTILITY & EVENTS -----------------

@tasks.loop(hours=24)
async def daily_shop_update_task():
    """Tự động cập nhật shop và quest hàng ngày."""
    await bot.wait_until_ready()
    update_daily_shop()

@bot.event
async def on_ready():
    print(f'🤖 Bot đã sẵn sàng! Đăng nhập dưới tên: {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="bhelp | Pet System"))
    # Chạy cập nhật shop và quest ngay khi bot khởi động
    update_daily_shop()
    daily_shop_update_task.start()

@bot.event
async def on_message(message):
    if message.author.bot or not message.content:
        return
        
    content = message.content.lower()
    is_command = content.startswith('b') and len(content) > 1 and not content.startswith('b ')
    
    try:
        if is_command and message.channel.guild:
            ctx = await bot.get_context(message)
            
            # Xử lý Quest Progress cho các lệnh
            if ctx.command and ctx.command.name in ["hunt", "h"]: progress_quest(message.author.id, "hunt")
            elif ctx.command and ctx.command.name in ["pve", "af"]: progress_quest(message.author.id, "pve")
            elif ctx.command and ctx.command.name in ["buy"]: progress_quest(message.author.id, "buy")

            # Cộng EXP cho lệnh (trừ tts)
            if ctx.command and ctx.command.name not in ["tts", "s"]:
                add_exp(message.author.id, 1, ctx=ctx) 
            
        # Logic kiếm xu ngẫu nhiên
        user = get_user(message.author.id)
        if not is_command:
            gain = random.randint(1, 3)
            user["coin"] = user.get("coin", 0) + gain
            
        save_data(users)
    except Exception:
        pass 
        
    await bot.process_commands(message)

## LỆNH HELP (ĐÃ CHẶN LỆNH CŨ BẰNG CÁCH DÙNG help_command=None ở Phần 1)
@bot.command(name="help", aliases=["commands", "hlep"])
async def help_cmd(ctx):
    txt = (
        "📚 **Danh sách lệnh** (sử dụng tiền tố **`b`**)\n"
        "**[CƠ BẢN]**\n"
        "`bhelp` — Hiển thị danh sách lệnh này\n"
        "`bdaily` — nhận thưởng hàng ngày\n"
        "`bbal` — xem số dư\n"
        "`bprofile` — xem hồ sơ cá nhân\n"
        "`bquest / bclaim` — nhiệm vụ hàng ngày / nhận thưởng\n"
        "**[PET & ITEM]**\n"
        "`bh` — đi săn pet (cooldown 60s)\n"
        "`bpve` — **PVE**: Đấu quái vật cày EXP/xu (cooldown 120s)\n"
        "`bboss` — **Boss**: Đấu Boss nhận thưởng khủng (cooldown 1h)\n"
        "`bz` — xem Pet (có ID pet và Stats)\n"
        "`bshop / bbuy <ID>` — cửa hàng (mua bằng ID)\n"
        "`binv / buse <ID> / bsell <ID>` — túi đồ / dùng đồ / bán đồ (bằng ID túi)\n"
        "`bteam <add/remove/show>` — quản lý đội pet\n"
        "`b equip <ID túi> <ID pet>` — trang bị item cho pet\n"
        "**[CHIẾN ĐẤU & KHÁC]**\n"
        "`bfight @người` — đấu Pet linh hoạt theo đội hình\n"
        "`bpvp @người <xu>` — thách đấu 1v1 cược xu\n"
        "`bbj <xu>` — chơi blackjack (dùng icon ➕/✋)\n"
        "`bs <text>` — bot đọc giọng (trong voice channel, alias cho `btts`)\n"
    )
    await ctx.send(txt)

## LỆNH TEXT TO SPEECH (tts, rút gọn: s)
@bot.command(name="tts", aliases=["s"])
async def tts_cmd(ctx, *, text: str):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("❌ Bạn phải ở trong một kênh thoại để dùng lệnh này.")

    # Giới hạn độ dài text để tránh tạo file quá lớn
    if len(text) > 200:
        return await ctx.send("❌ Văn bản quá dài. Vui lòng nhập tối đa 200 ký tự.")
        
    temp_file_path = None
    try:
        # 1. Tạo file âm thanh tạm thời
        tts = gTTS(text=text, lang='vi')
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tts.write_to_fp(tmp)
            temp_file_path = tmp.name

        # 2. Kết nối và phát âm thanh
        if ctx.voice_client is None:
            vc = await ctx.author.voice.channel.connect()
        else:
            vc = ctx.voice_client
        
        if vc.is_playing():
            vc.stop()
            
        # Sử dụng FFmpegPCMAudio. Sau khi cài FFmpeg bằng Dockerfile, lệnh này sẽ hoạt động.
        # 'after' đảm bảo file tạm được xóa sau khi phát xong
        vc.play(FFmpegPCMAudio(temp_file_path), after=lambda e: os.remove(temp_file_path) if temp_file_path and os.path.exists(temp_file_path) else None)
        await ctx.message.add_reaction("🔊")
        
    except Exception as e:
        # In lỗi chi tiết ra console và gửi tin nhắn lỗi
        print(f"LỖI TTS XẢY RA: {e}")
        await ctx.send(f"❌ Có lỗi xảy ra khi tạo/phát âm thanh: {e}")
        
    finally:
        # Đảm bảo file temp được xóa nếu có lỗi trước khi phát
        if temp_file_path and os.path.exists(temp_file_path) and not ctx.voice_client.is_playing():
             os.remove(temp_file_path)

@bot.command(name="leave", aliases=["disconnect", "dc"])
async def leave_cmd(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("👋 Đã ngắt kết nối khỏi kênh thoại.")
    else:
        await ctx.send("❌ Bot không ở trong kênh thoại nào.")
      # ----------------- CHẠY BOT -----------------
def save_data(data, file_name=DATA_FILE):
    """Ghi đè hàm lưu để đảm bảo lưu Global Data và Users."""
    data_store = users.copy()
    data_store['global_data'] = global_data
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data_store, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if not TOKEN:
        print("🚨 Lỗi: Vui lòng cấu hình biến môi trường DISCORD_TOKEN.")
    else:
        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print("🚨 Lỗi: Token Discord không hợp lệ. Vui lòng kiểm tra lại token của bạn.")
        except Exception as e:
            print(f"🚨 Lỗi không xác định: {e}")
          
