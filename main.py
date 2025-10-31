import discord
from discord.ext import commands
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
# Cần import cái này cho chức năng TTS (Phần 5)
from discord import FFmpegPCMAudio 

# --- CẤU HÌNH BOT (SỬ DỤNG BIẾN MÔI TRƯỜNG) ---
# Lấy Token từ Biến Môi Trường DISCORD_TOKEN
TOKEN = os.getenv("DISCORD_TOKEN") 

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=['!', 'b'], intents=intents)

# ----------------- DATA (JSON) -----------------
DATA_FILE = "user_data.json"

def load_data(file_name=DATA_FILE):
    """Tải dữ liệu từ file JSON."""
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data, file_name=DATA_FILE):
    """Lưu dữ liệu vào file JSON."""
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_data() 


# ----------------- DATA (JSON) -----------------
DATA_FILE = "user_data.json"

def load_data(file_name=DATA_FILE):
    """Tải dữ liệu từ file JSON."""
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data, file_name=DATA_FILE):
    """Lưu dữ liệu vào file JSON."""
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

users = load_data() 
# ----------------- DỮ LIỆU NGẪU NHIÊN & CẤU HÌNH PET -----------------
PET_NAMES = ["Mèo Thần Tốc", "Cún Lửa", "Rồng Cỏ", "Thỏ Điện", "Gấu Nước"]
PET_ELEMENTS = ["Lửa", "Nước", "Cỏ", "Điện", "Đất", "Gió"]
SKILLS = ["Tấn Công Mạnh", "Phòng Thủ Kín", "Hồi Máu", "Tốc Độ Cao", "Bảo Vệ"]

# Cấu hình Rarity (Tỉ lệ ra pet)
RARITY_CHANCES = {
    "Phổ Biến": 0.50,
    "Hiếm": 0.30,
    "Sử Thi": 0.15,
    "Thần Thoại": 0.05
}

# Cấu hình tiến hóa Pet
EVOLVE_CONFIG = {
    10: {"name_suffix": " Chiến Thần", "skill_slots": 1},
    30: {"name_suffix": " Tối Thượng", "skill_slots": 2}
}

HIDDEN_PET_NAME = "Phượng Hoàng Lửa"
HIDDEN_PET_RARITY = "Đấng Cứu Thế"
HIDDEN_PET_DATE = (1, 1) # Ví dụ: 1/1 (Tháng, Ngày)

# Cấu hình Đá Buff cho Hunt (Áp dụng tạm thời)
HUNT_BUFFS = {
    "Đá Tăng Tỉ Lệ": {"duration": 1800, "type": "catch_chance", "value": 0.15, "desc": "Tăng 15% tỉ lệ bắt Pet (30 phút)."},
    "Đá Nhân EXP": {"duration": 1800, "type": "exp_multiplier", "value": 2.0, "desc": "Nhân đôi EXP Pet nhận được (30 phút)."},
    "Đá Bùa May Mắn": {"duration": 3600, "type": "hidden_chance", "value": 0.05, "desc": "Tăng 5% cơ hội bắt Pet Ẩn (1 giờ)."}
}

CHEST_NAME = "💎 Rương Đá Thần" 

# Dữ liệu vật phẩm cửa hàng: {tên: giá}
SHOP_ITEMS = {
    "🎁 Hộp quà": 500,
    "🐾 Pet ngẫu nhiên": 1000,
    "🍖 Thức ăn": 200, 
    "💎 Đá quý": 2000 
}

# ----------------- CÁC HÀM HỖ TRỢ ECONOMY & LEVEL -----------------

def exp_for_level(level):
    """Tính EXP cần thiết cho cấp độ người chơi tiếp theo."""
    return 100 * level + 50 * (level ** 2)

def pet_exp_for_level(level):
    """Tính EXP cần thiết để Pet lên cấp tiếp theo."""
    return 50 + 20 * (level ** 2)

def get_user(uid):
    """Lấy dữ liệu người dùng theo ID, nếu chưa có sẽ tạo mới."""
    key = str(uid)
    if key not in users:
        users[key] = {
            "coin": 0,
            "pets": [],
            "inventory": [],
            "last_daily": None,
            "level": 1,
            "exp": 0,
            "buffs": {}
        }
        save_data(users)
    
    if "buffs" not in users[key]:
        users[key]["buffs"] = {}
        
    for pet in users[key]["pets"]:
        pet["exp"] = pet.get("exp", 0)
        pet["level"] = pet.get("level", 1)
        pet["evolution"] = pet.get("evolution", 0)
        
    return users[key]

def update_balance(uid, amount):
    """Thêm hoặc trừ xu."""
    user = get_user(uid)
    user["coin"] = user.get("coin", 0) + amount
    if user["coin"] < 0:
        user["coin"] = 0
    save_data(users)

def get_balance(uid):
    """Lấy số dư xu."""
    return get_user(uid).get("coin", 0)

def add_exp(uid, amount, ctx=None):
    """Thêm EXP cho người chơi và kiểm tra lên cấp."""
    user = get_user(uid)
    user["exp"] += amount
    level_up = False
    
    while user["exp"] >= exp_for_level(user["level"]):
        user["exp"] -= exp_for_level(user["level"])
        user["level"] += 1
        level_up = True

    save_data(users)
    
    if level_up and ctx:
        asyncio.create_task(ctx.send(f"🎉 **{ctx.author.display_name}** đã lên **Cấp độ {user['level']}**!"))
        
    return user["level"]

def random_roll_rarity():
    """Quay ngẫu nhiên tỉ lệ hiếm của pet."""
    roll = random.random()
    cumulative_chance = 0.0
    for rarity, chance in RARITY_CHANCES.items():
        cumulative_chance += chance
        if roll <= cumulative_chance:
            return rarity
    return "Phổ Biến"

def pet_power(pet):
    """Tính sức mạnh chiến đấu của Pet."""
    base = 100 
    rarity_bonus = {"Phổ Biến": 0, "Hiếm": 10, "Sử Thi": 25, "Thần Thoại": 50, "Đấng Cứu Thế": 100}
    level_bonus = pet.get("level", 1) * 5
    
    power = base + rarity_bonus.get(pet.get("rarity", "Phổ Biến"), 0) + level_bonus
    
    power += len(pet.get("skill", "")) // 3 
    if pet.get('extra_skill_1'): power += 10
    if pet.get('extra_skill_2'): power += 20

    return power

def add_pet_exp(pet, amount):
    """Thêm EXP cho pet, kiểm tra lên cấp và tiến hóa."""
    initial_level = pet.get("level", 1)
    pet["exp"] = pet.get("exp", 0) + amount
    res_msg = []
    
    level_up_count = 0
    
    while pet["exp"] >= pet_exp_for_level(pet["level"]):
        level_up_count += 1
        pet["exp"] -= pet_exp_for_level(pet["level"])
        pet["level"] += 1

    if level_up_count > 0:
        res_msg.append(f"⬆️ Lv **{initial_level}** -> **{pet['level']}**!")

    for level_mark, config in EVOLVE_CONFIG.items():
        current_evolution = pet.get("evolution", 0)
        
        if pet["level"] >= level_mark > current_evolution:
            pet['name'] += config['name_suffix']
            
            for i in range(1, config['skill_slots'] + 1):
                key = f"extra_skill_{i}"
                if pet.get(key) is None:
                    current_skills = [pet.get('skill')]
                    if pet.get('extra_skill_1'): current_skills.append(pet['extra_skill_1'])
                    if pet.get('extra_skill_2'): current_skills.append(pet['extra_skill_2'])
                    
                    new_skill = random.choice([s for s in SKILLS if s not in current_skills])
                    pet[key] = new_skill
                    res_msg.append(f"🔥 **{pet['name']}** tiến hóa! + Skill: **{new_skill}**!")

            pet["evolution"] = level_mark
            
    return res_msg
# ----------------- CÁC LỆNH ECONOMY & PET COMMANDS -----------------

## LỆNH BAL
@bot.command(name="bal", aliases=["b"])
async def balance_cmd(ctx):
    balance = get_balance(ctx.author.id)
    await ctx.send(f"💰 Số dư của **{ctx.author.display_name}**: **{balance:,}** xu.")

## LỆNH DAILY (Thêm Rương Đá Thần)
@bot.command(name="daily", aliases=["bdaily"])
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily_cmd(ctx):
    uid = ctx.author.id
    reward = 500
    item = CHEST_NAME 
    
    user = get_user(uid)
    user["inventory"].append(item)
    update_balance(uid, reward)
    save_data(users)
    
    await ctx.send(f"🎁 **{ctx.author.display_name}** nhận **{reward}** xu và hòm: **{item}**!")
    await balance_cmd(ctx)

@daily_cmd.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        h = secs // 3600; m = (secs%3600)//60; s = secs%60
        await ctx.send(f"⏰ Lệnh daily tái tạo sau **{h}g {m}p {s}s**.")

## LỆNH GACHA
@bot.command(name="gacha", aliases=["bgacha"])
async def gacha_cmd(ctx):
    cost = 500
    uid = ctx.author.id
    if get_balance(uid) < cost:
        return await ctx.send(f"❌ Bạn cần **{cost}** xu để chơi Gacha.")
    
    update_balance(uid, -cost)
    reward_type = random.choice(["coin", "item", "pet"])
    
    if reward_type == "coin":
        reward = random.randint(100, 1500)
        update_balance(uid, reward)
        res = f"🎉 Quay ra **{reward:,}** xu!"
    elif reward_type == "item":
        reward = random.choice(list(SHOP_ITEMS.keys()))
        user = get_user(uid)
        user["inventory"].append(reward)
        save_data(users)
        res = f"🎁 Quay ra vật phẩm **{reward}**!"
    elif reward_type == "pet":
        new_pet_name = random.choice(PET_NAMES)
        pet = {"name": new_pet_name, "rarity": random_roll_rarity(), "skill": random.choice(SKILLS), 
               "level":1, "exp": 0, "element": random.choice(PET_ELEMENTS), "is_hidden": False, "slot": 0, "evolution": 0}
        user = get_user(uid)
        user["pets"].append(pet)
        save_data(users)
        res = f"🎉 Quay ra Pet **{new_pet_name}** ({pet['rarity']})!"
        
    await ctx.send(f"🎲 Gacha (giá {cost} xu): {res}")

## LỆNH HUNT (Áp dụng Buff)
@bot.command(name="hunt", aliases=["bhunt"])
@commands.cooldown(1, 60, commands.BucketType.user)
async def hunt_cmd(ctx):
    uid = ctx.author.id
    user = get_user(uid)
    
    # --- XỬ LÝ BUFF ---
    base_catch_chance = 0.30
    base_exp_multiplier = 1.0
    base_hidden_chance = 0.01 
    
    active_buffs = {}
    current_time = int(time.time())
    
    for buff_type, buff_data in list(user["buffs"].items()):
        if buff_data["end_time"] > current_time:
            active_buffs[buff_type] = buff_data
            if buff_type == "catch_chance":
                base_catch_chance += buff_data["value"]
            elif buff_type == "exp_multiplier":
                base_exp_multiplier = buff_data["value"]
            elif buff_type == "hidden_chance":
                base_hidden_chance += buff_data["value"]
        else:
            del user["buffs"][buff_type]
            
    save_data(users)
    
    buff_msg = ""
    if active_buffs:
        buff_msg = " [Buff đang hoạt động: " + ", ".join(d['name'] for d in active_buffs.values()) + "]"

    # --- TIẾN HÀNH HUNT ---
    final_catch_chance = min(1.0, base_catch_chance)
    
    if random.random() < final_catch_chance:
        today = datetime.now()
        rarity = random_roll_rarity()
        is_hidden = False
        
        if (today.month, today.day) == HIDDEN_PET_DATE and random.random() < base_hidden_chance:
            pet_name = HIDDEN_PET_NAME; rarity = HIDDEN_PET_RARITY; is_hidden = True
            msg = f"🌟 **Kỳ tích!** Bạn tìm thấy **{pet_name}** ({rarity})!"
        else:
            pet_name = random.choice(PET_NAMES)
            msg = f"🎉 Bạn bắt được Pet **{pet_name}** ({rarity})!"
            
        pet_skill = random.choice(SKILLS)
        
        pet = {"name": pet_name, "rarity": rarity, "skill": pet_skill, "level": 1, "exp": 0,
               "element": random.choice(PET_ELEMENTS), "is_hidden": is_hidden, "slot": 0, "evolution": 0}
        
        user["pets"].append(pet)
        
        initial_exp = int(random.randint(5, 20) * base_exp_multiplier)
        level_up_messages = add_pet_exp(pet, initial_exp)
        
        save_data(users)
        
        response = f"{msg}\nKỹ năng Pet: **{pet_skill}**."
        response += f"\n(Pet nhận {initial_exp} EXP khởi điểm!)"
        if level_up_messages:
            response += " " + " ".join(level_up_messages)

        await ctx.send(response + buff_msg)
    else:
        update_balance(uid, 50)
        await ctx.send("💔 Không thấy pet. Nhận 50 xu an ủi." + buff_msg)
        
    await balance_cmd(ctx)
    
@hunt_cmd.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        secs = int(error.retry_after)
        await ctx.send(f"⏰ Lệnh hunt tái tạo sau **{secs}s**.")

## LỆNH SHOP
@bot.command(name="bshop")
async def bshop_cmd(ctx):
    shop_list = "\n".join([f"**{item}** — {price:,} xu" for item, price in SHOP_ITEMS.items()])
    
    embed = discord.Embed(
        title="🛍️ Cửa Hàng", 
        description=f"Dùng `!bbuy <tên món>` để mua đồ:\n\n{shop_list}", 
        color=0xffa500
    )
    embed.set_footer(text="Ví dụ: !bbuy Thức ăn")
    await ctx.send(embed=embed)

## LỆNH BUY
@bot.command(name="bbuy", aliases=["buy"])
async def bbuy_cmd(ctx, *, item_name: str = None):
    if not item_name:
        return await ctx.send("🛒 Mua: `!bbuy <tên món>` (Xem !bshop)")
        
    found_item_key = next((key for key in SHOP_ITEMS if item_name.lower() in key.lower()), None)
    
    if not found_item_key:
        return await ctx.send("❌ Món này không có trong cửa hàng.")

    price = SHOP_ITEMS[found_item_key]
    user = get_user(ctx.author.id)
    
    if user["coin"] < price:
        return await ctx.send("💰 Bạn không đủ xu để mua món này.")
        
    user["coin"] -= price
    user["inventory"].append(found_item_key)
    save_data(users)
    
    await ctx.send(f"✅ Đã mua **{found_item_key}** với giá **{price:,} xu**. Kiểm tra túi đồ bằng `!binv`.")

## LỆNH INVENTORY
@bot.command(name="binv", aliases=["items", "inv"])
async def binv_cmd(ctx):
    inventory = get_user(ctx.author.id).get("inventory", [])
    if not inventory:
        return await ctx.send("🎒 Túi đồ trống rỗng.")
        
    item_counts = {}
    for item in inventory:
        item_counts[item] = item_counts.get(item, 0) + 1
        
    items_list = "\n".join([f"• **{item}** x{count}" for item, count in item_counts.items()])
    
    embed = discord.Embed(
        title=f"🎒 Túi đồ của {ctx.author.display_name} ({len(inventory)} món)", 
        description=items_list, 
        color=0x40E0D0
    )
    await ctx.send(embed=embed)

## LỆNH USE ITEM 
@bot.command(name="buse", aliases=["use"])
async def buse_cmd(ctx, *, item: str = None):
    if not item:
        return await ctx.send("🎁 Dùng: `!buse <tên món>`")
        
    uid = ctx.author.id
    user = get_user(uid)
    inv = user.get("inventory", [])
    
    found_item = next((i for i in inv if item.lower() in i.lower()), None)
    
    if not found_item:
        return await ctx.send("❌ Bạn không có món này.")
        
    user["inventory"].remove(found_item)
    res = ""
    
    if found_item == CHEST_NAME: 
        stone_name = random.choice(list(HUNT_BUFFS.keys()))
        user["inventory"].append(stone_name)
        res = f"📦 Mở **{CHEST_NAME}** và nhận được **{stone_name}**! Dùng `!buse {stone_name}` để kích hoạt buff."
    
    elif found_item in HUNT_BUFFS: 
        buff_info = HUNT_BUFFS[found_item]
        current_time = int(time.time())
        end_time = current_time + buff_info["duration"]
        
        user["buffs"][buff_info["type"]] = {
            "end_time": end_time, 
            "value": buff_info["value"],
            "name": found_item
        }
        
        duration_str = f"{buff_info['duration'] // 60} phút" if buff_info['duration'] < 3600 else f"{buff_info['duration'] // 3600} giờ"
        res = f"✨ Đã kích hoạt **{found_item}**! {buff_info['desc']} (Hiệu lực {duration_str})."
    
    elif found_item == "🐾 Pet ngẫu nhiên":
        new_pet_name = random.choice(PET_NAMES)
        pet = {"name": new_pet_name, "rarity": random_roll_rarity(), "skill": random.choice(SKILLS), 
               "level":1, "exp": 0, "element": random.choice(PET_ELEMENTS), "is_hidden": False, "slot": 0, "evolution": 0} 
        user["pets"].append(pet)
        res = f"🎉 Bạn nhận Pet **{new_pet_name}**!"
    
    elif found_item == "🍖 Thức ăn":
        FEED_EXP = 100
        if not user["pets"]:
            user["inventory"].append(found_item) 
            save_data(users)
            return await ctx.send("🐾 Bạn không có pet để cho ăn.")
            
        p = random.choice(user["pets"])
        level_up_messages = add_pet_exp(p, FEED_EXP)
        
        res = f"🍖 Đã cho **{p['name']}** ăn. +**{FEED_EXP} EXP**."
        if level_up_messages:
            res += " " + " ".join(level_up_messages)
            
    elif found_item == "🎁 Hộp quà":
        reward = random.randint(100, 300)
        update_balance(uid, reward)
        res = f"🎁 Mở hộp quà: +{reward} 💰"
        
    elif found_item == "💎 Đá quý":
        res = f"✅ Đã sử dụng **{found_item}** (chưa có chức năng đặc biệt)."
    else:
        res = f"✅ Đã sử dụng **{found_item}** (chưa có chức năng đặc biệt)."
    
    save_data(users)
    await ctx.send(res)

## LỆNH ZOO
@bot.command(name="bzoo", aliases=["z","bpet","pet"])
async def bzoo_cmd(ctx):
    uid = ctx.author.id
    pets = get_user(uid).get("pets", [])
    if not pets:
        return await ctx.send("🐾 Bạn chưa có pet nào.")
    
    embed = discord.Embed(title=f"🦴 Kho Pet của {ctx.author.display_name} ({len(pets)} pet)", color=0xFEE3F5)
    for i, p in enumerate(pets, start=1):
        slot = f" [SLOT {p.get('slot')}]" if p.get("slot") else ""
        emoji = "🌟" if p.get("rarity") in ["Thần Thoại","Đấng Cứu Thế"] else "✨" if p.get("rarity") in ["Sử Thi","Bán Thần Thoại"] else ""
        
        skills = p['skill']
        if p.get('extra_skill_1'): skills += f", {p['extra_skill_1']}"
        if p.get('extra_skill_2'): skills += f", {p['extra_skill_2']}"
        
        exp_to_next = pet_exp_for_level(p['level'])
        
        embed.add_field(
            name=f"#{i} {p['name']}{slot}", 
            value=f"{emoji}{p['rarity']} | Lv {p['level']} (EXP: {p.get('exp', 0)}/{exp_to_next}) | {p['element']} | Skills: {skills}", 
            inline=False
        )
        
    embed.set_footer(text="Dùng !bteam add/remove <số thứ tự> để chỉnh đội hình.")
    await ctx.send(embed=embed)
      # ----------------- CÁC LỆNH BATTLE & TEAM -----------------

## LỆNH BTEAM (Quản lý đội pet 3v3)
@bot.group(name="bteam", aliases=["team"], invoke_without_command=True)
async def bteam_group(ctx):
    user = get_user(ctx.author.id)
    pets_in_team = sorted([p for p in user.get("pets", []) if p.get("slot", 0) > 0], key=lambda x: x['slot'])
    
    team_display = []
    for i in range(1, 4):
        pet = next((p for p in pets_in_team if p['slot'] == i), None)
        if pet:
            team_display.append(f"SLOT {i}: **{pet['name']}** (Lv {pet['level']})")
        else:
            team_display.append(f"SLOT {i}: (Trống)")
            
    await ctx.send(f"🦴 **Đội hình hiện tại:**\n" + "\n".join(team_display) + "\n\nDùng: `!bteam add <stt pet> <slot>` hoặc `!bteam remove <slot>`")

@bteam_group.command(name="add")
async def bteam_add(ctx, pet_index: int = None, slot: int = None):
    if pet_index is None or slot is None or slot not in [1, 2, 3]:
        return await ctx.send("❌ Cú pháp: `!bteam add <số thứ tự pet> <slot (1-3)>`. (Xem stt pet bằng !bzoo)")
        
    user = get_user(ctx.author.id)
    pets = user.get("pets", [])
    
    if not (1 <= pet_index <= len(pets)):
        return await ctx.send("❌ Số thứ tự pet không hợp lệ.")
        
    pet_to_add = pets[pet_index - 1]
    
    for p in pets:
        if p.get("slot") == slot:
            p["slot"] = 0
        if p.get("slot") == pet_to_add.get("slot"):
            p["slot"] = 0
            
    pet_to_add["slot"] = slot
    save_data(users)
    await ctx.send(f"✅ Đã thêm **{pet_to_add['name']}** (Lv {pet_to_add['level']}) vào **SLOT {slot}**.")

@bteam_group.command(name="remove")
async def bteam_remove(ctx, slot: int = None):
    if slot is None or slot not in [1, 2, 3]:
        return await ctx.send("❌ Cú pháp: `!bteam remove <slot (1-3)>`.")
        
    user = get_user(ctx.author.id)
    pets = user.get("pets", [])
    
    pet_removed = None
    for p in pets:
        if p.get("slot") == slot:
            p["slot"] = 0
            pet_removed = p["name"]
            break
            
    save_data(users)
    if pet_removed:
        await ctx.send(f"✅ Đã gỡ **{pet_removed}** khỏi **SLOT {slot}**.")
    else:
        await ctx.send(f"❌ SLOT {slot} đã trống.")

## LỆNH BBATTLE (3v3, pet người thắng nhận EXP)
@bot.command(name="bbattle", aliases=["b"])
async def bbattle_cmd(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ Không thể chiến với chính mình.")
        
    u1 = get_user(ctx.author.id); u2 = get_user(member.id)
    team1 = sorted([p for p in u1.get("pets",[]) if p.get("slot",0)>0], key=lambda x: x.get("slot"))[:3]
    team2 = sorted([p for p in u2.get("pets",[]) if p.get("slot",0)>0], key=lambda x: x.get("slot"))[:3]
    
    if len(team1)!=3 or len(team2)!=3:
        return await ctx.send("❌ Cả hai cần đủ 3 pet trong đội (dùng !bteam add).")
        
    power1 = sum(pet_power(p) for p in team1)
    power2 = sum(pet_power(p) for p in team2)
    
    WIN = 300; LOSE = -100
    
    if power1 > power2:
        winner_id = ctx.author.id
        winner_team = team1
        res = f"🎉 **Bạn thắng!** Nhận {WIN} xu."
        color = 0x00ff00
    elif power2 > power1:
        winner_id = member.id
        winner_team = team2
        res = f"💔 Đội đối thủ mạnh hơn. Bạn bị trừ {abs(LOSE)} xu."
        color = 0xff0000
    else:
        res = "🤝 Hòa! Không ai đổi xu và không pet nào lên cấp."
        color = 0xffff00
        winner_id = None
        winner_team = []
    
    if winner_id == ctx.author.id:
        update_balance(ctx.author.id, WIN)
        update_balance(member.id, LOSE)
    elif winner_id == member.id:
        update_balance(ctx.author.id, LOSE)
        update_balance(member.id, WIN)
        
    # --- LOGIC PET CỘNG EXP CHO NGƯỜI THẮNG ---
    exp_gain_msg = ""
    if winner_id:
        winner_user_data = get_user(winner_id)
        
        for pet_in_team in winner_team:
            original_pet = next((p for p in winner_user_data["pets"] if p.get("slot") == pet_in_team.get("slot")), None)
            
            if original_pet:
                exp_gained = random.randint(50, 150)
                level_up_messages = add_pet_exp(original_pet, exp_gained)
                
                exp_gain_msg += f"\n🏆 Pet **{original_pet['name']}** nhận **{exp_gained} EXP**!"
                if level_up_messages:
                    exp_gain_msg += " " + " ".join(level_up_messages)
        
        save_data(users) 
    
    em = discord.Embed(title="⚔️ Kết quả chiến trận Pet", description=res, color=color)
    em.add_field(name=ctx.author.display_name, value=f"Sức mạnh: **{int(power1)}**", inline=True)
    em.add_field(name=member.display_name, value=f"Sức mạnh: **{int(power2)}**", inline=True)
    
    if exp_gain_msg:
        em.add_field(name="✨ Pet Nhận EXP", value=exp_gain_msg, inline=False)
        
    await ctx.send(embed=em)

## LỆNH BPVP (Thách đấu 1v1 cược xu)
@bot.command(name="bpvp", aliases=["pvp"])
async def bpvp_cmd(ctx, member: discord.Member, amount: int):
    if member.id == ctx.author.id:
        return await ctx.send("❌ Không thể thách đấu chính mình.")
        
    if amount <= 0:
        return await ctx.send("❌ Số xu cược phải lớn hơn 0.")
        
    if get_balance(ctx.author.id) < amount or get_balance(member.id) < amount:
        return await ctx.send("❌ Một trong hai người không đủ xu để cược.")
        
    u1 = get_user(ctx.author.id); u2 = get_user(member.id)
    
    pet1 = next((p for p in u1.get("pets",[]) if p.get("slot",0)==1), None)
    pet2 = next((p for p in u2.get("pets",[]) if p.get("slot",0)==1), None)
    
    if not pet1 or not pet2:
        return await ctx.send("❌ Cả hai cần có pet ở **SLOT 1** trong đội hình (dùng !bteam add).")
        
    power1 = pet_power(pet1)
    power2 = pet_power(pet2)
    
    if power1 > power2:
        winner_id = ctx.author.id
        winner_name = ctx.author.display_name
        color = 0x00ff00
    elif power2 > power1:
        winner_id = member.id
        winner_name = member.display_name
        color = 0xff0000
    else:
        await ctx.send("🤝 Hòa! Không ai mất xu.")
        return
        
    if winner_id == ctx.author.id:
        update_balance(ctx.author.id, amount)
        update_balance(member.id, -amount)
    else:
        update_balance(ctx.author.id, -amount)
        update_balance(member.id, amount)
        
    embed = discord.Embed(title="⚔️ Kết quả Thách Đấu Pet", color=color)
    embed.add_field(name=f"{ctx.author.display_name} (Pet: {pet1['name']})", value=f"Sức mạnh: **{int(power1)}**", inline=True)
    embed.add_field(name=f"{member.display_name} (Pet: {pet2['name']})", value=f"Sức mạnh: **{int(power2)}**", inline=True)
    embed.set_footer(text=f"Người thắng: {winner_name} nhận {amount} xu.")
    
    await ctx.send(embed=embed)
      # ----------------- CÁC LỆNH UTILITY & EVENTS -----------------

@bot.event
async def on_ready():
    print(f'🤖 Bot đã sẵn sàng! Đăng nhập dưới tên: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    await bot.change_presence(activity=discord.Game(name="!bhelp | Pet System"))

@bot.event
async def on_message(message):
    if message.author.bot or not message.content:
        return
        
    content = message.content.lower()
    is_command = content.startswith('!') or (content.startswith('b') and len(content) > 1 and not content.startswith('b '))
    
    if content.startswith('b') and len(content) > 1 and not content.startswith('b '):
        message.content = '!' + message.content[1:]
    
    try:
        if is_command and message.channel.guild:
            ctx = await bot.get_context(message)
            if not content.startswith('!btts'):
                add_exp(message.author.id, 1, ctx=ctx) 
            
        user = get_user(message.author.id)
        if not is_command:
            gain = random.randint(1, 3)
            user["coin"] = user.get("coin", 0) + gain
            
        save_data(users)
    except Exception:
        pass
        
    await bot.process_commands(message)

## LỆNH HELP
bot.remove_command("help")
@bot.command(name="bhelp", aliases=["help","commands"])
async def help_cmd(ctx):
    txt = (
        "📚 **Danh sách lệnh** (sử dụng tiền tố `!` hoặc `b`)\n"
        "**[CƠ BẢN]**\n"
        "`bdaily` — nhận thưởng hàng ngày (có Rương Đá Thần)\n"
        "`bbal` — xem số dư\n"
        "`bgacha` — mở hòm (500 xu)\n"
        "`bprofile` — xem hồ sơ cá nhân (cấp độ/buff/pet/xu)\n"
        "`brank / !brank level` — bảng xếp hạng (xu/cấp độ)\n"
        "**[PET & ITEM]**\n"
        "`bhunt` — đi săn pet (cooldown 60s, áp dụng Đá Buff)\n"
        "`bzoo` — xem pet (hiển thị EXP/Level)\n"
        "`bshop / bbuy` — cửa hàng (có Thức ăn)\n"
        "`binv` — xem đồ\n"
        "`buse <món>` — sử dụng đồ (Thức ăn cộng EXP pet, Rương mở ra Đá Buff)\n"
        "`bteam` — quản lý đội pet\n"
        "**[CHIẾN ĐẤU & KHÁC]**\n"
        "`bbattle @người` — đấu pet 3v3 (người thắng pet nhận EXP)\n"
        "`bpvp @người <xu>` — thách đấu 1v1 cược xu\n"
        "`bbj <xu>` — chơi blackjack\n"
        "`bs <text>` — bot đọc giọng (trong voice channel)\n"
    )
    await ctx.send(txt)

## LỆNH PROFILE 
@bot.command(name="bprofile", aliases=["profile"])
async def bprofile_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = get_user(member.id)
    
    pets_in_team = [p for p in data.get("pets", []) if p.get("slot", 0) > 0]
    pets_display = ", ".join([f"SLOT {p['slot']}: {p['name']}" for p in sorted(pets_in_team, key=lambda x: x['slot'])]) or "Không có pet trong đội"
    
    current_level = data.get('level', 1)
    current_exp = data.get('exp', 0)
    exp_to_next = exp_for_level(current_level)
    
    active_buffs = []
    current_time = int(time.time())
    
    for buff_type, buff_data in list(data.get("buffs", {}).items()):
        if buff_data["end_time"] > current_time:
            time_left = buff_data["end_time"] - current_time
            time_str = f"{time_left // 60}m {time_left % 60}s"
            active_buffs.append(f"• {buff_data['name']} (còn {time_str})")
        else:
            del data["buffs"][buff_type] 
            save_data(users) 

    buffs_display = "\n".join(active_buffs) if active_buffs else "Không có buff nào."

    embed = discord.Embed(title=f"👤 Hồ sơ {member.display_name}", color=0x88ccff)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="✨ Cấp Độ Người Chơi", 
                    value=f"**Lv {current_level}** | EXP: {current_exp}/{exp_to_next}", 
                    inline=False)
    embed.add_field(name="🔮 Buffs đang hoạt động", value=buffs_display, inline=False)
    embed.add_field(name="💰 Tiền", value=f"**{data.get('coin',0):,}** xu", inline=False)
    embed.add_field(name="🐾 Đội Pet (3v3)", value=pets_display, inline=False)
    embed.add_field(name="🎒 Tổng Đồ", value=f"**{len(data.get('inventory',[]))}** món", inline=True)
    embed.add_field(name="🦴 Tổng Pet", value=f"**{len(data.get('pets',[]))}** con", inline=True)
    
    await ctx.send(embed=embed)

## LỆNH RANK (Xếp hạng Coin và Level)
@bot.group(name="brank", aliases=["rank"], invoke_without_command=True)
async def brank_group(ctx):
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("coin",0), reverse=True)
    lines = []
    
    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        try:
            u = await bot.fetch_user(int(uid))
            name = u.display_name.replace('`', '')
        except:
            name = f"User-{uid}"
        lines.append(f"**{i}.** {name} — **{data.get('coin',0):,}** xu")
    
    embed = discord.Embed(
        title="🏆 Top 10 người có nhiều xu nhất",
        description="\n".join(lines) if lines else "Chưa có ai trong bảng xếp hạng.",
        color=0xffd700
    )
    embed.set_footer(text="Dùng !brank level để xem BXH cấp độ.")
    await ctx.send(embed=embed)
    
@brank_group.command(name="level")
async def brank_level_cmd(ctx):
    sorted_users = sorted(users.items(), key=lambda x: (x[1].get("level",1), x[1].get("exp",0)), reverse=True)
    lines = []
    
    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        try:
            u = await bot.fetch_user(int(uid))
            name = u.display_name.replace('`', '')
        except:
            name = f"User-{uid}"
        lines.append(f"**{i}.** {name} — **Lv {data.get('level',1)}** ({data.get('exp',0)} EXP)")
    
    embed = discord.Embed(
        title="✨ Top 10 người có cấp độ cao nhất",
        description="\n".join(lines) if lines else "Chưa có ai trong bảng xếp hạng.",
        color=0x40E0D0
    )
    await ctx.send(embed=embed)

## LỆNH BLACKJACK
@bot.command(name="bbj", aliases=["bj"])
async def bbj_cmd(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Số xu cược phải lớn hơn 0.")
        
    uid = ctx.author.id
    if get_balance(uid) < amount:
        return await ctx.send("❌ Bạn không đủ xu để cược.")
        
    def deal_card():
        return random.randint(1, 11)
        
    def calculate_score(cards):
        score = sum(cards)
        while score > 21 and 11 in cards:
            cards[cards.index(11)] = 1
            score = sum(cards)
        return score
        
    player_cards = [deal_card(), deal_card()]
    dealer_cards = [deal_card(), deal_card()]
    
    player_score = calculate_score(player_cards)
    dealer_score = calculate_score(dealer_cards)

    await ctx.send(f"🃏 **BLACKJACK!** (Cược: {amount:,} xu)\n"
                   f"**Bạn** có: {player_cards} (Tổng: {player_score})\n"
                   f"**Dealer** có: [{dealer_cards[0]}, ?]")

    if player_score == 21:
        if dealer_score == 21:
            await ctx.send("🤝 Cả hai Blackjack! Hòa, hoàn lại xu.")
            return
        else:
            update_balance(uid, amount * 1.5)
            await ctx.send(f"👑 **BLACKJACK!** Bạn thắng {int(amount * 1.5):,} xu!")
            return

    if dealer_score == 21:
        update_balance(uid, -amount)
        await ctx.send(f"💔 Dealer Blackjack! Bạn mất {amount:,} xu.")
        return

    while player_score < 21:
        await ctx.send("Chọn **hit** (rút thêm) hay **stand** (dừng)? Gõ `hit` hoặc `stand`.")
        
        try:
            msg = await bot.wait_for('message', timeout=30.0, check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['hit', 'stand'])
        except asyncio.TimeoutError:
            await ctx.send("⏰ Hết giờ! Tự động chọn stand.")
            break
            
        if msg.content.lower() == 'hit':
            new_card = deal_card()
            player_cards.append(new_card)
            player_score = calculate_score(player_cards)
            await ctx.send(f"➕ Bạn rút: {new_card}. Tổng điểm: {player_cards} (Tổng: {player_score})")
            if player_score > 21:
                break
        elif msg.content.lower() == 'stand':
            break

    if player_score > 21:
        update_balance(uid, -amount)
        return await ctx.send(f"💥 **BUST!** Bạn vượt quá 21. Bạn mất {amount:,} xu.")
        
    await ctx.send(f"\nDealer lật bài: {dealer_cards} (Tổng: {dealer_score})")
    while dealer_score < 17:
        await asyncio.sleep(1)
        new_card = deal_card()
        dealer_cards.append(new_card)
        dealer_score = calculate_score(dealer_cards)
        await ctx.send(f"➕ Dealer rút: {new_card}. Tổng điểm: {dealer_cards} (Tổng: {dealer_score})")
        
    if dealer_score > 21:
        update_balance(uid, amount)
        return await ctx.send(f"🎉 Dealer **BUST!** Bạn thắng {amount:,} xu.")

    if player_score > dealer_score:
        update_balance(uid, amount)
        await ctx.send(f"🎉 Bạn ({player_score}) thắng Dealer ({dealer_score})! Bạn thắng {amount:,} xu.")
    elif dealer_score > player_score:
        update_balance(uid, -amount)
        await ctx.send(f"💔 Dealer ({dealer_score}) thắng Bạn ({player_score})! Bạn mất {amount:,} xu.")
    else:
        await ctx.send("🤝 Hòa! Hoàn lại xu.")

## LỆNH TTS (Text-to-Speech)
@bot.command(name="btts", aliases=["s"])
async def tts_cmd(ctx, *, text: str):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("❌ Bạn phải ở trong kênh thoại để bot có thể nói.")

    if ctx.voice_client and ctx.voice_client.is_connected():
        vc = ctx.voice_client
    else:
        vc = await ctx.author.voice.channel.connect()

    if vc.is_playing():
        vc.stop()

    try:
        tts = gTTS(text=text, lang='vi', slow=False)
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
            tts.save(fp.name)
            temp_file_path = fp.name

        vc.play(discord.FFmpegPCMAudio(source=temp_file_path), 
                after=lambda e: os.remove(temp_file_path) if os.path.exists(temp_file_path) else None)
        
        await ctx.send(f"🔊 Bot đang nói: `{text}`")
        
    except Exception as e:
        await ctx.send(f"❌ Có lỗi xảy ra khi tạo/phát âm thanh: {e}")
        if ctx.voice_client and ctx.voice_client.is_connected():
             await ctx.voice_client.disconnect()
  # ----------------- CHẠY BOT -----------------
if __name__ == "__main__":
    if not TOKEN:
        print("🚨 Lỗi: Vui lòng cấu hình biến môi trường DISCORD_TOKEN trên Railway.")
    else:
        try:
            # Đảm bảo bạn đã kích hoạt tất cả Intents cần thiết trong Discord Developer Portal
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print("🚨 Lỗi: Token Discord không hợp lệ. Vui lòng kiểm tra lại token của bạn.")
        except Exception as e:
            print(f"🚨 Lỗi không xác định: {e}")
