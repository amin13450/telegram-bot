import telebot
from telebot import types
import sqlite3
from datetime import datetime

TOKEN = "8607140908:AAHfRPmlis2iDSnxVlZx25iOi8djkDAEaiw"
bot = telebot.TeleBot(TOKEN)

# ==================== ডাটাবেস ====================
conn = sqlite3.connect('reward_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    referral_balance REAL DEFAULT 0,
    joined_channels INTEGER DEFAULT 0,
    subscribed_youtube INTEGER DEFAULT 0,
    verified INTEGER DEFAULT 0,
    referral_link TEXT,
    referred_by INTEGER,
    referral_count INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    method TEXT,
    account TEXT,
    status TEXT DEFAULT 'pending',
    timestamp TEXT
)
''')
conn.commit()

CHANNELS = [
    "https://t.me/monny33i8",
    "https://t.me/monnjhh",
    "https://t.me/monny1233",
    "https://t.me/monny1222i88",
    "https://t.me/monny12388"
]

YOUTUBE_LINK = "https://www.youtube.com/@incomehub-v6s"

# ==================== হেল্পার ফাংশন ====================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def create_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, referral_link) VALUES (?, ?, ?)", 
                  (user_id, username, f"https://t.me/{bot.get_me().username}?start={user_id}"))
    conn.commit()

def add_referral_bonus(referrer_id):
    if referrer_id:
        cursor.execute("UPDATE users SET balance = balance + 10, referral_balance = referral_balance + 10, referral_count = referral_count + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()

# ==================== মেইন মেনু কীবোর্ড ====================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("💰 Balance"), 
               types.KeyboardButton("👥 Refer"))
    markup.add(types.KeyboardButton("💸 উত্তোলন"))
    return markup

# ==================== স্টার্ট ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    create_user(user_id, username)

    user = get_user(user_id)

    # Referral handling
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id and user and user[8] is None:  # referred_by is None
                cursor.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referrer_id, user_id))
                conn.commit()
        except:
            pass

    # যদি ইতিমধ্যে ভেরিফাইড হয়ে থাকে
    if user and user[6] == 1:  # verified == 1
        bot.send_message(message.chat.id, "✅ আপনি ইতিমধ্যে ভেরিফাইড।\n\nওয়েলকাম ব্যাক!", 
                         parse_mode='Markdown', reply_markup=main_keyboard())
        main_menu(message.chat.id)  # Optional: inline menu
        return

    # প্রথমবার হলে টাস্ক দেখাবে
    bot.send_message(message.chat.id, 
                     "🎁 **Earn Instant Rewards Here** 🎁\n\n"
                     "💰 Joining Bonus: 20 TK\n👥 Referral Bonus: 10 TK Per Referral",
                     parse_mode='Markdown',
                     reply_markup=main_keyboard())

    show_channel_tasks(message.chat.id, user_id)

# ==================== চ্যানেল টাস্ক ====================
def show_channel_tasks(chat_id, user_id):
    text = "📢 **Complete All Mandatory Tasks Below:**\n\n"
    for i, ch in enumerate(CHANNELS, 1):
        text += f"{i}️⃣ Join Telegram Channel\n{ch}\n\n"
    text += "⚠️ User must join ALL channels before continuing."

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✅ Verify Channels", callback_data="verify_channels"))
    markup.add(types.InlineKeyboardButton("➡️ Continue", callback_data="continue_channels"))
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True)

# ==================== কলব্যাক হ্যান্ডলার ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if data == "verify_channels":
        cursor.execute("UPDATE users SET joined_channels = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        bot.answer_callback_query(call.id, "✅ Channels Verified!")
        show_youtube_task(call.message.chat.id, user_id)

    elif data == "continue_channels":
        user = get_user(user_id)
        if user and user[4] == 1:
            show_youtube_task(call.message.chat.id, user_id)
        else:
            bot.answer_callback_query(call.id, "❌ Please join all channels first!", show_alert=True)

    elif data == "verify_youtube":
        cursor.execute("UPDATE users SET subscribed_youtube = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        finalize_verification(call.message.chat.id, user_id)

    elif data in ["balance", "refer", "withdraw"]:
        if data == "balance":
            show_balance(call.message.chat.id, user_id)
        elif data == "refer":
            show_refer(call.message.chat.id, user_id)
        elif data == "withdraw":
            show_withdraw(call.message.chat.id, user_id)

# ==================== টেক্সট মেনু হ্যান্ডলার ====================
@bot.message_handler(content_types=['text'])
def handle_menu(message):
    text = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id

    if text == "💰 Balance":
        show_balance(chat_id, user_id)
    elif text == "👥 Refer":
        show_refer(chat_id, user_id)
    elif text == "💸 উত্তোলন":
        show_withdraw(chat_id, user_id)

# ==================== ইউটিউব + ফাইনাল ভেরিফিকেশন ====================
def show_youtube_task(chat_id, user_id):
    text = f"📺 **YouTube Subscription Step**\n\nSubscribe to our YouTube Channel:\n{YOUTUBE_LINK}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("✅ I Subscribed", callback_data="verify_youtube"))
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True)

def finalize_verification(chat_id, user_id):
    user = get_user(user_id)
    if user and user[6] == 1:  # Already verified
        bot.send_message(chat_id, "✅ আপনি ইতিমধ্যে ভেরিফাইড!", reply_markup=main_keyboard())
        return

    referrer_id = user[8] if user else None

    cursor.execute("UPDATE users SET verified = 1, balance = balance + 20 WHERE user_id = ?", (user_id,))
    conn.commit()

    if referrer_id:
        add_referral_bonus(referrer_id)

    bot.send_message(chat_id, "✅ **Verification Successful**\n\n🎁 You received 20 TK Joining Bonus.\n💰 Current Balance: 20 TK\n\nWelcome to our rewards program.", 
                     parse_mode='Markdown', reply_markup=main_keyboard())

def show_balance(chat_id, user_id):
    user = get_user(user_id)
    if user:
        text = f"💰 **Current Balance:** {user[2]} TK\n\n🎁 Joining Bonus: 20 TK\n👥 Referral Earnings: {user[3]} TK\n👥 Total Referrals: {user[9]}"
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=main_keyboard())

def show_refer(chat_id, user_id):
    user = get_user(user_id)
    ref_link = user[7] if user else ""
    text = f"👥 **Refer & Earn**\n\nInvite your friends and earn 10 TK for every successful referral.\n\n🔗 **Your Referral Link:**\n`{ref_link}`\n\n👥 Total Referrals: {user[9] if user else 0}\n💸 Referral Reward: 10 TK Per Successful Referral"
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=main_keyboard())

def show_withdraw(chat_id, user_id):
    user = get_user(user_id)
    if not user or user[2] < 50:
        bot.send_message(chat_id, "❌ Minimum withdrawal amount is 50 TK.", reply_markup=main_keyboard())
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📱 bKash", callback_data="withdraw_bKash"))
    markup.add(types.InlineKeyboardButton("📱 Nagad", callback_data="withdraw_Nagad"))
    markup.add(types.InlineKeyboardButton("📱 Rocket", callback_data="withdraw_Rocket"))
    bot.send_message(chat_id, "💸 **Select Payment Method**", reply_markup=markup)

# Withdraw Logic (আগের মতোই)
@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def withdraw_method(call):
    method = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, f"📱 Enter your {method} Account Number:")
    bot.register_next_step_handler(msg, process_account, method)

def process_account(message, method):
    account = message.text
    msg = bot.send_message(message.chat.id, "💰 Enter Withdrawal Amount (Minimum 50 TK):")
    bot.register_next_step_handler(msg, process_amount, method, account)

def process_amount(message, method, account):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        user = get_user(user_id)
        if amount < 50 or not user or user[2] < amount:
            bot.send_message(message.chat.id, "❌ Invalid amount or insufficient balance!", reply_markup=main_keyboard())
            return
        cursor.execute("INSERT INTO withdrawals (user_id, amount, method, account, timestamp) VALUES (?, ?, ?, ?, ?)",
                      (user_id, amount, method, account, datetime.now().isoformat()))
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ **Withdrawal Request Submitted Successfully**\n\n💰 Amount: {amount} TK\n📱 Method: {method}\n\n⏳ Payment will be processed within 72 hours to 5 days.", 
                         parse_mode='Markdown', reply_markup=main_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Invalid input!", reply_markup=main_keyboard())

# ==================== বট চালু ====================
print("✅ Bot is running...")
bot.infinity_polling()
