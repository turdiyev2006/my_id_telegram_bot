import os
import csv
import time
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, Defaults
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# .env faylni yuklash
load_dotenv()

# Muhitdan token va admin ID ni olish
TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

# Foydalanuvchi oxirgi marta /start yozgan vaqt
last_used = {}

# Log faylga yozish
def log_user(user):
    with open("log.csv", mode="a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now(), user.id, user.full_name, user.username])

# Tilga qarab salomlashish
def get_greeting(lang_code):
    return {
        'uz': "Salom",
        'ru': "Привет"
    }.get(lang_code, "Hello")

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Anti-spam (60 sekund kutish)
    if user_id in last_used and time.time() - last_used[user_id] < 60:
        await update.message.reply_text("⏱️ Iltimos, keyinroq yana urinib ko‘ring.")
        return
    last_used[user_id] = time.time()

    # Salomlashish
    greeting = get_greeting(user.language_code)
    text = (
        f"{greeting}, {user.first_name}!\n\n"
        f"🆔 Sizning Telegram ID: {user.id}\n"
        f"👤 Username: @{user.username if user.username else 'yo‘q'}\n"
        f"📛 Ism: {user.full_name}\n"
        f"🌐 Til: {user.language_code}"
    )

    # Inline tugma
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 ID ni nusxalash", callback_data="copy_id")]
    ])

    await update.message.reply_text(text, reply_markup=keyboard)

    # Admin loglash
    if user.id != ADMIN_ID:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 Yangi foydalanuvchi:\n{text}")
        log_user(user)

# Inline tugmaga javob
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "copy_id":
        user_id = query.from_user.id
        await query.message.reply_text(f"📋 Sizning ID: {user_id}")

# /help komandasi
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bu bot sizning Telegram ID, ism, username va tilingizni ko‘rsatadi.\n"
        "Foydalanish uchun /start buyrug‘ini yuboring."
    )

# /users komandasi (faqat admin uchun)
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        with open("log.csv", encoding="utf-8") as f:
            lines = f.readlines()[-20:]
        await update.message.reply_text("🗂 Oxirgi foydalanuvchilar:\n" + ''.join(lines))
    except FileNotFoundError:
        await update.message.reply_text("❌ Log fayli topilmadi.")

# /stats komandasi (admin uchun)
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        with open("log.csv", encoding="utf-8") as f:
            user_count = len(f.readlines())
        await update.message.reply_text(f"📊 Jami foydalanuvchilar soni: {user_count}")
    except FileNotFoundError:
        await update.message.reply_text("❌ Hali hech kim botdan foydalanmagan.")

# Botni ishga tushirish
if __name__ == "__main__":
    app = ApplicationBuilder()\
        .token(TOKEN)\
        .defaults(Defaults(tzinfo=pytz.timezone("Asia/Tashkent"))).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()
